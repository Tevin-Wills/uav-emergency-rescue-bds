"""
auto_sender.py — watch an outgoing-coordinates CSV and AUTO-transmit each new row
through the BDS-SMC node, with retry -> recycle -> red-flag handling.

Per coordinate:
  send -> success? done.
       -> timeout? retry once immediately (lap 2).
                   still timeout? recycle to the BACK of the queue as a fresh
                   send (after a short backoff) -- the others never wait.
  After --max-laps total laps without success -> permanent NEEDS ATTENTION flag
  on the dashboard (human intervention). survivor_id keeps duplicates collapsed.

Real mode:  opens the ESP32 serial port, sends "TX,lat,lon,alt,r,pri,id".
Mock mode:  simulates the ESP32 (no hardware). --mock also writes matching portal
            receipts to portal_inbox_mock.csv so the full loop shows CONFIRMED.

Watches:    data/outgoing_coords.csv   (header: lat,lon,alt,r_cm,priority,survivor_id)
Writes:     data/gap2_latency.csv (session='auto', + note)  ·  data/live_state.json
            data/portal_inbox_mock.csv (mock RX only)

Usage:
    python auto_sender.py --mock                       # no hardware
    python auto_sender.py --mock --mock-fail-sid 9     # force survivor 9 to fail (demo the flag)
    python auto_sender.py --port COM14                 # real ESP32
    python auto_sender.py --mock --max-laps 5 --backoff 4
"""

import argparse
import csv
import json
import os
import struct
import time
import random
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
COORDS_CSV = os.path.join(DATA, "outgoing_coords.csv")
OUT_CSV = os.path.join(DATA, "gap2_latency.csv")
LIVE = os.path.join(DATA, "live_state.json")
MOCK_PORTAL = os.path.join(DATA, "portal_inbox_mock.csv")

OUT_FIELDS = ["tx_num", "session", "weather", "cloud_pct", "datetime",
              "t1", "t2", "t3", "tx_latency_ms", "decode_latency_ms",
              "total_latency_ms", "payload", "note"]


def encode_payload(lat, lon, alt_m, r_cm, priority, survivor_id):
    packed = struct.pack(">iihHBB", round(lat * 1e7), round(lon * 1e7),
                         round(alt_m), int(r_cm), int(priority), int(survivor_id))
    return f"$CCTXM,0,BIN:{packed.hex().upper()}*4C"


def write_live(state):
    try:
        state["updated"] = time.time()
        with open(LIVE, "w") as f:
            json.dump(state, f)
    except Exception:
        pass


def append_mock_receipt(payload):
    new_file = not os.path.exists(MOCK_PORTAL)
    with open(MOCK_PORTAL, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["received_at_local", "row_json"])
        row = {"card_id": "15590673", "encode_type": False,
               "msg_data": payload, "created_at": datetime.now().isoformat()}
        w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    json.dumps(row, ensure_ascii=False)])


