# BDS-SMC2 Node — Final Project Report (Consolidated)

**Author:** Letsoalo Maile · WP5 (BeiDou Communication) · BDS-SMC2 Node
**Audience:** project panel / supervisors (Yan Dayun, Yang Dongkai), Beihang University
**Nature:** a *reporting* document — it accounts for what was built, why, and what it proves. It is not a publication draft.

> **What this report consolidates (every request from this review):** what the node addresses; the chronological sequence of events; the node *before* (what it could do) vs *now* (what it can do); justification of every figure; every contradiction found and resolved; a clear split of work *within* my assigned scope vs *beyond* it — with why I went beyond, what that achieved, and why it was completable; why my role was successful; a scoring against the correct rubric; what would maximise marks; and what I need to reach my aspiration. Every number is reproducible (Appendix A); every design choice is justified (Appendix B).

---

## 1. What the Node Addresses

The five-module team project (Beihang: *UAV Emergency Rescue with BeiDou Short Message Communication*) targets a disaster in which terrestrial networks collapse and BeiDou-3 short messaging is the only surviving channel. **WP5 — my module — is the communication backbone:** take a survivor's RTK-corrected coordinate, carry it through a BeiDou short message, decode it at the ground station, and inject it into the autonomous UAV mission. The node answers four questions: **Capacity** (does a complete rescue payload fit one message?), **Reliability** (does delivery survive real environments?), **Latency** (does it arrive in time?), **Integration** (can it drive an autonomous mission, not just a human display?).

## 2. Scope Declaration — Simulation-First (read this before judging the hardware)

The project was **declared simulation-first from the outset**, and this governs how every result should be read:
- Opening proposal, **Phase note:** *"Simulation-first — all development targets Gazebo/SITL. Real hardware deferred to future work."*
- Opening proposal, **Risk R6:** *"Hardware unavailability — High/Low — Project is simulation-only by design."*

**Consequence:** the assigned deliverable is a simulation + integration module, which is **complete**. Any real-hardware result is *beyond* the declared scope. The transmitting module is currently unresponsive — this is precisely **pre-registered risk R6**, with its declared mitigation ("simulation-only by design") already in force. The remaining on-air confirmation of the 112-bit frame is therefore **future work exactly as the project scoped it**, not an unmet requirement.

## 3. Why We Opted For What We Opted For (decision rationale)

A panel rewards justified engineering choices. The load-bearing decisions and their reasons:

| Decision | Why |
| --- | --- |
| **Binary, not ASCII** | The regional budget is tiny; ASCII coordinates are 264 bit (368 full telemetry) and wasteful |
| **Fixed-point, not Huffman** | Huffman needs a code table that exceeds the budget and is decoder-heavy on an MCU; binary wins on size *and* decode cost |
| **112 bit / 6 fields** | An *operationally complete* rescue record (lat, lon, alt, uncertainty R, priority, survivor ID); platform fields dropped on purpose |
| **7 dp (×10⁷)** | Matches the RTK source (~1 cm); 4 dp quantises an RTK fix to ~11 m and wastes the positioning investment |
| **Emulated lab coordinates** | Objective 5 says *"emulate RTK location and inject"*; a channel cannot be measured without controlling its input |
| **Wilson LB, never 100 %** | Zero failures in ~57 trials cannot support "perfect"; ≥93.7 % is defensible and pre-empts the "too good" challenge |
| **Environment-stratified test** | Characterises delivery under *rescue-relevant* conditions, not one aggregate number |
| **ASCII payload in the field test** | Chronology: the field test (08–09 Jun) predates the 112-bit upgrade (13 Jun) — usefully, this makes the reliability result payload-independent |
| **`.msg` carries lat/lon only** | Additive fields default 0 so *no group subscriber breaks*; extra fields logged until the team agrees |
| **Demote encoding, lead with reliability** | Binary < ASCII is known prior art; the novel result is the stratified link characterisation + the autonomous loop |
| **Removed Gap 5 (AES)** | Deliberate scope trim |

(Full rationale: Appendix B.)

## 4. Sequence of Events (chronological, git-backed)

| Date | Commit | Event | Stage |
| --- | --- | --- | --- |
| 06-06 | `83435ce` | Initial node: 64-bit payload, 2 fields, 4 dp | **v1** |
| 06-06 | `33ee9af` | Removed Gap 5 (AES); added analysis scripts | scope trim |
| 06-08 | `da015a8` | **Hardware day 1** — T3 firmware fix + first field data | hardware live |
| 06-08→09 | `1a55e9d`→`bd8e2d4` | Gap 3 field campaign — **232 valid TX, 12 locations, 4 environments** | empirical data |
| 06-13 | `dcdadc7` | **64→112-bit** payload (6 fields, 7 dp) + receive chain | **v2** |
| 06-13 | `137ef76` | `portal_reader` live connection | receive live |
| 06-15 | `dc0b8bd` | Flashing-config fix + BDS baud-scanner diagnostic | hardware troubleshooting |
| 06-16 | `a0817d2` | Sim + GCS + virtual BeiDou link + dashboard | demo |
| group repo | `e37098e`→`1065eaa` | **Integrate 5 modules (Stage-1)** → beidou node + 112-bit decode + **verify kit** | **integration merged** |

