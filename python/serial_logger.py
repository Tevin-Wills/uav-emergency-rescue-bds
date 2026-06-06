"""
serial_logger.py -- Gap 2 latency logger for BDS-SMC sessions.

Parses ESP32 serial output and extracts per-transmission latency.
Appends rows to data/gap2_latency.csv (same format as existing 30-TX dataset).

ESP32 serial markers (from esp32_sender.ino):
  [INIT] ...          -- startup
  [T1] <millis>       -- firmware fires AT command (T1 reference point)
  [TX#] <n>           -- TX sequence counter
  [ASCII TX] ...      -- payload echoed to serial
  OK / $CC / $RDTXA   -- BDS module / satellite ACK (T3)

Usage:
    python serial_logger.py --port COM3 --session morning --weather clear
    python serial_logger.py --port COM3 --session midday  --weather partly_cloudy --cloud_pct 30
    python serial_logger.py --demo
"""

import serial
import csv
import time
import argparse
import os
from datetime import datetime

DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_FILE  = os.path.join(DATA_DIR, "gap2_latency.csv")

FIELDNAMES = [
    "tx_num", "session", "weather", "cloud_pct", "datetime",
    "t1", "t2", "t3",
    "tx_latency_ms", "decode_latency_ms", "total_latency_ms",
]

# Lines from the BDS module that indicate satellite ACK (T3)
T3_MARKERS = ("$RDTXA", "RDTX", "Send Success", "SUCCESS", "Delivered")
# Lines that indicate module ACK (T2) -- often just "OK"
T2_MARKERS = ("OK", "$CCTXM", "$CC")

TIMEOUT_MS = 30_000   # 30s -- declare fail if no T3 within this window


def _next_tx_num(path: str) -> int:
    if not os.path.exists(path):
        return 1
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return 1
    try:
        return int(rows[-1]["tx_num"]) + 1
    except (KeyError, ValueError):
        return len(rows) + 1


def run_logger(port: str, baud: int, session: str, weather: str, cloud_pct: int, out: str):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tx_num     = _next_tx_num(out)
    write_hdr  = not os.path.exists(out)

    print(f"[LOGGER] Port={port} Baud={baud}")
    print(f"[LOGGER] Session={session}  Weather={weather}  Cloud={cloud_pct}%")
    print(f"[LOGGER] Appending from TX#{tx_num} -> {out}")
    print("[LOGGER] Press Ctrl+C to stop.\n")

    ser = serial.Serial(port, baud, timeout=1)

    t1 = t2 = t3 = None
    waiting = False

    with open(out, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_hdr:
            writer.writeheader()

        try:
            while True:
                line = ser.readline().decode("utf-8", errors="replace").strip()
                now  = int(time.time() * 1000)

                # Timeout: no satellite response within 30s
                if waiting and t1 and (now - t1) > TIMEOUT_MS:
                    print(f"  [TIMEOUT] TX#{tx_num} -- no satellite ACK in {TIMEOUT_MS//1000}s")
                    writer.writerow({
                        "tx_num": tx_num, "session": session,
                        "weather": weather, "cloud_pct": cloud_pct,
                        "datetime": datetime.now().isoformat(),
                        "t1": t1, "t2": t2 or "", "t3": "",
                        "tx_latency_ms": -1,
                        "decode_latency_ms": -1,
                        "total_latency_ms": -1,
                    })
                    f.flush()
                    tx_num += 1
                    t1 = t2 = t3 = None
                    waiting = False

                if not line:
                    continue

                print(f"  {line}")

                # T1: firmware fires the AT command
                if line.startswith("[T1]"):
                    t1, t2, t3 = now, None, None
                    waiting = True

                # T2: BDS module ACK (optional -- not always present)
                elif waiting and t2 is None and any(m in line for m in T2_MARKERS):
                    t2 = now

                # T3: satellite delivery confirmation
                elif waiting and any(m in line for m in T3_MARKERS):
                    t3 = now
                    tx_lat  = t3 - t1
                    dec_lat = (t3 - t2) if t2 else 0
                    writer.writerow({
                        "tx_num": tx_num, "session": session,
                        "weather": weather, "cloud_pct": cloud_pct,
                        "datetime": datetime.now().isoformat(),
                        "t1": t1, "t2": t2 or "", "t3": t3,
                        "tx_latency_ms": tx_lat,
                        "decode_latency_ms": dec_lat,
                        "total_latency_ms": tx_lat,
                    })
                    f.flush()
                    print(f"\n  >> TX#{tx_num} latency={tx_lat}ms  (decode={dec_lat}ms)\n")
                    tx_num += 1
                    t1 = t2 = t3 = None
                    waiting = False

        except KeyboardInterrupt:
            print(f"\n[LOGGER] Stopped. Last TX# written: {tx_num - 1}")
    ser.close()


def run_demo(out=OUT_FILE):
    import random
    print("[DEMO] Simulating 10 transmissions -- no hardware needed\n")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tx_num    = _next_tx_num(out)
    write_hdr = not os.path.exists(out)

    with open(out, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_hdr:
            writer.writeheader()
        for i in range(10):
            lat_ms = random.randint(1100, 4500)
            dec_ms = random.randint(6, 12)
            t1     = int(time.time() * 1000)
            row    = {
                "tx_num": tx_num + i, "session": "demo",
                "weather": "clear", "cloud_pct": 0,
                "datetime": datetime.now().isoformat(),
                "t1": t1, "t2": t1 + lat_ms - dec_ms, "t3": t1 + lat_ms,
                "tx_latency_ms": lat_ms,
                "decode_latency_ms": dec_ms,
                "total_latency_ms": lat_ms,
            }
            writer.writerow(row)
            print(f"  TX#{tx_num + i:3d}  latency={lat_ms:4d}ms")
            time.sleep(0.05)
    print(f"\n[DEMO] 10 rows appended to {out}")
    print("[DEMO] Run this to verify: python latency_analysis.py")


def main():
    parser = argparse.ArgumentParser(description="Gap 2 BDS-SMC session logger")
    parser.add_argument("--port",      default="COM3",
                        help="Serial port (e.g. COM3)")
    parser.add_argument("--baud",      type=int, default=9600)
    parser.add_argument("--session",   default="morning",
                        choices=["morning", "midday", "evening"],
                        help="Time-of-day session label for ANOVA")
    parser.add_argument("--weather",   default="clear",
                        choices=["clear", "partly_cloudy", "overcast", "rain"],
                        help="Sky condition")
    parser.add_argument("--cloud_pct", type=int, default=0,
                        help="Estimated cloud cover 0-100")
    parser.add_argument("--out",       default=OUT_FILE,
                        help="Output CSV path")
    parser.add_argument("--demo",      action="store_true",
                        help="Run with synthetic data (no hardware)")
    args = parser.parse_args()

    if args.demo:
        run_demo(args.out)
    else:
        run_logger(args.port, args.baud, args.session,
                   args.weather, args.cloud_pct, args.out)


if __name__ == "__main__":
    main()
