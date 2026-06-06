"""
telemetry_compare.py — Gap 6: compares ASCII / Binary / Huffman encoding sizes.

Full telemetry struct: lat, lon, alt, battery%, mode, flags, timestamp
Encodes in all formats, measures bit size, simulates transmission, decodes.

Usage:
    python telemetry_compare.py
    python telemetry_compare.py --out ../data/gap6_telemetry.csv
"""

import struct
import csv
import argparse
import os
from dahuffman import HuffmanCodec

# --- Sample telemetry payload — Yuhang District, Hangzhou ---
TELEMETRY = {
    "lat":       30.4196,
    "lon":      120.2977,
    "alt":       45.0,       # metres (Yuhang elevation)
    "battery":   87,         # percent
    "mode":       2,         # 2 = rescue
    "flags":   0b00000101,   # bit0=GPS_lock, bit2=comms_ok
    "timestamp": 1748822400, # 2026-06-02 00:00:00 UTC
}

def encode_ascii(t: dict) -> bytes:
    s = (f"$TELEM,{t['lat']:.4f},{t['lon']:.4f},{t['alt']:.1f},"
         f"{t['battery']},{t['mode']},{t['flags']},{t['timestamp']}")
    return s.encode("ascii")

def encode_binary(t: dict) -> bytes:
    # lat/lon: int32 (x10000), alt: uint16, battery: uint8,
    # mode(4b)+flags(4b): uint8, timestamp: uint32  -> 15 bytes total
    lat_i      = int(t["lat"] * 10000)
    lon_i      = int(t["lon"] * 10000)
    alt_i      = int(t["alt"])
    bat        = t["battery"] & 0xFF
    mode_flags = ((t["mode"] & 0x0F) << 4) | (t["flags"] & 0x0F)
    return struct.pack(">iiHBBI", lat_i, lon_i, alt_i, bat, mode_flags, t["timestamp"])

def decode_binary(raw: bytes) -> dict:
    lat_i, lon_i, alt_i, bat, mode_flags, ts = struct.unpack(">iiHBBI", raw)
    return {
        "lat":       lat_i / 10000.0,
        "lon":       lon_i / 10000.0,
        "alt":       float(alt_i),
        "battery":   bat,
        "mode":      (mode_flags >> 4) & 0x0F,
        "flags":     mode_flags & 0x0F,
        "timestamp": ts,
    }

def encode_huffman(t: dict) -> tuple:
    ascii_bytes = encode_ascii(t)
    codec = HuffmanCodec.from_data(ascii_bytes)
    encoded = codec.encode(ascii_bytes)
    return encoded, codec

def decode_huffman(encoded: bytes, codec) -> dict:
    decoded_bytes = bytes(codec.decode(encoded))
    s = decoded_bytes.decode("ascii")
    parts = s.replace("$TELEM,", "").split(",")
    return {
        "lat": float(parts[0]), "lon": float(parts[1]),
        "alt": float(parts[2]), "battery": int(parts[3]),
        "mode": int(parts[4]), "flags": int(parts[5]),
        "timestamp": int(parts[6]),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "data", "gap6_telemetry.csv"))
    args = parser.parse_args()

    t = TELEMETRY
    ascii_raw        = encode_ascii(t)
    binary_raw       = encode_binary(t)
    huff_raw, codec  = encode_huffman(t)

    ascii_bits  = len(ascii_raw)  * 8
    binary_bits = len(binary_raw) * 8
    huff_bits   = len(huff_raw)   * 8

    # Verify decodes
    dec_bin  = decode_binary(binary_raw)
    dec_huff = decode_huffman(huff_raw, codec)

    print("=== Gap 6: Telemetry Encoding Comparison ===\n")
    print(f"{'Format':<12} {'Bytes':>6} {'Bits':>6} {'vs ASCII':>12} {'vs Binary':>12}")
    print("-" * 52)

    def vs(a, b):
        diff = a - b
        pct = (1 - b/a) * 100 if a > 0 else 0
        return f"-{diff} ({pct:.1f}%)" if diff > 0 else f"+{abs(diff)}"

    print(f"{'ASCII':<12} {len(ascii_raw):>6} {ascii_bits:>6} {'baseline':>12} {vs(ascii_bits,ascii_bits):>12}")
    print(f"{'Binary':<12} {len(binary_raw):>6} {binary_bits:>6} {vs(ascii_bits,binary_bits):>12} {'baseline':>12}")
    print(f"{'Huffman':<12} {len(huff_raw):>6} {huff_bits:>6} {vs(ascii_bits,huff_bits):>12} {vs(binary_bits,huff_bits):>12}")

    print(f"\n[VERIFY] Binary  decode: lat={dec_bin['lat']:.4f} lon={dec_bin['lon']:.4f} alt={dec_bin['alt']}")
    print(f"[VERIFY] Huffman decode: lat={dec_huff['lat']:.4f} lon={dec_huff['lon']:.4f} alt={dec_huff['alt']}")

    rows = [
        {"format": "ASCII",   "bytes": len(ascii_raw),  "bits": ascii_bits,
         "compression_vs_ascii_pct": 0.0},
        {"format": "Binary",  "bytes": len(binary_raw), "bits": binary_bits,
         "compression_vs_ascii_pct": round((1 - binary_bits/ascii_bits)*100, 1)},
        {"format": "Huffman", "bytes": len(huff_raw),   "bits": huff_bits,
         "compression_vs_ascii_pct": round((1 - huff_bits/ascii_bits)*100, 1)},
    ]
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[SAVED] {args.out}")

if __name__ == "__main__":
    main()