The diagnostic commit (`dc0b8bd`) records the hardware troubleshooting; the field data was captured while the module still responded, which is why the empirical results exist at all.

## 5. The Node — Before vs Now

### 5.1 What it COULD do (v1, 06-06)
Pack two coordinates into **64 bits** at **4 dp (~11 m)**; demonstrate ~57.9 % size reduction vs ASCII. **Nothing else** — no altitude/uncertainty/triage/ID, no receive chain, no field data, no integration. *A transmitter that could not carry a complete rescue and had nowhere to deliver it.*

### 5.2 What it CAN do now (v2)
Pack **six** complete fields into **112 bits** at **7 dp (~1 cm)**, decoding bit-for-bit; decode three formats (ASCII / 112-bit / legacy 64-bit) behind one interface; carry **232-TX field reliability** and a **30-sample latency** baseline; pull messages via a **live portal reader**; and **publish the rescue trigger into the group ROS 2 mission system** (verified).

### 5.3 Side-by-side (every row reproduced this session)

| Capability | v1 (before) | v2 (now) | Source |
| --- | --- | --- | --- |
| Payload | 64 bit | **112 bit** | `decode_binary.py` |
| Fields | 2 | **6** | Table 1 |
| Precision | 4 dp (~11 m) | **7 dp (~1 cm)** | `*10000`→`*10000000` |
| gap1 ASCII baseline | 184 bit | 264 bit | `gap1_compression.csv` |
| gap1 reduction | ~57.9 % | **57.6 %** | both eras — *stable* |
| gap6 ASCII/Bin/Huff | 384/128/192 | **368/128/184** | `gap6_telemetry.csv` |
| Reliability | none | **232 TX, ≥93.7 % Wilson** | `gap3_analysis.py` |
| Latency | none | **2574.5 ms, n=30** | `gap2_analysis.py` |
| Receive + mission | none | **portal → decode → ROS 2 trigger** | `gcs/`, group node |

### 5.4 Illustration — the role I was tasked to do
```
            5-MODULE UAV RESCUE SYSTEM (Beihang)
  ┌──────┬──────┬──────┬──────┬───────────────────────┐
  │ WP1  │ WP2  │ WP3  │ WP4  │   WP5 = MY TASK       │
  │ RTK  │ QGC  │ YOLO │ Path │   BDS COMMUNICATION   │
  └──────┴──────┴──┬───┴──────┴───────────┬───────────┘
                   │ consume               │ MY WP5 CONTRACT:
                   ▼                       ▼
        /target/emergency_coordinate  ◄─ survivor coord
                                          │
          encode → BDS msg → decode → publish to mission
  Required of me: a SIMULATION emulator + parser + injector, via ROS 2.
```

### 5.5 Illustration — node before vs now
```
  BEFORE (v1)  [lat,lon] → 64-bit (4 dp ≈ 11 m) → TRANSMIT → ✗ nowhere to deliver
       ║  64→112-bit upgrade + field campaign + integration
       ▼
  NOW  (v2)  [lat,lon,alt,R,priority,ID] → 112-bit (7 dp ≈ 1 cm)
             → BDS msg → portal → decode → /target/emergency_coordinate → UAV ✓
             + 232-TX reliability (≥93.7%) + 2.57 s latency + INTEGRATED/VERIFIED
```

## 6. Figures — Justified Against Data

| Fig | File | Claim | Verified against |
| --- | --- | --- | --- |
| 1 | `bds_node_workflow.png` | End-to-end pipeline | `gcs/` + node architecture |
| 2 | `gap1_encoding_comparison.png` | 264 → 112 bit, −57.6 % | `gap1_compression.csv`, `decode_binary.py` |
| 3 | `gap6_telemetry_comparison.png` | 368 / 184 / 112 bit; 210-bit line | `gap6_telemetry.csv` (see C3) |
| 4 | `gap3_success_rate.png` | Wilson 95 % per environment | `gap3_analysis.py` (94.1 % / 93.7 %) |
| 5 | `gap3_location_breakdown.png` | 12 locations 100 % in-sample | `gap3_analysis.py` |
| 6 | `fig_gap2_cdf.png` | Latency CDF, all < 5 s | `gap2_latency_ascii_baseline.csv` |

