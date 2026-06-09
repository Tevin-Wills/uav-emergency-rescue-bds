# Level 3 Workplan — Resilient RTK Positioning for Disaster Rescue

**Module:** `rtk_positioning` — Student 1 (Tevin Wills)
**Created:** 2026-06-03
**Status:** Phase 2 complete through Step 2.8 — analyse_level3.py and figures remaining

---

## 1. Where We Are

### Level 1 — Complete ✓
Standalone ROS 2 RTK simulation. No PX4, no Gazebo. Proved the RTK noise model and
correction model work correctly. Established the baseline accuracy parameters and the
logging and analysis infrastructure that all subsequent levels build on.

Key results: 2,718 samples · Raw GNSS 2.394 m · RTK 0.101 m · 95.8% improvement

### Level 2 — Complete ✓
PX4/Gazebo-integrated RTK simulation. Real UAV pose from PX4 SITL. Correction-driven
state transitions via `rtcm_correction_simulator_node`. One deliberate CORRECTION_LOST
event with recovery demonstrated. QGC mission flown and cross-validated against ULog.

Key results: 10,282 samples · Raw GNSS 2.413 m · RTK 0.080 m · 96.7% improvement ·
98.1% time in RTK_FIXED

Level 2 results are the **Scenario 1 baseline** for Level 3. No re-running needed.

---

## 2. What Level 3 Is

### Research Question
*How do we achieve autonomous rescue mission success in disaster zones where GNSS
is degraded?*

This is an engineering question, not a failure study. The goal is to demonstrate
that the RTK module maintains mission-viable positioning across the realistic,
co-occurring degradation conditions of a disaster environment.

### Why a Compound Scenario (Not Four Separate Ones)
In a real disaster zone, degradation conditions do not present themselves one at a
time. Multipath from collapsed buildings, intermittent correction links from damaged
communications infrastructure, and variable satellite visibility all occur
simultaneously and compound each other. Treating them as separate, isolated tests
would be scientifically artificial and would not answer the real question.

**One compound disaster scenario** — modelling co-occurring, progressive degradation
that mirrors the actual mission — is the honest and correct model.

### Research Contribution
A resilient RTK positioning design for UAV disaster rescue that:
1. Models co-occurring disaster GNSS degradation realistically
2. Maintains mission-viable positioning throughout approach and landing phases
3. Provides continuous position uncertainty output so downstream modules can act
   on confidence, not just status codes
4. Demonstrates mission success under conditions where a naive implementation degrades

---

## 3. The Three-Run Comparison Structure

| Run | Conditions | Source | Purpose |
|-----|-----------|--------|---------|
| **Run 1 — Baseline** | Ideal. Open sky, reliable corrections | Level 2 results (already done) | Reference point. Best achievable accuracy |
| **Run 2 — Compound Disaster** | Co-occurring multipath + intermittent corrections, progressive degradation | **Level 3 primary build** | Core research demonstration |
| **Run 3 — Total Failure** | Zero corrections, GNSS_ONLY only, elevated noise | Config change only | Lower bound. System behaviour when everything fails |

Run 1 is already done. Run 2 is the Level 3 engineering work. Run 3 is a quick
config-only addition for completeness.

---

## 4. The Compound Disaster Scenario Design (Run 2)

The scenario models a single complete rescue mission. Conditions change as the UAV
moves through the disaster zone, not as artificial switches.

### Mission Phases and GNSS Conditions

| Phase | Approx. Time | GNSS Noise (std) | Correction Availability | Correction Quality |
|-------|-------------|-----------------|------------------------|-------------------|
| **Departure** — base to disaster zone edge | 0–120 s | 1.5 m (baseline) | Continuous, high quality | 0.95 |
| **Approach** — entering disaster zone | 120–240 s | Ramping 1.5→2.5 m | Intermittent (brief drops) | Degrading 0.95→0.60 |
| **Search zone** — operating over collapse | 240–600 s | 2.5–3.0 m (peak) | Periodic loss (30–45 s gaps every 90 s) | 0.50–0.70 |
| **Landing** — descending to survivor | 600–660 s | 2.5 m | Available but degraded quality | 0.55–0.65 |
| **Departure** — exit disaster zone | 660–780 s | Ramping 2.5→1.5 m | Restoring | Recovering 0.65→0.90 |

### Parameter Justification
- GNSS noise increase (1.5→3.0 m): consistent with published urban canyon multipath
  measurements in post-earthquake environments and reflected in ITU-R P.2040 signal
  propagation studies in obstructed environments
- Correction gaps (30–45 s loss periods): consistent with documented RTK link
  reliability in infrastructure-damaged disaster zones; matches CORRECTION_LOST
  behaviour already demonstrated in Level 2
- Correction quality degradation (0.95→0.55): models increased baseline-rover
  distance and obstruction as UAV penetrates disaster area

