# Level 2 Progress Report — PX4-Integrated RTK Positioning

**Project:** UAV Emergency Rescue BDS — RTK Positioning Module
**Author:** Tevin Wills (Student 1)
**Date:** 2026-06-18
**Scope:** Level 2 only (PX4/Gazebo integration and in-flight accuracy validation)

---

## 1. Summary

Level 2 takes the standalone RTK module proven in Level 1 and runs it against a **real
PX4/Gazebo flight**. The UAV pose is sourced from the Gazebo simulation through `ros_gz_bridge`,
and RTK status is driven by a simulated GPS_RTCM_DATA-style correction stream rather than a
hard-coded clock. The purpose at this level is to show two things: that the module **integrates
with the team's PX4 stack**, and that it **delivers centimetre-level position on a real flight** —
the accuracy a downstream module needs to geolocate a victim from the drone's own position.

**Headline result:** during the autonomous flight the RTK module held mean positioning error to
**0.047 m (4.7 cm)** against ground truth — a **98.0 % improvement** over raw GNSS (2.42 m) — and
remained in **RTK Fixed for 100 % of the flight**. The result is cross-validated against the raw
PX4 ULog, which independently reports a GPS accuracy estimate (EPH) of 0.90 m for the same flight.

> **Scope note on resilience.** A correction-loss (dropout) event is included, but in this run it
> occurs during the stationary initialization phase, not in flight. In-flight resilience to a
> *mid-mission* correction loss is tested at **Level 3** by design, so this report does not claim
> it.

---

## 2. What was done, and why

| What | Why |
|---|---|
| Replaced the Level 1 synthetic path with real UAV pose from PX4 SITL / Gazebo Harmonic (via `px4_pose_adapter_node`) | To validate the module against true vehicle flight dynamics, not a scripted path |
| Drove RTK status from a simulated correction stream (`rtcm_correction_simulator_node` → `SimulatedRtcm`) with quality, age, availability and loss | To model the GPS_RTCM_DATA correction transport realistically without falsely claiming real RTCM decoding |
| Flew an 8-waypoint autonomous QGC mission and logged it to CSV while PX4 recorded a ULog | To produce an independently verifiable flight record |
| Cross-validated the CSV against the PX4 ULog (trajectory, GPS EPH, altitude) | To prove the data is from a real PX4 flight, not a software-only simulation |
| Analysed the run as **two separate segments** — stationary initialization and autonomous flight | Because the logger ran ~7 min before take-off; blending the two would misreport ground/startup behaviour as flight performance |

---

## 3. Method (at a glance)

- **Stack:** ROS 2 Jazzy · PX4 SITL · Gazebo Harmonic · QGroundControl · `ros_gz_bridge` navsat sensor.
- **Correction model:** scripted quality timeline — 0–5 s unavailable (GNSS Only) → 5–15 s
  quality 0.5 (RTK Float) → 15–45 s quality 0.95 (RTK Fixed) → 45–50 s lost (Correction Lost) →
  50 s+ recovered (RTK Fixed). Noise per status: GNSS 1.50 m · Float 0.25 m · Fixed 0.03 m ·
  Lost 2.50 m. (Transition *timing* is scripted, not real ambiguity resolution — see
  `simulation_assumptions.md` §11.)
- **Run:** 1028 s CSV log (`rtk_level2_20260521_022231.csv`); take-off at t ≈ 497 s, landing at
  t ≈ 986 s; autonomous waypoint leg t ≈ 785–948 s. Paired ULog `qgc_mission_20260521.ulg` (166 s).
- **Segments analysed:**
  - **INITIALIZATION** — t < 50 s, stationary on the ground: convergence + correction-loss recovery.
  - **FLIGHT** — airborne window t ≈ 497–986 s (n ≈ 4 893): the in-flight accuracy result.
  - **MISSION** — horizontal waypoint leg t ≈ 785–948 s, which aligns with the ULog record.

---

## 4. What was successfully confirmed

1. **PX4 integration works.** The RTK module consumed real PX4/Gazebo pose through the adapter and
   produced raw GNSS, RTK position, status and accuracy outputs throughout a real autonomous mission.
   *(Fig 6)*
2. **Centimetre-level accuracy in flight.** Mean in-flight RTK error **0.047 m (4.7 cm)**, median
   0.046 m, P95 0.082 m — **98.0 %** better than raw GNSS (2.42 m), with the module in **RTK Fixed
   100 %** of the flight. *(Figs 1, 3, 5)*
3. **The correction state machine behaves correctly.** At initialization it converges
   GNSS → Float → Fixed and recovers from a simulated correction loss back to Fixed. *(Fig 2)*
4. **The data is real and self-consistent.** The PX4 ULog and the analysis CSV trace the same
   8-waypoint trajectory (≈ 209 × 215 m, 169 m max range) and a climb to ~50 m AGL; PX4's own GPS
   EPH (0.90 m) is an independent accuracy estimate consistent with the simulated GNSS noise level.
   *(Fig 6)*

---

## 5. Honest limitations

1. **Convergence and the correction-loss event are scripted and stationary.** They occur in the
   first 50 s, on the ground, ~7 min before take-off, on a fixed timeline — so they demonstrate the
   *status logic*, not real RTK convergence and not in-flight resilience. They are reported as an
   initialization sequence, separately from the flight result.
2. **The whole-log mean (0.080 m) is not the result.** It is inflated by the initialization
   transients; the reported figure is the in-flight value (0.047 m). The whole-log number is shown
   only for transparency.
3. **No real RTCM / carrier-phase processing.** Accuracy comes from a per-status Gaussian noise
   model; no real ambiguity resolution, RF, or BeiDou signal simulation occurs. Grounding the noise
   model in real GNSS behaviour is the goal of Phase 3 (RTKLIB).
4. **Fictional base-station coordinate.** The ENU base is a Beijing reference while the Gazebo
   flight is near Zürich; this is harmless for the metre-based error metrics (the transforms cancel),
   but the absolute lat/lon are not the physical flight location. *(see `simulation_assumptions.md` §11.3)*

---

## 6. Next task

1. **Level 3** — test in-flight resilience under sustained, compound GNSS degradation (mid-mission
   correction dropouts), and add the dynamic-uncertainty and mission-viability outputs that
   `path_planning` consumes.
2. **Phase 3 — RTKLIB validation:** post-process real BeiDou RINEX through RTKLIB and compare
   measured SPP / Float / Fixed accuracy against the simulated noise model.
3. **Integration:** expose the RTK position + status to the other four modules in the combined
   bring-up.

---

## 7. Figure index

| Fig | File | Purpose |
|---|---|---|
| 1 | `results/graphs/rtk_positioning/level2/l2_error_over_time.png` | Full session, initialization vs flight demarcated (log scale) |
| 2 | `.../l2_rtk_convergence.png` | Initialization sequence: convergence + correction-loss recovery (scripted, stationary) |
| 3 | `.../l2_error_distribution.png` | In-flight error distribution, raw GNSS vs RTK (RTK Fixed) |
| 4 | `.../l2_trajectory.png` | 2D flight trajectory, raw vs RTK against ground truth |
| 5 | `.../l2_accuracy_summary.png` | Error by segment, in-flight fix status, in-flight improvement |
| 6 | `.../l2_qgc_crossval.png` | ULog cross-validation: trajectory, 3-way accuracy (EPH), altitude |

*Figures regenerate with* `python3 results/graphs/rtk_positioning/analyse_level2.py` *(requires
numpy < 2 with matplotlib/scipy/pyulog; see the analysis-environment note in the graphs README).*