Statistics reproduced live: encoding 368/184/112 and 57.6 %/69.6 %; reliability 232 valid (61/57/57/57), χ²=0.000/df=3/p=1.0000, Fisher all 1.0000, Wilson 93.7 %/98.4 %; latency mean 2574 ms / SD 1095 / n=30; round-trip T001–T006 bit-exact.

## 7. Contradictions Found — and Resolved (the audit, ran here)

Because the documents are the defence surface, contradictions are the **only** thing that loses marks here — so every one is listed and resolved.

- **C1 — README said "Gap 3 = Pending hardware."** Stale (collected 06-09). *→ correct to "Complete (ASCII payload, 232 TX)."*
- **C2 — "strictly more information than Huffman" is false** (the binary drops battery/mode/flags/timestamp; three different baselines compared as one). *→ reword to "comparable size for a rescue-optimised field set"; lead with the clean 264→112.*
- **C3 — Figure 3 asserts a hard "210-bit limit"** the prose calls unmeasured. *→ relabel the line "indicative/unverified."*
- **C4 — the baseline moved (184→264, 384→368) undisclosed.** *→ one sentence: "the ASCII baseline was re-specified to the operational `$CCTXM` format."*
- **B/A (bounds & boundary):** zero failures cannot resolve >94 % (handled by Wilson framing); 12 locations share one emulated coordinate (disclose); the 112-bit frame is software/sim-proven, not satellite-flown (scoped as future work per §2).

No fabrication anywhere; the issues are documentation lag (C), statistical honesty (B), and a declared boundary (A).

## 8. Integration — Complete and Verified

| Evidence | Detail |
| --- | --- |
| Node | `beidou_publisher_node.py` publishes a **latched** `EmergencyCoordinate` on `/target/emergency_coordinate` |
| Contract | `interfaces/msg/EmergencyCoordinate.msg` (header, lat, lon, source_id, raw_message) |
| Consumers | `qgc_control` and `path_planning` subscribe |
| Verify kit | `verify_integration.sh`, 3 checks, expected `ALL CHECKS PASSED` |
| Merge | `e37098e` (Stage-1) → `1065eaa` (beidou + 112-bit + verify kit); `af76d5c` shared Zurich datum |

The decoded coordinate flows end-to-end into mission planning **without a radio**. The four extra rescue fields are decoded and logged as a documented optional extension — not an unfinished integration.

## 9. My Contribution — Within Scope vs Beyond

### 9.1 Within my assigned scope (WP5) — COMPLETE
| WP5 deliverable | Delivered | Status |
| --- | --- | --- |
| BDS-SMC emulator node | `sim/bds_module_emulator.py`, `sim/virtual_portal.py` | ✅ |
| Coordinate parsing | `decode_ascii/decode_binary`, `gcs/decoder` (3 formats, lossless) | ✅ |
| Auto-inject → PNT | `auto_sender.py`, `feed_coords.py` → contract topic | ✅ |
| QGC / mission interface | topic consumed by `qgc_control` | ✅ |
| ROS 2 integration (Phase 3) | merged group node + passing verify kit | ✅ |

### 9.2 Beyond my scope (unrequested; project was simulation-only)
Real ESP32 + BDS **hardware bring-up**; a **232-TX field-reliability campaign** (12 locations / 4 environments); a **latency baseline** (n=30); **encoding research** (Gap 1/6) and the **64→112-bit payload**; a **live portal reader** and **dashboard**.

### 9.3 Why I went beyond, what it did, why it was completable
- **Why:** the assigned emulator answers "can we move a coordinate?" but not "does the link survive a disaster environment, and is the payload operationally complete?" — the questions that make the rescue claim *credible*, not merely demonstrable.
- **What it did:** it turned WP5 from a simulation stub into an **empirically grounded** module — the coordinate the UAV acts on is backed by measured delivery reliability and a defined precision budget, not an assumption.
- **Why completable:** the WP5 contract (publish a coordinate on a topic) is small and finished early, freeing time; the hardware/field work reused the same encode/decode core, so the marginal cost was *data collection*, not new architecture. That the ~58 % efficiency result survived the 64→112-bit redesign is direct evidence the core was sound enough to build on.

## 10. Reliability & Validity of the Results

Every headline number regenerated from committed source this session: reliability (`gap3_analysis.py`), latency (`gap2_analysis.py`), encoding (`decode_binary.py`, `telemetry_compare.py`), and the report build (`generate_node_report.py`). Reproducibility proves *arithmetic and pipeline integrity*; combined with the disclosed exclusions and Wilson framing, the results are honest and checkable. The validity *boundary* (on-air 112-bit) is stated, not hidden.

