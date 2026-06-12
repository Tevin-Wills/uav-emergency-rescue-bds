# Paper 1 — Drafted Defence Sections
**Created:** 2026-06-12 · Closes risks #1, #4, #5, #8 (+ #9 proposal pack) from `BDS_SMC2_Node_Evaluation.md`
**Status:** draft text ready to lift into the dissertation. `[CITE: …]` marks where a verified reference must be inserted — do not submit with placeholders.

---

## SECTION A — Comparison With Existing Emergency Communication Systems (closes #4)

### A.1 The table

| Criterion | GSM/Cellular SOS | LoRa/LoRaWAN | COSPAS-SARSAT (406 MHz PLB) | Iridium SBD | **BDS-3 SMC (this work)** |
|---|---|---|---|---|---|
| Surviving ground infrastructure required | Cell towers + backhaul + power | Gateway within link range + backhaul | None (satellite) | None (satellite) | **None (satellite)** |
| Works when terrestrial networks destroyed | ✗ | ✗ (gateway is terrestrial) | ✓ | ✓ | **✓** |
| Custom data payload | ✓ (SMS 1120 bits) | ✓ (51–242 B by region/data-rate) [R2] | ✗ — fixed distress format, no user fields [R3] | ✓ (340 B MO) [R4] | **✓ 210 bits regional / 560 bits global** [R1] |
| Survivor-to-rescuer latency | Seconds (if network alive) | Seconds (if gateway alive) | Minutes–hours (LEOSAR/GEOSAR pass + MCC routing) [R5 — VERIFY exact figures] | Seconds–minutes | **2.57 s mean measured (n=30)** |
| Position precision conveyed | Cell/AGPS-dependent | Payload-defined | Coarse encoded position; refined by Doppler/GNSS [R3] | Payload-defined | **~1 cm encoding (7 dp fixed-point)** |
| Per-message cost | Carrier SMS | Free (own infra) | Free (treaty service) | Per-message commercial fee | Service-subscription [VERIFY: regional service terms] |
| Two-way | ✓ | ✓ | ✗ (one-way alert; Galileo RLS return link emerging) [R5 — VERIFY] | ✓ | Partially (RDSS supports receive; not exercised here) |
| Triage fields (ID, priority, uncertainty) | Possible, network-dependent | Possible | ✗ | Possible | **✓ demonstrated in 112 bits** |
| Field-measured delivery reliability in this class | n/a | Published gateway studies [R6 — VERIFY] | Published system stats [R5] | Published | **232/232 across 4 environments (this work); 97.72% over 2149 TX (system-level) [R1]** |

### A.2 The paragraph that goes under it

> Among systems usable when terrestrial infrastructure is destroyed, only COSPAS-SARSAT, commercial satellite messaging (e.g., Iridium SBD), and BDS SMC remain. COSPAS-SARSAT provides no user-defined payload: a beacon can say *where* it is, but not *who* needs help, *how urgently*, or *how precise the fix is* — the triage fields shown in this work to fit within a single 112-bit BDS-3 message. (A pointed coincidence: the COSPAS-SARSAT short-format message is itself 112 bits [R3] — the same budget that here carries a complete six-field triage payload.) Commercial satellite messaging carries arbitrary payloads but imposes per-message costs and proprietary infrastructure. BDS-3 SMC occupies a distinct position: treaty-grade independence from ground infrastructure, a user-defined payload sufficient for complete rescue triage, and — as measured here — single-digit-second delivery latency. The system-level field campaign of Li et al. [R1] reported 97.72% delivery over 2149 transmissions; the present work complements it with an environment-stratified measurement (open sky, light canopy, urban canyon, indoor) at the application layer.

### A.3 References for this section (verified 2026-06-13 unless marked VERIFY)

