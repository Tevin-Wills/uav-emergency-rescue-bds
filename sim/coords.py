"""
coords.py — input coordinate source for the virtual BeiDou link.

The node reads the survivors it transmits from data/outgoing_coords.csv
(header: lat,lon,alt,r_cm,priority,survivor_id). This is the pipeline's INPUT —
edit that CSV to change what gets sent through emulator -> portal -> dashboard.

If the CSV is missing or empty, we fall back to the built-in lab set (T001-T006)
so the demo always runs out of the box.
"""

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV = os.path.join(HERE, "..", "data", "outgoing_coords.csv")

# Lab ground-truth survivors T001-T006 (the set decode_binary.py round-trips).
FALLBACK = [
    (49.0068822, 8.4383287, 114.2, 160, 1, 1),
    (49.0070078, 8.4382004, 113.5, 1190, 2, 2),
    (49.0070315, 8.4375595, 113.8, 460, 2, 3),
    (49.0070212, 8.4376131, 114.5, 160, 0, 4),
    (49.0071041, 8.4371681, 114.0, 330, 0, 5),
    (49.0071067, 8.4371963, 114.0, 200, 2, 6),
]


def load_survivors(path=COORDS_CSV, fallback=True):
    """Return (survivors, source_description).

    survivors is a list of (lat, lon, alt_m, r_cm, priority, survivor_id) tuples.
    Only lat/lon are required (Objective 4 may emit position only); the rest default
    so the 112-bit payload is always well-formed:
        alt=0.0, r_cm=0, priority=1 (P1), survivor_id=row index.
    Malformed/blank rows are skipped.

    fallback=True  (demo): empty/missing CSV -> built-in T001-T006 set.
    fallback=False (watch): empty/missing CSV -> [] (an empty injection queue means
                   'wait for Objective 4', never auto-send the demo set)."""
    rows = []
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for idx, r in enumerate(csv.DictReader(f), start=1):
                try:
                    lat = float(r["lat"]); lon = float(r["lon"])   # required
                except (KeyError, ValueError, TypeError):
                    continue
                alt = float(r.get("alt") or 0.0)
                r_cm = int(float(r.get("r_cm") or 0))
                pri = int(float(r.get("priority") or 1))
                sid = int(float(r.get("survivor_id") or idx))
                rows.append((lat, lon, alt, r_cm, pri, sid))
    if rows:
        return rows, f"{len(rows)} row(s) from data/outgoing_coords.csv"
    if fallback:
        return list(FALLBACK), "built-in T001-T006 (outgoing_coords.csv was empty)"
    return [], "no coordinates yet (outgoing_coords.csv empty)"


if __name__ == "__main__":
    s, src = load_survivors()
    print(f"source: {src}")
    for row in s:
        print(" ", row)
