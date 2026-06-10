"""
rtk_error_model.py — RTK error-budget model (baseline / quality / age driven).

Pure, unit-testable functions implementing the standard RTK horizontal-error
budget so the simulation degrades the way real RTK does, and so each term can be
calibrated against RTKLIB or a real receiver:

  sigma_RTK = sqrt( floor_status^2 + (baseline_km * ppm / 1000)^2 + (age * age_drift)^2 )

Terms (all map to measurable quantities):
  floor_status   per-fix-type floor (FIXED ~0.01-0.03 m, FLOAT ~0.25 m, GNSS ~1.5 m)
                 -> receiver datasheet / RTKLIB measured error at ~0 baseline
  ppm            parts-per-million baseline growth, "mm per km" (1 ppm ~ 1 mm/km)
                 -> RTKLIB error-vs-baseline slope; receiver spec "X mm + 1 ppm"
  age * age_drift correction-latency decay ("age of differential")
                 -> RTKLIB age-of-differential field

Fix state also degrades with baseline (and is recoverable):
  baseline > fixed_limit_km -> cannot hold FIXED (drop to FLOAT)
  baseline > max_km         -> single-base correction unusable (GNSS only)
These thresholds are calibratable from the RTKLIB %-fixed-vs-baseline curve.
"""

import math


def baseline_term_m(baseline_km, ppm):
    """Baseline-dependent error in metres. ppm is 'mm per km' (1 ppm = 1 mm/km)."""
    return baseline_km * ppm / 1000.0


def rtk_sigma_m(floor_std_m, baseline_km, ppm, age_sec=0.0, age_drift=0.0):
    """Combine the RTK error-budget terms into a single horizontal sigma (m)."""
    bt = baseline_term_m(baseline_km, ppm)
    at = age_sec * age_drift
    return math.sqrt(floor_std_m ** 2 + bt ** 2 + at ** 2)


def degrade_status_for_baseline(status, baseline_km, fixed_limit_km, max_km):
    """Apply realistic baseline limits to the fix state (recoverable as baseline shrinks)."""
    if baseline_km > max_km:
        return 'GNSS_ONLY'
    if baseline_km > fixed_limit_km and status == 'RTK_FIXED':
        return 'RTK_FLOAT'
    return status
