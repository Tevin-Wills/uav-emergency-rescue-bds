# Speaker Notes — Figure 6: Mission Phase Accuracy
**File:** `figures/l3_mission_phase_accuracy.png`

## What this graph shows
The compound disaster broken down **by mission phase**, so we can see *where* in the
mission the system passes or fails its engineering targets.
- **Left:** box plots of error per phase (**log y**).
- **Right:** % of readings within the 2.0 m (approach) and 0.3 m (landing) thresholds.

## How to read it
- Five phases on the x-axis. Compare each phase's box against the **0.3 m** and **2.0 m**
  dashed lines.
- The right panel turns that into pass/fail percentages against the **90%** approach and
  **80%** landing targets.

## Key numbers (% within 2.0 m / % within 0.3 m)
- Departure **100% / 100%**, Approach **92% / 32%**, Search Zone **63% / 17%**,
  Landing **100% / 32%**, Exit **100% / 88%**.
- Overall: Approach **92.4% PASS**, Landing **31.5% FAIL** (target 80%).

## What to say
"Departure and Exit are essentially baseline-quality. The Search Zone is where we hurt —
that is by design, it is peak degradation. The honest finding is the landing threshold:
we hold approach-grade accuracy but do not consistently reach the 0.3 m precision-landing
bar during the disaster."

## Honest caveat
The landing shortfall is a real, reported limitation — it reflects RTK Float (not Fixed)
conditions during degradation. This is the headline item in the "next steps".
