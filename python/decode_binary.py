"""
decode_binary.py — decodes hex-encoded binary rescue payloads from BDS messages.
Counterpart to the sendBinary() function in esp32_sender.ino.

Message format: $CCTXM,<destID>,BIN:<hex28>*<CS>
112-bit rescue payload (14 bytes, big-endian, struct ">iihHBB"):
    Bytes 0-3   lat  (int32, x10,000,000 -> 7dp, ~1cm)
    Bytes 4-7   lon  (int32, x10,000,000)
    Bytes 8-9   alt  (int16, metres)
    Bytes 10-11 R    (uint16, centimetres, 0-655m)
    Byte  12    priority (0=P0, 1=P1, 2=P2)
    Byte  13    survivor_id (0-255)
Legacy 64-bit payloads (8 bytes, ">ii", lat/lon x10,000) are still decoded
for backwards compatibility with pre-upgrade logs.

Usage:
    python decode_binary.py
    python decode_binary.py --input ../data/raw_log.csv
"""

import struct
import argparse
import csv

# Lab system ground-truth coordinates T001-T006 (Table 5):
# (lat, lon, alt_m, r_cm, priority, survivor_id)
TEST_RESCUE_DATA = [
    (49.0068822, 8.4383287, 114.2, 160, 1, 1),   # T001  R1.6m  P1
    (49.0070078, 8.4382004, 113.5, 1190, 2, 2),  # T002  R11.9m P2
    (49.0070315, 8.4375595, 113.8, 460, 2, 3),   # T003  R4.6m  P2
    (49.0070212, 8.4376131, 114.5, 160, 0, 4),   # T004  R1.6m  P0
    (49.0071041, 8.4371681, 114.0, 330, 0, 5),   # T005  R3.3m  P0
    (49.0071067, 8.4371963, 114.0, 200, 2, 6),   # T006  R2.0m  P2
]


def encode_binary(lat, lon, alt_m, r_cm, priority, survivor_id):
    """Pack the 112-bit rescue payload exactly as the firmware does."""
    packed = struct.pack(
        ">iihHBB",
        round(lat * 10000000), round(lon * 10000000),
        round(alt_m), r_cm, priority, survivor_id,
    )
    return packed.hex().upper()


def decode_binary(msg: str):
    """Parse $CCTXM,<destID>,BIN:<hex>*CS.

    Returns (lat, lon, alt_m, r_cm, priority, survivor_id, bit_count).
    Legacy 64-bit payloads return None for the rescue fields.
    Undecodable input returns all None."""
    nothing = (None,) * 7
    try:
        clean = msg.split("*")[0].strip()
        parts = clean.split(",")
        # parts[0]="$CCTXM", parts[1]=destID, parts[2]="BIN:<hex>"
        if not parts[2].startswith("BIN:"):
            return nothing
        raw = bytes.fromhex(parts[2][4:])
        if len(raw) == 14:  # 112-bit rescue payload
            lat_i, lon_i, alt, r_cm, priority, survivor_id = struct.unpack(">iihHBB", raw)
            return (lat_i / 10000000.0, lon_i / 10000000.0, float(alt),
                    r_cm, priority, survivor_id, len(raw) * 8)
        if len(raw) == 8:   # legacy 64-bit coordinate-only payload
            lat_i, lon_i = struct.unpack(">ii", raw)
            return lat_i / 10000.0, lon_i / 10000.0, None, None, None, None, 64
        return nothing
    except Exception:
        return nothing


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=None)
    args = parser.parse_args()

    # Round-trip test on the lab ground-truth set — verifies 7dp precision holds
    print("=== Round-trip encode/decode test (lab T001-T006, 112-bit payload) ===")
    print(f"{'ID':>3} {'Lat In':>12} {'Lon In':>11} {'Alt':>6} {'R(m)':>6} {'Pri':>4}  "
          f"{'Lat Out':>12} {'Lon Out':>11} {'Bits':>5} {'Match':>6}")
    print("-" * 96)
    all_ok = True
    for lat, lon, alt, r_cm, pri, sid in TEST_RESCUE_DATA:
        hex_str = encode_binary(lat, lon, alt, r_cm, pri, sid)
        fake_msg = f"$CCTXM,0,BIN:{hex_str}"
        lat_o, lon_o, alt_o, r_o, pri_o, sid_o, bits = decode_binary(fake_msg)
        ok = (abs(lat - lat_o) < 5e-8 and abs(lon - lon_o) < 5e-8
              and alt_o == round(alt) and r_o == r_cm and pri_o == pri and sid_o == sid)
        all_ok &= ok
        print(f"T{sid:03d} {lat:>12.7f} {lon:>11.7f} {alt:>6.1f} {r_cm/100:>6.2f} P{pri:>3}  "
              f"{lat_o:>12.7f} {lon_o:>11.7f} {bits:>5} {'OK' if ok else 'FAIL':>6}")

    ascii_bits = 264  # Gap 1 ASCII baseline
    print(f"\n[RESULT] Rescue payload size  : 112 bits (fixed, 6 fields)")
    print(f"[RESULT] ASCII equivalent     : {ascii_bits} bits")
    print(f"[RESULT] Size reduction       : {(1 - 112/ascii_bits)*100:.1f}%")
    print(f"[RESULT] BDS-3 headroom       : {210 - 112} bits under the 210-bit limit")
    print(f"[RESULT] Round-trip           : {'ALL OK — 7dp precision preserved' if all_ok else 'FAILURES PRESENT'}")

    # Optionally decode from a live log
    if args.input:
        print(f"\n=== Decoding from {args.input} ===")
        with open(args.input) as f:
            reader = csv.DictReader(f)
            for row in reader:
                msg = row["raw_message"]
                if "BIN:" in msg:
                    lat, lon, alt, r_cm, pri, sid, bits = decode_binary(msg)
                    if lat is None:
                        continue
                    if bits == 112:
                        print(f"  T{sid:03d} lat={lat:.7f} lon={lon:.7f} alt={alt:.0f}m "
                              f"R={r_cm/100:.2f}m P{pri} bits={bits}")
                    else:
                        print(f"  lat={lat:.4f} lon={lon:.4f} bits={bits} (legacy)")


if __name__ == "__main__":
    main()
