"""
objective4_emit.py — stand-in for Objective 4 (RTK / target-position module) producing
a survivor coordinate for the BeiDou node to transmit.

THE INJECTION INTERFACE (Objective 4 -> Objective 5):
    Objective 4 appends ONE row to data/outgoing_coords.csv:
        lat,lon,alt,r_cm,priority,survivor_id
    Only lat,lon are required; alt/r_cm/priority/survivor_id default if omitted.
    The node (sim/run_all.py --watch) detects the new row and transmits it through
    the emulator -> portal -> GCS -> dashboard.

This script lets you exercise that interface without the real Objective 4. In the real
system, Objective 4 writes the same row (any process/language that appends a CSV line).

Usage:
    # arm the node in one terminal:
    python sim/run_all.py --watch
    # then, from Objective 4 (or this stand-in), emit a coordinate:
    python sim/objective4_emit.py --lat 47.3971 --lon 8.5462 --priority 0
    python sim/objective4_emit.py --demo        # emit a plausible RTK fix near the lab
"""

import argparse
import csv
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV = os.path.join(HERE, "..", "data", "outgoing_coords.csv")
HEADER = ["lat", "lon", "alt", "r_cm", "priority", "survivor_id"]


def _next_id():
    """survivor_id = current row count + 1 (so each emit is a new survivor)."""
    if not os.path.exists(COORDS_CSV):
        return 1
    with open(COORDS_CSV, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f)) + 1


def emit(lat, lon, alt=0.0, r_cm=0, priority=1, survivor_id=None):
    survivor_id = survivor_id if survivor_id is not None else _next_id()
    new = not os.path.exists(COORDS_CSV)
    with open(COORDS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(HEADER)
        w.writerow([f"{lat:.7f}", f"{lon:.7f}", alt, r_cm, priority, survivor_id])
    print(f"[OBJ4] emitted survivor T{survivor_id:03d}: "
          f"{lat:.7f}, {lon:.7f}, alt={alt}m, R={r_cm/100:.2f}m, P{priority} "
          f"-> data/outgoing_coords.csv")
    return survivor_id


def main():
    ap = argparse.ArgumentParser(description="Objective 4 output emitter (injection interface).")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--alt", type=float, default=0.0)
    ap.add_argument("--r-cm", type=int, default=0, help="RTK uncertainty radius, cm")
    ap.add_argument("--priority", type=int, default=1, choices=[0, 1, 2])
    ap.add_argument("--survivor-id", type=int, default=None)
    ap.add_argument("--demo", action="store_true",
                    help="emit a plausible RTK fix near the lab (Karlsruhe) with random jitter")
    a = ap.parse_args()

    if a.demo:
        lat = 49.0069 + random.uniform(-3e-4, 3e-4)
        lon = 8.4380 + random.uniform(-3e-4, 3e-4)
        emit(lat, lon, alt=114.0, r_cm=random.choice([120, 160, 200, 330]),
             priority=random.choice([0, 1, 2]))
        return
    if a.lat is None or a.lon is None:
        ap.error("provide --lat and --lon (or use --demo)")
    emit(a.lat, a.lon, a.alt, a.r_cm, a.priority, a.survivor_id)


if __name__ == "__main__":
    main()