### Mission-Phase Accuracy Thresholds
Two thresholds define what "mission-viable" means. These are the targets Level 3
must demonstrate the system can meet.

| Phase | Required Accuracy | Basis |
|-------|------------------|-------|
| **Approach and navigation** | ≤ 2.0 m horizontal | Sufficient for obstacle avoidance and waypoint navigation |
| **Precision landing** | ≤ 0.3 m horizontal | Required for reliable landing on/near survivor marker |

---

## 5. RTK Module Changes for Level 3

### 5.1 Compound Scenario Configuration
- `config/level3_disaster_scenario.yaml` — full parameter set for Run 2
- `config/level3_total_failure.yaml` — full parameter set for Run 3
- Parameters control time-varying noise profile and correction availability schedule

### 5.2 Time-Varying Noise Profile
The `rtcm_correction_simulator_node` currently uses a fixed correction profile.
Level 3 extends it to support a **mission-phase profile**: noise and correction
quality vary as a function of elapsed mission time, following the table in Section 4.

This is a configuration extension, not a new node. The same node reads a
phase-profile block from YAML instead of fixed values.

### 5.3 Dynamic Uncertainty Output
Currently the RTK module publishes a fixed accuracy value per status
(`/rtk/accuracy`). Level 3 makes this dynamic: the published uncertainty
is computed from current correction quality, correction age, and status,
not from a fixed lookup table. This gives `path_planning` and `qgc_control`
a continuous, real-time confidence signal.

Implemented inside `rtk_positioning_node.py`. No new topic required — the
existing `/rtk/accuracy` topic carries the dynamic value.

### 5.4 Mission Viability Signal (New Topic)
A new lightweight topic: `/rtk/mission_viability` (`std_msgs/String`)

Published values (non-overlapping, priority order):
- `LANDING_VIABLE`  — accuracy ≤ 0.3 m; safe to initiate precision landing
- `APPROACH_VIABLE` — accuracy 0.3–2.0 m; safe to navigate, not to land
- `DEGRADED`        — accuracy 2.0–4.0 m; below approach threshold, reduce speed / hold
- `INSUFFICIENT`    — accuracy > 4.0 m; abort phase or hold position

Note: the 4.0 m DEGRADED ceiling is 2× the approach threshold. Peak compound-scenario
noise reaches 3.0 m, so DEGRADED is reachable; INSUFFICIENT is the extreme edge case.

This is the signal `path_planning` will consume during integration to modulate
mission behaviour. For Level 3 standalone, it is logged and graphed.

### 5.5 Level 3 Launch and Runner
- `launch/level3_resilient_rtk.launch.py`
- `run_level3.sh`

---

## 6. Analysis and Outputs

### Analysis Script
`results/graphs/rtk_positioning/analyse_level3.py`

Extends the Level 2 analysis with scenario comparison and mission viability metrics.

### Figures to Produce

| Figure | Content |
|--------|---------|
| `l3_compound_scenario_profile.png` | GNSS noise and correction quality over mission time — the input conditions |
| `l3_error_over_time.png` | RTK error over full mission, shaded by phase |
| `l3_uncertainty_over_time.png` | Dynamic uncertainty output vs fixed Level 2 accuracy |
| `l3_viability_timeline.png` | Mission viability signal state over time |
| `l3_three_run_comparison.png` | Side-by-side accuracy: baseline vs compound vs total failure |
| `l3_mission_phase_accuracy.png` | Box plot of accuracy during approach phase vs landing phase |

### Key Metrics to Report
- % of approach phase within ≤ 2.0 m threshold (target: > 90%)
- % of landing phase within ≤ 0.3 m threshold (target: > 80%)
- RTK_FIXED time during compound scenario vs baseline
- Mean uncertainty during each mission phase
- Recovery time after each CORRECTION_LOST event

---

## 7. RTKLIB Parameter Validation (Supporting Work)

**Purpose:** Validate that the noise model parameters used in Levels 1, 2, and 3
are consistent with real GNSS measurements. This is not the main contribution — it
is the evidence that the parameters are not arbitrary.

**Method:**
- Download BeiDou RINEX observation files from IGS MGEX network
  (two co-located stations, short baseline, covering same time window)
- Run RTKLIB `rnx2rtkp` with BDS constellation
- Extract GNSS_ONLY, RTK_FLOAT, and RTK_FIXED accuracy figures
- Compare against simulation noise model parameters

**Output:** One table in the final report: real GNSS accuracy vs simulation parameters.

**When:** After Level 3 simulation runs are complete. Not required for the
progress report.

---

## 8. Phase Plan

### Phase 1 — Progress Report (Due: 2026-06-04)
No new code. Report writing only.

| Task | Content |
|------|---------|
| Report Level 1 | Methodology, implementation, results, 5 graphs |
| Report Level 2 | Methodology, implementation, results, QGC cross-validation, 6 graphs |
| Define Level 3 | Research question, compound scenario design, methodology, thresholds |
| Integration status | Contract compliance confirmed, full integration pending team milestone |

