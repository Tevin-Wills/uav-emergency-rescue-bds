# beidou_short_message

**Owner:** Student 5 — Letsoalo Maile
**Responsibility:** BeiDou short message send/receive, coordinate encoding, decode,
and rescue-coordinate forwarding to ROS 2.

> Consolidated into `main` from the `feature/beidou-sms` branch (originally named
> `beidou_sms`). Renamed to the contract package name `beidou_short_message`.

---

## Hardware

| Component | Detail |
|-----------|--------|
| MCU | ESP32 dev board |
| BDS Module | BDS-SMC/RDSS (RS232-TTL adapter) |
| Wiring | BDS RXD→GPIO16, TXD→GPIO17, VCC→3.3V, GND→GND |
| PC Software | XCOM V2.0 |

---

## Package Structure

```
beidou_short_message/
├── firmware/
│   └── esp32_sender/esp32_sender.ino   # ESP32 sender — change MODE to switch encoding
├── scripts/
│   ├── serial_logger.py       # Log serial output to CSV
│   ├── decode_ascii.py        # Gap 1 ASCII decode
│   ├── decode_binary.py       # Gap 1 binary decode
│   ├── latency_analysis.py    # Gap 2 latency stats (mean 2.58 s over 30 TX)
│   ├── field_test_logger.py   # Gap 3 field test (4 environments)
│   └── telemetry_compare.py   # Gap 6 ASCII/Binary/Huffman comparison
├── data/                      # gap1/2/5/6 result CSVs
├── figures/                   # fig1–fig5 result plots
├── docs/
│   ├── SETUP_CHECKLIST.md     # Step-by-step hardware setup
│   └── Lab7_Report.md         # Full dissertation report template
├── generate_figures.py
└── README.md
```

---

## Firmware Modes

Edit `MODE` in `firmware/esp32_sender/esp32_sender.ino`:

| MODE | Encoding | Research Gap |
|------|----------|-------------|
| 0 | ASCII | Gap 1 baseline + Gap 2 latency |
| 1 | Binary fixed-point (64-bit) | Gap 1 compression |
| 2 | Dynamic Huffman | Gap 6 compression |

---

## Key Results (Gap 2 — Latency)

| Metric | Value |
|--------|-------|
| Mean | 2.58 s |
| Std Dev | 1.09 s |
| Min | 1.07 s |
| Max | 4.49 s |
| Decode overhead | 8.4 ms |

> UAV waypoint update rate must not exceed ~0.4 Hz on this channel.

---

## ROS 2 Integration

This module's analysis/firmware code is complete, but it is **not yet wired into the
ROS 2 graph**. To integrate, a thin ROS 2 node must wrap the decode logic and publish
on the **contract topics** below.

**Contract topics (from `interfaces/integration_contract.md`) — integration target:**

| Topic | Type | Description |
|-------|------|-------------|
| `/rescue/beidou_message` | Custom | Raw decoded BeiDou short message |
| `/target/emergency_coordinate` | Custom | Extracted rescue coordinate from message |

Consumers: `qgc_control` and `path_planning` subscribe to `/target/emergency_coordinate`
to plan and upload the mission.

> ⚠️ Integration gap: the module's own draft README used topic names
> `/beidou/rescue_coords` and `/beidou/send_message`. The **contract names above are
> authoritative** — the ROS 2 wrapper must publish those.

---

## Quick Start (standalone analysis)

```bash
pip install pyserial pycryptodome matplotlib pandas dahuffman
python scripts/serial_logger.py      # log serial output from ESP32
python scripts/latency_analysis.py   # Gap 2 latency
python scripts/telemetry_compare.py  # Gap 6 encoding comparison
```

---

## TODO (for full system integration)

- [ ] Add `package.xml` + `setup.py`/`CMakeLists.txt` to make this a buildable ROS 2 package
- [ ] Implement a ROS 2 node wrapping the decode logic
- [ ] Publish decoded coordinate to `/target/emergency_coordinate` (contract topic)
- [ ] Publish raw message to `/rescue/beidou_message`

---

## BDS Network Login

| Field | Value |
|-------|-------|
| Portal | http://bdrd.hwasmart.com/ |
| User 1 | RCSSTEAP_3058_SM_1 |
| User 2 | RCSSTEAP_3058_SM_2 |
| Password | 123456 |
