# BDS-SMC2 — Action Items & Suggestions Log
**Session Date:** 2026-06-11
**Purpose:** Reference document for all suggestions, changes, and decisions made during design review.
**Status:** Come back to this before dissertation submission and before Paper 2 starts.

---

## SECTION 1 — IMMEDIATE ACTIONS (Paper 1 Blockers)

### 1.1 Gap 2 Data Collection — CRITICAL, NOT DONE
- [ ] Run `.\run_gap2_midday.bat` — before noon, same outdoor location as baseline
- [ ] Run `.\run_gap2_evening.bat` — after 6pm, same day as midday
- [ ] Both auto-stop at 30 TX each
- [ ] Record weather + cloud % manually before each session
- [ ] Power on ESP32 → wait 2 minutes → run bat → power off immediately after

**Why:** Without midday + evening sessions, ANOVA cannot run. Gap 2 analysis is incomplete. Paper 1 cannot be submitted.

---

### 1.2 ROS Integration — CORRECTED 2026-06-12: group uses ROS 2, not ROS 1
- [x] ROS 2 node already exists: `ros2_ws/src/beidou_short_message/.../beidou_publisher_node.py` in the group repo (`TP UAV/uav-emergency-rescue-bds-main`)
- [x] Topics per integration contract: `/target/emergency_coordinate` (interfaces/EmergencyCoordinate) + `/rescue/beidou_message` (std_msgs/String)
- [x] Binary decode (112-bit + legacy 64-bit) added to the node (2026-06-12)
- [ ] Propose extending EmergencyCoordinate.msg with alt / uncertainty_m / priority / survivor_id — NEEDS GROUP AGREEMENT (their coordinate_format.md already documents altitude + priority)

**Why:** Original note said ROS 1 — wrong. The group workspace is ROS 2 (colcon/rclpy). Datum rule: sim coordinates derive from Zurich datum (`bringup/config/datum.yaml`) — never hardcode lab/test coordinates into the group pipeline.

---

### 1.3 Hardware Session Checklist — DO WHEN HARDWARE IS AVAILABLE (added 2026-06-12)
- [ ] **Portal reader activation:** log in at bdrd.hwasmart.com → F12 → Application → Local Storage → copy `data`, `access_token`, `refresh_token` into `python/portal_config.json` → run `python python/portal_reader.py --dump` to see real message fields → wire reader into decoder
- [ ] **OPTION B (2026-06-12): all Gap 2 sessions on the 112-bit payload.** Flash MODE 1 firmware ONCE — no mode switching all day. Old ASCII baseline archived as `data/gap2_latency_ascii_baseline.csv` (renamed, not deleted)
- [ ] **Gap 2 morning session** — `.\run_gap2_morning.bat` 08:00–10:00. TX #1 doubles as the 112-bit acceptance check: module accepts 28-char hex? [T3] + LED? On portal? **Portal shows packed binary (112 bits) or ASCII hex text (224 bits)?** Fallback if rejected: R→uint8 = 104 bits (PAPER 1 BLOCKER)
- [ ] **Gap 2 midday session** — `.\run_gap2_midday.bat` 12:00–14:00, same day (+ optional power measurement) (PAPER 1 BLOCKER)
- [ ] **Gap 2 evening session** — `.\run_gap2_evening.bat` after 18:00, same day (PAPER 1 BLOCKER)
- [ ] **Group meeting:** propose adding alt / uncertainty_m / priority / survivor_id to `EmergencyCoordinate.msg` (their coordinate_format.md already documents altitude + priority)

---

## SECTION 2 — FIRMWARE CHANGES (112-bit Rescue Payload Upgrade)

### 2.1 File: `firmware/esp32_sender.ino` — `sendBinary()` function

| Change | Current | New | Reason |
|---|---|---|---|
| Precision multiplier | `lat * 10000` (4dp, ~11m) | `lat * 10000000` (7dp, ~1cm) | Match RTK precision from lab system |
| Payload array | `uint8_t payload[8]` | `uint8_t payload[14]` | 6 new bytes for new fields |
| Add Altitude | Missing in binary mode | `int16_t alt_i` — bytes 8–9 | Required for 3D rescue positioning |
| Add Uncertainty R | Missing | `uint16_t r_cm` — bytes 10–11 (centimetres) | Critical — defines search radius for rescuers |
| Add Priority | Missing | `uint8_t priority` — byte 12 (0=P0, 1=P1, 2=P2) | Multi-survivor triage |
| Add Survivor ID | Missing | `uint8_t survivor_id` — byte 13 (0–255) | Multi-victim tracking |

