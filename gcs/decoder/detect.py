"""
detect.py — GCS Layer 2: detect the encoding of a received BeiDou message and decode
it to a normalised survivor record.

Accepts whatever the portal stores in `msg_data`, in any of these forms:
    BIN:<hex28>                      (coded binary, what the sim/real portal stores)
    $CCTXM,0,BIN:<hex28>*CS          (full frame, e.g. if logged verbatim)
    $CCTXM,0,LAT:..,LON:..*CS         (ASCII baseline)
    汉字 / arbitrary text             (not a coordinate -> returned as type='text')

Returns a dict:
    {type, lat, lon, alt_m, r_cm, priority, survivor_id, bits, raw}
type is one of: 'binary', 'ascii', 'text', 'unknown'.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "python"))
from decode_binary import decode_binary  # noqa: E402


def _decode_ascii(frame: str):
    """Parse $CCTXM,id,LAT:<lat>,LON:<lon>*CS -> (lat, lon) or (None, None)."""
    try:
        clean = frame.split("*")[0]
        lat = lon = None
        for tok in clean.split(","):
            tok = tok.strip()
            if tok.startswith("LAT:"):
                lat = float(tok[4:])
            elif tok.startswith("LON:"):
                lon = float(tok[4:])
        return lat, lon
    except Exception:
        return None, None


def detect_and_decode(msg_data: str) -> dict:
    out = {"type": "unknown", "lat": None, "lon": None, "alt_m": None,
           "r_cm": None, "priority": None, "survivor_id": None, "bits": None,
           "raw": msg_data}
    if msg_data is None:
        return out
    s = msg_data.strip()

    # Normalise a bare "BIN:<hex>" into a frame decode_binary understands.
    if s.startswith("BIN:"):
        frame = f"$CCTXM,0,{s}"
    else:
        frame = s

    if "BIN:" in frame:
        lat, lon, alt, r_cm, pri, sid, bits = decode_binary(frame)
        if lat is not None:
            out.update(type="binary", lat=lat, lon=lon, alt_m=alt, r_cm=r_cm,
                       priority=pri, survivor_id=sid, bits=bits)
        return out

    if "LAT:" in frame and "LON:" in frame:
        lat, lon = _decode_ascii(frame)
        if lat is not None:
            out.update(type="ascii", lat=lat, lon=lon, bits=len(frame) * 8)
        return out

    # Not a coordinate payload (e.g. the old 汉字 "北斗" test messages).
    out["type"] = "text"
    return out


PRIORITY_LABEL = {0: "P0 (urgent)", 1: "P1 (normal)", 2: "P2 (low)"}


if __name__ == "__main__":
    samples = [
        "BIN:1D35DB5605079637007200A00101",
        "$CCTXM,0,LAT:49.0069,LON:8.4383*4F",
        "北斗",
    ]
    for s in samples:
        print(f"{s!r:48} -> {detect_and_decode(s)}")
