# BDS-SMC2 — Full Progress Checklist
**As of 2026-06-14.** Everything we planned from the start, what's done, and what's left (hardware vs no-hardware).

## ✅ DONE (no hardware) — built, tested, working

### Payload & encoding
- [x] 112-bit rescue payload designed (lat/lon 7dp, alt, R, priority, survivor_id)
- [x] Firmware `sendBinary()` rewritten to 14-byte payload (MODE 1 default)
- [x] `decode_binary.py` rewritten; round-trip bit-perfect on lab T001–T006
- [x] Gap 1 figure: 264 vs 112 bits (−57.6%)
- [x] Gap 6 figure + data: 368/184/112 bits (98 spare, beats Huffman 39%)

### Group integration (ROS 2)
- [x] Corrected ROS 1 → ROS 2 (group uses colcon/rclpy)
- [x] `beidou_publisher_node` decodes ASCII + 112-bit + legacy 64-bit
- [x] Ubuntu runbook + `verify_integration.sh` written
- [x] PR branch `node/binary-decode` pushed (3-file clean diff)

### Receive chain (PROVEN LIVE)
- [x] Portal API reverse-engineered (getHistoryMsg, 1-based offset, real fields)
- [x] `portal_reader.py` — verify-first auth, pulls real messages
- [x] **Logged in, got tokens, fetched 4 real messages into portal_inbox.csv** ✓
- [x] Token rotation handled (verify-first; clear re-copy message on expiry)

### Dashboard
- [x] `tx_dashboard.py` — payload journey dots, bit-perfect TX↔portal match, black-box Δt
- [x] `--sim` presentation mode (animates T001–T006)
- [x] In-flight live row; verified showing real portal data
- [x] `--mock-portal` mode for the full mock loop

### Auto-pipeline (mock)
- [x] `auto_sender.py` — watch CSV → auto-transmit each new row (`--mock`)
- [x] `feed_coords.py` — demo feeder (simulates upstream source)
- [x] Mock writes matching portal receipts → full CONFIRMED loop, no hardware
- [x] DESIGN_auto_sender.md (serial protocol + firmware parser for field day)

### Paper & docs
- [x] Node evaluation: 10-risk buyer table + remediation plan (audited)
- [x] Data audit — every number re-derived from raw CSVs (fixed 237→232, etc.)
- [x] Paper 1 Sections I–IV drafted (BDS_SMC2_Paper1_Draft.md)
- [x] Paper 1 Sections V–VIII drafted with fillable ⟦SLOT⟧ markers
- [x] gap2_analysis.py prints [PAPER SLOTS] block to fill them
- [x] Defence sections: comparison table, Wilson claim, exclusion appendix, repeat-TX policy
- [x] References R1–R4 verified (R5/R6 marked VERIFY)
- [x] Paper Plan Rev.2, Field Sheet (4-sheet), Progress Report, Presentation updated
- [x] Three-document structure mapped (BDS_SMC2_Document_Structure.md)
- [x] Workflow illustrations (route, dashboard, project Obj1–5, dashboard+Gazebo)
- [x] Linux run guide (LINUX_RUN_GUIDE.md)

## 🔶 TO DO — NO HARDWARE (can do now)

- [ ] Build retry → recycle → 5-lap cap → NEEDS ATTENTION flag (auto_sender + dashboard) — designed, mockable
- [ ] Verify R5 + R6 references at the library (~30 min)
- [ ] Open the PR on GitHub (one click) once network allows
- [ ] Push the 3 pending local commits (`git push origin node/bds-smc2`) — blocked by network/SSL only
- [ ] Group meeting: propose EmergencyCoordinate.msg extension (pack ready)
- [ ] (Optional) Make auto_sender mock write to its own file (not gap2_latency.csv)
- [ ] (Optional, Linux) Unified dashboard: Gazebo camera tile + ROS panels

## ❌ NEEDS HARDWARE — the field day (one outing)

- [ ] Flash command-mode firmware (serial TX parser) + 112-bit payload
- [ ] First TX: confirm module accepts 28-char hex (go/no-go) + on-air bit check
- [ ] Gap 2 morning session (30 TX, 112-bit) — Option B
- [ ] Gap 2 midday session (30 TX) + optional power measurement
- [ ] Gap 2 evening session (30 TX)
- [ ] Live portal corroboration (green CONFIRMED rows screenshotted)
- [ ] Run gap2_analysis.py → fill Paper 1 ⟦SLOT⟧ markers → Paper 1 evidence complete

## ❌ NEEDS THE GROUP MACHINE

- [ ] colcon build + verify_integration.sh (3/3) on Ubuntu
- [ ] Side-by-side demo: dashboard + Gazebo joined by ROS
- [ ] (Paper 2) live RTK feed, full pipeline latency budget

## Scoreboard
**Building: essentially complete.** Every remaining item is collect (field day), confirm
(library/group), or one optional feature (retry-flag). The project's bottleneck is now
calendar + hardware access, not work.
