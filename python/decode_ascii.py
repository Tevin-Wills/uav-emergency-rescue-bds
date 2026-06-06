"""
decode_ascii.py — Gap 1 baseline: decodes ASCII $CCTXM messages and measures bit size.

Message format: $CCTXM,<destID>,LAT:<lat>,LON:<lon>*<CS>

Usage:
    python decode_ascii.py
    python decode_ascii.py --input ../data/raw_log.csv
"""

import argparse
import csv
import os

SAMPLE_MESSAGES = [
    "$CCTXM,0,LAT:30.4196,LON:120.2977*XX",
    "$CCTXM,0,LAT:30.4200,LON:120.3001*XX",
    "$CCTXM,0,LAT:30.4188,LON:120.2955*XX",
]

def decode_ascii(msg: str):
    """Parse $CCTXM,<destID>,LAT:<lat>,LON:<lon>*CS and return (lat, lon, bit_count)."""
    try:
        # Strip checksum suffix if present
        clean = msg.split("*")[0].strip()
        parts = clean.split(",")
        # parts[0]="$CCTXM", parts[1]=destID, parts[2]="LAT:xx", parts[3]="LON:xx"
        lat = float(parts[2].split(":")[1])
        lon = float(parts[3].split(":")[1])
        bit_count = len(clean.encode("ascii")) * 8
        return lat, lon, bit_count
    except Exception:
        return None, None, None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=None, help="CSV log file from serial_logger.py")
    args = parser.parse_args()

    messages = SAMPLE_MESSAGES
    if args.input:
        with open(args.input) as f:
            reader = csv.DictReader(f)
            messages = [row["raw_message"] for row in reader
                        if "$CCTXM" in row["raw_message"] and "LAT:" in row["raw_message"]]

    print(f"{'Message':<45} {'Lat':>10} {'Lon':>11} {'Bits':>6}")
    print("-" * 76)
    results = []
    for msg in messages:
        lat, lon, bits = decode_ascii(msg)
        if lat is not None:
            print(f"{msg:<45} {lat:>10.4f} {lon:>11.4f} {bits:>6}")
            results.append({"message": msg, "lat": lat, "lon": lon, "bits": bits})

    if results:
        avg_bits = sum(r["bits"] for r in results) / len(results)
        print(f"\n[RESULT] Average ASCII bits per message : {avg_bits:.1f}")
        print(f"[RESULT] Binary alternative             : 64 bits (two int32)")
        print(f"[RESULT] Compression ratio              : {avg_bits/64:.2f}x")

        out = os.path.join(os.path.dirname(__file__), "..", "data", "gap1_compression.csv")
        with open(out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["message", "lat", "lon", "bits"])
            writer.writeheader()
            writer.writerows(results)
        print(f"[SAVED] {out}")

if __name__ == "__main__":
    main()
