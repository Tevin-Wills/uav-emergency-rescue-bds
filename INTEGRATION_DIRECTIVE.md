# BDS-SMC2 — INTEGRATION DIRECTIVE

**Purpose:** stand up the *entire* rescue chain — survivor coordinate → BeiDou short
message → ground portal → GCS decode → map/waypoint → **live dashboard** — with the
broken RF module replaced by a software emulator. Drop this file into a Claude Code
session (or read it yourself) and execute it top to bottom. When you are done, one
command brings the whole stack up in a browser.

This is a directive, not a discussion. Build what is specified. Do not invent parallel
systems. Do not "improve" the wire formats. If the acceptance checks at the bottom do
not pass, it is not done.

---

## 0. NON-NEGOTIABLE GROUND RULES

1. **Only the satellite RF hop is simulated.** Everything else is the project's real
   code. Do not fake the encode, the decode, the portal record shape, or the dashboard.
2. **Do not touch the wire contracts in §2.** The firmware, the decoder, the portal
   reader and the dashboard already agree on them. Change one, you break the chain.
3. **Do not modify** `firmware/esp32_sender.ino`, `python/decode_binary.py`, or the
   group ROS 2 interface. They are upstream truth. Integrate *around* them.
4. **Honesty boundary:** the methodology chapter must state what is real vs modelled.
   The table is in `sim/README.md`. Keep it accurate.
5. Windows console is cp1252. Every script that prints must call
   `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` or it dies on `·`/汉字.

---

## 1. THE PIPELINE

**Input:** the node reads the survivors it sends from `data/outgoing_coords.csv`
(`sim/coords.py`). Edit that file to change what gets transmitted; empty/missing →
built-in lab set T001–T006.

```
  data/outgoing_coords.csv ─┐
  (lat,lon,alt,r_cm,pri,id) │
  ┌── software ESP32 sender ─▼─┐   ┌─ BDS module emulator ─┐   ┌─ virtual portal ─┐
  │ encode 112-bit payload    │   │ validate $CCTXM frame │   │ store record     │
  │ build $CCTXM,...*CS  ──────┼──▶│ T2 ack                │   │ {card_id,        │
  │ (REAL firmware format)    │   │ model uplink latency  │   │  encode_type,    │
  └───────────────────────────┘   │ T3 "Send Success" ────┼──▶│  msg_data,       │
                                   │ decode + emit record  │   │  created_at}     │
                                   └───────────────────────┘   └────────┬─────────┘
                                                                         │
   ┌──────────────────────────── GCS (real) ────────────────────────────┘
   │ detect BIN/ASCII → decode → map.html + survivor.waypoints + ROS2 EmergencyCoordinate
   └───────────────────────────────────┬─────────────────────────────────
                                        │
                       ┌────────────────▼───────────────┐
                       │  DASHBOARD  (tx_dashboard.py)   │  ← TOP OF STACK
                       │  TX→T2→T3→PORTAL→DECODED, live  │
                       └────────────────────────────────┘
```

---

## 2. WIRE CONTRACTS (frozen — match these exactly)

**Command frame** (firmware `sendBinary()`):
```
$CCTXM,0,BIN:<28 hex>*<XX>\r\n
  payload = struct ">iihHBB": lat int32 e7, lon int32 e7, alt int16 m,
            R uint16 cm, priority u8, survivor_id u8   (14 bytes = 112 bits)
  <XX>    = XOR of every char AFTER '$', uppercase hex
  e.g.    $CCTXM,0,BIN:1D35DB5605079637007200A00101*05   (lab T001)
```

