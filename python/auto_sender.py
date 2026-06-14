"""
auto_sender.py — watch an outgoing-coordinates CSV and AUTO-transmit each new row
through the BDS-SMC node. Drop a coordinate in the file -> it flies. No manual step.

The operator only watches tx_dashboard.py (green = ok, red = error).

Real mode:  opens the ESP32 serial port, sends "TX,lat,lon,alt,r_cm,priority,id",
            reads the [T1]/[T2]/[T3] markers it already prints.
Mock mode:  simulates the ESP32 with realistic timing (no hardware) so the whole
            auto-trigger loop can be demonstrated end-to-end on the dashboard.

Watches:    data/outgoing_coords.csv   (header: lat,lon,alt,r_cm,priority,survivor_id)
Writes:     data/gap2_latency.csv      (TX log the dashboard reads; session='auto')
            data/live_state.json       (in-flight state for the dashboard live row)

Usage:
    python auto_sender.py --mock                # no hardware: simulate the node
    python auto_sender.py --port COM14          # real: drive the ESP32
    python auto_sender.py --mock --poll 0.5     # how often to check the file (seconds)
"""

import argparse
import csv
import json
import os
import struct
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
COORDS_CSV = os.path.join(DATA, "outgoing_coords.csv")
OUT_CSV = os.path.join(DATA, "gap2_latency.csv")
LIVE = os.path.join(DATA, "live_state.json")
MOCK_PORTAL = os.path.join(DATA, "portal_inbox_mock.csv")   # mock RX, never the real file

OUT_FIELDS = ["tx_num", "session", "weather", "cloud_pct", "datetime",
              "t1", "t2", "t3", "tx_latency_ms", "decode_latency_ms",
              "total_latency_ms", "payload"]


def encode_payload(lat, lon, alt_m, r_cm, priority, survivor_id):
    """Build the $CCTXM 112-bit message exactly as the firmware does."""
    packed = struct.pack(">iihHBB",
                         round(lat * 1e7), round(lon * 1e7), round(alt_m),
                         int(r_cm), int(priority), int(survivor_id))
    return f"$CCTXM,0,BIN:{packed.hex().upper()}*4C"


def write_live(state):
    try:
        state["updated"] = time.time()
        with open(LIVE, "w") as f:
            json.dump(state, f)
    except Exception:
        pass


def append_row(tx_num, payload, t1, t2, t3, ok):
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
            "total_latency_ms": lat, "payload": payload,
        })


def append_mock_receipt(payload):
    """Simulate the portal receiving this exact payload (mock RX side only)."""
    new_file = not os.path.exists(MOCK_PORTAL)
    with open(MOCK_PORTAL, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["received_at_local", "row_json"])
        row = {"card_id": "15590673", "encode_type": False,
               "msg_data": payload, "created_at": datetime.now().isoformat()}
        w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    json.dumps(row, ensure_ascii=False)])


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


# ── send one coordinate ───────────────────────────────────────

def send_mock(tx_num, rec, payload, mock_portal=True):
    """Simulate the ESP32: loaded -> module ack -> satellite ack, with delays.
    If mock_portal, also simulate the portal receiving the same payload."""
    import random
    sid = rec[5]
    t1 = int(time.time() * 1000)
    write_live({"state": "in_flight", "tx_num": tx_num, "session": "auto",
                "t1": True, "t2": False, "t3": False, "payload": payload})
    time.sleep(0.4)
    t2 = int(time.time() * 1000)
    write_live({"state": "in_flight", "tx_num": tx_num, "session": "auto",
                "t1": True, "t2": True, "t3": False, "payload": payload})
    time.sleep(random.uniform(1.6, 3.2))          # satellite round-trip
    ok = random.random() > 0.05                    # ~5% simulated timeout
    t3 = int(time.time() * 1000)
    if ok:
        write_live({"state": "complete", "tx_num": tx_num, "session": "auto",
                    "t1": True, "t2": True, "t3": True, "payload": payload})
        if mock_portal:
            time.sleep(0.6)                 # brief "satellite -> ground" transit
            append_mock_receipt(payload)
        print(f"  TX#{tx_num} survivor T{sid:03d}  CONFIRMED  ({t3 - t1} ms)")
    else:
        write_live({"state": "complete", "tx_num": tx_num, "session": "auto",
                    "t1": True, "t2": True, "t3": False, "payload": payload})
        print(f"  TX#{tx_num} survivor T{sid:03d}  TIMEOUT (simulated)")
    append_row(tx_num, payload, t1, t2, t3, ok)


def send_real(ser, tx_num, rec, payload, timeout_ms=30000):
    """Send the TX command and read the firmware's T1/T2/T3 markers."""
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
    append_row(tx_num, payload, t1, t2, t3 or 0, ok)
    print(f"  TX#{tx_num} survivor T{sid:03d}  {'CONFIRMED' if ok else 'TIMEOUT'}")


# ── watch loop ────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Auto-transmit new coordinates from a CSV.")
    ap.add_argument("--mock", action="store_true", help="simulate the ESP32 (no hardware)")
    ap.add_argument("--port", default="COM14", help="serial port of the ESP32")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--poll", type=float, default=0.5, help="file-check interval (s)")
    ap.add_argument("--send-backlog", action="store_true",
                    help="also send rows already in the file at startup")
    ap.add_argument("--no-mock-portal", action="store_true",
                    help="in mock mode, do NOT simulate portal receipts")
    args = ap.parse_args()

    os.makedirs(DATA, exist_ok=True)
    if not os.path.exists(COORDS_CSV):
        with open(COORDS_CSV, "w", newline="") as f:
            f.write("lat,lon,alt,r_cm,priority,survivor_id\n")
        print(f"[AUTO] created {COORDS_CSV} (empty). Append rows to trigger sends.")

    ser = None
    mock_portal = args.mock and not args.no_mock_portal
    if args.mock and mock_portal and os.path.exists(MOCK_PORTAL):
        os.remove(MOCK_PORTAL)              # fresh mock RX each demo run
    if not args.mock:
        import serial
        ser = serial.Serial(args.port, args.baud, timeout=1)
        time.sleep(2)

    seen = 0 if args.send_backlog else len(read_coords(COORDS_CSV))
    tx_num = seen
    mode = "MOCK (no hardware)" if args.mock else f"REAL ({args.port})"
    print(f"[AUTO] watching {os.path.normpath(COORDS_CSV)}  ({mode})")
    print(f"[AUTO] {seen} existing row(s) skipped. Drop a new row to auto-send. Ctrl+C to stop.\n")

    try:
        while True:
            rows = read_coords(COORDS_CSV)
            if len(rows) > seen:
                for rec in rows[seen:]:
                    tx_num += 1
                    payload = encode_payload(*rec)
                    print(f"[NEW COORD] T{rec[5]:03d} -> {payload}")
                    if args.mock:
                        send_mock(tx_num, rec, payload, mock_portal=mock_portal)
                    else:
                        send_real(ser, tx_num, rec, payload)
                seen = len(rows)
            time.sleep(args.poll)
    except KeyboardInterrupt:
        print("\n[AUTO] stopped.")
    finally:
        if ser:
            ser.close()


if __name__ == "__main__":
    main()