def append_row(tx_num, payload, t1, t2, t3, ok, note=""):
    new_file = not os.path.exists(OUT_CSV)
    with open(OUT_CSV, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        if new_file:
            w.writeheader()
        lat = (t3 - t1) if ok else -1
        w.writerow({
            "tx_num": tx_num, "session": "auto", "weather": "", "cloud_pct": "",
            "datetime": datetime.now().isoformat(),
            "t1": t1, "t2": t2 or "", "t3": t3 if ok else "",
            "tx_latency_ms": lat, "decode_latency_ms": (t3 - t2 if ok and t2 else 0),
            "total_latency_ms": lat, "payload": payload, "note": note,
        })


def read_coords(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        rows = []
        for r in csv.DictReader(f):
            try:
                rows.append((float(r["lat"]), float(r["lon"]), float(r["alt"]),
                             int(float(r["r_cm"])), int(r["priority"]), int(r["survivor_id"])))
            except (KeyError, ValueError):
                continue
        return rows


# ── one transmission attempt → returns (ok, t1, t2, t3) ───────

def attempt_mock(tx_num, rec, payload, mock_portal, fail_sid):
    sid = rec[5]
    t1 = int(time.time() * 1000)
    write_live({"state": "in_flight", "tx_num": tx_num, "session": "auto",
                "t1": True, "t2": False, "t3": False, "payload": payload})
    time.sleep(0.4)
    t2 = int(time.time() * 1000)
    write_live({"state": "in_flight", "tx_num": tx_num, "session": "auto",
                "t1": True, "t2": True, "t3": False, "payload": payload})
    time.sleep(random.uniform(1.4, 2.8))
    forced_fail = (fail_sid is not None and sid == fail_sid)
    ok = (not forced_fail) and (random.random() > 0.08)
    t3 = int(time.time() * 1000)
    write_live({"state": "complete", "tx_num": tx_num, "session": "auto",
                "t1": True, "t2": True, "t3": ok, "payload": payload})
    if ok and mock_portal:
        time.sleep(0.5)
        append_mock_receipt(payload)
    return ok, t1, t2, t3


def attempt_real(ser, tx_num, rec, payload, timeout_ms=30000):
    lat, lon, alt, r_cm, pri, sid = rec
    cmd = f"TX,{lat:.7f},{lon:.7f},{alt:.1f},{r_cm},{pri},{sid}\n"
    t1 = int(time.time() * 1000)
    write_live({"state": "in_flight", "tx_num": tx_num, "session": "auto",
                "t1": True, "t2": False, "t3": False, "payload": payload})
    ser.write(cmd.encode())
    t2 = t3 = None
    start = time.time()
    while (time.time() - start) * 1000 < timeout_ms:
        line = ser.readline().decode("utf-8", "replace").strip()
        if not line:
            continue
        now = int(time.time() * 1000)
        if any(m in line for m in ("OK", "$CC", "[T2]")) and t2 is None:
            t2 = now
            write_live({"state": "in_flight", "tx_num": tx_num, "session": "auto",
                        "t1": True, "t2": True, "t3": False, "payload": payload})
        if any(m in line for m in ("[T3]", "RDTX", "Send Success")):
            t3 = now
            break
    ok = t3 is not None
    write_live({"state": "complete", "tx_num": tx_num, "session": "auto",
                "t1": True, "t2": bool(t2), "t3": ok, "payload": payload})
    return ok, t1, t2 or 0, t3 or 0


# ── queue-driven watch loop ───────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Auto-transmit new coordinates with retry/recycle/flag.")
    ap.add_argument("--mock", action="store_true", help="simulate the ESP32 (no hardware)")
    ap.add_argument("--port", default="COM14", help="serial port of the ESP32")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--poll", type=float, default=0.5, help="file-check interval (s)")
    ap.add_argument("--max-laps", type=int, default=5,
                    help="total send attempts before NEEDS ATTENTION flag")
    ap.add_argument("--backoff", type=float, default=4.0,
                    help="seconds before a recycled coordinate is eligible again")
    ap.add_argument("--no-mock-portal", action="store_true",
                    help="in mock mode, do NOT simulate portal receipts")
    ap.add_argument("--mock-fail-sid", type=int, default=None,
                    help="(mock) force this survivor_id to always time out — demo the flag")
    ap.add_argument("--send-backlog", action="store_true",
                    help="also send rows already in the file at startup")
    args = ap.parse_args()

    os.makedirs(DATA, exist_ok=True)
    if not os.path.exists(COORDS_CSV):
        with open(COORDS_CSV, "w", newline="") as f:
            f.write("lat,lon,alt,r_cm,priority,survivor_id\n")

    mock_portal = args.mock and not args.no_mock_portal
    if args.mock and mock_portal and os.path.exists(MOCK_PORTAL):
        os.remove(MOCK_PORTAL)

    ser = None
    if not args.mock:
        import serial
        ser = serial.Serial(args.port, args.baud, timeout=1)
        time.sleep(2)

    seen = 0 if args.send_backlog else len(read_coords(COORDS_CSV))
    tx_num = 0
    queue = []   # items: {"rec", "payload", "lap", "eligible"}
    mode = "MOCK" if args.mock else f"REAL ({args.port})"
    print(f"[AUTO] watching {os.path.normpath(COORDS_CSV)}  ({mode})")
    print(f"[AUTO] retry once -> recycle -> max {args.max_laps} laps -> NEEDS ATTENTION. Ctrl+C to stop.\n")

    try:
        while True:
            # 1. enqueue any new coordinates
            rows = read_coords(COORDS_CSV)
            if len(rows) > seen:
                for rec in rows[seen:]:
                    queue.append({"rec": rec, "payload": encode_payload(*rec),
                                  "lap": 1, "eligible": time.time()})
                    print(f"[NEW COORD] T{rec[5]:03d} queued")
                seen = len(rows)

            # 2. pick the next eligible item (FIFO among those whose backoff passed)
            now = time.time()
            idx = next((i for i, it in enumerate(queue) if it["eligible"] <= now), None)
            if idx is None:
                time.sleep(args.poll)
                continue
            item = queue.pop(idx)
            rec, payload, lap = item["rec"], item["payload"], item["lap"]
            sid = rec[5]
            tx_num += 1

            if args.mock:
                ok, t1, t2, t3 = attempt_mock(tx_num, rec, payload, mock_portal, args.mock_fail_sid)
            else:
                ok, t1, t2, t3 = attempt_real(ser, tx_num, rec, payload)

            if ok:
                note = "" if lap == 1 else f"recovered (lap {lap})"
                append_row(tx_num, payload, t1, t2, t3, True, note)
                print(f"  TX#{tx_num} T{sid:03d}  CONFIRMED{(' ' + note) if note else ''}")
            elif lap >= args.max_laps:
                append_row(tx_num, payload, t1, t2, t3, False,
                           f"NEEDS ATTENTION ({lap} laps)")
                print(f"  TX#{tx_num} T{sid:03d}  *** NEEDS ATTENTION after {lap} laps ***")
            else:
                append_row(tx_num, payload, t1, t2, t3, False, f"timeout lap {lap}/{args.max_laps}")
                # lap 2 = immediate retry; laps 3+ = recycle as new (with backoff)
                next_lap = lap + 1
                delay = 0.0 if next_lap == 2 else args.backoff
                queue.append({"rec": rec, "payload": payload, "lap": next_lap,
                              "eligible": time.time() + delay})
                kind = "retry" if next_lap == 2 else "recycled as new"
                print(f"  TX#{tx_num} T{sid:03d}  TIMEOUT lap {lap} -> {kind}")
    except KeyboardInterrupt:
        print("\n[AUTO] stopped.")
    finally:
        if ser:
            ser.close()


if __name__ == "__main__":
    main()
