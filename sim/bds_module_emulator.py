"""
bds_module_emulator.py — software twin of the BeiDou RDSS module (EVBKIT_V3).

This is the "virtual BeiDou link" that stands in for the physical RF uplink so the
dissertation end-to-end pipeline can be demonstrated while the hardware module is
faulty (see _photos/ and the 2026-06-15/16 bring-up notes: module powered but never
replies — serial/crossover fault).

WHAT IS REAL vs MODELLED
  REAL      : the $CCTXM command frame + XOR checksum (parsed/validated here exactly
              as the firmware builds it), the binary payload encode/decode, and the
              GCS decode→map→waypoint pipeline downstream.
  MODELLED  : the satellite uplink itself — replaced by this emulator, which returns
              the same module-ack (T2) and delivery-confirm (T3) lines the firmware
              listens for, after a latency drawn from the Gap-2 measured distribution
              (mean 2574.5 ms), with optional delivery-drop and RDSS service-interval
              rate limiting.

It can run two ways:
  1. In-process (sim/run_sim.py) — zero install, instant demo.
  2. Over a real serial port (a com0com virtual COM pair) — flash the REAL firmware,
     point it at the emulator, and it lights the green LED on [T3] just like the radio
     would have. See sim/README.md.

The module reply strings are chosen to satisfy the firmware's T2/T3 detection in
firmware/esp32_sender/esp32_sender.ino (indexOf "OK"/"CCTXM" for T2;
"RDTX"/"Send"/"0500" for T3).
"""

import os
import sys
import random
import time
from datetime import datetime, timezone

# Reuse the real decoder/encoder so the emulator and the dissertation agree byte-for-byte.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))
from decode_binary import decode_binary  # noqa: E402


# ── frame helpers (mirror esp32_sender.ino exactly) ───────────────────────────

def nmea_checksum(body: str) -> str:
    """XOR over every char of `body` AFTER the leading '$', as calcChecksum() does."""
    cs = 0
    for ch in body[1:]:          # skip '$'
        cs ^= ord(ch)
    return f"{cs:02X}"


def build_cctxm_binary(hex28: str, dest_id: int = 0) -> str:
    """Build the exact frame the firmware transmits: $CCTXM,<dest>,BIN:<hex>*<CS>\\r\\n"""
    body = f"$CCTXM,{dest_id},BIN:{hex28}"
    return f"{body}*{nmea_checksum(body)}\r\n"


def validate_frame(line: str):
    """Return (ok, reason, payload_field). payload_field is e.g. 'BIN:1D35...'."""
    line = line.strip()
    if not line.startswith("$CCTXM"):
        return False, "not a $CCTXM frame", None
    if "*" not in line:
        return False, "missing checksum delimiter", None
    body, cs = line.rsplit("*", 1)
    cs = cs.strip()
    want = nmea_checksum(body)
    if cs.upper() != want:
        return False, f"checksum mismatch (got {cs}, want {want})", None
    parts = body.split(",")
    if len(parts) < 3:
        return False, "too few fields", None
    return True, "ok", parts[2]          # 'BIN:<hex>' / 'LAT:..' / 'HUF:<hex>'


# ── the emulator ──────────────────────────────────────────────────────────────

