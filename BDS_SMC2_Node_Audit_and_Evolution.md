# BDS-SMC2 Node — Audit, Evolution, and Limitation-Reporting Guide

**Purpose.** This document does four things an examiner looks for at once:
1. States what the **initial** analysis and figures actually said (Node v1).
2. Audits the **current** node against it (Node v2), showing the evolution.
3. Lists every limitation found, ranked, with the evidence each rests on.
4. Gives a **precisely-justified score** and a **marks-maximisation guide** — how to report each limitation so it earns credit instead of costing it.

Everything below was reproduced from the committed scripts and CSVs (every figure regenerated, every statistic re-run). No number here is asserted without a source file.

---

## 1. What the INITIAL analysis said (Node v1 — commit `83435ce`, 2026-06-06)

The first node was a **coordinate-only transmitter**. The initial figures and analysis reported:

| Quantity | Initial value | Source (v1) |
| --- | --- | --- |
| Payload | **64 bit**, 2 fields (lat, lon) | `decode_binary.py` struct `">ii"` |
| Coordinate precision | **4 dp (~11 m)** | `lat*10000` |
| gap1 ASCII baseline | **184 bit** | `gap1_compression.csv` |
| gap1 reduction (binary vs ASCII) | **~57.9 %** | `decode_binary.py` v1 |
| gap6 telemetry (ASCII / Binary / Huffman) | **384 / 128 / 192 bit** | `gap6_telemetry.csv` v1 |
| gap6 Huffman reduction | **50.0 %** | v1 |
| Gap 2 latency | template only | — |
| Gap 3 reliability | not yet collected | — |
| Receive chain / UAV integration | none | — |

**Initial verdict (what v1 figures supported):** a proven binary-compression idea (~58 % smaller than ASCII) on a transmitter that carried an **operationally incomplete** 2-field, 11-metre payload, with **no** receive chain, no field reliability data, and no mission integration.

---

## 2. The CURRENT node (Node v2 — after commit `dcdadc7`, 2026-06-13)

| Quantity | Current value | Source (v2) | Reproduced? |
| --- | --- | --- | --- |
| Payload | **112 bit**, 6 fields | `decode_binary.py` `">iihHBB"` | ✅ round-trip bit-exact, T001–T006 |
| Fields | lat, lon, alt, uncertainty R, priority, survivor ID | Table 1, report | ✅ |
| Coordinate precision | **7 dp (~1 cm)** | `lat*10000000` | ✅ |
| gap1 ASCII baseline | **264 bit** (real `$CCTXM` format) | `gap1_compression.csv` | ✅ |
| gap1 reduction | **57.6 %** | `decode_binary.py` | ✅ |
| gap6 (ASCII / Binary / Huffman) | **368 / 128 / 184 bit** | `gap6_telemetry.csv` | ✅ |
| Reliability | **232 valid TX**, 100 % in-sample, Wilson LB **93.7 %** / pooled **98.4 %** | `gap3_analysis.py` | ✅ χ²=0.000, df=3, p=1.0000 |
| Latency (archived ASCII baseline) | **2574.5 ms**, SD 1094.7, n=30 | `gap2_analysis.py` | ✅ mean 2574, std 1095 |
| Receive chain | portal_reader → decoder → ROS 2 trigger | `gcs/`, `python/portal_reader.py` | software-exercised |

---

## 3. Evolution at a glance (v1 → v2)

| Aspect | v1 (initial) | v2 (current) | Direction |
| --- | --- | --- | --- |
| Payload size | 64 bit | 112 bit | richer |
| Fields carried | 2 | 6 | richer |
| Precision | 4 dp (~11 m) | 7 dp (~1 cm) | ~1000× finer |
| Coordinate reduction vs ASCII | ~57.9 % | 57.6 % | **stable across redesign** |
| Field reliability | none | 232 TX, ≥93.7 % LB | new evidence |
| Latency evidence | none | n=30 baseline | new evidence |
| Receive + UAV loop | none | software-complete | new capability |

**One-line evolution claim you can defend:** *the node moved from a 2-field, 11-metre, transmit-only prototype to a 6-field, centimetre-precision, software-complete rescue pipeline — while the core efficiency result (~58 % vs ASCII) held through the redesign.*

---

## 4. Limitations (audit findings, ranked) — with the evidence each rests on

### Tier A — Blocks the strongest version of the claim
- **A1. The 112-bit frame has never been transmitted on hardware.** It exists only as a `struct.pack` round-trip and a simulation harness. *Evidence: no hardware-TX commit after `dcdadc7`; report §6.4 concedes it.*
- **A2. The empirical campaign used the predecessor (ASCII) payload.** 228/232 reliability rows are tagged `[ASCII TX]`; the latency baseline is ASCII. *Evidence: `gap3_field_test.csv`; chronology — field test 06-08/09 predates the 112-bit upgrade 06-13.*

