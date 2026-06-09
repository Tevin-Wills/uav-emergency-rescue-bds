# beidou_sms

**Owner:** Member 5 — Letsoalo Maile
**Responsibility:** BeiDou short message send/receive, coordinate encoding, and rescue coordinate forwarding to ROS 2.

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
beidou_sms/
├── firmware/
│   └── esp32_sender/
│       └── esp32_sender.ino   # ESP32 sender — change MODE to switch encoding
├── scripts/
│   ├── serial_logger.py       # Log serial output to CSV
│   ├── decode_ascii.py        # Gap 1 ASCII decode
│   ├── decode_binary.py       # Gap 1 binary decode
│   ├── latency_analysis.py    # Gap 2 latency stats (mean 2.58s over 30 TX)
│   ├── field_test_logger.py   # Gap 3 field test (4 environments)
│   └── telemetry_compare.py   # Gap 6 ASCII/Binary/Huffman comparison
├── data/
│   ├── gap1_compression.csv   # Encoding bit-size results
│   ├── gap2_latency.csv       # 30-transmission latency log
│   ├── gap5_encryption.csv    # AES-128 overhead results
│   └── gap6_telemetry.csv     # Compression comparison results
├── docs/
│   ├── SETUP_CHECKLIST.md     # Step-by-step hardware setup
│   └── Lab7_Report.md         # Full dissertation report template
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

**Published topic:** `/beidou/rescue_coords`
Decoded lat/lon from incoming BDS short message → forwarded to `path_planning`.

**Subscribed topic:** `/beidou/send_message`
Outgoing message requests from ground control.

---

## Quick Start

```bash
# Install Python deps
pip install pyserial pycryptodome matplotlib pandas dahuffman

# Log serial output from ESP32
python scripts/serial_logger.py

# Analyse latency (Gap 2)
python scripts/latency_analysis.py

# Compare encoding formats (Gap 6)
python scripts/telemetry_compare.py
```

---

## BDS Network Login

| Field | Value |
|-------|-------|
| Portal | http://bdrd.hwasmart.com/ |
| User 1 | RCSSTEAP_3058_SM_1 |
| User 2 | RCSSTEAP_3058_SM_2 |
| Password | 123456 |
