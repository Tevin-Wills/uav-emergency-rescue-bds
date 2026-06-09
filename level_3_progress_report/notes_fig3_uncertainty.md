# Speaker Notes — Figure 3: Dynamic Uncertainty vs Fixed (Level 2)
**File:** `figures/l3_uncertainty_over_time.png`

## What this graph shows
Whether the system's *self-reported* uncertainty is honest. Two stacked panels, both on a
**log y-axis**:
- **Top:** Level 3 dynamic `rtk_std` (blue) vs the flat Level 2 fixed value (~0.03 m).
- **Bottom:** actual RTK error vs the reported uncertainty — they should track each other.

## How to read it
- Top panel: the Level 3 uncertainty ramps up and down with the degradation (sawtooth),
  while Level 2's single fixed value sits flat near the floor — that is the
  "**overconfident**" baseline behaviour.
- Bottom panel: where the reported-uncertainty line rises and falls with the actual error,
  the system "knows" how good its fix is.

## Key numbers
- Level 2 fixed uncertainty: **≈ 0.030 m** (flat, regardless of conditions).
- Level 3 dynamic uncertainty spans **~0.03 m → ~4.6 m**, tracking the phase profile.
- Thresholds overlaid at **0.30 m** and **2.0 m**.

## What to say
"A fixed-accuracy model is dangerous in a disaster — it claims 3 cm even when it is 4 m
off. Level 3 reports a *dynamic* uncertainty that rises honestly during degradation, which
is what a path planner needs to make a safe go / no-go landing decision."

## Honest caveat
The log scale was chosen deliberately: on a linear axis the 0.03 m baseline and the whole
sub-0.3 m landing band are invisible against the axis. Log makes the decision-relevant
detail legible without hiding the growth.