**New byte layout:**
```
Bytes 0–3   → lat  (int32, ×10,000,000)
Bytes 4–7   → lon  (int32, ×10,000,000)
Bytes 8–9   → alt  (int16, metres)
Bytes 10–11 → R    (uint16, centimetres, 0–65535cm = 0–655m)
Byte  12    → priority (uint8: 0=P0, 1=P1, 2=P2)
Byte  13    → survivor_id (uint8: 0–255)
Total       → 14 bytes = 112 bits
```

**Time estimate:** 20 minutes coding + 1–2 hours hardware verification

---

### 2.2 File: `python/decode_binary.py`

| Change | Current | New |
|---|---|---|
| Struct format | `struct.unpack(">ii", raw)` | `struct.unpack(">iihHBB", raw)` |
| Lat/lon divisor | `/ 10000.0` | `/ 10000000.0` |
| Return values | `lat, lon, bit_count` | `lat, lon, alt, r_cm, priority, survivor_id, bit_count` |
| Round-trip test | Tests 4dp precision | Update to verify 7dp precision holds |

---

### 2.3 Hardware Verification Required
- [ ] Flash updated firmware to ESP32 (DIO mode, 40MHz, disconnect GPIO16/17 first)
- [ ] Send 1 test TX — confirm green LED flashes and [T3] Send Success appears in log
- [ ] Confirm BDS module accepts 28-character hex string (current is 16-character)
- [ ] If module rejects: fallback — reduce R to uint8 (1 byte, 0–255m) → total becomes 104 bits

**Risk:** BDS module `$CCTXM` content field may have its own buffer limit. Must verify physically.

---

## SECTION 3 — PAYLOAD FIELD SWAP ACCOUNTING

### What Was Removed vs Added

| Removed (old telemetry) | Bytes | Bits |
|---|---|---|
| Battery (uint8) | 1 byte | 8 bits |
| Mode (uint8) | 1 byte | 8 bits |
| Timestamp (uint32) | 4 bytes | 32 bits |
| **Total removed** | **6 bytes** | **48 bits** |

| Added (rescue fields) | Bytes | Bits |
|---|---|---|
| Uncertainty R (uint16) | 2 bytes | 16 bits |
| Priority (uint8) | 1 byte | 8 bits |
| Survivor ID (uint8) | 1 byte | 8 bits |
| **Total added** | **4 bytes** | **32 bits** |

**Net result: −2 bytes, −16 bits. Payload shrinks from 128 → 112 bits.**
**More rescue-critical data in fewer bits.**

---

## SECTION 4 — FIGURE UPDATES REQUIRED

### 4.1 Gap 1 Figure (`figures/gap1_encoding_comparison.png`)
- Current: ASCII 264 bits vs Binary **64 bits** = 75.8% reduction
- After upgrade: ASCII 264 bits vs Binary **112 bits** = 57.6% reduction
- [ ] Update `generate_figures.py` `fig_gap1()` — change binary bits from 64 to 112
- [ ] Update figure title to reflect rescue payload not coordinate-only

### 4.2 Gap 6 Figure (`figures/gap6_telemetry_comparison.png`)
- Current: Binary **128 bits** (−65% vs ASCII)
- After upgrade: Binary **112 bits** (−69.6% vs ASCII)
- Gap vs Huffman widens from 56 bits → **72 bits**
- [ ] Update `generate_figures.py` `fig_gap6()` — change binary bits from 128 to 112
- [ ] Update subtitle from `lat · lon · alt · battery · mode · flags · timestamp` to `lat(7dp) · lon(7dp) · alt · uncertainty(R) · priority · survivor ID`

**WARNING:** Changing the binary fields means the ASCII and Huffman baselines must be recalculated on the same rescue fields for the comparison to remain valid. Options:
- **Option A:** Keep same fields, only fix precision multiplier → binary drops 128→112, Huffman stays 184, ASCII stays 368. Safe and clean.
- **Option B:** Recompute all three bars on rescue-specific fields → new ASCII ≈440 bits, new Huffman ≈200–210 bits, binary = 112 bits. Stronger but requires rerunning Huffman on new string.

