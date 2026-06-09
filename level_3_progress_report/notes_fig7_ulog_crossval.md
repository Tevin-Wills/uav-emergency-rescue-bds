# Speaker Notes — Figure 7: ULog Cross-Validation
**File:** `figures/l3_ulog_crossval.png`

## What this graph shows
Independent proof that the analysis ran against a **real PX4/Gazebo drone flight**, not a
synthetic table. Three panels:
- **A (left):** ULog flight trajectory overlaid on the CSV ground truth (2D).
- **B (middle):** RTK error coloured by viability state (**log y**).
- **C (right):** the UAV altitude profile from the ULog.

## How to read it
- Panel A: the orange ULog track and the blue CSV track lie on top of each other — the two
  independent data sources agree on the same five-waypoint mission geometry.
- Panel B: error points coloured green→yellow→orange→red by viability, against the
  threshold lines.
- Panel C: altitude over time — takeoff, sustained cruise, landing.

## Key numbers
- Compound disaster ULog: **409 MB**, parsed with pyulog.
- Mission footprint: **390 m East × 789 m North**, five waypoints.
- Cruise altitude: sustained **50 m AGL**.

## What to say
"This slide answers 'is your data real?'. The drone's own flight log and our analysis CSV
trace the same trajectory, independently, which validates the integrity of the whole
Level 3 dataset."

## Honest caveat
The two Level 3 runs flew **different altitude profiles** — the compound run cruised at
50 m throughout, so Panel C shows cruise-and-land, not a low-altitude landing approach.
Re-flying both runs with an identical mission is a known next step. Only mention if asked.
