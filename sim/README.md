# Virtual BeiDou Link — end-to-end simulation of the BDS-SMC2 rescue chain

This package lets the dissertation demonstrate the **complete** rescue data path —
survivor coordinate → BeiDou short message → ground portal → GCS decode → map →
UAV waypoint — **without** a working RF module. The physical satellite uplink is the
one link that is replaced by a software model; every other stage is the project's
real code.

## Why this is methodologically sound

The satellite uplink is **not the contribution** of this dissertation — BeiDou RDSS is
established commercial infrastructure (Li G. et al., *Adv. Space Res.* 67(5), 2021,
reports 97.72 % over 2149 TX). The contribution is the **encoding** of rescue
coordinates into a 112-bit short message and the **GCS pipeline** that decodes and
dispatches it. Both are software and are fully validated here. Replacing an
unavailable RF link with a Hardware/Software-in-the-Loop model is standard practice.

### What is REAL vs MODELLED

| Stage | Status | Notes |
|-------|--------|-------|
| `$CCTXM` command frame + XOR checksum | **REAL** | byte-identical to `firmware/esp32_sender.ino` (verified: `…00A00101*05`) |
| 112-bit payload encode / decode | **REAL** | reuses `python/decode_binary.py` (round-trips T001–T006) |
| Module ack (T2) / delivery (T3) replies | **MODELLED** | strings chosen to satisfy the firmware's real T2/T3 detector |
| Uplink latency | **MODELLED** | drawn from Gap-2 measured distribution (mean 2574.5 ms) |
| Delivery success | **MODELLED** | default 100 % (matches Gap-3 field result); `--drop-rate` to vary |
| Portal record shape | **REAL** | `{card_id, encode_type, msg_data, created_at}` — same as the live portal |
| GCS decode → map → waypoint | **REAL** | `gcs/` package, unchanged for sim vs live |

Document this table in the methodology chapter and the emulation boundary is fully defensible.

## Run it

```bash
# One-command full demo (instant): 6 survivors T001–T006
python sim/run_sim.py

# Variants
python sim/run_sim.py --n 3 --realtime      # actually wait the modelled latency
python sim/run_sim.py --drop-rate 0.1        # model 10 % delivery loss
```

Outputs:
- `gcs/output/map.html` — Leaflet map, one pin + uncertainty circle per survivor (open in a browser)
- `gcs/output/survivor.waypoints` — QGC WPL 110 mission (load in QGroundControl / Mission Planner)
- `data/portal_inbox_sim.csv` — portal records (same shape as the real inbox)
- `data/sim_latency.csv` — Gap-2-schema latency rows, tagged `source=sim` (never mixed with field data)

Run the GCS layer on its own against either source:
```bash
python gcs/main.py --source sim     # the records sim/run_sim.py produced
python gcs/main.py --source live    # the real data/portal_inbox.csv (2025 portal capture)
```

## Authentic path — real firmware over a virtual COM pair (optional)

If you want the **actual ESP32 firmware** in the loop (lights the green LED on [T3]
exactly as the radio would have), use a com0com virtual serial pair instead of the
in-process link:

1. Install **com0com** (Null-modem emulator). Create a pair, e.g. `COM20 ⇄ COM21`.
2. Flash the unmodified `firmware/esp32_sender.ino`, but route its UART2 to the PC
   pair end (or bridge COM14's `[BINARY TX]` line — see `sender_bridge.py`).
3. Start the module emulator on the other end:
   ```bash
   python sim/bds_module_emulator.py --port COM21
   ```
4. (optional) Start the HTTP portal so the unmodified reader works:
   ```bash
   python sim/virtual_portal.py          # serves http://127.0.0.1:8799
   ```
   then point `python/portal_reader.py`'s `BASE_URL` at it.

The emulator validates the frame, replies T2 then T3 after the modelled latency, and
posts a portal record — the firmware sees `[T2]` / `[T3] Send Success` and flashes the
green LED, just like a successful transmission.

## Files

| File | Role |
|------|------|
| `bds_module_emulator.py` | software twin of the EVBKIT_V3 RDSS module (the link model) |
| `virtual_portal.py` | local portal store + HTTP API mimicking `bdrdserver.hwasmart.com` |
| `run_sim.py` | one-command in-process end-to-end demo |
| `../gcs/` | the real GCS pipeline: detect → map → waypoint |
