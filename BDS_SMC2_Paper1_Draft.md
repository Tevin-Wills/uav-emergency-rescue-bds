# Paper 1 — Working Draft, Sections I–IV
**Title (working):** A 112-bit Binary Rescue Payload over BeiDou-3 Short Message Communication: Environment-Stratified Reliability and Latency for UAV Search-and-Rescue
**Author:** Letsoalo Maile
**Status:** Sections I–IV drafted 2026-06-13 (no new data required). Sections V–VIII await the field day. References [R1]–[R6] resolved in `BDS_SMC2_Paper1_Sections.md` §A.3; [REF-n] markers need sourcing during assembly.
**Style note:** written for MDPI Drones (empirical systems paper). Lift paragraphs as-is; tighten during assembly.

---

## I. Introduction

When a major disaster strikes — earthquake, flood, landslide — the terrestrial communication infrastructure that survivors would use to call for help is frequently among the first casualties. Cellular base stations lose power or backhaul, and coverage collapses precisely where and when it is most needed [REF-1: disaster comms failure study]. In the critical early hours of a rescue operation, the dominant cost is not reaching victims but *finding* them: search teams expend their most valuable resource, time, establishing positions that survivors may already know precisely.

The BeiDou-3 navigation satellite system (BDS-3) offers a capability unique among global navigation satellite systems: Short Message Communication (SMC), which allows a terminal to transmit a short data message directly through the satellite constellation with no dependence on terrestrial networks [R1]. The regional (RDSS) service carries up to 210 bits per message. This is sufficient, in principle, to carry a survivor's position to a rescue coordination point through infrastructure that cannot be destroyed by the disaster — but 210 bits is far too small for conventional text encodings of rescue data, and the practical behaviour of the link under rescue-relevant conditions (obstructed sky, urban canyons, indoor environments) has not been characterised at the application level.

This paper asks whether BDS-3 SMC can serve as the communication backbone of an autonomous UAV rescue system: a pipeline in which a survivor's RTK-corrected position is encoded into a single short message, transmitted via satellite, decoded at a ground station, and used to trigger a UAV mission to the survivor's location. Answering this requires four subsidiary questions, each addressed empirically:

1. **Capacity** — can a *complete* rescue payload (position at RTK-grade precision, altitude, position uncertainty, triage priority, survivor identity) fit within a single 210-bit message? (Sections V.A, designed in III.B)
2. **Reliability** — does delivery survive the propagation environments where rescues actually occur? (Section VI)
3. **Latency** — does the message arrive fast enough for real-time rescue coordination, and does this vary with time of day? (Section V)
4. **Integration** — can the decoded message drive an autonomous UAV mission pipeline rather than terminating at a human-read display? (Section III.D)

**Contributions.** This work makes four contributions. (i) A 112-bit binary rescue payload that carries six operationally complete rescue fields — latitude and longitude at 7 decimal places (≈1 cm encoding precision), altitude, uncertainty radius, triage priority, and survivor identifier — within 53% of the BDS-3 regional message budget, verified bit-perfect against RTK ground-truth records. (ii) The first environment-stratified, application-layer measurement of BDS-3 SMC delivery reliability, spanning open sky, light canopy, urban canyon, and indoor conditions (232 valid transmissions across 12 locations), reported with Wilson confidence bounds rather than point estimates. (iii) An end-to-end latency characterisation of the transmission chain, including a per-message measurement of the satellite ground-segment transit time obtained by cross-matching transmitted payloads against independent portal receipts. (iv) An empirical demonstration that fixed-point binary packing outperforms Huffman entropy coding by 39% for structured rescue telemetry while carrying more fields — a result that contradicts the default assumption that compression is the answer to small message budgets.

We deliberately narrow the novelty claim: the system-level field campaign of Li et al. [R1] established BDS-3 global SMC feasibility with 2149 transmissions (97.72% delivery). The present work is complementary and application-layer: it characterises the *regional* service as a *rescue data link* — stratified by propagation environment, carrying a complete triage payload, and integrated into a UAV mission pipeline.

## II. Background and Related Work

### II.A BDS-3 Short Message Communication

BDS-3 provides two SMC services [R1]: a regional service via geostationary satellites (RDSS), offering up to 210 bits per message over the Asia-Pacific region, and a global service via the MEO constellation's inter-satellite links offering up to 560 bits. A terminal transmits an application message through an L-band uplink; the space and ground segments route it to the recipient — in this work, an operator web portal acting as the rescue coordination endpoint. The transmitting module reports two acknowledgments observable at the terminal: command acceptance, and a satellite-segment acknowledgment indicating the message was accepted for delivery. Critically for experimental design, the segment between the satellite acknowledgment and ground delivery exposes no telemetry to the user; we treat it as a black box and measure it externally (Section IV.D).