- **[R1]** Li G., Guo S., Lv J., Zhao K., He Z., "Introduction to global short message communication service of BeiDou-3 navigation satellite system," *Advances in Space Research*, 67(5):1701–1708, 2021. doi:10.1016/j.asr.2020.12.011. ⚠ NOTE: earlier project notes wrongly attributed this to "Geodesy and Geodynamics" — corrected.
- **[R2]** LoRa Alliance, *RP002-1.0.4 LoRaWAN Regional Parameters*, 2022. (Max application payload 51–242 B depending on region/data rate — confirm exact table values against the spec PDF.)
- **[R3]** COSPAS-SARSAT, *C/S T.001: Specification for COSPAS-SARSAT 406 MHz Distress Beacons*. (Short format = 112 data bits, long = 144; user protocols carry ID, not arbitrary payload.) cospas-sarsat.int
- **[R4]** Iridium, *Short Burst Data (SBD) Service* — 9602/9603 transceiver: 340 B mobile-originated max. iridium.com/services/iridium-sbd
- **[R5]** COSPAS-SARSAT system documentation / NOAA SARSAT training material — **VERIFY latency figures** before quoting minutes–hours.
- **[R6]** LoRa range/coverage evaluation study — candidate: Petäjäjärvi et al., "On the coverage of LPWANs," ITST 2015 — **VERIFY before citing**.

---

## SECTION B — Methods Framing: Emulated RTK Injection (closes #1)

> **Coordinate source.** This study evaluates the transmission layer of a rescue messaging system; position *acquisition* is explicitly out of scope, consistent with Objective 5: *"Emulate survivor's precise location corrected with RTK and inject into BDS short messaging."* Accordingly, the transmitted coordinates are not synthesized values but ground-truth RTK fixes (records T001–T006, Table 5) produced by the laboratory positioning system, injected at the encoder boundary at their native 7-decimal-place precision. This follows standard practice in channel and link characterisation, where known reference data is injected so that fidelity, loss, and latency can be attributed to the link rather than to the data source. The encoder boundary is a defined interface: any GNSS/RTK source emitting WGS-84 coordinates can replace the emulated input without firmware changes beyond the injection call.

**One-sentence viva answer:** "Hardcoding is the emulation method the objective specifies — I measure the channel, and you cannot measure a channel without controlling what enters it."

---

## SECTION C — Statistical Claims and Exclusion Appendix (closes #5)

### C.1 The reliability claim (use this wording, never "100%")