**What is NOT in the progress report:** Level 3 simulation results (not yet run),
RTKLIB validation, full-system integration results.

---

### Phase 2 — Level 3 Implementation
Order matters. Each step depends on the previous.

| Step | Task | Deliverable |
|------|------|-------------|
| 2.1 | Design compound scenario YAML parameters | `config/level3_disaster_scenario.yaml` |
| 2.2 | Extend `rtcm_correction_simulator_node` to support time-varying phase profile | Updated node, still backwards-compatible with Level 2 |
| 2.3 | Implement dynamic uncertainty calculation in `rtk_positioning_node` | Dynamic `/rtk/accuracy` output |
| 2.4 | Add `/rtk/mission_viability` topic | New publisher in `rtk_positioning_node` |
| 2.5 | Update logger to capture new fields | Updated `logger_node.py`, new CSV columns |
| 2.6 | Create Level 3 launch file and runner | `launch/level3_resilient_rtk.launch.py`, `run_level3.sh` |
| 2.7 | Run compound disaster scenario (Run 2) | Level 3 CSV log |
| 2.8 | Run total failure scenario (Run 3) | Total failure CSV log |
| 2.9 | Write and run `analyse_level3.py` | 6 publication-ready figures |

**Constraint:** Level 1 and Level 2 must remain runnable after all changes.
All modifications are additive or parameterised — no existing behaviour is broken.

---

### Phase 3 — RTKLIB Validation (Supporting)

| Step | Task | Deliverable |
|------|------|-------------|
| 3.1 | Identify suitable IGS MGEX BeiDou station pair | Station names and download URLs |
| 3.2 | Download RINEX observation and navigation files | Local RINEX files |
| 3.3 | Install RTKLIB and configure `rnx2rtkp` | Working RTKLIB setup |
| 3.4 | Run post-processing, extract accuracy statistics | RTKLIB output log |
| 3.5 | Build validation table | Table for final report Chapter 5 |

---

### Phase 4 — Final Report (Chapter Updates)

| Chapter | Status | Level 3 additions |
|---------|--------|-------------------|
| Chapter 1 — Introduction | Existing | Minor update: mention disaster-zone resilience framing |
| Chapter 2 — Background | Existing | Add: GNSS degradation in disaster environments, compound scenario justification |
| Chapter 3 — System Design | Existing | Add: Level 3 architecture, mission viability signal, compound scenario design |
| Chapter 4 — Implementation | Existing L1/L2 | Add: Level 3 implementation details |
| Chapter 5 — Results | Existing L1/L2 | Add: Level 3 results, RTKLIB validation table, three-run comparison |
| Chapter 6 — Integration | Pending | Written after integration milestone |
| Chapter 7 — Conclusion | Pending | Written last |

---

### Phase 5 — Integration (Pending Team Milestone)

This phase cannot start until other modules are ready. It is listed here so
the dependency is explicit.

| Task | Requires |
|------|---------|
| Add `/rtk/mission_viability` to integration contract | Coordination with Student 4 (path_planning) |
| Full-system launch with compound disaster scenario | All 5 modules running |
| Measure landing accuracy under disaster conditions | target_detection_tracking running |
| Update Chapter 6 | Integration session complete |

---

## 9. Deliverables Summary

| Deliverable | Phase | Status |
|-------------|-------|--------|
| Level 1 complete (code + results + graphs) | — | Done ✓ |
| Level 2 complete (code + results + graphs) | — | Done ✓ |
| Progress report (L1, L2, L3 plan) | 1 | Done ✓ |
| `config/level3_disaster_scenario.yaml` | 2.1 | Done ✓ |
| `config/level3_total_failure.yaml` | 2.1 | Done ✓ |
| Extended `rtcm_correction_simulator_node` | 2.2 | Done ✓ |
| Dynamic uncertainty in `rtk_positioning_node` | 2.3 | Done ✓ |
| `/rtk/mission_viability` topic | 2.4 | Done ✓ |
| Updated `logger_node` | 2.5 | Done ✓ |
| Level 3 launch file + runner | 2.6 | Done ✓ |
| Level 3 Run 2 — compound disaster (drone flying, 878 s) | 2.7 | Done ✓ |
| Level 3 Run 3 — total failure (drone flying, 843 s) | 2.8 | Done ✓ |
| Level 3 analysis script + 6 figures | 2.9 | **In progress** |
| RTKLIB validation table | 3 | Pending |
| Final report chapters updated | 4 | Pending |
| Full integration run | 5 | Blocked — team dependency |

---

## 10. What Must Not Change

- Level 1 launch (`level1_rtk_sim.launch.py`) must remain runnable
- Level 2 launch (`level2_rtk_px4_sim.launch.py`) must remain runnable
- Topic names and message types in the integration contract must not change
  without coordinating with the team
- All existing CSV logs and graphs must be preserved
