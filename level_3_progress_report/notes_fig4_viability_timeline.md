# Speaker Notes — Figure 4: Mission Viability Timeline
**File:** `figures/l3_viability_timeline.png`

## What this graph shows
The decision signal the rest of the autonomy stack consumes. Two stacked panels:
- **Top:** a coloured state strip — the viability state at every instant.
- **Bottom:** the underlying RTK error (log y) with the threshold lines that define the states.

## How to read it
- State strip colours: **green = LANDING_VIABLE (≤0.3 m)**, **yellow = APPROACH_VIABLE
  (≤2.0 m)**, **orange = DEGRADED (≤4.0 m)**, **red = INSUFFICIENT (>4.0 m)**.
- Read the strip left-to-right as the mission's "traffic light" — the bottom panel shows
  *why* each colour was assigned.

## Key numbers
- Thresholds: **0.30 m / 2.00 m / 4.00 m**.
- The mission spends most of its time **APPROACH_VIABLE**, dips to DEGRADED/INSUFFICIENT
  only in Search-Zone dropouts, and returns to **LANDING_VIABLE** as corrections recover.

## What to say
"This is the output a path planner actually uses. Instead of a raw error number, it gets a
discrete state: can I land here, can I only approach, or should I hold? The system
correctly downgrades itself during dropouts and upgrades again on recovery."

## Honest caveat
The state is derived from reported uncertainty, so it is only as good as that signal —
which is exactly why Figure 3 (uncertainty honesty) matters.