### II.B Encoding for small message budgets

Prior work on fitting useful data into BDS SMC messages has concentrated on compression: lossy compression schemes for sensor streams [REF-2: Springer MTA 2022 lossy BDS-3 compression], dual-stage dictionary/entropy models for maritime safety text [REF-3: JMSE 2023 dual-stage], and byte-encoding-enhanced prediction models [REF-4: JMSE 2024]. These approaches share an assumption: that the payload is *text-like* and the problem is statistical redundancy. For structured numeric telemetry, an alternative is to abandon character representation entirely and pack fields at their native binary widths. Section V.A tests these alternatives head-to-head on identical rescue data.

### II.C Satellite distress systems

The incumbent infrastructure-free distress system is COSPAS-SARSAT, whose 406 MHz beacons transmit a fixed-format message of 112 (short) or 144 (long) data bits [R3]. The format carries beacon identity and a coarse encoded position, refined on the ground by Doppler or GNSS data; it has no user-definable payload, so triage information (who, how urgent, how precise) cannot be conveyed. Commercial satellite messaging (e.g., Iridium SBD, 340 B mobile-originated [R4]) carries arbitrary payloads at per-message cost over proprietary infrastructure. Terrestrial LPWAN approaches such as LoRaWAN carry 51–242 B per uplink depending on region and data rate [R2] but require a surviving gateway within link range — re-introducing the infrastructure dependence the disaster scenario excludes. The comparison is tabulated in Section VII (Table X). A pointed coincidence frames this work's capacity claim: COSPAS-SARSAT's short format and the proposed rescue payload are both 112 bits — but where the former carries identity alone, the latter carries a complete six-field triage record.

### II.D UAV rescue integration

BDS SMC has been combined with UAVs primarily as a backup command link or for identity authentication in emergency UAV networks [REF-5: UAV BeiDou auth protocol 2021]. Emergency-information transmission platforms have demonstrated text and image delivery over BDS-3 [REF-6: urban emergency picture transmission, IEEE 2023]. In these systems the received message terminates at a human operator. To our knowledge, no published system closes the loop from a BDS-SMC rescue message to an *autonomous* UAV mission trigger; Section III.D describes such an integration into a five-module ROS 2 rescue system.

## III. System Design

### III.A Hardware node

The transmitting node comprises an ESP32 microcontroller and a BDS-3 RDSS communication module with a circular patch antenna, connected over UART through an RS232-TTL converter (Fig. 1). The node fires one message per cycle; firmware timestamps the command issue ([T1]), the module's acceptance ([T2]), and the satellite-segment acknowledgment ([T3]) on its serial output, where a logging host records them. Total component cost is low (commodity development hardware), supporting the reproducibility goal: the complete firmware, logging, decoding, and analysis toolchain is released with this paper, implemented with Python standard-library dependencies only.

### III.B The 112-bit rescue payload

The payload design (Table 1) packs six fields into 14 bytes, big-endian:

| Bytes | Field | Type | Resolution / range |
|---|---|---|---|
| 0–3 | Latitude | int32 ×10⁷ | 7 dp ≈ 1.1 cm |
| 4–7 | Longitude | int32 ×10⁷ | 7 dp |
| 8–9 | Altitude | int16 | 1 m, ±32 km |
| 10–11 | Uncertainty radius R | uint16 | 1 cm, 0–655 m |
| 12 | Priority | uint8 | P0/P1/P2 triage class |
| 13 | Survivor ID | uint8 | 0–255 |

Three design decisions deserve justification. First, the ×10⁷ coordinate scaling matches the precision of the RTK source: encoding at 4 decimal places (a common choice in ASCII implementations) quantises an RTK fix to ≈11 m, silently destroying two orders of magnitude of positioning investment before transmission. Second, the *uncertainty radius* is carried explicitly because it defines the rescuer's search area; a coordinate without uncertainty is operationally incomplete. Third, three fields common in telemetry designs — battery, mode, timestamp — are deliberately absent: battery and mode describe the transmitting platform (available to its operator through richer channels), and the timestamp duplicates the receive-time record created independently at the portal. The result is 112 bits — 53% of the 210-bit regional budget, leaving 98 bits of headroom.

### III.C Receive chain

Messages are delivered to the operator portal. A portal-reader process polls the portal's API, de-duplicates arrivals, and records message content and receive time. A decoder unpacks the payload; a status instrument (Section IV.D) cross-matches each transmission against portal receipts by payload content, yielding per-message delivery corroboration and ground-segment transit time. The receive chain is one-way as exercised; the RDSS service supports terminal-directed messages, so an application-layer acknowledgment is an implementation matter left as future work (the repeat-transmission policy in Section VII quantifies delivery assurance without it).

