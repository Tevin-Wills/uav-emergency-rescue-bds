"""
run_sim.py — ONE-COMMAND end-to-end demonstration of the BDS-SMC2 rescue chain
with the satellite uplink replaced by the software module emulator.

Pipeline (the "virtual BeiDou link"):

   software ESP32 sender  -->  BDS module emulator  -->  virtual portal store
   (real $CCTXM encode)       (T2 ack, modelled T3        (portal record)
                               delivery + latency)               |
                                                                 v
                                   GCS:  portal read -> decode -> map -> waypoint

Everything except the RF hop is the project's real code: the firmware's exact frame
+ checksum, decode_binary.py, and the gcs/ pipeline. Run it, then open the printed
map.html and survivor.waypoints.

    python sim/run_sim.py                # 6 survivors (lab T001-T006), instant
    python sim/run_sim.py --n 3 --realtime   # 3, with real modelled latency waits
    python sim/run_sim.py --drop-rate 0.1    # model 10% delivery loss

This writes data/portal_inbox_sim.csv (portal records) and data/sim_latency.csv
(Gap-2-schema latency rows, source-tagged 'sim' so it is never confused with field data).
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime

# Windows consoles default to cp1252 and choke on the status glyphs / 汉字 below.
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
from gcs.decoder.detect import PRIORITY_LABEL
from gcs import main as gcs_main

DATA_DIR = os.path.join(HERE, "..", "data")
SIM_LATENCY_CSV = os.path.join(DATA_DIR, "sim_latency.csv")

LAT_COLS = ["tx_num", "session", "weather", "cloud_pct", "datetime", "t1", "t2", "t3",
            "tx_latency_ms", "decode_latency_ms", "total_latency_ms", "payload"]


def _log_latency(rows):
    new = not os.path.exists(SIM_LATENCY_CSV)
    with open(SIM_LATENCY_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(LAT_COLS + ["source"])
        for r in rows:
            w.writerow(r + ["sim"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=None,
                    help="number of transmissions (default: one per coordinate in the CSV)")
    ap.add_argument("--drop-rate", type=float, default=0.0, help="modelled delivery loss prob")
    ap.add_argument("--realtime", action="store_true", help="actually sleep the modelled latency")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    survivors, src = load_survivors()
    n = a.n if a.n is not None else len(survivors)

    print("=" * 72)
    print(" BDS-SMC2  —  end-to-end rescue chain  (RF uplink = software emulator)")
    print("=" * 72)
    print(f"[INPUT] {src}  ->  sending {n} transmission(s)")

    emu = BdsModuleEmulator(drop_rate=a.drop_rate, seed=a.seed)
    store = PortalStore()
    # fresh run: clear prior sim store AND latency log so outputs reflect only this run
    for p in (store.path, SIM_LATENCY_CSV):
        if os.path.exists(p):
            os.remove(p)

    lat_rows = []
    delivered = 0
    for i in range(n):
        lat, lon, alt, r_cm, pri, sid = survivors[i % len(survivors)]
        hex28 = encode_binary(lat, lon, alt, r_cm, pri, sid)
        frame = build_cctxm_binary(hex28)

        t1 = time.time()
        print(f"\n--- TX #{i+1}  (survivor T{sid:03d}, {PRIORITY_LABEL[pri]}) ---")
        print(f"[ESP32] {frame.strip()}")

        out = emu.handle_command(frame)
        # T2 (module ack)
        print(f"[MODULE] T2 {out['t2_reply'].decode().strip()}  (command accepted)")
        if a.realtime:
            time.sleep(out["latency_s"])
        # T3 (delivery)
        t3_line = out["t3_reply"].decode().strip()
        if out["delivered"]:
            delivered += 1
            print(f"[MODULE] T3 {t3_line}  (uplink {out['latency_s']:.2f}s)  ✅")
            store.post(out["record"])
            print(f"[PORTAL] record stored: {out['record']['msg_data']}  "
                  f"@ {out['record']['created_at']}")
        else:
            print(f"[MODULE] T3 {t3_line}  ❌ (modelled loss)")

        tx_ms = int(out["latency_s"] * 1000)
        lat_rows.append([i + 1, "sim", "n/a", "", datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         int(t1 * 1000), int(t1 * 1000) + 300, int(t1 * 1000) + tx_ms,
                         tx_ms, "", tx_ms, f"BIN:{hex28}"])

    _log_latency(lat_rows)

    print("\n" + "=" * 72)
    print(f" TRANSMISSION SUMMARY: {delivered}/{n} delivered "
          f"({100*delivered/n:.0f}%)  ·  latency rows -> data/sim_latency.csv")
    print("=" * 72)

    # ── hand off to the real GCS pipeline ──────────────────────────────────
    print("\n>>> GCS PIPELINE (portal read -> decode -> map -> waypoint)\n")
    gcs_main.run(source="sim")

    print("\nDone. Open the map.html above in a browser to see the survivors on the map.")


if __name__ == "__main__":
    main()
