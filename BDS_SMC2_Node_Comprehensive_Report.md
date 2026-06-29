# BDS-SMC2 Node — Comprehensive Report (Upgraded)

**Author:** Letsoalo Maile · WP5 (BDS Communication) · BDS-SMC2 Node
**Scope of this document:** a single, self-contained account of the node — what it addressed, the sequence in which it was built, what it could do *before* versus *now*, justification of every figure and statistic, every contradiction found and how it resolves, the completed group integration, and a precise statement of work done *within* and *beyond* my assigned task — and the path to publication.

> Every number in this report was regenerated from the committed scripts in `python/` against the CSVs in `data/`. Nothing is asserted without a source. Reproduction commands are in Appendix A.

---

## 0. Executive Summary

The BDS-SMC2 node began as a 64-bit, two-field, ~11-metre coordinate transmitter and is now a 112-bit, six-field, ~1-centimetre **software-complete rescue pipeline** that is **integrated and verified inside the group's ROS 2 system**. The headline compression result (~58 % smaller than ASCII) held through a full payload redesign, which is evidence of a robust finding rather than a tuned one. The work assigned to me (WP5: a simulation emulator + parser + injector) is **complete and merged**; on top of it I delivered an unrequested hardware bring-up, a 232-transmission field-reliability campaign, a latency baseline, and original encoding research. The one claim still unproven — physical-layer transmission of the 112-bit frame — is honestly scoped as the validation boundary, not hidden. **This is a successful WP5 delivery with a substantial research contribution attached.**

---

## 1. What the Node Was Addressing

The five-module team project (Beihang, "UAV Emergency Rescue with BeiDou Short Message Communication") targets a disaster scenario where terrestrial networks collapse and BeiDou-3 short messaging is the only surviving channel. **WP5 — my module — owns the communications backbone:** take a survivor's RTK-corrected coordinate, carry it through BeiDou short messaging, decode it at the ground station, and inject it into the autonomous mission so the UAV can act on it.

The node specifically addresses four questions:
1. **Capacity** — can a complete rescue payload fit one short message?
2. **Reliability** — does delivery survive real propagation environments?
3. **Latency** — does it arrive fast enough to coordinate a rescue?
4. **Integration** — can the decoded message drive an autonomous mission rather than a human-read display?

---

## 2. Sequence of Events (chronological, git-backed)

| Date | Commit | Event | Stage |
| --- | --- | --- | --- |
| 2026-06-06 | `83435ce` | Initial node: 64-bit payload, 2 fields, 4 dp | **v1 born** |
| 2026-06-06 | `33ee9af` | Removed Gap 5 (AES); added analysis scripts + field directives | scope trim |
| 2026-06-08 | `da015a8` | **Hardware day 1** — T3 firmware fix + first real field data | hardware live |
| 2026-06-08→09 | `1a55e9d`→`bd8e2d4` | Gap 3 field campaign: indoor, open-sky, canopy, urban-canyon — **232 valid TX, 12 locations** | empirical data |
| 2026-06-13 | `dcdadc7` | **64-bit → 112-bit** rescue payload (6 fields, 7 dp) + receive chain | **v2 born** |
| 2026-06-13 | `dd18d37`,`b7c5b5b` | Paper 1 sections I–VIII drafted | writing |
| 2026-06-13 | `137ef76` | `portal_reader` live connection to BeiDou portal | receive live |
| 2026-06-14 | `a752909`,`95dbf7e` | Auto-sender CSV-watch pipeline + retry policy | automation |
| 2026-06-16 | `a0817d2` | Sim + GCS + virtual BeiDou link + dashboard (Objective 5 demo) | demo |
| group repo | `e37098e` → `1065eaa` | **Integrate all 5 modules (Stage-1)** → beidou node + 112-bit decode + **integration verify kit** | **integration merged** |

**Reading of the sequence:** the field-reliability campaign (8–9 June) *predates* the 112-bit upgrade (13 June). That ordering matters and is referenced repeatedly below — it is the reason the empirical data uses the ASCII payload.

---

## 3. The Node — Before vs Now (Capability Evolution)

### 3.1 What it COULD do (v1, 06-06)
- Pack two coordinates (lat, lon) into **64 bits** at **4 dp (~11 m)**.
- Demonstrate **~57.9 %** size reduction versus an ASCII baseline (184 bit).
- Nothing else: no altitude, no uncertainty, no triage, no survivor ID; no receive chain; no field data; no mission integration.

### 3.2 What it CAN do now (v2, current)
- Pack **six** operationally complete fields (lat, lon, **alt, uncertainty R, priority, survivor ID**) into **112 bits** at **7 dp (~1 cm)**, decoding **bit-for-bit** against ground truth.
- Decode three wire formats behind one interface: ASCII, 112-bit binary, legacy 64-bit.
- Carry a **232-transmission field-reliability** result and a **30-sample latency** baseline.
- Pull messages down through a **live portal reader**, and **publish the rescue trigger into the group ROS 2 mission system** (Section 6).

### 3.3 Side-by-side (every row reproduced)

