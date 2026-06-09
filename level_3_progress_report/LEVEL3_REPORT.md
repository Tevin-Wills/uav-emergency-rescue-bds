# Level 3 Progress Report — Resilient RTK for Disaster Rescue

**Project:** UAV Emergency Rescue BDS — RTK Positioning Module
**Author:** Tevin Wills (Student 1)
**Date:** 2026-06-04
**Scope:** Level 3 only (resilient RTK under compound disaster conditions)

---

## 1. Summary

Level 3 tests whether the RTK positioning system can support an autonomous rescue mission
in a disaster zone where GNSS is progressively and simultaneously degraded. We designed a
single **compound disaster scenario** — not four isolated failures — flew it on a real
PX4/Gazebo drone mission, and analysed the result against engineering thresholds for
approach navigation and precision landing.

**Headline result:** RTK held mean positioning error to **0.968 m** under sustained
multi-factor degradation — about **5× better** than the total-failure case (4.776 m), and
about **20×** the ideal baseline (0.048 m). The system **passed** the approach threshold
(**92.4%** of samples within 2.0 m, target ≥ 90%) but **fell short** of the
precision-landing threshold (**31.5%** within 0.3 m, target ≥ 80%).

---

## 2. What was done, and why

| What | Why |
|---|---|
| Designed a 5-phase compound degradation profile (Departure → Approach → Search Zone → Landing → Exit) | Real disaster zones degrade on several axes at once; isolated single-fault tests do not represent that |
| Modelled three co-occurring degradations: GNSS noise (1.5 → 2.75 m), correction quality (0.95 → 0.60), and periodic correction dropouts (up to 37.5 s every 90 s) | To stress the system the way a collapsing-structure search would |
| Added a **dynamic uncertainty** output and a **mission viability** state signal (LANDING / APPROACH / DEGRADED / INSUFFICIENT) | A path planner needs an honest, time-varying confidence signal, not a fixed accuracy claim |
| Flew the scenario as a real 5-waypoint QGC mission (390 m × 789 m) on PX4/Gazebo | To validate against true vehicle flight, not a stationary hover |
| Ran a **total-failure** control (corrections cut entirely) and reused the **Level 2** ideal run as a baseline | To bracket the disaster result between best and worst case |
| Produced 7 analysis figures and cross-validated the data against the raw PX4 ULog | To make the result publication-/presentation-ready and provably real |

---

## 3. Method (scenario at a glance)

| Phase | Time (s) | GNSS noise σ | Correction quality | Dropouts |
|---|---|---|---|---|
| Departure | 0–120 | 1.5 m | 0.95 | none |
| Approach | 120–240 | 1.5 → 2.5 m | 0.95 → 0.60 | 5 s / 60 s |
| Search Zone | 240–600 | 2.75 m | 0.60 | 37.5 s / 90 s |
| Landing | 600–660 | 2.5 m | 0.60 | none |
| Exit | 660–780 | 2.5 → 1.5 m | 0.65 → 0.90 | none |

**Viability states:** LANDING_VIABLE ≤ 0.3 m · APPROACH_VIABLE ≤ 2.0 m ·
DEGRADED ≤ 4.0 m · INSUFFICIENT > 4.0 m.

---

## 4. What was successfully confirmed

1. **RTK degrades gracefully, not catastrophically.** Mean error **0.968 m** in the
   compound disaster vs **4.776 m** with no corrections — RTK keeps the mission ~5×
   more accurate even under disaster conditions. *(Fig 2, Fig 5)*
2. **Approach navigation is viable.** **92.4%** of approach-phase samples within 2.0 m,
   beating the ≥ 90% target. *(Fig 6)*
3. **The uncertainty signal is honest.** Reported `rtk_std` rises and falls *with* actual
   error (0.03 → 4.6 m), unlike the flat, overconfident Level 2 fixed value. *(Fig 3)*
4. **The viability state machine behaves correctly** — it downgrades during dropouts and
   recovers to LANDING_VIABLE as corrections return. *(Fig 4)*
5. **The data is real and self-consistent.** The PX4 ULog (409 MB) and the analysis CSV
   trace the same 5-waypoint trajectory; both confirm the 390 × 789 m mission. *(Fig 7)*

---

## 5. Honest limitations

1. **Precision landing not met:** only **31.5%** of landing-phase samples within 0.3 m
   (target 80%). This reflects RTK Float, not Fixed, lock during degradation — the key
   open engineering gap.
2. **Run altitude mismatch:** the compound run cruised at 50 m throughout, while the
   total-failure run descended to ~20 m. The two runs are not strictly identical flights,
   so the altitude profile (Fig 7C) shows cruise-and-land rather than a full low-altitude
   approach. Per-run error statistics are unaffected.
3. **Phase windows are time-reconstructed** and lead the actual degradation onset by a few
   tens of seconds; the Exit phase slightly overruns the designed 780 s.
4. **Baseline is a different mission** (Level 2, shorter) — used as an accuracy-only
   reference, noted as such.

---

## 6. Next task

1. **Close the landing gap** — implement an RTK re-initialisation / Fixed-lock recovery
   protocol on entering the landing phase, or extend the landing window for re-convergence.
2. **Re-fly both Level 3 runs with one identical mission** (ideally including the WP4 20 m
   descent) so the runs are strictly comparable.
3. **Phase 3 — RTKLIB validation:** post-process real BeiDou RINEX data through RTKLIB and
   compare measured SPP / Float / Fixed accuracy against the simulation parameters, to
   ground the noise model in real GNSS behaviour. *(Plan: `PHASE3_RTKLIB_PLAN.md`.)*
4. **Push Level 3 work to the team GitHub** once the above are scheduled.

---

## 7. Figure index

| Fig | File | Purpose |
|---|---|---|
| 1 | `figures/l3_compound_scenario_profile.png` | The imposed 5-phase degradation model |
| 2 | `figures/l3_error_over_time.png` | RTK vs raw error over the mission (log) |
| 3 | `figures/l3_uncertainty_over_time.png` | Dynamic vs fixed uncertainty (log) |
| 4 | `figures/l3_viability_timeline.png` | Mission viability state + error (log) |
| 5 | `figures/l3_three_run_comparison.png` | Baseline vs compound vs total failure |
| 6 | `figures/l3_mission_phase_accuracy.png` | Accuracy & threshold pass/fail per phase |
| 7 | `figures/l3_ulog_crossval.png` | ULog cross-validation (trajectory/error/altitude) |