### III.D ROS 2 integration

The decoded coordinate enters a five-module UAV rescue system (RTK positioning, flight control, target detection, path planning, and this work's communication module) as a ROS 2 node publishing `/target/emergency_coordinate` (latched QoS), which the mission-planning modules consume as the rescue trigger. The node decodes all three message formats (ASCII, 112-bit binary, legacy 64-bit) behind an unchanged topic interface, so integration imposed no changes on any consuming module. [TODO: cite group integration contract / system architecture figure.]

## IV. Methodology

### IV.A Coordinate source: emulated RTK injection

This study evaluates the transmission layer; position acquisition is out of scope by design, consistent with the project objective to *"emulate survivor's precise location corrected with RTK and inject into BDS short messaging."* The transmitted coordinates are ground-truth RTK fixes (records T001–T006, Table 2) produced by the laboratory positioning system, injected at the encoder boundary at native 7-decimal precision. This follows standard practice in link characterisation: fidelity, loss and latency can only be attributed to the channel if the injected data is controlled. The encoder boundary is a defined interface; any WGS-84 GNSS source can replace the emulated input without firmware changes beyond the injection call.

### IV.B Reliability experiment (delivery success by environment)

Four propagation environments were selected to span rescue-relevant conditions: open sky, light canopy, urban canyon, and indoor. Each environment contributed three locations; each location received ~20 transmissions (one per 10 s cycle), yielding 232 valid transmissions. Success was recorded on the satellite-segment acknowledgment; Section IV.D describes the independent corroboration. Analysis uses Wilson score intervals for per-environment success proportions — chosen over normal approximation because observed proportions lie at the boundary — a χ² test of homogeneity across environments, and pairwise Fisher exact tests with Bonferroni correction. We pre-commit to claiming only the Wilson lower bound, not observed point estimates: zero failures in n≈57 per cell supports "≥93.7% per environment at 95% confidence" and nothing stronger. **Exclusions:** 33 logged rows from one location/day were excluded due to an instrumentation defect (the logger's success marker predated a firmware fix and could not detect acknowledgments); the location was re-collected in full, and the complete raw log including excluded rows is published. No row with a detected acknowledgment was excluded.

### IV.C Latency experiment (time-of-day sessions)

End-to-end transmission latency is defined as T3 − T1: command issue to satellite-segment acknowledgment. Three 30-transmission sessions (morning, midday, evening) are collected at a fixed location on a single day, all carrying the operational 112-bit payload, and compared by one-way ANOVA. A prior 30-transmission session collected with the ASCII payload is retained as an archived reference group, excluded from the time-of-day analysis (a payload-format difference would confound it) and used instead for a secondary payload-format comparison. [TODO Section V: insert session statistics, ANOVA, CDF figure after the field day.]

### IV.D Delivery corroboration and black-box transit

The firmware's acknowledgment is a necessary but self-reported success criterion. To corroborate it independently, the exact transmitted message bytes are recorded per transmission and matched against portal receipts: a transmission is *confirmed* when its payload appears verbatim in a portal message (bit-perfect criterion), proving end-to-end content integrity through the satellite segment. The interval between satellite acknowledgment and portal receipt additionally yields a per-message upper bound on the ground-segment transit time — a quantity not exposed by any BDS user interface and, to our knowledge, not previously reported per-message at the application layer. [TODO Section V/VI: insert confirmation rate and transit-time distribution after the field day.]

### IV.E Encoding experiment

Three encodings of identical rescue data are compared by exact bit count: ASCII text (baseline), dynamic Huffman coding of the ASCII string (entropy-coding benchmark), and the fixed-point binary payload of Section III.B. All three decode losslessly; binary round-trip is verified bit-perfect on all six ground-truth records. The Huffman benchmark is reported with an implementation caveat material to deployability: dynamic Huffman requires conveying the code table, which itself exceeds the message budget, so its figure represents a lower bound unavailable in practice without a pre-agreed static table.

---

## Assembly checklist (delete before submission)
- [ ] Fig. 1: hardware/system diagram (use `figures/payload_route_illustration.png` as base)
- [ ] Table 2: T001–T006 ground-truth records
- [ ] Resolve [REF-1]…[REF-6] (candidates in `BDS_SMC2_Node_Evaluation.md` paper list; verify before citing)
- [ ] Sections V–VIII from `BDS_SMC2_Paper1_Sections.md` (results wording, comparison table, limitations, repeat-TX policy) + field-day numbers
- [ ] Venue template (MDPI Drones), author affiliations, data-availability statement (publish raw CSVs incl. excluded rows)