---

## SECTION 5 — LAB SYSTEM vs NODE COMPARISON

### Lab System Data (Supervisor)
```
T001: 49.0068822, 8.4383287, 114.2m, R1.6m,  P1
T002: 49.0070078, 8.4382004, 113.5m, R11.9m, P2
T003: 49.0070315, 8.4375595, 113.8m, R4.6m,  P2
T004: 49.0070212, 8.4376131, 114.5m, R1.6m,  P0
T005: 49.0071041, 8.4371681, 114.0m, R3.3m,  P0
T006: 49.0071067, 8.4371963, 114.0m, R2.0m,  P2
```

### Current Gap Between Node and Lab System

| Field | Lab System | Current Node | Gap |
|---|---|---|---|
| Survivor ID | T001–T006 | Missing | HIGH |
| Lat precision | 7 dp (~1cm) | 4 dp (~11m) | CRITICAL |
| Lon precision | 7 dp (~1cm) | 4 dp (~11m) | CRITICAL |
| Altitude | Real value | Missing in binary/ASCII | HIGH |
| Uncertainty R | Explicit (1.6m–11.9m) | Missing | CRITICAL |
| Priority/Class | P0/P1/P2 | Missing | HIGH |

**After 112-bit upgrade: all 6 gaps are closed.**

### Business Verdict
The lab system produces operationally complete rescue data but has no transmission layer.
The BDS-SMC2 node has a proven transmission layer (100% delivery, Gap 3) but carries an incomplete payload.
**The optimal rescue system = lab coordinate format encoded inside the BDS-SMC2 binary scheme.**
Result: 112 bits, full rescue fields, 100% delivery proven, 98 bits headroom under BDS limit.

---

## SECTION 6 — WEAKNESSES THAT RISK REJECTION

### Rejection-Level (Must Fix or Address)

| Issue | Detail | Fix |
|---|---|---|
| Hardcoded coordinates | `lat = 30.4196` hardcoded — no live GPS | Frame as testbed limitation OR connect GPS module before submission |
| T3 detection heuristic | `burstCount >= 3` declares success regardless of content | Add clear justification in paper or tighten detection logic |
| Huffman tree not transmitted | Decoder cannot work without the tree — undeployable as described | Either use static predefined Huffman table OR explicitly acknowledge in paper |
| No baseline comparison | No comparison vs LoRa, GSM, COSPAS-SARSAT | Add at least one existing system comparison from literature |
| 100% success rate suspicion | χ²=0.000, p=1.000 raises reviewer suspicion | Document every filtered `timeout` row with clear justification |

### Major (Will Trigger Revision)

| Issue | Fix |
|---|---|
| Encoding degrades RTK precision (4dp=11m) | Implement 112-bit upgrade (×10M multiplier) |
| Gap 2 single location only | Collect midday + evening sessions |
| Gap 2 morning session only | Collect midday + evening sessions |
| No power consumption data | Measure ESP32 + BDS module current draw during TX |
| No acknowledgment mechanism | Document as limitation — one-way communication only |

### Moderate (Acknowledge in Limitations Section)

| Issue |
|---|
| Single hardware unit tested — no generalisability claim |
| Third-party portal dependency (bdrd.hwasmart.com) — single point of failure |
| Destination ID hardcoded as 0 — no multi-unit addressing |
| "Indoor" environment not precisely defined |
| No worst-case latency analysis |
| Gap 1 bit-count overhead figure (+10) is approximate |

---

## SECTION 7 — DATA COLLECTION PLAN

### Paper 1 — Still Outstanding

| Session | Bat File | When | Status |
|---|---|---|---|
| Gap 2 Midday | `run_gap2_midday.bat` | Before noon | ❌ Not done |
| Gap 2 Evening | `run_gap2_evening.bat` | After 6pm | ❌ Not done |
| 112-bit verification TX | Flash new firmware, 1 TX | After firmware update | ❌ Not done |

### Paper 2 — Future Data Collection Required

