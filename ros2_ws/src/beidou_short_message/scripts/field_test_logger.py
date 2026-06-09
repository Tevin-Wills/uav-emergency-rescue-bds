"""
field_test_logger.py — Gap 3: records success/fail for each transmission in the field.

Environments: open_sky, light_canopy, urban_canyon, indoor
20 transmissions per environment -> 80 total rows

Usage:
    python field_test_logger.py --env open_sky
    python field_test_logger.py --env urban_canyon --port COM3
    python field_test_logger.py --summary
"""

import serial
import csv
import time
import argparse
from datetime import datetime
import os
import math
from collections import defaultdict

ENVIRONMENTS = ["open_sky", "light_canopy", "urban_canyon", "indoor"]
OUT_FILE = "../data/gap3_field_test.csv"

def log_field_test(env: str, port: str, baud: int, n: int):
    if env not in ENVIRONMENTS:
        print(f"[ERROR] env must be one of: {ENVIRONMENTS}")
        return

    print(f"[FIELD] Environment: {env} | Target: {n} transmissions")
    print(f"[FIELD] Waiting for messages on {port} at {baud} baud...")

    ser = serial.Serial(port, baud, timeout=1)  # 1s readline timeout for responsive polling

    write_header = not os.path.exists(OUT_FILE)
    with open(OUT_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["timestamp", "environment", "attempt", "result", "latency_ms", "notes"])

        attempt   = 0
        t_start   = 0       # PC time when [TX#] was detected
        waiting   = False   # True between [TX#] and a BDS response

        print(f"  Listening — press EN on ESP32 to start transmissions...")

        while attempt < n:
            line = ser.readline().decode("utf-8", errors="replace").strip()
            now  = int(time.time() * 1000)

            # Transmission timeout: no BDS response within 30 s of [TX#]
            if waiting and (now - t_start) > 30000:
                print(f"  [TIMEOUT] Attempt {attempt} — no BDS response in 30 s")
                writer.writerow([datetime.now().isoformat(), env, attempt,
                                 "fail", -1, "no_response_30s"])
                f.flush()
                waiting = False

            if not line:
                continue

            # ESP32 fires a transmission
            if line.startswith("[TX#]"):
                attempt += 1
                t_start = now
                waiting = True
                print(f"  Attempt {attempt}/{n} detected — waiting for BDS response...")

            # Success: BDS module acknowledged or coordinate echoed back
            elif waiting and any(tok in line for tok in
                                 ["$CC", "BIN:", "HUF:", "OK", "Send Success",
                                  "SUCCESS", "$RDTXA"]):
                latency = now - t_start
                print(f"  [OK] {latency} ms — {line[:60]}")
                writer.writerow([datetime.now().isoformat(), env, attempt,
                                 "success", latency, line[:60]])
                f.flush()
                waiting = False

            # Explicit failure reported by the ESP32 sketch
            elif waiting and any(tok in line.upper() for tok in
                                 ["NO SIGNAL", "FAIL", "ERROR", "TIMEOUT"]):
                print(f"  [FAIL] {line[:60]}")
                writer.writerow([datetime.now().isoformat(), env, attempt,
                                 "fail", -1, line[:60]])
                f.flush()
                waiting = False

    ser.close()
    print(f"\n[FIELD] Done. Results saved to {OUT_FILE}")

def print_summary():
    if not os.path.exists(OUT_FILE):
        print("[ERROR] No data file found. Run a field test first.")
        return

    counts = defaultdict(lambda: {"success": 0, "total": 0, "latencies": []})
    with open(OUT_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            env = row["environment"]
            counts[env]["total"] += 1
            if row["result"] == "success":
                counts[env]["success"] += 1
                try:
                    counts[env]["latencies"].append(int(row["latency_ms"]))
                except ValueError:
                    pass

    print(f"\n{'Environment':<20} {'Succ':>6} {'Total':>6} {'Rate':>8} {'95% CI':>10} {'Avg Lat':>10}")
    print("-" * 66)
    for env in ENVIRONMENTS:
        c = counts.get(env, {"success": 0, "total": 0, "latencies": []})
        n, s = c["total"], c["success"]
        if n == 0:
            print(f"{env:<20} {'—':>6} {'0':>6} {'—':>8} {'—':>10} {'—':>10}")
            continue
        p   = s / n
        ci  = 1.96 * math.sqrt(p * (1 - p) / n)
        avg_lat = (sum(c["latencies"]) / len(c["latencies"])) if c["latencies"] else -1
        print(f"{env:<20} {s:>6} {n:>6} {p*100:>7.1f}% {f'±{ci*100:.1f}%':>10} {avg_lat:>9.0f}ms")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env",     default=None)
    parser.add_argument("--port",    default="COM3")
    parser.add_argument("--baud",    type=int, default=9600)
    parser.add_argument("--n",       type=int, default=20)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    if args.summary:
        print_summary()
    elif args.env:
        log_field_test(args.env, args.port, args.baud, args.n)
    else:
        print("Use --env <environment> to log, or --summary to see results.")
        print(f"Environments: {ENVIRONMENTS}")

if __name__ == "__main__":
    main()
