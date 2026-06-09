# Speaker Notes — Figure 2: RTK Positioning Error Over Mission Time
**File:** `figures/l3_error_over_time.png`

## What this graph shows
The headline *result*: how positioning error behaves through the whole compound mission,
comparing **raw GNSS error (amber)** against **RTK-corrected error (blue)**, on a
**log y-axis** so sub-decimetre and multi-metre values are both readable.

## How to read it
- Log scale: each gridline is a 10× change. The blue (RTK) line sits well below the amber
  (raw) line for almost the entire mission — that gap is the value RTK adds.
- Background shading = mission phase. Vertical spikes in the Search Zone line up with the
  **Correction Lost** dropout windows from Figure 1.
- Two threshold lines: **2.0 m** (approach) and **0.3 m** (landing).

## Key numbers
- Raw GNSS mean **≈ 3.6 m**; RTK-corrected mean **0.968 m** — RTK holds error ~4× lower.
- RTK max excursion **9.79 m**, only during dropout windows.
- Approach ≤ 2.0 m: **92.4%** of samples; Landing ≤ 0.3 m: **31.5%**.

## What to say
"Even under sustained degradation, RTK keeps error roughly four times below raw GNSS.
The spikes are honest — they are exactly the correction-loss windows, and the system
recovers each time corrections return."

## Honest caveat
The blue line briefly meets the amber line during full dropouts — when there is no
correction, RTK has nothing to correct with. That is expected, not a bug.
