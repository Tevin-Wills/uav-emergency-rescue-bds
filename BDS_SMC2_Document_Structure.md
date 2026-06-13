# BDS-SMC2 — Three-Document Structure
**Created 2026-06-13.** The work produces THREE nested documents, not two. This file is the canonical structure map.

```
OBJECTIVE 5 REPORT  — parent; proves Objective 5 within the group UAV rescue project
        |              (dissertation / supervisor / group deliverable)
        +--> PAPER 1   — transmission-layer slice (journal: MDPI Drones)
        +--> PAPER 2   — end-to-end-system slice (journal: IEEE Access / Drones)
```

Objective 5: *"Emulate survivor's precise location corrected with RTK and inject into BDS short messaging (Class+PNT)."*

---

## Document 1 — Objective 5 Report (parent)

| # | Section | Content | Source |
|---|---|---|---|
| 1 | Introduction & Objective 5 | Rescue problem; objective stated; "accomplish efficiently" defined | new |
| 2 | Role in the group system | Node 5 among the 5 modules; integration contract | group repo |
| 3 | Research gaps (backbone) | Gaps 1/2/3/6 as the necessary conditions of Objective 5 | Progress Report 2 |
| 4 | System design | Hardware, firmware, 112-bit payload, receive chain | Draft III |
| 5 | Results per gap | Fit / reliability / latency / compression | Progress Report 3-6 |
| 6 | Collective interpretation | Conjunctive-chain argument -> Objective 5 met efficiently | Progress Report 8 |
| 7 | Integration & demonstration | ROS 2 node, dashboard, end-to-end chain | new + dashboard |
| 8 | Limitations & future work | Emulated RTK, one-way link, single unit -> Paper 2 | Draft VII.D |
| 9 | Conclusion | Objective 5 accomplished with margin; 2 papers as outputs | new |

## Document 2 — Paper 1 (transmission layer)  [BDS_SMC2_Paper1_Draft.md]

I Intro · II Background · III System Design · IV Methodology · V Results:Latency+Encoding ·
VI Results:Reliability · VII Discussion · VIII Conclusion.
Status: I-IV, VI, VII, VIII drafted; V prose final with fillable slots.

## Document 3 — Paper 2 (end-to-end system)  [not yet written]

I Intro (Paper1 proved link; this proves pipeline) · II Background (RTK/GCS/ROS2/MAVLink) ·
III Architecture (RTK->encode->satellite->portal->decode->ROS2->UAV) · IV Methodology
(live RTK, multi-survivor, latency budget) · V-VI Results · VII-VIII Discussion+Conclusion.
Depends on: Paper 1 submitted + group integration session data.

---

## Content flow (write the report, get ~70% of both papers)

| Asset | Report | Paper 1 | Paper 2 |
|---|---|---|---|
| 112-bit payload | core (4) | core (III) | inherited foundation |
| Gaps 1,2,3,6 | all (5) | all | cited as proven |
| ROS 2 integration | 7 | brief (III.D) | CORE (III-IV) |
| Group system context | CENTRAL (2) | one paragraph | core (I) |
| Dashboard / black-box dt | 7 | IV.D + VI.C | latency budget |
| Comparison table | 6 | VII | reused |

**Principle:** one evidence base, three altitudes. Report = comprehensive, group-facing.
Paper 1 = transmission slice, sharpened. Paper 2 = system slice. Same data, different framing.