| Dataset | Minimum Sample | Purpose |
|---|---|---|
| RTK → BDS TX accuracy | 30 TX per coordinate set | Quantify coordinate accuracy loss through transmission chain |
| GCS decode latency | 30+ samples | End-to-end system latency |
| Multi-survivor scenario | 3 full runs of 6 TX each | Validate survivor ID field and multi-victim tracking |
| ROS node publish rate | 50+ samples | Prove ROS integration is real-time capable |
| MAVLink injection latency | 20+ samples | Validate GCS software layer — Objective 5 |
| UAV positional error | Derived from Gap 2 data | No new hardware needed — modelled from existing latency data |

---

## SECTION 8 — TOOLS USED (FOR PRESENTATION)

| Tool | Used For | Why Chosen |
|---|---|---|
| Python | All scripts | Free, cross-platform, standard in academic research |
| `csv` (stdlib) | Data file reading | Built-in, no install, lightweight |
| `statistics` (stdlib) | Mean, median, std dev | Built-in, transparent and auditable |
| `math` (stdlib) | Wilson CI, ANOVA formulas | Built-in, formulas fully visible |
| `struct` (stdlib) | Binary encode/decode | Only correct tool for byte-level binary packing |
| `scipy.stats` | Chi-square, Fisher exact, ANOVA p-value | Industry-standard, peer-reviewed implementations |
| `matplotlib` | All dissertation figures | Publication-quality PNG, full layout control |
| `numpy` | Bar chart x-axis positioning | Minimal use — only for `np.arange` tick positioning |
| `HardwareSerial` (ESP32) | UART2 comms with BDS module | Built into ESP32 Arduino framework |
| `argparse` (stdlib) | CLI flags on analysis scripts | Built-in, makes scripts reproducible without code edits |

**Why NOT MATLAB:** Requires licence — not reproducible by examiners.
**Why NOT pandas:** Avoided deliberately — `csv` stdlib keeps analysis auditable for dissertation examiners.
**Why NOT ML libraries:** No training problem — all statistics are classical hypothesis tests.

---

## SECTION 9 — DISSERTATION FRAMING NOTES

### Data Classification
The collected data is **experimental ground-truth data**, not training data.
- Gap 2 morning session = **baseline reference** for time-of-day latency comparison
- Gap 3 field test data = **empirical evidence** for delivery reliability hypothesis
- Lab system (T001–T006) = **ground-truth coordinate reference** — your node is the transmission layer

### Recommended Wording — Lab Data
> *"Data collected in this study serves as experimental ground-truth evidence, with the Gap 2 morning session constituting the baseline reference for latency comparison across time-of-day conditions."*

### Recommended Wording — 112-bit Upgrade
> *"The initial binary encoding demonstrated a 75.8% size reduction for coordinate-only transmission. Building on this, a complete rescue payload incorporating survivor ID, altitude, uncertainty radius, and priority classification was designed within the same 112-bit binary scheme — achieving 57.6% reduction while carrying operationally complete rescue data, compared to Huffman's 184-bit partial payload."*

### Recommended Wording — Binary vs Huffman
> *"Binary encoding outperforms Huffman for structured numeric telemetry because it eliminates ASCII overhead entirely rather than compressing it. The proposed 112-bit rescue payload extends this finding — carrying a complete 6-field rescue message in 112 bits, 39% fewer bits than Huffman's 184-bit partial payload, while fitting within the BDS-3 210-bit limit with 98 bits to spare."*

---

## SECTION 10 — PAPER 2 SCOPE (FUTURE)

**Working Title:** *"End-to-End BDS-3 Short Message Rescue System: RTK Coordinate Injection, GCS Decoding, and UAV MAVLink Integration via ROS"*

**Prerequisite:** Paper 1 must be submitted first.

**What Paper 2 proves:** Paper 1 proves the transmission layer works. Paper 2 proves the full pipeline works (GPS → encode → transmit → decode → display → MAVLink).

**New hardware needed:**
- RTK GPS receiver (for live coordinate input)
- GCS computer running portal reader + decoder + map display
- MAVLink-compatible ground station (Mission Planner or QGroundControl)

**Software to build:**
- ROS 1 node wrapping serial logger (see Section 1.2)
- Portal reader (polls bdrd.hwasmart.com)
- BDS message decoder
- Map display layer
- MAVLink export layer

---

*Document last updated: 2026-06-11*
*All suggestions are discussion-only unless marked with a checkbox [x] indicating implementation.*