class BdsModuleEmulator:
    """A faithful-enough RDSS module: validates a command, acks it (T2), then after a
    modelled uplink latency confirms delivery (T3) and emits a ground-station record."""

    def __init__(self, card_id="15590673", latency_mean_ms=2574.5, latency_sd_ms=600.0,
                 drop_rate=0.0, service_interval_s=0.0, seed=None, log=print):
        self.card_id = card_id
        self.latency_mean_ms = latency_mean_ms
        self.latency_sd_ms = latency_sd_ms
        self.drop_rate = drop_rate                 # 0.0 == 100% delivery (matches Gap 3)
        self.service_interval_s = service_interval_s  # RDSS civil min interval; 0 = off
        self.rng = random.Random(seed)
        self.log = log
        self._last_tx_time = None
        self.tx_count = 0

    # --- modelled physics -----------------------------------------------------
    def _sample_latency_s(self):
        ms = self.rng.gauss(self.latency_mean_ms, self.latency_sd_ms)
        return max(0.8, min(6.0, ms / 1000.0))

    def _rate_limited(self):
        if self.service_interval_s <= 0 or self._last_tx_time is None:
            return False
        return (time.time() - self._last_tx_time) < self.service_interval_s

    # --- the one entry point --------------------------------------------------
    def handle_command(self, line: str):
        """Process one command frame. Returns a dict describing the outcome:
            {ok, t2_reply, t3_reply, latency_s, delivered, record, decoded, reason}
        t2_reply/t3_reply are bytes to write back on the serial line (None if N/A)."""
        ok, reason, field = validate_frame(line)
        if not ok:
            # A real module answers a bad frame with an error code, not silence.
            return {"ok": False, "reason": reason,
                    "t2_reply": b"$CCERR,checksum\r\n", "t3_reply": None,
                    "latency_s": 0.0, "delivered": False, "record": None, "decoded": None}

        if self._rate_limited():
            wait = self.service_interval_s - (time.time() - self._last_tx_time)
            return {"ok": False, "reason": f"频度 rate-limit ({wait:.0f}s to next slot)",
                    "t2_reply": b"$CCERR,freq\r\n", "t3_reply": None,
                    "latency_s": 0.0, "delivered": False, "record": None, "decoded": None}

        self._last_tx_time = time.time()
        self.tx_count += 1

        # T2 — module accepted the command (mirrors firmware indexOf "OK"/"CCTXM").
        t2_reply = b"$CCTXM,OK*00\r\n"

        # Modelled uplink.
        latency_s = self._sample_latency_s()
        delivered = self.rng.random() >= self.drop_rate

        decoded = None
        record = None
        t3_reply = None
        if field.startswith("BIN:"):
            hex28 = field[4:]
            lat, lon, alt, r_cm, pri, sid, bits = decode_binary(f"$CCTXM,0,BIN:{hex28}")
            if lat is not None:
                decoded = {"lat": lat, "lon": lon, "alt_m": alt, "r_cm": r_cm,
                           "priority": pri, "survivor_id": sid, "bits": bits}
            msg_data = f"BIN:{hex28}"
            encode_type = True
        elif field.startswith("HUF:"):
            msg_data, encode_type = field, True
        else:  # ASCII LAT:..,LON:..
            msg_data, encode_type = field, True

        if delivered:
            # T3 — satellite delivered (mirrors firmware indexOf "RDTX"/"Send"/"0500").
            t3_reply = b"$RDTXA,0,Send Success,0500*00\r\n"
            record = {
                "card_id": self.card_id,
                "encode_type": encode_type,
                "msg_data": msg_data,
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            }
        else:
            t3_reply = b"$RDTXA,0,Send Fail,0501*00\r\n"

        return {"ok": True, "reason": "delivered" if delivered else "dropped",
                "t2_reply": t2_reply, "t3_reply": t3_reply, "latency_s": latency_s,
                "delivered": delivered, "record": record, "decoded": decoded}


# ── serial runner (for the com0com virtual-COM-pair path) ─────────────────────

def run_serial(port, baud=9600, portal_post=None, **kw):
    """Run the emulator on a real/virtual serial port. `portal_post(record)` is an
    optional callback (e.g. POST to sim/virtual_portal.py)."""
    import serial  # pyserial
    emu = BdsModuleEmulator(**kw)
    ser = serial.Serial(port, baud, timeout=0.2)
    print(f"[EMU] BDS module emulator on {port} @ {baud} — waiting for $CCTXM frames")
    buf = b""
    try:
        while True:
            chunk = ser.read(256)
            if chunk:
                buf += chunk
                while b"\n" in buf:
                    raw, buf = buf.split(b"\n", 1)
                    line = raw.decode("ascii", "replace").strip()
                    if not line:
                        continue
                    out = emu.handle_command(line)
                    if out["t2_reply"]:
                        ser.write(out["t2_reply"])
                    print(f"[EMU] RX {line}  -> {out['reason']}")
                    if out["t3_reply"]:
                        time.sleep(out["latency_s"])
                        ser.write(out["t3_reply"])
                        print(f"[EMU] T3 after {out['latency_s']:.2f}s: "
                              f"{out['t3_reply'].decode().strip()}")
                    if out["record"] and portal_post:
                        portal_post(out["record"])
    except KeyboardInterrupt:
        print("\n[EMU] stopped")
    finally:
        ser.close()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="BeiDou RDSS module emulator (serial mode).")
    ap.add_argument("--port", required=True, help="serial port, e.g. COM21 (com0com pair end)")
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--drop-rate", type=float, default=0.0)
    ap.add_argument("--service-interval", type=float, default=0.0,
                    help="RDSS civil min interval seconds (0=off)")
    a = ap.parse_args()
    run_serial(a.port, a.baud, drop_rate=a.drop_rate, service_interval_s=a.service_interval)
