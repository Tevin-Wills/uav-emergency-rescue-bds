# Archived Level 3 logs — NOT used in analysis

These two CSVs are kept for traceability but were **not** used to generate the
Level 3 figures (`results/graphs/rtk_positioning/level3/`, generated 2026-06-04).

| File | Why archived |
|---|---|
| `rtk_level3_compound_disaster_20260603_163345(DONT USE).csv` | Drone was in **Hold** (hovering) — ground-truth X-span is only 0.1 m. Invalid; the run must fly waypoints. |
| `rtk_level3_compound_disaster_20260605_215957.csv` | Created **2026-06-05**, after the figures were already generated (2026-06-04). Short run (414 s / 3994 rows). Not part of the analysis. |

## The two valid runs (kept in the parent folder)
- `rtk_level3_compound_disaster_20260603_195803.csv` — 879 s, 390 m X-span
- `rtk_level3_total_failure_20260603_201957.csv` — 843 s, 390 m X-span

Note: `analyse_level3.py` selects the *latest* compound CSV by filename. Keeping
the Jun-5 file in the parent folder would have caused it to be picked by mistake;
moving it here restores correct selection of the `195803` run.
