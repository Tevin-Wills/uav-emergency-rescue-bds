"""
feed_coords.py — DEMO feeder. Simulates an upstream source (lab system / another
objective / a live RTK feed) by appending lab rescue records T001-T006 to
data/outgoing_coords.csv one at a time, with a delay between each.

Run this alongside auto_sender.py --mock to watch the full hands-off loop:
each appended row auto-triggers a transmission that appears on the dashboard.

Usage:
    python feed_coords.py                 # append T001-T006, ~6 s apart
    python feed_coords.py --interval 3    # faster
    python feed_coords.py --loop          # keep cycling forever
"""

import argparse
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
COORDS = os.path.join(HERE, "..", "data", "outgoing_coords.csv")

# Lab ground-truth rescue records (Table 5): lat,lon,alt,r_cm,priority,survivor_id
RECORDS = [
    (49.0068822, 8.4383287, 114.2, 160, 1, 1),
    (49.0070078, 8.4382004, 113.5, 1190, 2, 2),
    (49.0070315, 8.4375595, 113.8, 460, 2, 3),
    (49.0070212, 8.4376131, 114.5, 160, 0, 4),
    (49.0071041, 8.4371681, 114.0, 330, 0, 5),
    (49.0071067, 8.4371963, 114.0, 200, 2, 6),
]


def main():
    ap = argparse.ArgumentParser(description="Feed demo coordinates into outgoing_coords.csv")
    ap.add_argument("--interval", type=float, default=6.0, help="seconds between rows")
    ap.add_argument("--loop", action="store_true", help="cycle the records forever")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(COORDS), exist_ok=True)
    if not os.path.exists(COORDS):
        with open(COORDS, "w", newline="") as f:
            f.write("lat,lon,alt,r_cm,priority,survivor_id\n")

    print(f"[FEED] appending records to {os.path.normpath(COORDS)} every {args.interval}s")
    print("[FEED] (auto_sender.py --mock will pick each one up and 'transmit' it)\n")
    n = 0
    try:
        while True:
            for rec in RECORDS:
                with open(COORDS, "a", newline="") as f:
                    f.write(",".join(str(x) for x in rec) + "\n")
                n += 1
                print(f"[FEED] saved survivor T{rec[5]:03d}  ({rec[0]}, {rec[1]})")
                time.sleep(args.interval)
            if not args.loop:
                break
    except KeyboardInterrupt:
        pass
    print(f"\n[FEED] done — {n} coordinate(s) saved.")


if __name__ == "__main__":
    main()