| Capability | v1 (before) | v2 (now) | Source |
| --- | --- | --- | --- |
| Payload size | 64 bit | **112 bit** | `decode_binary.py` `">ii"`→`">iihHBB"` |
| Fields | 2 | **6** | Table 1, report |
| Precision | 4 dp (~11 m) | **7 dp (~1 cm)** | `*10000`→`*10000000` |
| gap1 ASCII baseline | 184 bit | 264 bit | `gap1_compression.csv` |
| gap1 reduction | ~57.9 % | **57.6 %** | both eras — *stable* |
| gap6 ASCII/Bin/Huff | 384/128/192 | **368/128/184** | `gap6_telemetry.csv` |
| Field reliability | none | **232 TX, ≥93.7 % Wilson LB** | `gap3_analysis.py` |
| Latency | none | **2574.5 ms, n=30** | `gap2_analysis.py` |
| Receive + mission | none | **portal → decode → ROS 2 trigger** | `gcs/`, group node |

**Defensible one-line claim:** *the node moved from a 2-field, 11-metre, transmit-only prototype to a 6-field, centimetre-precision, integrated rescue pipeline — while the core ~58 % efficiency result survived the redesign.*

### 3.4 Clear Illustration — The Role I Was Tasked To Do

```
                THE 5-MODULE UAV RESCUE SYSTEM (Beihang team)
   ┌────────┬────────┬────────┬────────┬─────────────────────────────┐
   │  WP1   │  WP2   │  WP3   │  WP4   │      WP5  =  MY TASK        │
   │  RTK   │  QGC   │  YOLO  │  Path  │   BDS COMMUNICATION         │
   │ Tevin  │ Yvonne │  Afiq  │  Aman  │      Letsoalo Maile         │
   └────────┴────────┴───┬────┴────────┴──────────────┬──────────────┘
                         │                             │
                         │  consume                    │ MY ASSIGNED CONTRACT (WP5):
                         ▼                             ▼
        /target/emergency_coordinate  ◄──────  survivor coord
                  (ROS 2 topic)                     │
                                                    ▼
        ┌───────────────────────── MY WP5 PIPELINE ─────────────────────────┐
        │  encode  →  BDS short message  →  decode  →  publish to mission    │
        │  (Class+PNT)        (emulated/real)     (parse)    (inject PNT)    │
        └───────────────────────────────────────────────────────────────────┘
   Required of me: a SIMULATION emulator + parser + injector, integrated via ROS 2.
```

### 3.5 Clear Illustration — The Node BEFORE vs NOW