> Across 232 valid transmissions stratified over four propagation environments (open sky n=61, light canopy n=57, urban canyon n=57, indoor n=57), all transmissions were acknowledged by the satellite segment ([T3] confirmation). With zero observed failures, the data supports a 95% Wilson lower confidence bound of **≥93.7% per-environment delivery reliability** (≥98.4% pooled). No environment effect was detectable (χ²=0.000, df=3, p=1.000; pairwise Fisher's exact, Bonferroni-corrected, all p=1.000). We emphasise that zero failures in n≈57 per cell bounds reliability from below but cannot distinguish reliability values above ~94%; environments imposing deeper fades (sub-basement, dense urban indoor, heavy rain) are required to localise the failure boundary and are identified as future work.

### C.2 Exclusion appendix (real numbers from the dataset — verified 2026-06-12)

> **Appendix X — Excluded records.** The raw field log contains 265 rows, of which 33 were excluded from analysis. All 33 exclusions share a single cause, location, and day: location OS-1 (open sky), 2026-06-08, attempts 1–33, annotated at collection time as *"T3 detection bug — firmware fix pending; logger could not detect satellite ACK."* The logger's success criterion depended on a serial marker the firmware did not yet emit; the satellite acknowledgments were therefore undetectable by instrumentation, not absent. The firmware was corrected (commit history: T3 detection via UART2 buffering) and **location OS-1 was re-collected in full** (23 valid transmissions, commit 89c5037). No row with a detected satellite ACK was excluded; no row was excluded for any reason other than the instrumentation defect described. The complete raw log, including excluded rows, is published with this work.

**Why this defends itself:** the exclusions are (i) total at one location, (ii) annotated in the data *at collection time* — not retrofitted, (iii) followed by a full re-collection rather than deletion. A reviewer checking the CSV finds exactly this story.

---

## SECTION D — Limitations: One-Way Link and Repeat-Transmission Policy (closes #8)

### D.1 Limitation statement

> The link as exercised is one-way: the survivor's node receives a satellite-segment acknowledgment ([T3]) confirming acceptance, but no application-layer acknowledgment from the rescue ground station reaches the survivor. The survivor therefore cannot distinguish "message delivered to rescuers" from "message accepted by the satellite". The BDS RDSS service supports message reception at the terminal, so closing this loop is an implementation matter rather than a system impossibility; it is left as future work.

### D.2 Repeat-transmission policy (the engineering mitigation, from our own data)

> Absent end-to-end acknowledgment, delivery assurance is obtained statistically by repetition. With measured per-attempt delivery probability bounded below by p = 0.937 (Section C), k independent attempts deliver at least one message with probability 1−(1−p)^k:

| Attempts k | Delivery probability (worst-case p=0.937) | Added air-time (10 s TX interval) |
|---|---|---|
| 1 | ≥ 93.70% | — |
| 2 | ≥ 99.60% | +10 s |
| 3 | ≥ 99.975% | +20 s |
| 4 | ≥ 99.998% | +30 s |

> A three-repeat policy therefore exceeds 99.97% worst-case delivery assurance at a cost of 20 seconds — negligible against rescue-operation timescales. The 112-bit payload's survivor-ID field makes repeats idempotent at the receiver (duplicates collapse on ID).

### D.3 Failure-modes subsection (rigor — disclose before being asked)

> **Known failure modes and single points of failure.** (1) The operator portal is a third-party dependency on the receive path; its outage blinds the ground station even when transmissions succeed. (2) A single hardware unit was tested; unit-to-unit variance is uncharacterised. (3) The regional service imposes transmission-frequency limits; sustained high-rate operation risks throttling. (4) Destination addressing was fixed (ID 0); multi-unit deployments require the addressing scheme present in the message format but not exercised here. (5) The T3 acknowledgment confirms satellite-segment acceptance, not ground-segment delivery; portal cross-matching (instrumented in this work's dashboard) closes this gap operationally.

---

## SECTION E — EmergencyCoordinate.msg Extension Proposal (pack for #9 — group meeting)

**The ask (4 added lines, fully backwards-compatible):**

```
# interfaces/msg/EmergencyCoordinate.msg  — proposed additions
float32 altitude        # metres AMSL, 0.0 if unknown
float32 uncertainty_m   # horizontal uncertainty radius R, 0.0 if unknown
uint8   priority        # 0=P0 (critical), 1=P1, 2=P2; 0 default
uint8   survivor_id     # 0-255 victim identifier, 0 if unassigned
```

**Arguments, in meeting order:**
1. Additive fields default to zero — **no existing subscriber breaks**, no launch file changes.
2. Their own `interfaces/coordinate_format.md` already documents `altitude` and `priority` for the emergency target — this implements the team's documented spec, not a new idea.
3. The data already flows: live demo command (decoded fields appear in the node log today):
   `ros2 run beidou_short_message beidou_publisher_node --ros-args -p raw_message:='$CCTXM,0,BIN:1D35DB5605079637007200A00101*CS'`
4. Consumer value: path_planning gets a search radius (R) instead of a point; qgc_control gets priority for multi-survivor ordering.
5. Cost: one .msg edit + `colcon build` of `interfaces`. Nothing else changes until consumers *choose* to read the new fields.

---

*All numeric claims in this document re-verified against the raw datasets on 2026-06-12 (audit in `BDS_SMC2_Node_Evaluation.md`). References resolved 2026-06-13 (Section A.3); only items marked **VERIFY** still need checking against the primary documents before submission.*
