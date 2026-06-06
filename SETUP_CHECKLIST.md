# BDS-SMC2 UAV Rescue System — Setup Checklist

## Software Install (PC) ✅ COMPLETE
- [x] Python 3.14 installed
- [x] pip install pyserial matplotlib pandas dahuffman scipy reportlab fpdf2 — all installed
- [x] Arduino IDE 1.8.19 installed
- [x] ESP32 board package installed (China mirror: https://dl.espressif.cn/dl/package_esp32_index.json)
- [x] XCOM V2.0 already installed
- [x] Sketch compiles clean (287 KB, 21% flash)

## Firmware ✅ COMPLETE
- [x] esp32_sender.ino — MODE 0 ASCII (Gap 1 & 2 & 3)
- [x] esp32_sender.ino — MODE 1 Binary (Gap 1)
- [x] esp32_sender.ino — MODE 2 Huffman (Gap 6)
- [x] Coordinates set: lat=30.4196, lon=120.2977 (Yuhang District, Hangzhou)
- [x] AT command format confirmed: $CCTXM,<destID>,<content>*<CS>\r\n

## Python Scripts ✅ COMPLETE
- [x] serial_logger.py — logs all serial output to CSV
- [x] decode_ascii.py — Gap 1 ASCII decode (updated format)
- [x] decode_binary.py — Gap 1 binary decode (updated format + Hangzhou coords)
- [x] latency_analysis.py — Gap 2 latency stats
- [x] field_test_logger.py — Gap 3 field test (fixed timeout/failure detection)
- [x] gap2_analysis.py — Gap 2 ANOVA + CDF + UAV error model
- [x] gap3_analysis.py — Gap 3 chi-square + Fisher's exact + Wilson CI
- [x] telemetry_compare.py — Gap 6 all-format comparison (ASCII / Binary / Huffman)

## Lab Report ✅ COMPLETE
- [x] Lab7_Report.md — full report template with all Gap sections and result tables

---

## Hardware (needs lab kit)
- [ ] Hardware wiring (see Lab7_Report.md Section 2.1)
- [ ] Log in to http://bdrd.hwasmart.com/ and bind BDS card (ID + IMSI from card back)
  - Username: RCSSTEAP_3058_SM_1 or RCSSTEAP_3058_SM_2 | Password: 123456
- [ ] Upload firmware to ESP32 (select COM port, click Upload)
- [ ] Confirm XCOM receives response (press EN on ESP32)

## Experiments (needs hardware + outdoor)
- [ ] Gap 1 — ASCII vs Binary encoding (run both modes, record bit sizes)
- [ ] Gap 2 — Latency measurement (30 transmissions, MODE=0, open sky)
- [ ] Gap 3 — Field test (4 environments × 3 locations × 20 transmissions)
- [ ] Gap 6 — Telemetry comparison (run telemetry_compare.py, fill Lab7_Report.md table)
