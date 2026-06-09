"""
field_test_logger.py -- Gap 3 field test logger.

Records success/fail per transmission for each environment + location.
Appends to data/gap3_field_test.csv.

Environments: open_sky, light_canopy, urban_canyon, indoor
Locations per environment: 3 (e.g. OS-1, OS-2, OS-3)

Usage:
    python field_test_logger.py --env open_sky --location OS-1 --gps "30.4196,120.2977" --weather clear
    python field_test_logger.py --env urban_canyon --location UC-2 --obstruction 70 --n 50
    python field_test_logger.py --summary
    python field_test_logger.py --demo
"""

import serial
import csv
import time
import argparse
import os
import math
from datetime import datetime
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_FILE = os.path.join(DATA_DIR, "gap3_field_test.csv")

ENVIRONMENTS = ["open_sky", "light_canopy", "urban_canyon", "indoor"]

FIELDNAMES = [
    "timestamp", "environment", "location_id",
    "gps_lat", "gps_lon", "sky_obstruction_pct",
    "weather", "antenna_dir",
    "attempt", "result", "latency_ms", "notes",
]

T3_MARKERS = ("$RDTXA", "RDTX", "Send Success", "SUCCESS", "Delivered",
              "$CC", "BIN:", "HUF:", "OK")
FAIL_TOKENS = ("NO SIGNAL", "FAIL", "ERROR", "TIMEOUT")
TIMEOUT_MS  = 30_000


def _parse_gps(gps_str: str):
    try:
        parts = gps_str.split(",")
        return float(parts[0].strip()), float(parts[1].strip())
    except Exception:
        return 0.0, 0.0