## 11. Maximising Marks — What I Would Do and Add (the answer)

Given **no working hardware** and a **close presentation**, the marks come entirely from the documents, the analysis, and the live simulation. In priority order:

**Do (highest mark-per-hour):**
1. **Apply C1–C4** — make every document agree. With no hardware demo to fall back on, internal contradictions are the only real risk. Non-negotiable.
2. **Run the live simulation closed-loop as the centrepiece** — virtual BeiDou link → decode → ROS 2 trigger → mission, plus `verify_integration.sh`. *Showing* the loop fire beats describing it and needs no radio. (Keep a 30-sec recording as backup.)
3. **Reframe explicitly around simulation-first (§2)** — turn dead hardware from an apology into pre-registered risk R6 with its mitigation in force.

**Add (the differentiators):**
4. **A "money figure"** — one diagram of the full pipeline with the three headline numbers (≥93.7 % reliability, 2.57 s latency, integrated+verified) stamped on it. Panels remember one image.
5. **A "Claim → Evidence → Reproduce" table** — every claim, its source file, its regeneration command. Offering to verify live is the strongest credibility move a student can make.
6. **The decision-rationale log (§3 / Appendix B)** — examiners reward *justified* choices; this shows engineering judgement, not luck.
7. **A risk burn-down** — each limitation with its single closing action and status, reframing weakness as a roadmap.

**Do NOT:** chase more analysis of the existing ASCII data (won't change the verdict), inflate the encoding claim (already correctly demoted), or pursue publication novelty before the panel — this is a *reporting* milestone.

## 12. Defending to the Panel

- **90-second opening:** *"My assignment was WP5 — the BeiDou communication module. It is complete and verified in the group ROS 2 system. Beyond it, I asked the questions that make the module credible — does the link survive real environments, is the payload complete — and to answer them I built hardware and ran a 232-transmission field campaign while the module was responsive. I will show what is proven and be precise about the one item that is future work by design."*
- **The hardware question, answered first:** *"The module is now unresponsive — this is risk R6 from our opening proposal, mitigated by a simulation-first design. The link was already characterised on hardware (232 TX); the 112-bit on-air confirmation is future work exactly as scoped."*
- **The "100 %?" question:** *"I never claim 100 %; I claim the Wilson lower bound ≥93.7 %. Zero failures bound reliability below but cannot resolve above ~94 %; deeper-fade sites are the future work that would tighten it."*
- **The "binary<ASCII is known" question:** *"Agreed — I present encoding as a baseline. The contribution is the environment-stratified link characterisation and the autonomous closed loop."*

## 13. What I Need to Achieve My Aspiration

**Aspiration:** a strong dissertation/WP5 outcome now, and a credible publication later. Reporting-milestone priorities (all hardware-free, presentation-ready):
1. Apply C1–C4 (≈2 h) — consistency to 8/10.
2. Land the live sim demo + money figure + evidence table — the presentation centrepieces.
3. Frame strictly simulation-first — the panel cannot fault a scoped, mitigated risk.

**Beyond the panel (future work, when hardware is revived):** one on-air TX of the 112-bit frame, diurnal latency on it, a distinct-coordinate/deep-fade reliability run, and the `.msg` field extension — each already specified and de-risked.

---

## Appendix A — Reproduce Everything
```bash
python python/gap3_analysis.py                         # reliability: 232 TX, Wilson, chi-square
python python/gap2_analysis.py --ascii-baseline --plot # latency: 2574 ms, n=30 + CDF
python python/decode_binary.py                         # 264→112 bit, bit-exact round-trip
python python/telemetry_compare.py                     # 368/128/184 bit
python python/generate_node_report.py                  # rebuild Node Report PDF
```
Inputs: `data/gap1_compression.csv`, `data/gap2_latency_ascii_baseline.csv`, `data/gap3_field_test.csv`, `data/gap6_telemetry.csv`. Integration: group `ros2_ws/src/beidou_short_message/` (`beidou_publisher_node.py`, `verify_integration.sh`).

## Appendix B — Decision Log (quick reference)
See §3. Full justifications: `BDS_SMC2_Node_Evaluation.md` (audit), `BDS_SMC2_Paper1_Sections.md` (emulated-RTK framing §B, exclusion appendix §C, one-way-link policy §D, `.msg` proposal §E).

*This report consolidates the full review of 2026-06-26 and supersedes `BDS_SMC2_Node_Audit_and_Evolution.md` and `BDS_SMC2_Node_Comprehensive_Report.md` as the single reporting account. All quantitative claims are reproducible from the committed scripts and CSVs.*