### Tier B — Caps the strength of the existing results
- **B1. Zero failures everywhere → cannot resolve true reliability above ~94 %.** χ²=0.000, p=1.000; the test cannot distinguish environments. *Evidence: `gap3_analysis.py` output.*
- **B2. "Twelve locations" share one hardcoded coordinate** (`30.4196, 120.2977`); no genuine fade/multipath diversity. *Evidence: `gap3_field_test.csv` gps columns.*
- **B3. Latency is a single n=30 session, on the superseded payload** — cannot support a diurnal-stability claim. *Evidence: `gap2_latency_ascii_baseline.csv`.*

### Tier C — Reporting/consistency defects (cheap to fix)
- **C1. README `:13` still says "Gap 3 = Pending hardware"** — contradicts the data and report §5.2. *Evidence: git shows Gap 3 collected 06-09.*
- **C2. "Strictly more information than Huffman" (§5.1) is false** — the 112-bit binary drops battery/mode/flags/timestamp that the 368-bit ASCII/Huffman carry; three different baselines (264/368/112) are compared as if equivalent. *Evidence: `telemetry_compare.py` vs `decode_binary.py`.*
- **C3. Figure 3 draws a hard "210-bit limit" the prose calls "unmeasured."** *Evidence: `gap6_telemetry_comparison.png` vs report §2.1/§6.4.*
- **C4. The comparison baseline moved (184→264, 384→368) without being flagged.** *Evidence: gap1/gap6 CSV diffs.*

---

## 5. Marks-maximisation guide — how to report a limitation so it EARNS marks

The core principle examiners reward: **a limitation you name, bound, and plan for is scholarship; a limitation you hide is a defect.** You lose marks for *unstated* weaknesses and for *overclaiming* — almost never for a weakness you characterise well. Apply this pattern to each finding:

> **State it → Bound it → Attribute it → Mitigate it → Show it doesn't sink the contribution.**

Worked examples for your three biggest limitations:

**A1 (112-bit never flown) — turn it into scope, not failure.**
> *"This study contributes the encoding, decode chain, and integration; physical-layer acceptance of the 14-byte frame is defined as the validation boundary of this objective. The pipeline is byte-identical in simulation, so the remaining risk is isolated to one module-buffer test (fallback: R→uint8, 104 bit)."*
Marks gained: you show you know exactly what is and isn't proven, and you've de-risked the gap to a single named test.

**A2 (reliability used ASCII payload) — convert chronology into a virtue.**
> *"The field campaign (8–9 June) preceded the payload upgrade (13 June); it therefore characterises the link itself, independent of payload, which is the more general result. The 112-bit frame inherits this channel reliability and adds only buffer-acceptance as an open variable."*
Marks gained: you reframe a sequencing artefact as a *cleaner* experiment (link characterised separately from payload).

**B1/B2 (100 % everywhere, one coordinate) — pre-empt the examiner's attack.**
> *"Zero failures bound reliability from below (Wilson ≥93.7 %) but cannot resolve values above ~94 %; the tested environments may not stress link margin, and all sessions used a fixed emulated coordinate. Deep-fade sites (sub-basement, reinforced structures) are identified as the conditions that would localise the failure boundary."*
Marks gained: you say the damaging sentence *before the examiner does*, which removes its power and demonstrates statistical maturity.

**General rules for the reporting section:**
1. **Put a "Limitations and Validity Boundary" subsection in the main body**, not buried — examiners grade what they can find.
2. **Every limitation gets a mitigation or future-work line.** A naked limitation reads as an excuse; a limitation + plan reads as a roadmap.
3. **Match every claim's verb to its evidence.** "We *demonstrate*" needs hardware; "we *show in simulation*" / "we *establish the bound*" is honest and unattackable. Downgrading verbs is the cheapest mark-saver you have.
4. **Disclose the moving baseline (C4) yourself** in one sentence — "the ASCII baseline was re-specified to the operational `$CCTXM` format" — so no reviewer can present it as something you hid.
5. **Fix C1–C3 before submission.** Internal contradictions are the one category examiners treat as carelessness rather than honest limitation, and they are free to fix.

---

## 6. The one move that maximises the score

Everything in Tier C is free marks (fix the README, the Huffman wording, the figure label, disclose the baseline change). Tier B is honest framing (Section 5 above). **Tier A is the only one that needs the lab:** a single satellite transmission of the real 112-bit frame, with a portal screenshot, converts "we show in simulation" into "we demonstrate" across the entire paper — and moves Empirical Validity from 3/10 toward 7–8/10 on its own.

*Reproduce any figure or statistic in this document with the scripts in `python/`; all inputs are the committed CSVs in `data/`.*
