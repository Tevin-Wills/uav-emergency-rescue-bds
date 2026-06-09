# Speaker Notes — Figure 5: Three-Run Comparison
**File:** `figures/l3_three_run_comparison.png`

## What this graph shows
The bracketing experiment: best case, disaster case, worst case, side by side.
- **Left:** box plots of RTK error for the three runs (**log y**).
- **Right:** key metrics bar chart (mean / median / P95 error, and % of readings within
  the 2.0 m and 0.3 m thresholds).

## How to read it
- Boxes = interquartile range; whiskers = **5th–95th percentile**; points beyond are
  individual samples.
- Three runs: **Baseline (Level 2, ideal)**, **Compound Disaster**, **Total Failure**
  (corrections cut entirely).

## Key numbers
| Run | Mean | P95 |
|---|---|---|
| Baseline (L2) | **0.048 m** | 0.083 m |
| Compound Disaster | **0.968 m** | 4.98 m |
| Total Failure | **4.776 m** | 8.34 m |

- Compound disaster sits **~20×** above baseline but **~5×** below total failure.

## What to say
"This brackets the problem. Baseline is our ceiling at 5 cm. Total failure — no
corrections at all — is the floor at nearly 5 m mean. The compound disaster lands in
between: degraded but still usable for approach. RTK buys us roughly a 5× improvement even
in the disaster case."

## Honest caveat
The right panel uses a twin axis (metres on the left, % on the right). A 100% bar is drawn
at the same height as ~9 m — read the labels, not the bar heights, across the divider.
