"""
serial_logger.py — Reads from BDS module / XCOM serial port and saves all messages to CSV.
Run this first to confirm your receive chain is alive before any Gap work.

Usage:
    python serial_logger.py --port COM3 --baud 9600 --out ../data/raw_log.csv
"""

import serial
import csv
import time
import argparse
from datetime import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM3", help="Serial port (e.g. COM3 or /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--out", default="../data/raw_log.csv")
    args = parser.parse_args()

    print(f"[LOGGER] Opening {args.port} at {args.baud} baud...")
    ser = serial.Serial(args.port, args.baud, timeout=1)

    with open(args.out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_ms", "timestamp_iso", "raw_message"])

        print(f"[LOGGER] Logging to {args.out}. Press Ctrl+C to stop.")
        try:
            while True:
                line = ser.readline().decode("utf-8", errors="replace").strip()
                if line:
                    ts_ms = int(time.time() * 1000)
                    ts_iso = datetime.now().isoformat()
                    writer.writerow([ts_ms, ts_iso, line])
                    f.flush()
                    print(f"[{ts_iso}] {line}")
        except KeyboardInterrupt:
            print("\n[LOGGER] Stopped.")

if __name__ == "__main__":
    main()
