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
- [x] Hardware wiring confirmed (ESP32 + BDS module + green LED on GPIO27)
- [x] Log in to http://bdrd.hwasmart.com/ — Username: RCSSTEAP_3058_SM_1 | Password: 123456
- [x] Upload firmware to ESP32 (COM14, ESP32 Dev Module, 115200 baud)
- [x] Confirmed XCOM/Serial Monitor receives response at 115200 baud
- [x] BOOT+RESET sequence confirmed: hold BOOT → press/release RESET → release BOOT → click Upload

## Firmware Fix — MUST DO FIRST NEXT SESSION
- [ ] **Step 1 — Open Arduino IDE**
  - File → Open → `firmware\esp32_sender\esp32_sender.ino`
  - T3 fix is already written in the file — no code changes needed
- [ ] **Step 2 — Select board and port**
  - Tools → Board → `ESP32 Dev Module`
  - Tools → Port → `COM14`
  - Tools → Upload Speed → `115200`
- [ ] **Step 3 — Upload using BOOT sequence**
  - Hold BOOT button on ESP32
  - Press and release RESET button
  - Release BOOT button
  - Click Upload arrow in Arduino IDE
- [ ] **Step 4 — Verify T3 fix works**
  - Open Tools → Serial Monitor, set baud to `115200`
  - Press EN button on ESP32
  - Wait for a transmission — you must see this line appear:
    ```
    [T3] Send Success
    ```
  - Green LED must flash when this appears
  - If you see only `[T1]` and `[T2]` but no `[T3]` — the fix did not upload correctly, repeat Step 3

## Gap 3 — Re-collect OS-1 (previous data invalid due to T3 bug)
- [ ] **Step 5 — Find a truly open-sky location**
  - No buildings, trees, or walls within 45° of the horizon in any direction
  - Point antenna toward the south (toward the equator — BeiDou GEO satellites are there)
  - Sports field centre or rooftop are ideal
- [ ] **Step 6 — Run OS-1 logger**
  - Double-click `run_gap2.bat` OR in terminal:
    ```
    python python/serial_logger.py --port COM14 --baud 115200 --session os1_redo --weather clear --cloud_pct 0
    ```
  - Send at least 20 transmissions
  - Confirm `latency_ms` column is filled (not empty) — this is how you know T3 is working

## Experiments — Status
- [x] Gap 1 — ASCII vs Binary encoding — **COMPLETE** (264 bits vs 64 bits, −75.8%)
- [~] Gap 2 — Latency measurement — **BASELINE DONE** (30 TX, mean=2.57s)
  - [ ] Midday session still needed: `--session midday`
  - [ ] Evening session still needed: `--session evening`
  - [ ] Run `gap2_analysis.py` after all 3 sessions collected
- [~] Gap 3 — Field test — **IN PROGRESS** (OS-1 redo needed, then 11 more locations)
  - [ ] OS-1 redo (open sky, no obstructions) — after firmware fix
  - [ ] OS-2 and OS-3 (two more open-sky spots)
  - [ ] LC-1, LC-2, LC-3 (light canopy / forest edge)
  - [ ] UC-1, UC-2, UC-3 (urban canyon / between buildings)
  - [ ] IN-1, IN-2, IN-3 (indoor — corridor, room, basement)
  - [ ] Run `gap3_analysis.py` after all 12 locations done
- [x] Gap 6 — Telemetry comparison — **COMPLETE** (ASCII=368b, Binary=128b, Huffman=184b)
