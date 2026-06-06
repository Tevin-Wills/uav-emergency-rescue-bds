# BDS-SMC2 — UAV BeiDou Rescue Communication System

Dissertation research project measuring the performance of BeiDou Short Message Communication (BDS-SMC/RDSS) for UAV search-and-rescue telemetry. The system runs on an ESP32 dev board and investigates four research gaps across encoding efficiency, transmission latency, environmental reception, and telemetry compression.

---

## Research Gaps Addressed

| Gap | Description | Status |
|-----|-------------|--------|
| Gap 1 | ASCII vs Binary coordinate encoding (bit-size) | Complete |
| Gap 2 | End-to-end latency (T1/T2/T3, 30 transmissions) | Baseline collected |
| Gap 3 | Field test delivery rate (4 envs × 3 locations × 20 TX) | Pending hardware |
| Gap 6 | Telemetry compression: ASCII / Binary / Huffman | Complete |

---

## Repository Structure

```
BDS-SMC2/
├── firmware/
│   └── esp32_sender/
│       └── esp32_sender.ino   # ESP32 firmware — change MODE to switch gap
├── python/
│   ├── serial_logger.py       # Logs all serial output to CSV
│   ├── decode_ascii.py        # Gap 1 — ASCII decode
│   ├── decode_binary.py       # Gap 1 — Binary decode
│   ├── latency_analysis.py    # Gap 2 — Latency stats
│   ├── field_test_logger.py   # Gap 3 — Field test (4 environments)
│   └── telemetry_compare.py   # Gap 6 — All-format comparison
├── data/
│   ├── gap1_compression.csv   # Gap 1 results
│   ├── gap2_latency.csv       # Gap 2 results
│   ├── gap3_field_test.csv    # Gap 3 results
│   └── gap6_telemetry.csv     # Gap 6 results
├── results/                   # Analysis output (generated locally)
├── SETUP_CHECKLIST.md         # Step-by-step hardware & software setup
└── Lab7_Report.md             # Full report template with gap sections
```

---

## Hardware Setup

| Component | Detail |
|-----------|--------|
| MCU | ESP32 dev board |
| BDS Module | BDS-SMC/RDSS module (RS232-TTL adapter) |
| Wiring | BDS RXD → GPIO16, TXD → GPIO17, VCC → 3.3V, GND → GND |
| LED | Green LED → GPIO27 |
| PC Software | XCOM V2.0 (receives BDS module responses) |

---

## Firmware Modes (edit `MODE` in `esp32_sender.ino`)

```cpp
int MODE = 0;  // 0=ASCII  1=Binary  2=Huffman (Gap 6)
```

| MODE | Gap | Description |
|------|-----|-------------|
| 0 | Gap 1, 2 & 3 | ASCII coordinate encoding — baseline |
| 1 | Gap 1 | Binary fixed-point encoding (64-bit vs 264-bit ASCII) |
| 2 | Gap 6 | Dynamic Huffman compression of full telemetry string |

---

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/letsoalomaile1/BDS-SMC2.git
cd BDS-SMC2
```

### 2. Install Python dependencies
```bash
pip install pyserial matplotlib pandas dahuffman scipy reportlab fpdf2
```

### 3. Flash firmware
- Open `firmware/esp32_sender/esp32_sender.ino` in Arduino IDE 1.8.19
- Set `MODE` to the experiment you want to run
- Select your COM port → Upload

### 4. Log serial output
```bash
python python/serial_logger.py
```

### 5. Run analysis
```bash
python python/latency_analysis.py      # Gap 2
python python/field_test_logger.py     # Gap 3
python python/telemetry_compare.py     # Gap 6
```

---

## BDS Network Login

| Field | Value |
|-------|-------|
| Portal | http://bdrd.hwasmart.com/ |
| User 1 | RCSSTEAP_3058_SM_1 |
| User 2 | RCSSTEAP_3058_SM_2 |
| Password | 123456 |

> Bind your BDS card using the ID + IMSI printed on the card back before first use.

---

## AT Command Format

```
$CCTXM,<destID>,<content>*<checksum>\r\n
```

Checksum = NMEA XOR of all bytes between `$` and `*`.

---

## Contributing / Teammate Workflow

1. **Fork or clone** this repo
2. **Create a branch** for your experiment: `git checkout -b gap3-field-test`
3. **Add your data** to `data/` and update the matching `.csv`
4. **Run the analysis script** to verify your numbers
5. **Open a Pull Request** — tag `@letsoalomaile1` for review

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed git workflow.

---

## Dependencies

| Tool | Version |
|------|---------|
| Arduino IDE | 1.8.19 |
| ESP32 board package | via Espressif mirror |
| Python | 3.14 |
| pyserial | latest |
| matplotlib | latest |
| pandas | latest |
| dahuffman | latest |

---

## License

Academic use only — dissertation project, Letsoalo Maile, 2026.
