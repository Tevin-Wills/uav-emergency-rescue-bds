"""
run_all.py — ONE COMMAND that boots the entire integrated BDS-SMC2 stack:

    software ESP32  ->  BDS module emulator  ->  virtual portal  ->  GCS  ->  DASHBOARD
    (real $CCTXM)       (T2/T3 + latency)        (portal records)   (decode) (live web UI)

It runs a continuous transmission feeder (the virtual BeiDou link) AND launches the
existing tx_dashboard.py pointed at the sim data, so you watch every message climb
node -> satellite -> portal in the browser, live. This is the top of the stack: the
"BDS dashboard".

    python sim/run_all.py                 # live demo @ http://localhost:8765
    python sim/run_all.py --interval 6    # a transmission every 6 s
    python sim/run_all.py --drop-rate 0.1 # model 10% delivery loss (shows TIMEOUTs)
    python sim/run_all.py --no-browser    # don't auto-open the browser

Ctrl+C stops the feeder and the dashboard. After it runs, gcs/output/map.html and
gcs/output/survivor.waypoints are also refreshed by `python gcs/main.py --source sim`.
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "python"))

from bds_module_emulator import BdsModuleEmulator, build_cctxm_binary
from virtual_portal import PortalStore
from decode_binary import encode_binary
from coords import load_survivors

DATA_DIR = os.path.join(HERE, "..", "data")
SIM_LAT = os.path.join(DATA_DIR, "sim_latency.csv")
LIVE_JSON = os.path.join(DATA_DIR, "live_state.json")
DASHBOARD = os.path.join(HERE, "..", "python", "tx_dashboard.py")

LAT_COLS = ["tx_num", "session", "weather", "cloud_pct", "datetime", "t1", "t2", "t3",
            "tx_latency_ms", "decode_latency_ms", "total_latency_ms", "payload", "note"]


def _append_latency(row):
    new = not os.path.exists(SIM_LAT)
    with open(SIM_LAT, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(LAT_COLS)
        w.writerow(row)


def _write_live(obj):
    obj["updated"] = time.time()
    with open(LIVE_JSON, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def _clear_live():
    _write_live({"state": "idle"})


def _transmit_one(emu, store, survivor, tx_num, stop):
    """Send one survivor through the link. Returns True if stop was tripped mid-flight."""
    lat, lon, alt, r_cm, pri, sid = survivor
    hex28 = encode_binary(lat, lon, alt, r_cm, pri, sid)
    frame = build_cctxm_binary(hex28)
    t1 = time.time()
    out = emu.handle_command(frame)

    # publish in-flight state (dashboard live row: T1 + T2 lit, climbing to satellite)
    _write_live({"state": "in_flight", "tx_num": tx_num, "session": "sim-live",
                 "t1": True, "t2": True, "t3": False, "payload": frame.strip()})
    if stop.wait(out["latency_s"]):
        return True

    if out["delivered"]:
        store.post(out["record"])
        t3_val = int((t1 + out["latency_s"]) * 1000)
        total = int(out["latency_s"] * 1000)
        note = ""
    else:
        t3_val = ""           # TIMEOUT in the dashboard
        total = "-1"
        note = "modelled delivery loss"
    _append_latency([
        tx_num, "sim-live", "n/a", "", datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        int(t1 * 1000), int(t1 * 1000) + 300, t3_val,
        int(out["latency_s"] * 1000), "", total, f"$CCTXM,0,BIN:{hex28}", note])
    _clear_live()
    print(f"[TX] #{tx_num} T{sid:03d}  {lat:.7f},{lon:.7f}  "
          f"{'DELIVERED' if out['delivered'] else 'LOST'}  {out['latency_s']:.2f}s")
    return False


def _fresh_start(store):
    for p in (SIM_LAT, store.path, LIVE_JSON):
        if os.path.exists(p):
            os.remove(p)


def feeder(interval, drop_rate, seed, stop):
    """Demo mode: continuously cycle the CSV survivors, one TX per `interval` seconds."""
    emu = BdsModuleEmulator(drop_rate=drop_rate, seed=seed)
    store = PortalStore()
    survivors, src = load_survivors()
    print(f"[FEED] input: {src}")
    _fresh_start(store)

    i = 0
    while not stop.is_set():
        if _transmit_one(emu, store, survivors[i % len(survivors)], i + 1, stop):
            break
        i += 1
        if stop.wait(max(0.0, interval - 0)):
            break
    _clear_live()


def watch_feeder(poll, drop_rate, seed, stop):
    """Event-driven mode: watch data/outgoing_coords.csv and transmit each NEW row
    as Objective 4 appends it. This is the 'Objective 4 output -> node transmits'
    integration: the CSV is the injection interface between position (RTK) and BDS."""
    emu = BdsModuleEmulator(drop_rate=drop_rate, seed=seed)
    store = PortalStore()
    _fresh_start(store)
    print("[WATCH] node armed — waiting for Objective 4 to write coordinates to "
          "data/outgoing_coords.csv (Ctrl+C to stop)")

    sent = 0
    while not stop.is_set():
        survivors, _ = load_survivors(fallback=False)
        if len(survivors) > sent:
            new = survivors[sent:]
            print(f"[WATCH] Objective 4 produced {len(new)} new coordinate(s) -> transmitting")
            for s in new:
                if stop.is_set():
                    break
                _transmit_one(emu, store, s, sent + 1, stop)
                sent += 1
        else:
            _clear_live()
        if stop.wait(poll):
            break
    _clear_live()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--watch", action="store_true",
                    help="event-driven: watch data/outgoing_coords.csv and transmit each new "
                         "row as Objective 4 produces it (the injection interface)")
    ap.add_argument("--poll", type=float, default=1.0, help="watch poll interval (s)")
    ap.add_argument("--interval", type=float, default=10.0,
                    help="demo mode: seconds between transmissions (ignored with --watch)")
    ap.add_argument("--drop-rate", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()

    print("=" * 70)
    print(" BDS-SMC2 — full stack: emulator -> portal -> GCS -> dashboard")
    print(f" mode: {'WATCH (Objective 4 -> node)' if a.watch else 'DEMO (cycle CSV)'}")
    print("=" * 70)

    # launch the dashboard (reads the sim files the feeder writes)
    dash = subprocess.Popen([sys.executable, DASHBOARD, "--sim-data", "--port", str(a.port)])
    url = f"http://localhost:{a.port}"
    time.sleep(1.0)
    if not a.no_browser:
        webbrowser.open(url)
    print(f"[RUN] dashboard: {url}   (Ctrl+C to stop everything)")

    stop = threading.Event()
    if a.watch:
        t = threading.Thread(target=watch_feeder,
                             args=(a.poll, a.drop_rate, a.seed, stop), daemon=True)
    else:
        t = threading.Thread(target=feeder,
                             args=(a.interval, a.drop_rate, a.seed, stop), daemon=True)
    t.start()
    try:
        while t.is_alive():
            t.join(0.5)
    except KeyboardInterrupt:
        print("\n[RUN] stopping…")
    finally:
        stop.set()
        dash.terminate()
        # refresh the static GCS artifacts from whatever the portal collected
        try:
            subprocess.run([sys.executable, os.path.join(HERE, "..", "gcs", "main.py"),
                            "--source", "sim"], timeout=20)
        except Exception:
            pass
    print("[RUN] done.")


if __name__ == "__main__":
    main()