**Module replies** (what the emulator must send; firmware's T2/T3 detector keys on these):
```
T2 (accepted) : a line containing "OK" or "CCTXM"     → e.g. $CCTXM,OK*00
T3 (delivered): a line containing "RDTX"/"Send"/"0500" → e.g. $RDTXA,0,Send Success,0500*00
```

**Portal record** (one JSON object per delivered message, real portal shape):
```json
{"card_id":"15590673","encode_type":true,"msg_data":"BIN:<28 hex>","created_at":"<ISO8601 Z>"}
```

**TX latency CSV** (`data/sim_latency.csv`, dashboard-readable, = gap2 schema):
```
tx_num,session,weather,cloud_pct,datetime,t1,t2,t3,tx_latency_ms,decode_latency_ms,total_latency_ms,payload,note
  delivered → t3 = ms timestamp, total_latency_ms = ms
  lost      → t3 = "" , total_latency_ms = "-1"   (dashboard shows TIMEOUT)
```

**Live in-flight state** (`data/live_state.json`, dashboard animates it):
```json
{"state":"in_flight","tx_num":N,"session":"sim-live","t1":true,"t2":true,"t3":false,"payload":"$CCTXM...","updated":<epoch>}
```

---

## 3. COMPONENT INVENTORY (verify each exists and does its one job)

| File | Job | Must |
|------|-----|------|
| `data/outgoing_coords.csv` | pipeline INPUT / injection interface | one survivor per row; Objective 4 appends here |
| `sim/coords.py` | input loader | read the CSV; `fallback=True` demo→T001–T006, `fallback=False` watch→[] |
| `sim/objective4_emit.py` | Objective 4 stand-in | append a coordinate row (the injection-interface contract) |
| `firmware/esp32_sender.ino` | real encoder (untouched) | source of the frame format in §2 |
| `python/decode_binary.py` | real decoder (untouched) | `decode_binary()` round-trips T001–T006 |
| `sim/bds_module_emulator.py` | software twin of EVBKIT_V3 module | validate frame, T2, model latency+drop, T3, emit record |
| `sim/virtual_portal.py` | local portal | `PortalStore` (file) + HTTP API mimicking `bdrdserver.hwasmart.com` |
| `gcs/decoder/detect.py` | detect BIN/ASCII/text | normalise `msg_data` → survivor dict |
| `gcs/display/map_view.py` | Leaflet map | `gcs/output/map.html`, pin + R circle per survivor |
| `gcs/export/waypoint.py` | UAV tasking | QGC WPL 110 `.waypoints` + ROS2 `EmergencyCoordinate` map |
| `gcs/main.py` | GCS orchestrator | `--source sim|live` |
| `sim/run_sim.py` | batch end-to-end | one pass, prints TX→T3→portal→GCS |
| `sim/run_all.py` | **the integrator** | continuous feeder + launches dashboard |
| `python/tx_dashboard.py` | the dashboard | `--sim-data` reads `sim_latency.csv` + `portal_inbox_sim.csv` |

If any are missing, build them to the contracts in §2. Do not rename files; the
launcher and dashboard reference these exact paths.

---

## 4. INTEGRATION STEPS (idempotent — verify, then build only what's missing)

1. **Confirm the contracts.** `python python/decode_binary.py` → must print
   "Round-trip ALL OK". This proves encode/decode agree with the firmware.
2. **Confirm the emulator speaks the frame.**
   `python -c "import sys;sys.path.insert(0,'sim');import bds_module_emulator as m;print(m.nmea_checksum('$CCTXM,0,BIN:1D35DB5605079637007200A00101'))"`
   → must print `05`.
3. **Confirm the batch chain.** `python sim/run_sim.py --n 6` → must end with
   "6/6 delivered" and write `gcs/output/map.html` + `gcs/output/survivor.waypoints`.
4. **Confirm the dashboard reads sim data.** `python python/tx_dashboard.py --sim-data`
   must start; the page at `http://localhost:8765` must show 6 TX, all CONFIRMED /
   bit-perfect. (Stop it after checking.)
5. **Wire it into one command.** `sim/run_all.py` must: clear stale sim files, run the
   feeder (a TX every `--interval` s), write `sim_latency.csv` + `portal_inbox_sim.csv`
   + `live_state.json`, launch `tx_dashboard.py --sim-data`, open the browser, and on
   Ctrl+C refresh `gcs/main.py --source sim`.

---

## 5. LAUNCH SEQUENCE

```bash
# THE one command — full live stack in the browser (DEMO: cycles the CSV):
python sim/run_all.py
#   options: --interval 6   --drop-rate 0.1   --port 8765   --no-browser

# EVENT-DRIVEN — node waits, transmits when Objective 4 emits a coordinate:
python sim/run_all.py --watch
#   then, from Objective 4 (or the stand-in):
python sim/objective4_emit.py --lat 47.3971 --lon 8.5462 --priority 0
#   (Objective 4 = RTK/position module. Contract: append one row
#    lat,lon[,alt,r_cm,priority,survivor_id] to data/outgoing_coords.csv.
#    Only lat,lon required; the node transmits each new row automatically.)

# Batch (no server), good for a deterministic screenshot/log:
python sim/run_sim.py --n 6

# GCS only, against real captured 2025 portal data:
python gcs/main.py --source live

# Dashboard only (if you fed the sim files some other way):
python python/tx_dashboard.py --sim-data
```

---

## 6. ACCEPTANCE CRITERIA (definition of done — all must hold)

- [ ] `python sim/run_sim.py --n 6` prints **6/6 delivered**.
- [ ] First TX frame is exactly `$CCTXM,0,BIN:1D35DB5605079637007200A00101*05`.
- [ ] `gcs/output/map.html` exists and pins 6 survivors; P0 (T004/T005) render red.
- [ ] `gcs/output/survivor.waypoints` is valid `QGC WPL 110`, P0 ordered first.
- [ ] `python sim/run_all.py` opens a dashboard that shows live rows climbing
      TX → T2 → T3 → PORTAL, summary cards reading Confirmed/Bit-perfect, mean
      latency ≈ 2.4 s.
- [ ] `--drop-rate 0.1` produces visible TIMEOUT rows (modelled loss).
- [ ] `python gcs/main.py --source live` reads the real 2025 capture and labels the
      four 「北斗」 rows as non-coordinate text (proves the decoder runs on real data).

If every box is ticked, the dissertation can demonstrate the complete system end to
end and the only stated limitation is the emulated RF uplink — which is documented.

---

## 7. KNOWN GOTCHAS

- cp1252 console → reconfigure stdout to utf-8 (see §0.5).
- `run_sim.py` and `run_all.py` **reset** `sim_latency.csv` + `portal_inbox_sim.csv`
  at start so a run shows only its own messages. Don't "fix" this into append mode.
- Alt is int16 metres by design — sub-metre altitude is intentionally lost in the
  112-bit payload. Not a bug.
- The dashboard's own `--sim` flag is the OLD synthetic animation (no real pipeline).
  For the integrated stack use `--sim-data` (or just run `sim/run_all.py`).
- Real-firmware-in-the-loop path (com0com virtual COM pair) is in `sim/README.md`;
  it is optional and does not block the software demo.

---

## 8. KICKOFF PROMPT  (paste this into a fresh Claude Code session in this repo)

> Read `INTEGRATION_DIRECTIVE.md` in the repo root and bring up the full BDS-SMC2
> stack it specifies (encode → BDS module emulator → virtual portal → GCS →
> dashboard), with the satellite RF hop simulated.
>
> Do this:
> 1. Run the §6 acceptance checks. For each, report PASS/FAIL with the evidence line.
> 2. If anything is missing or FAILs, build/fix it to the §2 wire contracts only —
>    do not modify `firmware/esp32_sender.ino`, `python/decode_binary.py`, or the
>    group ROS 2 interface, and do not change the frame/portal/CSV formats.
> 3. When all §6 boxes pass, start the integrated stack with `python sim/run_all.py`
>    and give me the dashboard URL plus the paths to `gcs/output/map.html` and
>    `gcs/output/survivor.waypoints`.
> 4. Summarise, in 5 lines, what is REAL vs MODELLED, citing `sim/README.md`.
>
> Constraint: only the satellite uplink may be simulated; every other stage must be
> the project's real code. Keep the cp1252/utf-8 rule. Stop and ask only if an
> acceptance check cannot be made to pass.
