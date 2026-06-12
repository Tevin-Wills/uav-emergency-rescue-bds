# BDS-SMC2 Node — Buyer's Evaluation (Updated)
**Evaluation date:** 2026-06-12
**Perspective:** A buyer comparing rescue-coordination systems, deciding whether this node is worth acquiring and what risks remain priced into the deal.
**Previous evaluation:** 2026-06-11 (Section 5 of `BDS_SMC2_Action_Items.md`)

---

## 1. The Verdict Yesterday vs Today

**Yesterday's verdict:**
> "The lab system produces operationally complete rescue data but has no transmission layer. The BDS-SMC2 node has a proven transmission layer (100% delivery) but carries an incomplete payload."

**Today's verdict:**
> The node now carries the lab system's complete rescue payload through its proven transmission layer AND delivers it into a working UAV mission pipeline. The product gap is closed in software; what remains is field proof, not design.

---

## 2. The Six Gaps That Blocked the Sale — Status

| Field | Lab System | Node Yesterday | Node Today | Status |
|---|---|---|---|---|
| Survivor ID | T001–T006 | Missing | uint8, 0–255 | ✅ CLOSED |
| Lat precision | 7 dp (~1 cm) | 4 dp (~11 m) | 7 dp (~1 cm) | ✅ CLOSED |
| Lon precision | 7 dp (~1 cm) | 4 dp (~11 m) | 7 dp (~1 cm) | ✅ CLOSED |
| Altitude | Real value | Missing | int16 metres | ✅ CLOSED (1 m resolution; 0.1 m possible at same size) |
| Uncertainty R | Explicit (1.6–11.9 m) | Missing | uint16 cm (0–655 m) | ✅ CLOSED |
| Priority | P0/P1/P2 | Missing | uint8 | ✅ CLOSED |

**Proof:** all six lab rescue-report records (T001–T006) encode to 112-bit messages and decode back bit-perfect — verified by automated round-trip test (`decode_binary.py`). The report that the lab system prints is now, line for line, what the node transmits.

---

## 3. What the Buyer Gets Today That Didn't Exist Yesterday

| Capability | Yesterday | Today |
|---|---|---|
| Payload | 64-bit coordinate-only | 112-bit complete rescue payload, 98 bits under BDS-3 limit |
| Receive chain | Messages died on the web portal | `portal_reader.py` polls the portal API, de-duplicates, logs to CSV |
| UAV integration | Simulated coordinate only | ROS 2 node decodes real ASCII / 112-bit / legacy binary; contract-compliant with the 5-module UAV system |
| Mission trigger | Make-believe | Decoded coordinate publishes to `/target/emergency_coordinate` → mission planning reacts |
| Verification | Manual | One-command integration check (`verify_integration.sh`, 3/3 checks) |
| Efficiency vs alternatives | −65% vs ASCII | −69.6% vs ASCII, 39% fewer bits than Huffman with MORE fields |

---

## 4. Open Risks — What a Buyer Still Discounts For

### Deal-breakers if unaddressed (rejection-level, unchanged from yesterday)

| # | Risk | Why the buyer cares | Mitigation path |
|---|---|---|---|
| 1 | **No live GPS input** — coordinates are hardcoded (now T001 instead of Hangzhou, but still hardcoded) | The "survivor position" is typed in by an engineer | Connect RTK/GPS module, or frame as testbed limitation explicitly |
| 2 | **28-char hex payload unverified on hardware** | The whole 112-bit upgrade is software-proven only; the BDS module's `$CCTXM` buffer may reject it | 1 test TX (fallback ready: R→uint8, 104 bits) |
| 3 | **T3 success heuristic** (`burstCount >= 3`) | "Delivered" may be declared without confirming delivery | Tighten detection or justify in documentation |
| 4 | **No comparison vs incumbent systems** (LoRa, GSM, COSPAS-SARSAT) | A buyer never buys without seeing the competition | Literature comparison table |
| 5 | **100% success rate with p=1.000** | Sounds too good; invites audit | Document every filtered timeout row |

### Major (price reduction, not rejection)

| # | Risk | Status |
|---|---|---|
| 6 | Gap 2 latency: single morning session only | Midday + evening sessions still outstanding — **Paper 1 blocker** |
| 7 | No power consumption data | Not measured |
| 8 | One-way link, no acknowledgment | Document as limitation |
| 9 | Rescue fields stop at the ROS boundary | `EmergencyCoordinate.msg` extension awaiting group agreement — fields are decoded and logged, not published |
| 10 | Portal reader untested live | Built and dry-run tested; needs browser tokens for first live poll |

### Acknowledged limitations (disclosed, not fixed)