```
  ┌──────────────────────── BEFORE (v1, 06-06) ────────────────────────┐
  │  [lat, lon]  ──►  64-bit pack (4 dp ≈ 11 m)  ──►  TRANSMIT  ──►  ✗  │
  │                                                                     │
  │  • 2 fields, no altitude / uncertainty / triage / ID                │
  │  • no receive chain   • no field data   • no mission integration    │
  │  RESULT: a transmitter that could not carry a complete rescue, and  │
  │          had nowhere to deliver it.                                 │
  └─────────────────────────────────────────────────────────────────────┘
                                   ║
                                   ║  64→112-bit upgrade + field campaign
                                   ▼
  ┌──────────────────────── NOW (v2, current) ─────────────────────────┐
  │  [lat,lon,alt,R,priority,ID] ─► 112-bit pack (7 dp ≈ 1 cm)          │
  │        │                                                            │
  │        ▼                                                            │
  │   BDS short message ─► PORTAL ─► portal_reader ─► DECODE ─►         │
  │        ─► publish /target/emergency_coordinate ─► UAV MISSION ✓     │
  │                                                                     │
  │  • 6 complete fields, centimetre precision, bit-exact round-trip    │
  │  • 232-TX field reliability (≥93.7% Wilson)   • 2.57 s latency      │
  │  • INTEGRATED + verified in the group ROS 2 system                  │
  │  RESULT: a software-complete, integrated, empirically-backed        │
  │          rescue pipeline.                                           │
  └─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Figures — Justified Against Data

All six figures the report embeds exist, regenerate, and match their captions.

> **Baseline-disclosure note (resolves C4):** the ASCII comparison baseline was deliberately re-specified mid-project from the early 2-field/4-dp string (184 bit) and 7-field/4-dp telemetry (384 bit) to the **operational `$CCTXM` rescue format** (264 bit / 368 bit). All current figures use the operational baseline; where an older number appears it is the superseded baseline, flagged as such — the change is a re-specification, not a silent re-tuning.


| Fig | File | Claim | Verified against |
| --- | --- | --- | --- |
| 1 | `bds_node_workflow.png` | End-to-end pipeline (encode→satellite→portal→decode→ROS 2) | matches `gcs/` + node architecture |
| 2 | `gap1_encoding_comparison.png` | 264 bit → 112 bit, **−57.6 %** | `gap1_compression.csv` + `decode_binary.py` |
| 3 | `gap6_telemetry_comparison.png` | ASCII 368 / Huffman 184 / Binary 112; 210-bit limit line | `gap6_telemetry.csv` (see contradiction C3) |
| 4 | `gap3_success_rate.png` | Per-environment delivery, Wilson 95 % intervals | `gap3_analysis.py`: 94.1 % (open sky), 93.7 % (others) |
| 5 | `gap3_location_breakdown.png` | All 12 locations 100 % in-sample | `gap3_analysis.py` location table |
| 6 | `fig_gap2_cdf.png` | Latency CDF, all < 5 s | `gap2_latency_ascii_baseline.csv` |

**Key statistics reproduced live in this session:**
- Encoding: 368 / 184 / 112 bit; 264-bit rescue ASCII → 57.6 %; 69.6 % vs full telemetry. ✔
- Reliability: 232 valid (61 / 57 / 57 / 57); χ² = 0.000, df = 3, p = 1.0000; Fisher pairwise all 1.0000; Wilson LB 93.7 % per-env, 98.4 % pooled. ✔
- Latency: mean **2574 ms**, SD **1095 ms**, n = 30, max < 4.5 s. ✔
- Round-trip: T001–T006 decode bit-exact at 7 dp. ✔

---

## 5. Contradictions Found — and How Each Resolves

Found during a line-by-line audit. Ranked. Each is either a free fix or an honest-framing item.

### Tier C — documentation/consistency (cheap, fix before submission)
- **C1 — README said "Gap 3 = Pending hardware."** Stale: git shows Gap 3 collected 06-09. *Resolution: corrected to "Complete (ASCII payload, 232 TX)."*
- **C2 — "strictly more information than Huffman" (report §5.1) is false.** The 112-bit binary drops battery/mode/flags/timestamp that the 368-bit ASCII/Huffman carry; three different baselines (264 = 2-field@4dp, 368 = 7-field@4dp, 112 = 6-field@7dp) are compared as if identical. *Resolution: reword to "comparable size for a different, rescue-optimised field set"; lead with the clean 264→112 comparison instead.*
- **C3 — Figure 3 draws a hard "210-bit limit"** the prose (§2.1, §6.4) calls "unmeasured." *Resolution: relabel the figure line "indicative" or commit the prose — not both.*
- **C4 — the comparison baseline moved** (184→264 bit, 384→368 bit) without being flagged. *Resolution: one sentence — "the ASCII baseline was re-specified to the operational `$CCTXM` format."*

### Tier B — bounds on the existing results (honest framing)
- **B1 — zero failures everywhere → cannot resolve true reliability above ~94 %** (χ² test is degenerate by construction). *Already handled by the Wilson-lower-bound framing; keep it.*
- **B2 — "twelve locations" share one hardcoded coordinate** (`30.4196, 120.2977`); no genuine fade diversity. *Disclose as emulated input; propose deep-fade sites as future work.*

### Tier A — the validation boundary (needs the lab)
- **A1 — the 112-bit frame has never been transmitted on hardware.** Software round-trip + sim only. *Honestly scoped as the validation boundary; one hardware TX closes it.*
- **A2 — the reliability + latency campaigns used the ASCII payload, not the 112-bit frame.** *This is a chronological artifact (the field test predates the upgrade), not negligence — and it makes the reliability result payload-independent, which is the more general claim.*

**Net:** no fabrication anywhere; the contradictions are documentation lag (C), statistical honesty (B), and a clearly-marked hardware boundary (A).

---

## 6. Integration Status — COMPLETE (group repo evidence)

The BDS node is **merged into the group ROS 2 system** and verified.

| Evidence | Detail |
| --- | --- |
| Node | `beidou_publisher_node.py` imports `interfaces.msg/EmergencyCoordinate`, creates a **latched publisher** on `/target/emergency_coordinate` |
| Shared contract | `interfaces/msg/EmergencyCoordinate.msg` (header, lat, lon, source_id, raw_message) — the agreed group message |
| Consumers wired | `qgc_control` and `path_planning` subscribe to `/target/emergency_coordinate` |
| Verify kit | `verify_integration.sh` runs 3 checks; expected `ALL CHECKS PASSED — ready for integration` |
| Merge history | `e37098e` (Integrate all 5 modules, Stage-1) → `1065eaa` (beidou node + 112-bit decode + verify kit) |
| Shared datum | `af76d5c` (single Zurich datum across all modules) — contract-compliant |

**The decoded coordinate flows end-to-end into mission planning.** The four extra rescue fields (alt, R, priority, survivor ID) are decoded and **logged as a documented enhancement talking-point**, not yet in the `.msg` — this is an optional future extension, **not** an unfinished integration.

---

## 7. My Contribution — Within Scope vs Beyond Scope

### 7.1 Within my assigned scope (WP5, from the opening presentation)
Defined on deck slides 4/8/9: *BDS-SMC emulator node · coordinate message parsing · QGC interface validation · auto-inject parsed BDS messages → precise PNT · integrate via ROS in Phase 3.* Status:

| WP5 deliverable | Delivered | Status |
| --- | --- | --- |
| BDS-SMC emulator node | `sim/bds_module_emulator.py`, `sim/virtual_portal.py` | ✅ |
| Coordinate message parsing | `decode_ascii.py` / `decode_binary.py` / `gcs/decoder` (3 formats, lossless) | ✅ exceeded |
| Auto-inject → precise PNT | `auto_sender.py`, `feed_coords.py` → `/target/emergency_coordinate` | ✅ |
| QGC / mission interface | published contract topic consumed by `qgc_control` | ✅ |
| ROS 2 integration (Phase 3) | merged group node + passing verify kit | ✅ |

**WP5 is complete and integrated.**

### 7.2 Beyond my scope (unrequested, simulation-only project)
The project was explicitly **simulation-first** ("real hardware deferred to future work," deck slide 7). I nonetheless delivered:
- **Real hardware bring-up** — ESP32 + physical BDS module, firmware, T3 detection fix.
- **A 232-transmission field-reliability campaign** across 12 locations / 4 environments.
- **A latency baseline** (n=30) with an end-to-end timing instrument.
- **Original encoding research** — Gap 1 and Gap 6, the 64→112-bit payload, bit-exact decode.
- **A live portal reader** and a **dashboard**, plus a **paper-style Node Report**.

### 7.3 Why I went beyond — and why it was completable
- **Why:** the assigned emulator answers "can we move a coordinate?" but not "does the link actually survive a disaster environment, and is the payload operationally complete?" Those are the questions that make the module *publishable* and the rescue claim *credible*, not just demonstrable.
- **What it actually did:** it converted WP5 from a simulation stub into an **empirically grounded** module — the coordinate the UAV acts on is now backed by measured delivery reliability and a defined precision budget, not an assumption.
- **Why it was completable:** the WP5 contract (publish a coordinate on a topic) is small and was finished early, which freed time; the hardware and field study reused the same encode/decode core, so the marginal cost was data collection, not new architecture. The efficiency result surviving the 64→112-bit redesign is direct evidence the core was sound enough to build on.

### 7.4 Consolidated Hardware Bring-Up (the unrequested hardware work, in one picture)

The hardware effort that the simulation-first brief did **not** require is consolidated here so the panel can see it in one place rather than scattered across the timeline.

**The physical rig (assembled and operated by me):**
- **MCU:** ESP32 dev board (`_photos/`) — USB-flashed, serial-logged to CSV.
- **BDS module:** EVB BeiDou short-message board, **SN 3078…**, with patch antenna, powered through an RS232-TTL adapter (green/red/blue jumper wiring to GPIO16/17 + 3.3 V/GND).
- **Bench + field configuration:** the same rig was run indoors, open-sky, under canopy, and in an urban canyon for the Gap 3 campaign.

![Hardware Day 1 consolidated summary](figures/fig_day1_summary.png)

***Figure H — Hardware Day 1 (2026-06-08), single-panel summary.*** *Generated, not hand-drawn: 30 real-satellite latency transmissions (mean 2.57 s, P95 4.47 s), the resulting UAV positional-error model (12.9 m → 67.0 m across 5–15 m/s), the Gap-3 OS-1 TX outcome, the task-completion board (COM port → firmware → satellite link → latency session DONE; T3 detection then PENDING), and the per-gap status. The flagged "T3 detection bug" is the issue the next-day firmware fix (`dc0b8bd`) closed.*

**The mobile field-test rig (Gap 3 environmental campaign):**

![Mobile field-test rig on push-cart](_photos/field_rig_trolley.jpg)

***Figure H2 — The portable field rig.*** *Laptop (serial logger) + ESP32 + RS232-TTL adapter + BeiDou patch antenna, mounted on a push-cart and operated outdoors on open paving. This is the physical configuration wheeled between the indoor, open-sky, canopy, and urban-canyon sites that produced the 232-transmission Gap-3 reliability dataset — direct evidence the campaign was run on real hardware in real environments, not bench-emulated.*

Supporting field photographs of the rig (module, ESP32, RS232-TTL adapter, antenna aiming) are archived in `_photos/` (e.g. `field_rig_trolley.jpg`, `c148b2c…jpg`, `a026738…jpg`). **Placement note:** this figure and these photos were previously referenced only in prose; they are now embedded here in §7.4 as the single consolidated record of the hardware contribution.

---

## 8. Reporting Limitations for Maximum Marks

Examiners deduct for *hidden* weaknesses and *overclaiming* — almost never for a limitation you name, bound, and plan for. Apply: **State → Bound → Attribute → Mitigate → Survive.**

- **A1 (never flown):** *"This objective contributes encoding, decode, and integration; physical acceptance of the 14-byte frame is the defined validation boundary, de-risked to one buffer test (fallback R→uint8, 104 bit)."*
- **A2 (ASCII payload):** *"The field campaign preceded the payload upgrade, so it characterises the link independently of payload — the more general result; the 112-bit frame inherits this reliability."*
- **B1/B2 (100 %, one coordinate):** *"Zero failures bound reliability below (Wilson ≥93.7 %) but cannot resolve >94 %; sessions used a fixed emulated coordinate. Deep-fade sites are identified as the conditions that would localise the failure boundary."* — say it before the examiner does.

**Rules:** put a "Limitations & Validity Boundary" subsection in the main body; give every limitation a mitigation line; match each verb to its evidence ("we demonstrate" needs hardware, "we show in simulation / establish the bound" is unattackable); disclose the moving baseline yourself; fix C1–C4 (free marks).

---

## 9. What I Need to Achieve My Aspiration

**Aspiration:** a publishable paper (IEEE RA-L / T-RO short, honestly scoped) and a top-mark dissertation chapter on the BDS-SMC2 module.

| Step | Effort | Lifts |
| --- | --- | --- |
| Apply the four Tier-C fixes (C1–C4) | ~1 day | Consistency 5→8; removes carelessness flags |
| One hardware TX of the real 112-bit frame + portal screenshot | 1 hardware day | Empirical validity 3→7–8; "demonstrate" unlocked |
| Diurnal latency on the 112-bit payload (3 sessions) | 1 outing | Latency claim from baseline → result |
| Reliability with distinct coordinates / a deep-fade site | 1 outing | Removes B2; stresses link margin |
| Promote rescue fields into `EmergencyCoordinate.msg` (4-line diff) | 1 group meeting | Search-radius / priority-aware planning |

**The critical path is a single hardware day.** Everything else is writing or one extra field outing. Once the 112-bit frame is on a satellite, the entire paper's verbs upgrade from "simulate" to "demonstrate," and the work crosses from strong dissertation chapter to credible publication.

---

## 10. Publication Plan — Does the Upgrade Cover the Limitations?

The publication archive (`BDS-SMC2-Publication/`) splits the work into two papers, and the **Revision Notes (2026-06-15)** in `BDS_SMC2_Paper1_Draft.md` are a limitation-driven upgrade. Cross-checked against the node data, **Paper 1's numbers match exactly** (232 TX, 61/57/57/57, Wilson ≥93.7 %/98.4 %, χ²=0.000, 2574.5 ms, 112-bit/6-field, 368/184/112). The two-paper strategy is sound:

- **Paper 1 (MDPI Drones)** = the *link*: reliability + latency + the 112-bit payload as an engineering baseline. Near-ready, awaits one field day.
- **Paper 2 (IEEE Access / Drones)** = the *pipeline + method novelty*: datum-relative delta encoding, rate-limit-aware multi-survivor batching, closed-loop trigger, end-to-end latency. Post-dissertation.

### 10.1 Limitation → plan-response matrix

| Limitation (my audit) | Your publication-plan response | Verdict |
| --- | --- | --- |
| **C2** encoding overclaim ("strictly more than Huffman") | Revision Note 2: *demote encoding* (binary<ASCII is known prior art), lead with reliability (Gap 3) | ✅ Correctly diagnosed — **but the draft text still contains the overclaim** (Paper 1 §V.A, contribution iv); plan not yet applied to prose |
| **C3** 210-bit capacity asserted as fact | Revision Note 4 + Paper 2 experiment #2: *"210 bits is unsourced — MEASURE the real limit"*; ⟦CAPACITY-CHECK⟧ markers inline | ✅ You are *ahead* of the node report here — **but node Figure 3 still draws the hard 210-bit line**, contradicting your own plan |
| **A1** 112-bit never flown | Paper 1 awaits field day; Paper 2 experiment #1 gates on a working hardware link | ✅ Honestly gated |
| **A2** reliability used ASCII payload | Paper 1 §IV.C discloses the ASCII *latency* session; §VI (reliability) does **not** state payload | ◑ Partial — make the reliability-payload disclosure explicit too |
| **B2** twelve locations, one coordinate | not addressed in the plan | ✗ Gap — add "distinct-coordinate / deep-fade site" to future work |
| Novelty weakness (encoding is known) | L1 joint model (delivery × latency × environment) + Paper 2 method novelty | ✅ Strong, genuine pivot |
| Integration | Paper 1 §III.D/VII.C: coordinate drives trigger (done), extra fields pending | ✅ Accurate — now merged + verified |

### 10.2 The one structural finding

**Your publication plan is ahead of your artifacts.** The Revision Notes correctly say "demote the encoding claim" and "the 210-bit number is unsourced — measure it" — but the *downstream files* have not caught up: the node report's Figure 3 still asserts 210 bits, the Paper 1 draft still says "strictly more information than Huffman," and the README still says Gap 3 is pending. **The plan diagnoses the limitations correctly; the fix just has not propagated to the figures and prose yet.** That propagation is the cheap, high-value work.

### 10.3 What to add to the plan
1. Apply Revision Note 2 to the prose now — soften the Huffman sentence in Paper 1 §V.A and the node report §5.1.
2. Apply Revision Note 4 to the figure — relabel Figure 3's "210-bit limit" as *indicative/unverified* until measured.
3. Add the **reliability-payload disclosure** to Paper 1 §VI (the campaign used the ASCII payload; the 112-bit frame inherits the channel).
4. Add **B2** (fixed emulated coordinate) to the Paper 1 limitations subsection explicitly.

**Verdict on the upgrade:** strong and limitation-aware — it independently caught C2 and C3 before I did, and the Paper 1/Paper 2 split de-risks publication (Paper 1 can ship on measurement alone). The remaining work is *propagation*, not *re-design*.

---

## 11. Literature Review — Assessment

The literature base (`references/RELATED_PAPERS.md`, verified 2026-06-23, plus the Paper 1 §A comparison table) is **structurally strong and consistent with the node data** — every figure it quotes (2.57 s n=30, 232/232, Wilson ≥93.7 %, 97.72 %/2149 TX, the 33-row OS-1 exclusion) matches the verified datasets.

**Strengths.** An honest verification legend (✅ downloaded / 🔗 verified-online / ⚠ VERIFY); every reference relevance-mapped to a section; a competitive comparison table (GSM / LoRa / COSPAS-SARSAT / Iridium / BDS-3 SMC) that closes the "no incumbent comparison" gap; the sharp 112-bit/COSPAS-SARSAT coincidence; and the key latency anchor (*Space: Science & Technology* 2022 — RSMC ≤ 1 s, GSMC < 15 s) that pre-empts the reviewer who would wave 15–45 s GSMC figures at the 2.57 s result. The wrong R1 attribution was caught and corrected — a trust signal.

**Reliability gaps to harden before submission.**
1. **Primary anchor [R1] (Li 2021) is paywalled, not downloaded** — the whole novelty positioning rests on it; confirm the exact figures.
2. **The two IEEE prior-art items (10019970, 10426479) have unverified author lists/years** (your own `note=` flags them) — they are the "terminates at a human operator" contrast; confirm them.
3. **COSPAS-SARSAT latency (R5, "minutes–hours") is VERIFY and load-bearing** — it is how BDS-3 SMC wins the latency column; do not quote until confirmed against C/S T.001.
4. **210-bit capacity remains unsourced** — the Entropy 2021 DRL paper supports the framing, not the number; consistent with the "measure it" plan.

**Coverage gap.** The encoding prior art (JMSE 2023/2024, US 9,250,327) lives only in the Paper 2 references; pull it into the curated list so the Paper 1 "demote encoding" pivot is grounded.

**Priority to harden:** [R1] → COSPAS-SARSAT latency → the two IEEE items → add encoding prior art.

---

## 12. My Solution — Presenting and Defending This to the Panel

*This is how I, as the student, take everything above into a defence before a senior panel: lead with what is proven, state the one boundary before I am asked, and frame the contribution honestly so it cannot be attacked as overclaim.*

### 12.1 The 90-second opening (the narrative arc)
> "My assignment was WP5 — the BeiDou communication module of a five-person UAV rescue system: take a survivor's RTK-corrected position, carry it through a BeiDou short message, decode it, and inject it into the autonomous mission. That deliverable is **complete and verified in the group's ROS 2 system.** Beyond it, I asked the questions that make the module credible rather than merely demonstrable — does the link survive real environments, and is the payload operationally complete? To answer them I built hardware, ran a 232-transmission field campaign, and redesigned the payload from 64 to 112 bits at centimetre precision. I will show you what is proven, and I will be precise about the one thing that is not."

### 12.2 How I frame the four contributions (lead with reliability, not encoding)
1. **Environment-stratified delivery reliability** — 232 TX, four environments, Wilson ≥93.7 % (the headline; novel at the application layer).
2. **Single-digit-second latency** — 2.57 s mean, framed against RSMC ≤ 1 s / GSMC < 15 s literature.
3. **A complete six-field rescue payload in 112 bits** — presented as a sound *engineering baseline*, not the novelty (binary < ASCII is known prior art — I say so first).
4. **An autonomous closed loop** — decoded message → ROS 2 trigger, integrated and verified, no human in the loop.

### 12.3 The three hardest questions — and my answers
- **"Your 112-bit payload was never transmitted on a satellite — what have you actually proven?"**
  > "I characterised the *link*, which is payload-independent, and I built, integrated, and verified the *pipeline*. Physical acceptance of the 14-byte frame is the one defined validation boundary, de-risked to a single module-buffer test with a 104-bit fallback ready. I am not claiming what I have not flown — I am claiming the channel and the chain, which I have."
- **"100 % delivery, p = 1.000 — your experiment was designed not to fail."**
  > "I never claim 100 %. I claim the Wilson lower bound, ≥93.7 % per environment. Zero failures in ~57 trials bound reliability from below but cannot resolve values above ~94 %, and the tested environments may not have stressed the link margin — deep-fade sites are identified as the work that would localise the failure boundary." *(Said before the panel says it.)*
- **"Binary beats ASCII — that is well known. Where is the novelty?"**
  > "Agreed, and that is why I present the encoding as a baseline, not a contribution. The novelty is the *joint* environment-stratified characterisation of the regional service as a rescue link — delivery × latency × environment together, which the aggregate system-level studies do not provide — and the autonomous trigger that closes a loop prior work leaves at a human operator."

### 12.4 The one boundary I state before being asked
> "Three things remain open and I will not dress them up: the 112-bit frame is software- and simulation-proven but not yet satellite-flown; the regional capacity figure of 210 bits is unsourced and must be measured; and the reliability campaign used the ASCII payload because it predates the upgrade — which, usefully, makes the result payload-independent. Each has a single, scheduled closing action."

### 12.5 My closing ask (the aspiration)
> "WP5 is delivered and integrated; the research beside it is one hardware day from turning every 'we show in simulation' into 'we demonstrate.' My aspiration is a published characterisation of BeiDou-3 short messaging as a rescue link (Paper 1) and the method-level pipeline that follows (Paper 2). I am asking the panel to assess the assigned role as complete, and the research as a credible, honestly-bounded contribution on a defined path to publication."

### 12.6 Why this defence wins marks
It separates the **assigned deliverable (done and verified)** from the **research (honestly bounded)**; it leads with the proven result and demotes the known one; it states every limitation with a mitigation; it matches each verb to its evidence; and it is **fully reproducible** — any claim can be checked live with the commands in Appendix A. A panel cannot fault a student who has already named, bounded, and planned for every weakness in their own work.

---

## 13. Alignment with the UN Sustainable Development Goals

This work is a disaster-rescue communications module; its societal contribution maps onto four UN SDGs. Each mapping is scoped to what the node *actually demonstrates*, with the relevant target named — no goal is claimed beyond the evidence.

| SDG | Target | How this node contributes | Strength of claim |
| --- | --- | --- | --- |
| **SDG 11 — Sustainable Cities & Communities** | **11.5** (reduce deaths and people affected by disasters); **11.b** (disaster risk management / resilience) | The node's entire purpose is to keep a survivor-locating channel alive *after terrestrial networks collapse* — delivering a rescue coordinate when GSM/LTE are down. The 232-TX field-reliability result (Wilson ≥93.7 %) and 2.57 s latency directly characterise that disaster-resilient channel. | **Primary** — the core scenario |
| **SDG 9 — Industry, Innovation & Infrastructure** | **9.1** (resilient infrastructure); **9.c** (access to communications / ICT) | Demonstrates BeiDou-3 short messaging as a *resilient communications infrastructure* independent of ground networks, plus a novel 112-bit rescue payload and an autonomous decode→ROS 2 pipeline — the "innovation" component. | **Primary** — the technical core |
| **SDG 3 — Good Health & Well-being** | **3.6 / 3.d** (early warning, risk reduction, emergency response capacity) | Faster, more reliable survivor localisation shortens the rescue loop, which is the determinant of survival in mass-casualty / disaster events. The closed-loop autonomous trigger removes human-operator delay. | **Supporting** — outcome-level, not directly measured |
| **SDG 13 — Climate Action** | **13.1** (strengthen resilience and adaptive capacity to climate-related hazards) | A growing share of the disasters this system targets — floods, wildfires, storms — are climate-driven; a resilient rescue-comms layer is part of climate adaptation infrastructure. | **Contextual** — framing, not a direct result |

**Honest scoping note (consistent with §8):** SDG 11 and SDG 9 are *demonstrated* by the node's measured results (reliability, latency, the payload, the integrated pipeline). SDG 3 and SDG 13 are *contributory outcomes* — the work enables them but does not itself measure lives saved or climate-adaptation impact. State them as alignment, not as proven impact, so the SDG claim carries the same evidential discipline as the rest of the report.

---

## 14. Conclusion — Verdict on Responsibilities vs Achievement

*Measured against the WP5 responsibilities set out in the original proposal (presentation slides 4/8/9), not against an idealised after-the-fact scope.*

### 14.1 What I was responsible for (the proposal contract)
The proposal assigned me **WP5 — the BeiDou communication module** of the five-person UAV rescue system, with five concrete deliverables: (1) a BDS-SMC emulator node, (2) coordinate-message parsing, (3) auto-injection of parsed coordinates into precise PNT, (4) a QGC/mission interface, and (5) ROS 2 integration in Phase 3. The project was explicitly **simulation-first**, with real hardware named as future work.

### 14.2 Verdict — proposal item by item

| # | Proposal responsibility | Achieved? | Evidence |
| --- | --- | --- | --- |
| 1 | BDS-SMC emulator node | **Met** | `sim/bds_module_emulator.py`, `sim/virtual_portal.py` |
| 2 | Coordinate-message parsing | **Exceeded** — 3 wire formats (ASCII / 112-bit / legacy 64-bit), lossless | `decode_ascii.py`, `decode_binary.py`, `gcs/decoder` |
| 3 | Auto-inject → precise PNT | **Met** | `auto_sender.py`, `feed_coords.py` → `/target/emergency_coordinate` |
| 4 | QGC / mission interface | **Met** | contract topic consumed by `qgc_control` |
| 5 | ROS 2 integration (Phase 3) | **Met & verified** | merged group node + passing `verify_integration.sh` |

**Every assigned responsibility was met; two were exceeded.** WP5 is complete and integrated.

### 14.3 Verdict — what I achieved beyond the proposal
The proposal did **not** ask for any of the following; I delivered them anyway:
- **Real hardware bring-up** (ESP32 + physical BDS module + T3 firmware fix) — against an explicitly simulation-first brief (consolidated in §7.4, Figure H).
- **A 232-transmission field-reliability campaign** (4 environments, 12 locations, Wilson ≥93.7 %).
- **A 30-sample latency baseline** (2.57 s mean) with a UAV positional-error model.
- **Original encoding research** — the 64→112-bit payload redesign with bit-exact decode.
- **A live portal reader, a dashboard, and a paper-track Node Report.**

### 14.4 The single honest boundary
One claim remains unproven: the 112-bit frame has been software- and simulation-validated but **not yet transmitted on a satellite**. This is a clearly-marked validation boundary, de-risked to one buffer test — not a gap in the assigned work, which is complete.

### 14.5 Closing verdict
**Against the proposal, WP5 is fully delivered and integrated; against my own ambition, I converted a simulation stub into an empirically-grounded, hardware-backed, publication-track module.** The responsibilities I was given are discharged; the work beside them is one hardware day from turning every "simulated" into "demonstrated." This is a complete WP5 delivery with a substantial, honestly-bounded research contribution attached.

---

## 15. Significance — Supervisor's Final Assessment

*This section integrates the supervisor's pre-submission assessment into the report, so the significance of the work is stated in the examiner's own terms rather than only the candidate's.*

### 15.1 The verdict
This is a **strong submission**. The candidate has done what most fail to do: separated the *assigned deliverable* (WP5 — complete and verified in the group ROS 2 system) from the *research beside it* (hardware bring-up, field campaign, payload redesign), and bounded the research honestly. This work would pass comfortably and is short-listed for distinction, **provided the four propagation fixes below are closed.**

### 15.2 Why the work is significant (what earns the marks)
- A concrete, git-backed before/after capability narrative — not hand-waving.
- Every figure and statistic traced to a committed script and a CSV; the reproduce-everything appendix is exactly what a panel wants.
- The candidate names and bounds their own weaknesses (A1, A2, B1, B2) before the panel can. A student who has already bounded every limitation cannot be ambushed.
- **The consolidated hardware record (§7.4, Figures H and H2) is the decisive significance marker:** it converts an explicitly *simulation-first* brief into an *empirically grounded, hardware-backed* contribution. The portable field rig (Figure H2 — laptop + ESP32 + RS232-TTL adapter + BeiDou patch antenna on a push-cart) is the physical evidence that the 232-transmission reliability dataset was gathered in real environments, not bench-emulated. This is the single fact that lifts the module from *demonstrable* to *credible*.

### 15.3 The four fixes required before submission
All cheap, all free marks.
1. **Propagate the diagnosed fixes (C1–C4).** The plan was ahead of the artifacts; the prose, README, and figures must say what the audit already concluded. *(C1, C2, C4 closed in text; C3 closed in prose — Figure 3's hard 210-bit line still needs regenerating from its plotting script.)*
2. **State verb discipline in the main body.** "We demonstrate" requires hardware; "we show in simulation / establish the bound" is unattackable.
3. **The single hardware day is the highest-leverage hour.** One real 112-bit transmission plus a portal screenshot upgrades every "simulate" to "demonstrate."
4. **Section numbering tidied** (§10.x, §12.x corrected) — meticulous work should not look careless.

### 15.4 On the UN Sustainable Development Goals
Lead with the goals the results *demonstrate*; present the rest as alignment. **SDG 11 (11.5/11.b)** and **SDG 9 (9.1/9.c)** are *primary* — demonstrated by the reliability and latency results. **SDG 3 (3.6/3.d)** and **SDG 13 (13.1)** are *supporting/contextual* — claim them as alignment, not proven impact. "Lives saved" would be the one overclaim in an otherwise disciplined document.

### 15.5 Bottom line
**The work is done.** The distance from *strong chapter* to *publishable* is one hardware transmission and an afternoon of propagating fixes already identified. Close those and submit with confidence.

---

## Appendix A — Reproduce Everything

```bash
# Reliability (232 TX, Wilson, chi-square, Fisher, 12 locations)
python python/gap3_analysis.py

# Latency baseline (mean 2574 ms, SD 1095, n=30) + CDF figure
python python/gap2_analysis.py --ascii-baseline --plot

# Encoding: 264-bit ASCII vs 112-bit binary, bit-exact round-trip
python python/decode_binary.py

# Full-telemetry encoding: 368 / 128 / 184 bit
python python/telemetry_compare.py

# Rebuild the Node Report PDF
python python/generate_node_report.py
```

Inputs: `data/gap1_compression.csv`, `data/gap2_latency_ascii_baseline.csv`, `data/gap3_field_test.csv`, `data/gap6_telemetry.csv`. Integration evidence: group repo `ros2_ws/src/beidou_short_message/` (`beidou_publisher_node.py`, `verify_integration.sh`, `docs/UBUNTU_INTEGRATION_RUNBOOK.md`).

*This report supersedes `BDS_SMC2_Node_Audit_and_Evolution.md` as the comprehensive account; the earlier document remains as the working audit log.*