def log_field_test(env, location, gps, obstruction, weather, antenna_dir,
                   port, baud, n, out):
    if env not in ENVIRONMENTS:
        print(f"[ERROR] --env must be one of: {ENVIRONMENTS}")
        return

    gps_lat, gps_lon = _parse_gps(gps)
    write_hdr = not os.path.exists(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)

    print(f"[FIELD] env={env}  location={location}  n={n}")
    print(f"[FIELD] GPS=({gps_lat:.4f},{gps_lon:.4f})  obstruction={obstruction}%  weather={weather}")
    print(f"[FIELD] Waiting on {port} @ {baud} baud  (30s timeout per TX)")
    print("[FIELD] Press Ctrl+C to stop early.\n")

    ser = serial.Serial(port, baud, timeout=1)

    attempt = 0
    t_start = 0
    waiting = False

    with open(out, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_hdr:
            writer.writeheader()

        def write_row(result, latency_ms, notes=""):
            writer.writerow({
                "timestamp":         datetime.now().isoformat(),
                "environment":       env,
                "location_id":       location,
                "gps_lat":           gps_lat,
                "gps_lon":           gps_lon,
                "sky_obstruction_pct": obstruction,
                "weather":           weather,
                "antenna_dir":       antenna_dir,
                "attempt":           attempt,
                "result":            result,
                "latency_ms":        latency_ms,
                "notes":             notes,
            })
            f.flush()

        try:
            while attempt < n:
                line = ser.readline().decode("utf-8", errors="replace").strip()
                now  = int(time.time() * 1000)

                # Timeout check
                if waiting and (now - t_start) > TIMEOUT_MS:
                    print(f"  [TIMEOUT] Attempt {attempt}/{n}")
                    write_row("fail", -1, "no_response_30s")
                    waiting = False

                if not line:
                    continue

                print(f"  {line}")

                if "[T1]" in line or "[TX#]" in line:
                    if "[TX#]" in line:
                        attempt += 1
                        t_start = now
                        waiting = True
                        print(f"  Attempt {attempt}/{n} ...")

                elif waiting and any(m in line for m in T3_MARKERS):
                    latency = now - t_start
                    print(f"  [OK] {latency}ms")
                    write_row("success", latency, line[:60])
                    waiting = False

                elif waiting and any(tok in line.upper() for tok in FAIL_TOKENS):
                    print(f"  [FAIL] {line[:60]}")
                    write_row("fail", -1, line[:60])
                    waiting = False

        except KeyboardInterrupt:
            print(f"\n[FIELD] Stopped at attempt {attempt}/{n}")

    ser.close()
    print(f"\n[FIELD] Done. Results -> {out}")
    print(f"[FIELD] Run --summary to see success rates.\n")


def print_summary(out):
    if not os.path.exists(out):
        print("[ERROR] No data file found. Run a field test first.")
        return

    counts = defaultdict(lambda: {"success": 0, "total": 0, "latencies": [], "locations": set()})
    with open(out, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            env = row["environment"]
            counts[env]["total"] += 1
            counts[env]["locations"].add(row.get("location_id", ""))
            if row["result"] == "success":
                counts[env]["success"] += 1
                try:
                    counts[env]["latencies"].append(int(row["latency_ms"]))
                except ValueError:
                    pass

    print(f"\n{'Environment':<20} {'Locs':>5} {'Succ':>6} {'Total':>6} "
          f"{'Rate':>8} {'95% CI':>10} {'Avg Lat':>10}")
    print("-" * 73)
    for env in ENVIRONMENTS:
        c = counts.get(env, {"success": 0, "total": 0, "latencies": [], "locations": set()})
        n_total, s = c["total"], c["success"]
        locs = len(c["locations"])
        if n_total == 0:
            print(f"{env:<20} {'—':>5} {'—':>6} {'0':>6} {'—':>8} {'—':>10} {'—':>10}")
            continue
        p      = s / n_total
        ci     = 1.96 * math.sqrt(p * (1 - p) / n_total) if n_total > 0 else 0
        avg_lat = int(sum(c["latencies"]) / len(c["latencies"])) if c["latencies"] else -1
        print(f"{env:<20} {locs:>5} {s:>6} {n_total:>6} "
              f"{p*100:>7.1f}% {f'+-{ci*100:.1f}%':>10} {avg_lat:>9}ms")
    print()


def run_demo(out):
    import random
    print("[DEMO] Simulating 5 TX per environment -- no hardware needed\n")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    write_hdr = not os.path.exists(out)
    success_rates = {"open_sky": 0.95, "light_canopy": 0.80,
                     "urban_canyon": 0.60, "indoor": 0.30}

    with open(out, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_hdr:
            writer.writeheader()
        for env in ENVIRONMENTS:
            for i in range(1, 6):
                ok  = random.random() < success_rates[env]
                lat = random.randint(1200, 4000) if ok else -1
                writer.writerow({
                    "timestamp": datetime.now().isoformat(),
                    "environment": env, "location_id": f"{env[:2].upper()}-1",
                    "gps_lat": 30.4196, "gps_lon": 120.2977,
                    "sky_obstruction_pct": {"open_sky": 0, "light_canopy": 20,
                                            "urban_canyon": 60, "indoor": 90}[env],
                    "weather": "clear", "antenna_dir": "south",
                    "attempt": i, "result": "success" if ok else "fail",
                    "latency_ms": lat, "notes": "demo",
                })
                status = f"OK {lat}ms" if ok else "FAIL"
                print(f"  {env:<20} attempt {i}  {status}")
    print(f"\n[DEMO] Rows written to {out}")
    print("[DEMO] Run --summary to see rates.")


def main():
    parser = argparse.ArgumentParser(description="Gap 3 field test logger")
    parser.add_argument("--env",         default=None, choices=ENVIRONMENTS)
    parser.add_argument("--location",    default="XX-1",
                        help="Location ID e.g. OS-1, LC-2, UC-3, IN-1")
    parser.add_argument("--gps",         default="0.0,0.0",
                        help="GPS coordinates as 'lat,lon'")
    parser.add_argument("--obstruction", type=int, default=0,
                        help="Sky obstruction 0-100 percent")
    parser.add_argument("--weather",     default="clear",
                        choices=["clear", "partly_cloudy", "overcast", "rain"])
    parser.add_argument("--antenna_dir", default="south",
                        help="Antenna direction (south from Hangzhou faces equator)")
    parser.add_argument("--port",        default="COM3")
    parser.add_argument("--baud",        type=int, default=9600)
    parser.add_argument("--n",           type=int, default=20,
                        help="Number of transmissions (20 minimum, 50 for Transactions)")
    parser.add_argument("--out",         default=OUT_FILE)
    parser.add_argument("--summary",     action="store_true")
    parser.add_argument("--demo",        action="store_true")
    args = parser.parse_args()

    if args.demo:
        run_demo(args.out)
    elif args.summary:
        print_summary(args.out)
    elif args.env:
        log_field_test(args.env, args.location, args.gps,
                       args.obstruction, args.weather, args.antenna_dir,
                       args.port, args.baud, args.n, args.out)
    else:
        print("Use --env to log, --summary to see results, or --demo to test.")
        print(f"Environments: {ENVIRONMENTS}")
        print("Example:")
        print('  python field_test_logger.py --env open_sky --location OS-1 --gps "30.4196,120.2977"')


if __name__ == "__main__":
    main()
