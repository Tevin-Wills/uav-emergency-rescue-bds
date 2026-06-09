"""
latency_analysis.py — Gap 2: reads T1/T2/T3 timestamps from log and computes latency stats.

T1 = ESP32 prints "[T1] <millis>" at transmission
T2 = Python serial_logger records arrival timestamp_ms
T3 = Python decode completes (logged here)

Usage:
    python latency_analysis.py --input ../data/gap2_latency.csv
    python latency_analysis.py --demo   (generates 30 synthetic rows to test the analysis)
"""

import csv
import argparse
import statistics
import time
from datetime import datetime

def parse_log_for_latency(log_file: str):
    """Extract T1/T2/T3 triplets from the raw serial log CSV.

    T1 = PC timestamp when the ESP32's [T1] line arrives over serial (send time proxy)
    T2 = PC timestamp when the BDS response/decoded coordinate arrives
    T3 = PC timestamp when Python finishes processing that response

    Both T1 and T2 use the same PC clock, so subtraction gives real latency.
    The ESP32's millis() value in the [T1] message is intentionally ignored here.
    """
    rows = []
    pending_t1 = None
    with open(log_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            msg = row["raw_message"]
            ts = int(row["timestamp_ms"])
            if msg.startswith("[T1]"):
                pending_t1 = ts  # PC clock at send time
            elif pending_t1 is not None and ("$CC" in msg or "$TELEM" in msg or "BIN" in msg):
                t1 = pending_t1
                t2 = ts                          # PC clock at receive time
                t3 = int(time.time() * 1000)     # PC clock after decode (near-instant)
                rows.append({"t1": t1, "t2": t2, "t3": t3,
                             "tx_latency_ms": t2 - t1,
                             "decode_latency_ms": t3 - t2,
                             "total_latency_ms": t3 - t1})
                pending_t1 = None
    return rows

def generate_demo_data(n=30):
    import random
    rows = []
    base_t1 = int(time.time() * 1000)
    for i in range(n):
        t1 = base_t1 + i * 10000
        tx_lat = random.randint(800, 4500)   # 0.8s–4.5s BDS typical
        dec_lat = random.randint(1, 15)       # decode is fast
        t2 = t1 + tx_lat
        t3 = t2 + dec_lat
        rows.append({"t1": t1, "t2": t2, "t3": t3,
                     "tx_latency_ms": tx_lat,
                     "decode_latency_ms": dec_lat,
                     "total_latency_ms": tx_lat + dec_lat})
    return rows

def print_stats(rows):
    tx = [r["tx_latency_ms"] for r in rows]
    dec = [r["decode_latency_ms"] for r in rows]
    total = [r["total_latency_ms"] for r in rows]

    print(f"\n{'Metric':<25} {'Mean':>8} {'StdDev':>8} {'Min':>8} {'Max':>8}")
    print("-" * 60)
    for label, vals in [("TX latency (ms)", tx), ("Decode latency (ms)", dec), ("Total latency (ms)", total)]:
        print(f"{label:<25} {statistics.mean(vals):>8.1f} {statistics.stdev(vals):>8.1f} "
              f"{min(vals):>8} {max(vals):>8}")
    print(f"\n[n={len(rows)} transmissions]")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=None)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--out", default="../data/gap2_latency.csv")
    args = parser.parse_args()

    if args.demo:
        print("[DEMO] Generating 30 synthetic latency rows...")
        rows = generate_demo_data(30)
    elif args.input:
        rows = parse_log_for_latency(args.input)
    else:
        print("Provide --input <log.csv> or --demo")
        return

    print_stats(rows)

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["t1", "t2", "t3", "tx_latency_ms",
                                                "decode_latency_ms", "total_latency_ms"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[SAVED] {args.out}")

if __name__ == "__main__":
    main()