- Single hardware unit — no generalisability claim
- Third-party portal (bdrd.hwasmart.com) is a single point of failure; token-based auth adds a manual browser step
- Destination ID hardcoded to 0 — no multi-unit addressing
- Altitude carried at 1 m resolution (lab reports 0.1 m); decimetre encoding possible within the same 112 bits if required
- "Indoor" environment definition, worst-case latency analysis still open

---

## 5. Buyer's Bottom Line

**Yesterday** this was two half-products: a data system that couldn't transmit and a transmitter that couldn't carry the data.

**Today** it is one integrated product with a software-complete pipeline:
*survivor data → 112-bit BDS-SMC → satellite → portal → reader → ROS 2 → UAV mission.*

**The buyer signs after seeing three things:**
1. One hardware TX proving the BDS module accepts the 112-bit message (risk #2)
2. One live portal poll pulling that message down (risk #10)
3. The Gap 2 midday/evening data completing the latency story (risk #6)

All three are scheduled for the next hardware session (`BDS_SMC2_Action_Items.md`, Section 1.3).

---

## 6. Remediation Plan (added 2026-06-12)

> **STATUS UPDATE (same day):** all Workstream A desk items are DRAFTED in `BDS_SMC2_Paper1_Sections.md` —
> #4 comparison table (Section A), #1 emulated-RTK framing (B), #5 Wilson claim + exclusion appendix (C),
> #8 one-way limitation + repeat-TX policy + failure modes (D), #9 .msg proposal pack (E).
> Remaining open: hardware items (#2, #6, #7, #10-live, #3-live) and the group meeting (#9).

### Workstream A — Writing + existing data (no hardware needed)

| Risk | Examiner's question | Answer strategy |
|---|---|---|
| #1 Hardcoded coords | "No GPS — real system?" | Objective 5 says *"EMULATE survivor's precise location corrected with RTK"* — lab T001–T006 ground truth IS the stated method. Contribution = transmission layer; position acquisition = RTK module's job. Define injection interface in architecture. |
| #3 T3 heuristic | "How do you know it was delivered?" | PLAN (not yet done): make portal receipt the delivery ground truth. Gap 3 has 232 valid TX whose `result` column comes from firmware [T3] detection — portal cross-matching is NOT yet recorded in the dataset. Use portal_reader.py to cross-match TX log vs portal inbox, then claim "portal-corroborated". Until then, T3 = timing instrument AND success criterion (disclose this). |
| #4 No baseline | "Why not LoRa/GSM/COSPAS-SARSAT?" | Literature table: GSM = infrastructure-dependent (dead in disasters); LoRa = needs gateways; COSPAS-SARSAT = no custom payload, minutes–hours latency; Iridium = per-message cost. BDS-SMC: no ground infrastructure, 210-bit payload, measured 2.57 s. |
| #5 100% suspicion | "Test designed not to fail?" | (a) Claim the Wilson lower bound (57/57 → ≥93.7% at 95% CI), not 100%. (b) Appendix documenting every filtered timeout row. (c) Concede environments may not stress link margin; propose deep-indoor tests as future work. |
| #8 No ACK | "How does the survivor know?" | Document one-way limitation + repeat-TX policy: k repeats → 1−(1−p)^k delivery probability, computable from own data. RDSS receive = future work. |
| #7 Power (design now) | "Energy per message?" | USB power meter during TX session → J/message + messages-per-battery. |

### Workstream B — One hardware day (Section 1.3 checklist)

| Risk | Plan |
|---|---|
| #2 | 1 test TX of T001 message. ALSO VERIFY: does the module transmit hex as binary (112 bits on-air) or as ASCII chars (224 bits — over limit)? Portal message view shows which. Bit-accounting argument depends on it. Fallback: R→uint8 (104 bits). |
| #6 | Midday bat → flash + test TX + power measurement → evening bat. One outing closes #2, #6, #7. |
| #10 | Browser tokens → portal_reader.py --dump → map fields → wire decoder → full-chain demo. |

### Workstream C — One group conversation

| Risk | Plan |
|---|---|
| #9 | Bring: live T001 demo command, exact 4-line .msg diff (altitude/uncertainty_m/priority/survivor_id), backwards-compat argument (additive fields default 0), and their own coordinate_format.md which already documents altitude + priority. |

### Core thesis sentence every risk defends
*Empirical proof that a complete 6-field rescue payload fits a 112-bit BDS-3 message with delivery reliability ≥93.7% (Wilson LB) and ~2.6 s latency, integrated into a UAV mission pipeline.*

---

*Companion documents: `BDS_SMC2_Action_Items.md` (master suggestion log), `docs/UBUNTU_INTEGRATION_RUNBOOK.md` in the group repo (integration verification).*
