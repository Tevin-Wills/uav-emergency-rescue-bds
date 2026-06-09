"""
Level 3 RTK Positioning — Analysis and Visualisation
=====================================================
Seven publication-quality figures from three simulation runs and ULog cross-validation.

  Run 1 — Baseline        : Level 2 CSV  (ideal PX4 mission, full corrections)
  Run 2 — Compound Disaster: Level 3 CSV  (5-phase time-varying degradation)
  Run 3 — Total Failure   : Level 3 CSV  (GNSS only, zero corrections)

Figures produced (saved to level3/):
  l3_compound_scenario_profile.png  — GNSS noise and correction quality over mission time
  l3_error_over_time.png            — RTK error shaded by mission phase
  l3_uncertainty_over_time.png      — Dynamic uncertainty vs Level 2 fixed accuracy
  l3_viability_timeline.png         — Mission viability state and RTK error over time
  l3_three_run_comparison.png       — Three-run RTK error box plots and key metrics
  l3_mission_phase_accuracy.png     — Phase-level accuracy vs engineering thresholds
  l3_ulog_crossval.png              — ULog ground truth trajectory cross-validation

Usage:
    python3 analyse_level3.py
"""

import os
import csv
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec
from scipy.stats import gaussian_kde
from pyulog import ULog

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
L3_LOG_DIR = os.path.join(SCRIPT_DIR, '..', '..', 'logs', 'rtk_positioning', 'level3')
L2_LOG_DIR = os.path.join(SCRIPT_DIR, '..', '..', 'logs', 'rtk_positioning', 'level2')
ULOG_PATH  = os.path.join(SCRIPT_DIR, '..', '..', 'logs',
                           'rtk_level3_compound_disaster_20260603.ulg')
OUT_DIR    = os.path.join(SCRIPT_DIR, 'level3')
os.makedirs(OUT_DIR, exist_ok=True)

# ── CSV selection ─────────────────────────────────────────────────────────────
cd_csvs = sorted(f for f in os.listdir(L3_LOG_DIR)
                 if f.startswith('rtk_level3_compound_disaster') and f.endswith('.csv')
                 and '163345' not in f)
if not cd_csvs:
    raise FileNotFoundError(f'No valid compound disaster CSV in {L3_LOG_DIR}')
CD_CSV = os.path.join(L3_LOG_DIR, cd_csvs[-1])

tf_csvs = sorted(f for f in os.listdir(L3_LOG_DIR)
                 if f.startswith('rtk_level3_total_failure') and f.endswith('.csv'))
if not tf_csvs:
    raise FileNotFoundError(f'No total failure CSV in {L3_LOG_DIR}')
TF_CSV = os.path.join(L3_LOG_DIR, tf_csvs[-1])

l2_csvs = sorted(f for f in os.listdir(L2_LOG_DIR)
                 if f.startswith('rtk_level2') and f.endswith('.csv'))
if not l2_csvs:
    raise FileNotFoundError(f'No Level 2 CSV in {L2_LOG_DIR}')
L2_CSV = os.path.join(L2_LOG_DIR, l2_csvs[-1])

print(f'[analyse_level3] Compound disaster : {os.path.basename(CD_CSV)}')
print(f'[analyse_level3] Total failure     : {os.path.basename(TF_CSV)}')
print(f'[analyse_level3] Level 2 baseline  : {os.path.basename(L2_CSV)}')
print(f'[analyse_level3] ULog              : {os.path.basename(ULOG_PATH)}')

# ── Data loading helpers ──────────────────────────────────────────────────────
def load_rows(path):
    with open(path) as f:
        return [r for r in csv.DictReader(f) if r['ros_time_sec'].strip()]

def col_f(rows, key, fallback=np.nan):
    out = []
    for r in rows:
        v = r.get(key, '').strip()
        try:
            out.append(float(v))
        except (ValueError, TypeError):
            out.append(fallback)
    return np.array(out)

def col_s(rows, key):
    return np.array([r.get(key, '').strip() for r in rows])

# ── Load CSVs ─────────────────────────────────────────────────────────────────
cd_rows = load_rows(CD_CSV)
tf_rows = load_rows(TF_CSV)
l2_rows = load_rows(L2_CSV)

# ── Compound disaster arrays ──────────────────────────────────────────────────
cd_t0      = float(cd_rows[0]['ros_time_sec'])
cd_elapsed = np.array([float(r['ros_time_sec']) - cd_t0 for r in cd_rows])
cd_gt_x    = col_f(cd_rows, 'ground_truth_x', 0.0)   # East (m)
cd_gt_y    = col_f(cd_rows, 'ground_truth_y', 0.0)   # North (m)
cd_raw_err = col_f(cd_rows, 'raw_gnss_error_m', 0.0)
cd_rtk_err = col_f(cd_rows, 'rtk_error_m', 0.0)
cd_rtk_std = col_f(cd_rows, 'rtk_std_m', np.nan)
cd_status  = col_s(cd_rows, 'rtk_status_name')
cd_viab    = col_s(cd_rows, 'mission_viability')
cd_noise   = col_f(cd_rows, 'gnss_noise_std_m', np.nan)
cd_quality = col_f(cd_rows, 'correction_quality', np.nan)
cd_rtk_lat = col_f(cd_rows, 'rtk_lat', np.nan)
cd_rtk_lon = col_f(cd_rows, 'rtk_lon', np.nan)

# Mission elapsed: t=0 when drone first exceeds 5 m horizontal displacement
cd_horiz  = np.sqrt(cd_gt_x**2 + cd_gt_y**2)
fly_start = next((i for i, d in enumerate(cd_horiz) if d > 5.0), 0)
cd_mt0    = cd_elapsed[fly_start]
cd_me     = cd_elapsed - cd_mt0

# Phase assignment
def assign_phases(me):
    phases = []
    for t in me:
        if   t < 0:   phases.append('Pre-flight')
        elif t < 120: phases.append('Departure')
        elif t < 240: phases.append('Approach')
        elif t < 600: phases.append('Search Zone')
        elif t < 660: phases.append('Landing')
        else:         phases.append('Exit')
    return np.array(phases)

PHASE_NAMES = ['Departure', 'Approach', 'Search Zone', 'Landing', 'Exit']

cd_phase  = assign_phases(cd_me)
cd_flying = cd_phase != 'Pre-flight'

# ── Total failure arrays ──────────────────────────────────────────────────────
tf_t0      = float(tf_rows[0]['ros_time_sec'])
tf_elapsed = np.array([float(r['ros_time_sec']) - tf_t0 for r in tf_rows])
tf_gt_x    = col_f(tf_rows, 'ground_truth_x', 0.0)
tf_gt_y    = col_f(tf_rows, 'ground_truth_y', 0.0)
tf_rtk_err = col_f(tf_rows, 'rtk_error_m', 0.0)
tf_raw_err = col_f(tf_rows, 'raw_gnss_error_m', 0.0)
tf_flying  = np.sqrt(tf_gt_x**2 + tf_gt_y**2) > 5.0

# ── Level 2 baseline arrays ───────────────────────────────────────────────────
l2_t0      = float(l2_rows[0]['ros_time_sec'])
l2_elapsed = np.array([float(r['ros_time_sec']) - l2_t0 for r in l2_rows])
l2_gt_x    = col_f(l2_rows, 'ground_truth_x', 0.0)
l2_gt_y    = col_f(l2_rows, 'ground_truth_y', 0.0)
l2_rtk_err = col_f(l2_rows, 'rtk_error_m', 0.0)
l2_raw_err = col_f(l2_rows, 'raw_gnss_error_m', 0.0)
l2_rtk_std = col_f(l2_rows, 'rtk_std_m', np.nan)
l2_status  = col_s(l2_rows, 'rtk_status_name')
l2_flying  = np.sqrt(l2_gt_x**2 + l2_gt_y**2) > 2.0

# ── Key statistics ────────────────────────────────────────────────────────────
cd_err_fly = cd_rtk_err[cd_flying]
tf_err_fly = tf_rtk_err[tf_flying]
l2_err_fly = l2_rtk_err[l2_flying]

cd_raw_fly = cd_raw_err[cd_flying]
l2_raw_fly = l2_raw_err[l2_flying]

cd_std_fly = cd_rtk_std[cd_flying & ~np.isnan(cd_rtk_std)]
l2_std_fly = l2_rtk_std[l2_flying & ~np.isnan(l2_rtk_std)]

m_dep  = cd_phase == 'Departure'
m_app  = cd_phase == 'Approach'
m_srch = cd_phase == 'Search Zone'
m_land = cd_phase == 'Landing'
m_exit = cd_phase == 'Exit'

app_data  = cd_rtk_err[m_app]
land_data = cd_rtk_err[m_land]
pct_app   = 100.0 * np.mean(app_data  <= 2.0) if len(app_data)  > 0 else 0.0
pct_land  = 100.0 * np.mean(land_data <= 0.3) if len(land_data) > 0 else 0.0
print(f'Approach accuracy (≤2.0 m): {pct_app:.1f}%  (target >90%)')
print(f'Landing accuracy  (≤0.3 m): {pct_land:.1f}%  (target >80%)')

# ENU conversion (same base station as Levels 1 and 2)
BASE_LAT      = 39.981000
BASE_LON      = 116.344000
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(BASE_LAT))
M_PER_DEG_LAT = 111320.0
cd_rtk_east  = (cd_rtk_lon - BASE_LON) * M_PER_DEG_LON
cd_rtk_north = (cd_rtk_lat - BASE_LAT) * M_PER_DEG_LAT

# ── Load ULog ─────────────────────────────────────────────────────────────────
print('[analyse_level3] Loading ULog ...')
ulog   = ULog(ULOG_PATH)
ul_lp  = next(d for d in ulog.data_list if d.name == 'vehicle_local_position_groundtruth')
ul_gp  = next(d for d in ulog.data_list if d.name == 'vehicle_global_position_groundtruth')
ul_mr  = next(d for d in ulog.data_list if d.name == 'mission_result')
ul_nav = next(d for d in ulog.data_list if d.name == 'navigator_mission_item')

ul_t0_us  = ul_lp.data['timestamp'][0]
ul_t_sec  = (ul_lp.data['timestamp'] - ul_t0_us) / 1e6
ul_north  = ul_lp.data['x']          # NED x = North
ul_east   = ul_lp.data['y']          # NED y = East
ul_alt    = -ul_lp.data['z']         # NED z down → alt positive up

# Mission start = first seq_reached >= 0 in mission_result
ul_mr_t   = (ul_mr.data['timestamp'] - ul_t0_us) / 1e6
ul_mr_seq = ul_mr.data['seq_reached']
mis_idx   = np.where(ul_mr_seq >= 0)[0]
ul_mis_t0 = float(ul_mr_t[mis_idx[0]]) if len(mis_idx) > 0 else 0.0

# Clip to mission period with 30 s lead-in
ul_mask    = ul_t_sec >= max(0, ul_mis_t0 - 30.0)
ul_me      = ul_t_sec[ul_mask] - ul_mis_t0   # mission elapsed
ul_east_m  = ul_east[ul_mask]
ul_north_m = ul_north[ul_mask]
ul_alt_m   = ul_alt[ul_mask]

# Waypoints from navigator_mission_item
nav_lat_raw = ul_nav.data['latitude']
nav_lon_raw = ul_nav.data['longitude']
if np.nanmax(np.abs(nav_lat_raw)) > 3.14:
    nav_lat_deg, nav_lon_deg = nav_lat_raw, nav_lon_raw
else:
    nav_lat_deg, nav_lon_deg = np.degrees(nav_lat_raw), np.degrees(nav_lon_raw)

UL_REF_LAT = float(ul_gp.data['lat'][0])
UL_REF_LON = float(ul_gp.data['lon'][0])
UL_M_LON   = 111320.0 * math.cos(math.radians(UL_REF_LAT))
wp_east_all  = (nav_lon_deg - UL_REF_LON) * UL_M_LON
wp_north_all = (nav_lat_deg - UL_REF_LAT) * 111320.0

# Deduplicate: keep waypoints 50 m–3 km from origin, >10 m from any already kept.
# The 3 km upper bound rejects uninitialised navigator_mission_item entries
# (lat=0/lon=0) which convert to offsets of thousands of km and wreck the plot.
mission_wps = []
for e, n in zip(wp_east_all, wp_north_all):
    if not (np.isfinite(e) and np.isfinite(n)):
        continue
    dist_origin = math.sqrt(e**2 + n**2)
    if dist_origin < 50 or dist_origin > 3000:
        continue
    if not any(math.sqrt((e - pe)**2 + (n - pn)**2) < 10 for pe, pn in mission_wps):
        mission_wps.append((e, n))

# ── Colour scheme ─────────────────────────────────────────────────────────────
PHASE_COLORS = {
    'Departure':   '#3498DB',
    'Approach':    '#F39C12',
    'Search Zone': '#E74C3C',
    'Landing':     '#9B59B6',
    'Exit':        '#27AE60',
    'Pre-flight':  '#BDC3C7',
}
VIAB_COLORS = {
    'LANDING_VIABLE':  '#27AE60',
    'APPROACH_VIABLE': '#F1C40F',
    'DEGRADED':        '#E67E22',
    'INSUFFICIENT':    '#C0392B',
}
VIAB_LABELS = {
    'LANDING_VIABLE':  'Landing Viable  (≤0.30 m)',
    'APPROACH_VIABLE': 'Approach Viable (≤2.00 m)',
    'DEGRADED':        'Degraded        (≤4.00 m)',
    'INSUFFICIENT':    'Insufficient    (>4.00 m)',
}
STATUS_COLORS = {
    'GNSS_ONLY':       '#E67E22',
    'RTK_FLOAT':       '#F1C40F',
    'RTK_FIXED':       '#27AE60',
    'CORRECTION_LOST': '#8E44AD',
}
# Unified, colourblind-safe scheme rolled across all figures:
#   blue = compound disaster / RTK-corrected result (the study subject)
#   amber = raw / uncorrected GNSS error
#   slate gray = Level 2 baseline (neutral ideal reference)
#   dark red = total failure (danger)
C_BASE = '#566573'   # slate gray — Level 2 baseline / ideal reference
C_CD   = '#1A5276'   # deep blue  — compound disaster / RTK-corrected error
C_TF   = '#C0392B'   # dark red   — total failure
C_RAW  = '#B9770E'   # amber      — raw / uncorrected GNSS error

# Engineering-threshold line colours — unified to the viability bands they define,
# so a given threshold reads the same colour in every figure.
THR_LAND = VIAB_COLORS['LANDING_VIABLE']    # 0.3 m landing threshold  — green
THR_APPR = VIAB_COLORS['APPROACH_VIABLE']   # 2.0 m approach threshold — yellow
THR_DEGR = VIAB_COLORS['DEGRADED']          # 4.0 m degraded ceiling   — orange

plt.rcParams.update({
    'font.family':        'DejaVu Sans',
    'font.size':          11,
    'axes.titlesize':     12,
    'axes.titleweight':   'bold',
    'axes.labelsize':     11,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'xtick.labelsize':    10,
    'ytick.labelsize':    10,
    'legend.fontsize':    9.5,
    'legend.framealpha':  0.93,
    'legend.edgecolor':   '#CCCCCC',
    'figure.dpi':         150,
    'savefig.dpi':        300,
    'savefig.bbox':       'tight',
    'savefig.pad_inches': 0.18,
})

# ── Helpers ───────────────────────────────────────────────────────────────────
def shade_phases(ax, me, phases, alpha=0.10):
    i = 0
    while i < len(phases):
        p = phases[i]; j = i
        while j < len(phases) and phases[j] == p:
            j += 1
        ax.axvspan(me[i], me[min(j, len(me) - 1)],
                   color=PHASE_COLORS.get(p, '#BDC3C7'), alpha=alpha, linewidth=0)
        i = j

def phase_boundaries(me, phases, skip=('Pre-flight',)):
    """Returns list of (t_start, t_mid, t_end, phase_name) for each phase band."""
    result = []
    i = 0
    while i < len(phases):
        p = phases[i]; j = i
        while j < len(phases) and phases[j] == p:
            j += 1
        if p not in skip:
            t_s = me[i]
            t_e = me[min(j - 1, len(me) - 1)]
            result.append((t_s, (t_s + t_e) / 2, t_e, p))
        i = j
    return result

def label_phases_top(ax, me, phases, y_frac=0.97):
    ylo, yhi = ax.get_ylim()
    y_label  = ylo + y_frac * (yhi - ylo)
    for t_s, t_mid, t_e, p in phase_boundaries(me, phases):
        if len(seen := set()) == 0 or True:   # always draw, uniqueness handled below
            pass
    seen = set()
    for t_s, t_mid, t_e, p in phase_boundaries(me, phases):
        if p not in seen:
            ax.text(t_mid, y_label, p, ha='center', va='top',
                    fontsize=7.5, color='#333333', style='italic',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                              alpha=0.72, edgecolor='none'))
            seen.add(p)

def add_phase_vlines(ax, me, phases):
    prev = None
    for i, p in enumerate(phases):
        if p != prev and prev is not None and prev != 'Pre-flight' and p != 'Pre-flight':
            ax.axvline(me[i], color='#95A5A6', ls='--', lw=0.8, alpha=0.6)
        prev = p

def phase_patch_handles():
    return [mpatches.Patch(facecolor=PHASE_COLORS[p], alpha=0.60,
                           edgecolor='none', label=p)
            for p in PHASE_NAMES]

def smooth(arr, w=30):
    return np.convolve(arr, np.ones(w) / w, mode='same')

# ─────────────────────────────────────────────────────────────────────────────
# Figure 1 — Compound Scenario Profile
# ─────────────────────────────────────────────────────────────────────────────
print('[1/7] Generating: l3_compound_scenario_profile.png')

me_fly    = cd_me[cd_flying]
noise_fly = cd_noise[cd_flying]
qual_fly  = cd_quality[cd_flying]
phase_fly = cd_phase[cd_flying]
stat_fly1 = cd_status[cd_flying]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7),
                                gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.10},
                                sharex=True)
fig.subplots_adjust(left=0.08, right=0.97, top=0.88, bottom=0.10)
fig.suptitle(
    'Compound Disaster Scenario — Input Conditions Over Mission Time\n'
    'Level 3 Resilient RTK  |  5-Phase Progressive Degradation Profile',
    fontsize=12, fontweight='bold', y=0.97)

# ── Panel 1: GNSS noise ──
shade_phases(ax1, me_fly, phase_fly, alpha=0.09)
ax1.plot(me_fly, noise_fly, color='#E74C3C', lw=2.0, alpha=0.92,
         label='GNSS Noise Std (m)')
ax1.axhline(1.50, color='#27AE60', ls=':', lw=1.2, alpha=0.7,
            label='Baseline (1.50 m — open sky)')
ax1.axhline(2.75, color='#C0392B', ls=':', lw=1.2, alpha=0.7,
            label='Peak search zone (2.75 m — over collapse)')
ax1.set_ylabel('GNSS Noise Std (m)')
ax1.set_ylim(1.0, 3.2)
ax1.grid(True, ls='--', lw=0.4, alpha=0.45)
# Centred legend: sits in the empty band below the 2.75 m plateau and above the
# 1.50 m baseline, clear of both the data line and the top phase labels.
ax1.legend(loc='center', fontsize=9.0)
add_phase_vlines(ax1, me_fly, phase_fly)
label_phases_top(ax1, me_fly, phase_fly, y_frac=0.96)

# ── Panel 2: Correction quality ──
shade_phases(ax2, me_fly, phase_fly, alpha=0.09)

# Correction gaps are recorded via rtk_status == CORRECTION_LOST (the quality
# column is NOT set to NaN during a dropout), so the gap mask must key off status.
gap_mask  = stat_fly1 == 'CORRECTION_LOST'
qual_plot = np.where(gap_mask, np.nan, qual_fly)   # break the line during gaps

ax2.plot(me_fly, qual_plot, color='#2471A3', lw=2.0, alpha=0.92,
         label='Correction Quality')
ax2.fill_between(me_fly, 0, 1, where=gap_mask,
                 color=STATUS_COLORS['CORRECTION_LOST'], alpha=0.25, linewidth=0,
                 label='Correction Lost (gap)')
ax2.axhline(0.95, color='#27AE60', ls=':', lw=1.2, alpha=0.7,
            label='Baseline (0.95 — ideal link)')
ax2.axhline(0.60, color='#C0392B', ls=':', lw=1.2, alpha=0.7,
            label='Minimum (0.60 — damaged comms)')
ax2.set_ylabel('Correction Quality (0–1)')
ax2.set_xlabel('Mission Elapsed Time (s)')
ax2.set_ylim(-0.05, 1.10)
ax2.grid(True, ls='--', lw=0.4, alpha=0.45)
# Lower-right (exit region): clear of the rising quality line and free of any
# correction-gap bands, so it never occludes a data feature.
ax2.legend(loc='lower right', fontsize=9.0)
add_phase_vlines(ax2, me_fly, phase_fly)

ax1.set_xlim(me_fly[0], me_fly[-1])

plt.savefig(os.path.join(OUT_DIR, 'l3_compound_scenario_profile.png'))
plt.close()

# ─────────────────────────────────────────────────────────────────────────────
# Figure 2 — RTK Error Over Time (compound disaster)
# ─────────────────────────────────────────────────────────────────────────────
print('[2/7] Generating: l3_error_over_time.png')

err_fly  = cd_rtk_err[cd_flying]
raw_fly  = cd_raw_err[cd_flying]
stat_fly = cd_status[cd_flying]
W = 30

fig, ax = plt.subplots(figsize=(14, 5.8))
fig.subplots_adjust(left=0.08, right=0.97, top=0.87, bottom=0.24)

shade_phases(ax, me_fly, phase_fly, alpha=0.10)

ax.plot(me_fly, raw_fly,         color=C_RAW, lw=0.5, alpha=0.12)
ax.plot(me_fly, err_fly,         color=C_CD,  lw=0.5, alpha=0.12)
ax.plot(me_fly, smooth(raw_fly), color=C_RAW, lw=1.8, alpha=0.85,
        label='Raw GNSS Error (3 s mean)')
ax.plot(me_fly, smooth(err_fly), color=C_CD,  lw=2.2, alpha=0.95,
        label='RTK-Corrected Error (3 s mean)')

# Log y-axis: RTK error spans ~0.04 m (fixed) to ~12 m (dropouts) — ~2.5 decades.
# On a linear axis the landing-critical sub-metre detail is crushed onto the x-axis.
ybot = 0.01
ytop = max(float(np.nanmax(raw_fly)) * 1.30, 14.0)
ax.set_yscale('log')
ax.set_ylim(ybot, ytop)

# Correction-lost shading (full plot height)
cl_mask = stat_fly == 'CORRECTION_LOST'
ax.fill_between(me_fly, ybot, ytop, where=cl_mask,
                color=STATUS_COLORS['CORRECTION_LOST'],
                alpha=0.18, linewidth=0, label='Correction Lost')

# Threshold lines (unified viability colours: green = landing, yellow = approach)
ax.axhline(2.0, color=THR_APPR, ls='--', lw=1.4, alpha=0.90,
           label='Approach threshold (2.0 m)')
ax.axhline(0.3, color=THR_LAND, ls='--', lw=1.4, alpha=0.90,
           label='Landing threshold (0.3 m)')

add_phase_vlines(ax, me_fly, phase_fly)
label_phases_top(ax, me_fly, phase_fly, y_frac=0.97)

ax.set_xlim(me_fly[0], me_fly[-1])
ax.set_xlabel('Mission Elapsed Time (s)', labelpad=6)
ax.set_ylabel('3D Positioning Error (m, log scale)')
ax.set_title(
    'RTK Positioning Error Over Mission Time — Compound Disaster Scenario\n'
    'Level 3 Resilient RTK  |  5-Phase Degradation Profile  |  390 m × 789 m Coverage',
    pad=8)
ax.grid(True, ls='--', lw=0.4, alpha=0.45)
# Placed just outside the axes (top-right): the amber raw line runs at ~3.5 m
# across the full width, so any in-plot legend would cover it. savefig bbox='tight'
# expands the canvas to include an outside legend.
ax.legend(loc='upper left', bbox_to_anchor=(1.005, 1.0), fontsize=9.0, ncol=1)

stats_text = (
    f'Compound Disaster — Flying period:  '
    f'Raw GNSS μ = {np.mean(raw_fly):.3f} m   |   '
    f'RTK μ = {np.mean(err_fly):.3f} m   |   '
    f'RTK max = {np.max(err_fly):.2f} m   |   '
    f'Approach ≤2.0 m: {pct_app:.1f}%   |   '
    f'Landing ≤0.3 m: {pct_land:.1f}%'
)
fig.text(0.08, 0.04, stats_text, fontsize=8.5, va='bottom', ha='left',
         bbox=dict(boxstyle='round,pad=0.45', facecolor='#F8F9FA',
                   alpha=0.95, edgecolor='#CCCCCC'))

plt.savefig(os.path.join(OUT_DIR, 'l3_error_over_time.png'))
plt.close()

# ─────────────────────────────────────────────────────────────────────────────
# Figure 3 — Dynamic Uncertainty vs Level 2 Fixed Accuracy
# ─────────────────────────────────────────────────────────────────────────────
print('[3/7] Generating: l3_uncertainty_over_time.png')

cd_std_fly2 = cd_rtk_std[cd_flying]
l2_std_mean = float(np.nanmean(l2_std_fly))  # Level 2 mean uncertainty (flat reference)

fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(14, 7.5),
                                      gridspec_kw={'height_ratios': [3, 2], 'hspace': 0.10},
                                      sharex=True)
fig.subplots_adjust(left=0.09, right=0.97, top=0.88, bottom=0.10)
fig.suptitle(
    'RTK Uncertainty Output — Dynamic (Level 3) vs Fixed (Level 2)\n'
    'Validates that the uncertainty signal tracks actual degradation',
    fontsize=12, fontweight='bold', y=0.97)

# ── Top: uncertainty comparison ──
shade_phases(ax_top, me_fly, phase_fly, alpha=0.09)

ax_top.plot(me_fly, cd_std_fly2, color=C_CD, lw=1.8, alpha=0.90,
            label='Level 3 dynamic rtk_std (reported uncertainty)')
ax_top.axhline(l2_std_mean, color=C_BASE, ls='--', lw=2.0, alpha=0.85,
               label=f'Level 2 mean rtk_std = {l2_std_mean:.3f} m  (fixed per-status)')
ax_top.axhline(0.3,  color=THR_LAND, ls=':', lw=1.2, alpha=0.80)
ax_top.axhline(2.0,  color=THR_APPR, ls=':', lw=1.2, alpha=0.80)
ax_top.text(me_fly[-1] - 5, 0.36, '0.30 m', color=THR_LAND, fontsize=8, ha='right', fontweight='bold')
ax_top.text(me_fly[-1] - 5, 2.12, '2.00 m', color=THR_APPR, fontsize=8, ha='right', fontweight='bold')
# The Level 2 line sits at ~0.03 m, essentially on the axis — annotate it inline
# so its near-zero "flat / overconfident" value is legible, not lost in the spine.
ax_top.annotate(f'Level 2 ≈ {l2_std_mean:.3f} m (flat, overconfident)',
                xy=(me_fly[len(me_fly)//3], l2_std_mean),
                xytext=(me_fly[len(me_fly)//3], 0.95), fontsize=8.5, color=C_BASE,
                fontweight='bold', ha='center', va='bottom',
                arrowprops=dict(arrowstyle='-|>', color=C_BASE, lw=1.2))

add_phase_vlines(ax_top, me_fly, phase_fly)
# Log y: on a linear axis the Level 2 line (~0.03 m) and the whole sub-0.3 m
# landing-viability band were crushed flat against the spine and unreadable —
# yet that band IS the landing decision. Log (floor 0.01 m) makes the L2 line
# and the sub-metre detail legible while the growth ramps stay clearly visible.
ax_top.set_yscale('log')
ax_top.set_ylim(0.01, max(float(np.nanmax(cd_std_fly2)) * 1.5, 6.0))
label_phases_top(ax_top, me_fly, phase_fly, y_frac=0.97)
ax_top.set_ylabel('RTK Uncertainty / Std (m, log scale)')
ax_top.grid(True, ls='--', lw=0.4, alpha=0.45, which='both')
# Lowered below the top phase-label band so Landing/Exit labels stay visible.
ax_top.legend(loc='upper right', bbox_to_anchor=(1.0, 0.88), fontsize=9.5)

# ── Bottom: actual RTK error (ground truth comparison) ──
shade_phases(ax_bot, me_fly, phase_fly, alpha=0.09)
ax_bot.plot(me_fly, err_fly,         color=C_CD,  lw=0.6, alpha=0.18)
ax_bot.plot(me_fly, smooth(err_fly), color=C_CD,  lw=2.0, alpha=0.92,
            label='Actual RTK error (ground truth)')
ax_bot.plot(me_fly, cd_std_fly2,     color='#884EA0', lw=1.2, ls='--', alpha=0.70,
            label='Reported uncertainty (rtk_std)')

add_phase_vlines(ax_bot, me_fly, phase_fly)
# Log y to match the top panel (shared scale) and to lift the departure/landing
# error (~0.03 m) and the reported-std line off the spine — on linear they were
# flattened onto the axis, hiding whether uncertainty tracks error at low values.
ax_bot.set_yscale('log')
ax_bot.set_ylim(0.01, max(float(np.nanmax(err_fly)) * 1.5, 6.0))
ax_bot.set_xlabel('Mission Elapsed Time (s)', labelpad=6)
ax_bot.set_ylabel('Error / Std (m, log scale)')
ax_bot.set_title('Actual RTK Error vs Reported Uncertainty — uncertainty should track error',
                 fontsize=10, pad=4)
ax_bot.grid(True, ls='--', lw=0.4, alpha=0.45, which='both')
ax_bot.legend(loc='upper right', fontsize=9.0)
ax_bot.set_xlim(me_fly[0], me_fly[-1])

plt.savefig(os.path.join(OUT_DIR, 'l3_uncertainty_over_time.png'))
plt.close()

# ─────────────────────────────────────────────────────────────────────────────
# Figure 4 — Mission Viability Timeline
# ─────────────────────────────────────────────────────────────────────────────
print('[4/7] Generating: l3_viability_timeline.png')

# Only flying rows with non-empty viability
viab_fly  = cd_viab[cd_flying]
has_viab  = viab_fly != ''
me_v      = me_fly[has_viab]
viab_v    = viab_fly[has_viab]
phase_v   = phase_fly[has_viab]
err_v     = err_fly[has_viab]

fig, (ax_v, ax_e) = plt.subplots(2, 1, figsize=(14, 7),
                                   gridspec_kw={'height_ratios': [2, 3], 'hspace': 0.08},
                                   sharex=True)
fig.subplots_adjust(left=0.09, right=0.97, top=0.88, bottom=0.16)
fig.suptitle(
    'Mission Viability Signal Over Time — Compound Disaster Scenario\n'
    'Level 3 Resilient RTK  |  State transitions drive path_planning decisions',
    fontsize=12, fontweight='bold', y=0.97)

# ── Top: viability state strip ──
VIAB_ORDER = ['LANDING_VIABLE', 'APPROACH_VIABLE', 'DEGRADED', 'INSUFFICIENT']
for state in VIAB_ORDER:
    mask_s = viab_v == state
    ax_v.fill_between(me_v, 0, 1, where=mask_s,
                      color=VIAB_COLORS[state], alpha=0.88, linewidth=0)

# Annotate each viability state ONCE, on its widest contiguous band. The state
# oscillates every ~40 s in the search zone, so labelling every segment (the old
# behaviour) produced unreadable overlapping text. One label per state on its
# widest run stays informative without crowding; the legend covers the rest.
segments = []   # (state, t_mid, span)
i = 0
while i < len(viab_v):
    s = viab_v[i]; j = i
    while j < len(viab_v) and viab_v[j] == s:
        j += 1
    t_s = me_v[i]; t_e = me_v[min(j - 1, len(me_v) - 1)]
    segments.append((s, (t_s + t_e) / 2, t_e - t_s))
    i = j

for state in VIAB_ORDER:
    runs = [seg for seg in segments if seg[0] == state]
    if not runs:
        continue
    _, t_mid, span = max(runs, key=lambda seg: seg[2])
    if span > 25:                       # only if the widest run has room for text
        ax_v.text(t_mid, 0.5, state.replace('_', ' '),
                  ha='center', va='center', fontsize=8.0,
                  fontweight='bold', color='white')

# Phase vlines on viability strip
add_phase_vlines(ax_v, me_v, phase_v)
ax_v.set_ylim(0, 1)
ax_v.set_yticks([])
ax_v.set_ylabel('Viability State')
ax_v.spines['left'].set_visible(False)

viab_handles = [mpatches.Patch(facecolor=VIAB_COLORS[s], alpha=0.85,
                                edgecolor='none', label=VIAB_LABELS[s])
                for s in VIAB_ORDER if s in set(viab_v)]
# Legend in the gutter ABOVE the strip: at 'upper right' it sat on the state
# strip itself and occluded part of the Approach/Landing-viable band, which is
# the very information the strip exists to show. One horizontal row clears it.
ax_v.legend(handles=viab_handles, loc='lower center', bbox_to_anchor=(0.5, 1.01),
            fontsize=8.5, ncol=4, frameon=True)

# ── Bottom: RTK error with threshold lines ──
shade_phases(ax_e, me_v, phase_v, alpha=0.09)

ax_e.plot(me_v, err_v,         color=C_CD, lw=0.5, alpha=0.15)
ax_e.plot(me_v, smooth(err_v), color=C_CD, lw=2.0, alpha=0.92,
          label='RTK Error (3 s mean)')

ax_e.axhline(0.3, color=VIAB_COLORS['LANDING_VIABLE'],  ls='--', lw=1.5, alpha=0.85,
             label='Landing threshold (0.3 m)')
ax_e.axhline(2.0, color=VIAB_COLORS['APPROACH_VIABLE'], ls='--', lw=1.5, alpha=0.85,
             label='Approach threshold (2.0 m)')
ax_e.axhline(4.0, color=VIAB_COLORS['DEGRADED'],        ls='--', lw=1.2, alpha=0.65,
             label='Degraded ceiling (4.0 m)')

add_phase_vlines(ax_e, me_v, phase_v)
# Log y: on linear the 0.3 m landing threshold sat on the spine (indistinguishable
# from the axis) and the sub-metre error in departure/landing/exit was invisible.
# Log (floor 0.01 m) lifts the threshold clear and makes the low-error phases legible.
ax_e.set_yscale('log')
ax_e.set_ylim(0.01, max(float(np.nanmax(err_v)) * 1.5, 6.0))
label_phases_top(ax_e, me_v, phase_v, y_frac=0.97)
ax_e.set_xlim(me_v[0], me_v[-1])
ax_e.set_xlabel('Mission Elapsed Time (s)', labelpad=6)
ax_e.set_ylabel('RTK Error (m, log scale)')
ax_e.grid(True, ls='--', lw=0.4, alpha=0.45, which='both')
# Below the panel: the threshold reference lines span the full width, so any
# in-axes legend crosses them. Placing it under the axis (one row) clears the
# 2.0/4.0 m lines entirely — consistent with Fig 6/Fig 7.
ax_e.legend(loc='upper center', bbox_to_anchor=(0.5, -0.16), fontsize=9.0,
            ncol=4, frameon=True)

plt.savefig(os.path.join(OUT_DIR, 'l3_viability_timeline.png'))
plt.close()

# ─────────────────────────────────────────────────────────────────────────────
# Figure 5 — Three-Run Comparison
# ─────────────────────────────────────────────────────────────────────────────
print('[5/7] Generating: l3_three_run_comparison.png')

fig = plt.figure(figsize=(15, 6.2))
fig.subplots_adjust(left=0.07, right=0.97, top=0.85, bottom=0.14, wspace=0.38)
fig.suptitle(
    'Three-Run RTK Accuracy Comparison — Baseline vs Compound Disaster vs Total Failure\n'
    'Level 3 Resilient RTK  |  Flying-period data only',
    fontsize=12, fontweight='bold', y=0.97)

gs5  = GridSpec(1, 2, figure=fig, wspace=0.38)
axBP = fig.add_subplot(gs5[0])
axKM = fig.add_subplot(gs5[1])

# ── Panel A: Box plots ──
datasets    = [l2_err_fly,   cd_err_fly,     tf_err_fly]
box_colors  = [C_BASE,       C_CD,           C_TF]
box_labels  = ['Baseline\n(Level 2)', 'Compound\nDisaster', 'Total\nFailure']

bp = axBP.boxplot(datasets, patch_artist=True, widths=0.5, whis=[5, 95],
                   medianprops=dict(color='white', lw=2.0),
                   whiskerprops=dict(lw=1.2),
                   capprops=dict(lw=1.2),
                   flierprops=dict(marker='o', ms=2.5, alpha=0.35))
for patch, col in zip(bp['boxes'], box_colors):
    patch.set_facecolor(col)
    patch.set_alpha(0.78)
for whisker, cap in zip(bp['whiskers'], bp['caps']):
    whisker.set_color('#555555')
    cap.set_color('#555555')

axBP.axhline(2.0, color=THR_APPR, ls='--', lw=1.4, alpha=0.90,
             label='Approach threshold (2.0 m)')
axBP.axhline(0.3, color=THR_LAND, ls='--', lw=1.4, alpha=0.90,
             label='Landing threshold (0.3 m)')

axBP.set_xticks([1, 2, 3])
axBP.set_xticklabels(box_labels, fontsize=10)
axBP.set_ylabel('RTK-Corrected Positioning Error (m, log scale)')
axBP.set_title('RTK Error Distribution by Scenario\n(boxes = IQR, whiskers = 5th–95th pct)', pad=6)
# Log y: the three distributions span ~0.04 m (baseline) to ~15 m (total failure).
# On a linear axis the baseline and compound boxes collapse onto the x-axis.
axBP.set_yscale('log')
axBP.set_ylim(0.01, max(float(np.percentile(tf_err_fly, 99)) * 1.4, 20.0))
axBP.grid(True, axis='y', ls='--', lw=0.4, alpha=0.5, which='both')
axBP.legend(loc='upper left', fontsize=8.5)

# Annotate median on each box (multiplicative offset so the label clears the box on log)
for i, data in enumerate(datasets, 1):
    med = np.median(data)
    axBP.text(i, med * 1.35, f'{med:.3f} m',
              ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='white',
              bbox=dict(boxstyle='round,pad=0.2', facecolor=box_colors[i-1],
                        alpha=0.85, edgecolor='none'))

# ── Panel B: Key metrics — error (m) on left axis, % within threshold on right axis ──
# Metres (0–8) and percentages (0–100) must NOT share one y-axis: split onto twin axes.
err_metrics = ['Mean\nError (m)', 'Median\nError (m)', '95th Pct\nError (m)']
pct_metrics = ['% within\n2.0 m', '% within\n0.3 m']

l2_err_m = [np.mean(l2_err_fly), np.median(l2_err_fly), np.percentile(l2_err_fly, 95)]
cd_err_m = [np.mean(cd_err_fly), np.median(cd_err_fly), np.percentile(cd_err_fly, 95)]
tf_err_m = [np.mean(tf_err_fly), np.median(tf_err_fly), np.percentile(tf_err_fly, 95)]

l2_pct = [100*np.mean(l2_err_fly <= 2.0), 100*np.mean(l2_err_fly <= 0.3)]
cd_pct = [100*np.mean(cd_err_fly <= 2.0), 100*np.mean(cd_err_fly <= 0.3)]
tf_pct = [100*np.mean(tf_err_fly <= 2.0), 100*np.mean(tf_err_fly <= 0.3)]

axKM2 = axKM.twinx()
axKM2.spines['top'].set_visible(False)
xe = np.arange(len(err_metrics))                            # 0,1,2  → metres  (left axis)
xp = np.arange(len(pct_metrics)) + len(err_metrics) + 0.5   # 3.5,4.5 → percent (right axis)
w  = 0.26

# Error bars (left axis, metres)
be1 = axKM.bar(xe - w, l2_err_m, w, color=C_BASE, alpha=0.82, edgecolor='white', label='Baseline')
be2 = axKM.bar(xe,     cd_err_m, w, color=C_CD,   alpha=0.82, edgecolor='white', label='Compound Disaster')
be3 = axKM.bar(xe + w, tf_err_m, w, color=C_TF,   alpha=0.82, edgecolor='white', label='Total Failure')
# Percentage bars (right axis, %)
bp1 = axKM2.bar(xp - w, l2_pct, w, color=C_BASE, alpha=0.82, edgecolor='white')
bp2 = axKM2.bar(xp,     cd_pct, w, color=C_CD,   alpha=0.82, edgecolor='white')
bp3 = axKM2.bar(xp + w, tf_pct, w, color=C_TF,   alpha=0.82, edgecolor='white')

yhi_m = max(max(l2_err_m), max(cd_err_m), max(tf_err_m)) * 1.32
axKM.set_ylim(0, yhi_m)
axKM2.set_ylim(0, 119)

for bars, vals in [(be1, l2_err_m), (be2, cd_err_m), (be3, tf_err_m)]:
    for bar, v in zip(bars, vals):
        axKM.text(bar.get_x() + bar.get_width()/2, v + yhi_m * 0.02, f'{v:.2f}',
                  ha='center', va='bottom', fontsize=7.5, fontweight='bold', rotation=90)
for bars, vals in [(bp1, l2_pct), (bp2, cd_pct), (bp3, tf_pct)]:
    for bar, v in zip(bars, vals):
        axKM2.text(bar.get_x() + bar.get_width()/2, v + 2, f'{v:.0f}%',
                   ha='center', va='bottom', fontsize=7.5, fontweight='bold', rotation=90)

# Divider separating the metres group from the percentage group
axKM.axvline(len(err_metrics) - 0.25, color='#BBBBBB', ls='-', lw=1.0, alpha=0.7)

axKM.set_xticks(list(xe) + list(xp))
axKM.set_xticklabels(err_metrics + pct_metrics, fontsize=9.0)
axKM.set_ylabel('Positioning Error (m)')
axKM2.set_ylabel('Readings Within Threshold (%)')
axKM.set_title('Key Metrics by Scenario', pad=6)
axKM.grid(True, axis='y', ls='--', lw=0.4, alpha=0.5)
axKM.legend(fontsize=9.0, loc='upper center')

plt.savefig(os.path.join(OUT_DIR, 'l3_three_run_comparison.png'))
plt.close()

# ─────────────────────────────────────────────────────────────────────────────
# Figure 6 — Mission Phase Accuracy vs Thresholds
# ─────────────────────────────────────────────────────────────────────────────
print('[6/7] Generating: l3_mission_phase_accuracy.png')

phase_masks_ord = [m_dep, m_app, m_srch, m_land, m_exit]
phase_data      = [cd_rtk_err[m] for m in phase_masks_ord]
phase_colors_ord = [PHASE_COLORS[p] for p in PHASE_NAMES]

fig, (axPH, axPCT) = plt.subplots(1, 2, figsize=(15, 6.4))
fig.subplots_adjust(left=0.07, right=0.97, top=0.84, bottom=0.22, wspace=0.38)
fig.suptitle(
    'RTK Accuracy by Mission Phase — Compound Disaster Scenario\n'
    'Level 3 Resilient RTK  |  Engineering thresholds: Approach ≤2.0 m  |  Landing ≤0.3 m',
    fontsize=12, fontweight='bold', y=0.97)

# ── Panel A: Box plot per phase ──
bp2 = axPH.boxplot(phase_data, patch_artist=True, widths=0.5, whis=[5, 95],
                    medianprops=dict(color='white', lw=2.0),
                    whiskerprops=dict(lw=1.2), capprops=dict(lw=1.2),
                    flierprops=dict(marker='o', ms=2.5, alpha=0.35))
for patch, col in zip(bp2['boxes'], phase_colors_ord):
    patch.set_facecolor(col)
    patch.set_alpha(0.80)
for whisker, cap in zip(bp2['whiskers'], bp2['caps']):
    whisker.set_color('#555555')
    cap.set_color('#555555')

axPH.axhline(2.0, color=THR_APPR, ls='--', lw=1.6, alpha=0.90,
             label='Approach threshold (2.0 m)')
axPH.axhline(0.3, color=THR_LAND, ls='--', lw=1.6, alpha=0.90,
             label='Landing threshold (0.3 m)')

# Log y: phase medians span 0.05 m (Departure/Exit) to ~0.6 m, with Search-Zone
# fliers to ~8 m. On a linear axis the Departure/Exit boxes collapse onto the axis.
axPH.set_yscale('log')
axPH.set_ylim(0.01, max(float(np.percentile(np.concatenate(phase_data), 99)) * 1.5, 10.0))
axPH.set_xticks(range(1, len(PHASE_NAMES) + 1))
axPH.set_xticklabels(PHASE_NAMES, fontsize=9.5)
axPH.set_ylabel('RTK-Corrected Positioning Error (m, log scale)')
axPH.set_title('Error Distribution per Mission Phase\n(boxes = IQR, whiskers = 5th–95th pct)', pad=6)
axPH.grid(True, axis='y', ls='--', lw=0.4, alpha=0.5, which='both')
axPH.legend(loc='upper right', fontsize=9.0)

for i, (data, col) in enumerate(zip(phase_data, phase_colors_ord), 1):
    if len(data) > 0:
        med = np.median(data)
        axPH.text(i, med * 1.35, f'{med:.3f} m',
                  ha='center', va='bottom', fontsize=8.0, fontweight='bold',
                  color='white',
                  bbox=dict(boxstyle='round,pad=0.2', facecolor=col,
                            alpha=0.90, edgecolor='none'))

# ── Panel B: % meeting threshold per phase ──
thresholds = [None, 2.0, None, 0.3, None]   # apply threshold where meaningful
thresh_labels = {2.0: '≤2.0 m (approach)', 0.3: '≤0.3 m (landing)'}

pct_2m = [100.0 * np.mean(d <= 2.0) if len(d) > 0 else 0.0 for d in phase_data]
pct_03 = [100.0 * np.mean(d <= 0.3) if len(d) > 0 else 0.0 for d in phase_data]

x_ph = np.arange(len(PHASE_NAMES))
w_ph = 0.38
axPCT.bar(x_ph - w_ph/2, pct_2m, w_ph, color=THR_APPR, alpha=0.85,
          edgecolor='white', label='% within 2.0 m (approach threshold)')
axPCT.bar(x_ph + w_ph/2, pct_03, w_ph, color=THR_LAND, alpha=0.85,
          edgecolor='white', label='% within 0.3 m (landing threshold)')

axPCT.axhline(90, color=THR_APPR, ls=':', lw=1.6, alpha=0.80,
              label='Approach target (90%)')
axPCT.axhline(80, color=THR_LAND, ls=':', lw=1.6, alpha=0.80,
              label='Landing target (80%)')

for xi, (p2, p3) in enumerate(zip(pct_2m, pct_03)):
    axPCT.text(xi - w_ph/2, p2 + 1.5, f'{p2:.0f}%', ha='center',
               va='bottom', fontsize=8.0, fontweight='bold')
    axPCT.text(xi + w_ph/2, p3 + 1.5, f'{p3:.0f}%', ha='center',
               va='bottom', fontsize=8.0, fontweight='bold')

axPCT.set_xticks(x_ph)
axPCT.set_xticklabels(PHASE_NAMES, fontsize=9.5)
axPCT.set_ylabel('Percentage of Phase (%)')
axPCT.set_title('Percentage of Readings Within Engineering Thresholds\nby Mission Phase', pad=6)
axPCT.set_ylim(0, 112)
axPCT.grid(True, axis='y', ls='--', lw=0.4, alpha=0.5)
# Below the axis (bars fill the panel, so an in-axes legend would cover them).
axPCT.legend(loc='upper center', bbox_to_anchor=(0.5, -0.13), ncol=2, fontsize=8.5)

plt.savefig(os.path.join(OUT_DIR, 'l3_mission_phase_accuracy.png'))
plt.close()

# ─────────────────────────────────────────────────────────────────────────────
# Figure 7 — ULog Cross-Validation
# ─────────────────────────────────────────────────────────────────────────────
print('[7/7] Generating: l3_ulog_crossval.png')

fig = plt.figure(figsize=(16, 6.2))
fig.subplots_adjust(left=0.06, right=0.97, top=0.85, bottom=0.20, wspace=0.36)
fig.suptitle(
    'ULog Cross-Validation — PX4 Ground Truth vs RTK Simulation (Compound Disaster)\n'
    'Level 3 Resilient RTK  |  Confirms simulation ran against real drone flight data',
    fontsize=12, fontweight='bold', y=0.97)

gs7  = GridSpec(1, 3, figure=fig, wspace=0.36)
axT  = fig.add_subplot(gs7[0])   # trajectory
axE  = fig.add_subplot(gs7[1])   # error + viability overlay
axA  = fig.add_subplot(gs7[2])   # altitude profile

# ── Panel A: 2D trajectory ──
# ULog trajectory (East=ul_east_m, North=ul_north_m) — flying portion
ul_fly_mask = ul_east_m**2 + ul_north_m**2 > 25   # >5 m from origin
axT.plot(ul_east_m[ul_fly_mask], ul_north_m[ul_fly_mask],
         color='#1C2833', lw=1.6, zorder=4, label='ULog Ground Truth Path')

# CSV RTK estimates — flying rows, subsampled
step = max(1, cd_flying.sum() // 1200)
rtk_e_fly  = cd_rtk_east[cd_flying]
rtk_n_fly  = cd_rtk_north[cd_flying]
valid_rtk  = ~np.isnan(rtk_e_fly)
axT.scatter(rtk_e_fly[valid_rtk][::step], rtk_n_fly[valid_rtk][::step],
            color=C_CD, s=5, alpha=0.35, zorder=3, label='RTK Estimates (CSV)')

# CSV ground truth path
axT.plot(cd_gt_x[cd_flying], cd_gt_y[cd_flying],
         color='#5D6D7E', lw=0.8, ls='--', alpha=0.60, zorder=2, label='CSV Ground Truth')

# Mission waypoints
for i, (we, wn) in enumerate(mission_wps):
    axT.scatter(we, wn, marker='^', s=60, color='#E74C3C', zorder=6,
                edgecolors='white', linewidths=0.7)
    axT.text(we + 15, wn + 15, f'WP{i+1}', fontsize=7.5, color='#E74C3C', fontweight='bold')

# Home marker
axT.plot(0, 0, 'o', color='#8E44AD', ms=9, zorder=7)
axT.text(10, -30, 'Home', fontsize=8.0, color='#8E44AD', fontweight='bold')

axT.set_xlabel('East (m)  [NED-y / ENU-x]')
axT.set_ylabel('North (m)  [NED-x / ENU-y]')
axT.set_title('2D Flight Trajectory\nULog vs CSV Overlay', pad=6)
axT.set_aspect('equal', adjustable='datalim')
axT.grid(True, ls='--', lw=0.4, alpha=0.5)
axT.legend(loc='upper left', fontsize=8.0)

# ── Panel B: RTK error with viability colour coding ──
# Colour each sample by its viability state
viab_seg_me  = me_fly[has_viab]
viab_seg_err = smooth(err_fly)[has_viab]
viab_seg_v   = viab_fly[has_viab]

axE.plot(me_fly, smooth(err_fly), color='#AAB7B8', lw=3.0, alpha=0.40)
for state, col in VIAB_COLORS.items():
    mask_s = viab_seg_v == state
    axE.scatter(viab_seg_me[mask_s], viab_seg_err[mask_s],
                s=6, color=col, alpha=0.70, linewidths=0, zorder=3,
                label=state.replace('_', ' '))

# Thresholds drawn in neutral dark grey here: the green/yellow used elsewhere is
# taken by the viability-coloured scatter in this panel, so reusing it would blend
# the reference lines into the data points.
axE.axhline(4.0, color='#2C3E50', ls='-.', lw=1.2, alpha=0.85)
axE.axhline(2.0, color='#2C3E50', ls='--', lw=1.2, alpha=0.85)
axE.axhline(0.3, color='#2C3E50', ls=':',  lw=1.2, alpha=0.85)
# Labels on the LEFT edge (empty departure region) so they clear the top-right legend.
axE.text(me_fly[0], 4.2,  '4.0 m', color='#2C3E50', fontsize=7.5, ha='left', va='bottom')
axE.text(me_fly[0], 2.15, '2.0 m', color='#2C3E50', fontsize=7.5, ha='left', va='bottom')
axE.text(me_fly[0], 0.32, '0.3 m', color='#2C3E50', fontsize=7.5, ha='left', va='bottom')
add_phase_vlines(axE, me_fly, phase_fly)
# Log y + limit set from the plotted (smoothed) values, not raw error: previously
# ylim came from raw err max (~9.8 m) while the plot shows smoothed data (~4.6 m),
# leaving a large empty top and crushing the sub-metre detail onto the axis.
axE.set_yscale('log')
axE.set_ylim(0.01, max(float(np.nanmax(viab_seg_err)) * 1.5, 6.0))
axE.set_xlim(me_fly[0], me_fly[-1])
axE.set_xlabel('Mission Elapsed Time (s)')
axE.set_ylabel('RTK Error (m, log scale)')
axE.set_title('RTK Error Colour-Coded by\nMission Viability State', pad=6)
axE.grid(True, ls='--', lw=0.4, alpha=0.45, which='both')
viab_handles2 = [mpatches.Patch(facecolor=VIAB_COLORS[s], alpha=0.80, edgecolor='none',
                                 label=s.replace('_', ' '))
                 for s in ['LANDING_VIABLE', 'APPROACH_VIABLE', 'DEGRADED', 'INSUFFICIENT']
                 if s in set(viab_v)]
# Legend below the panel: at top-right it overlapped the DEGRADED spikes (~4 m,
# 400-560 s) and the 2.0/4.0 m threshold lines. Moving it under the axis (as in
# Fig 6 Panel B) keeps it clear of the data at every elapsed time.
axE.legend(handles=viab_handles2, loc='upper center', bbox_to_anchor=(0.5, -0.13),
           fontsize=8, ncol=2, frameon=True)

# ── Panel C: ULog altitude profile ──
axA.plot(ul_me, ul_alt_m, color='#1C2833', lw=1.8, label='Altitude AGL (ULog)')
axA.axhline(50.0, color='#3498DB', ls='--', lw=1.0, alpha=0.70,
            label='Mission altitude (50 m)')
axA.fill_between(ul_me, 0, ul_alt_m, color='#1C2833', alpha=0.08)
# NOTE: the seq= mission-item markers were removed (non-consecutive numbering,
# overlapping timestamps, cluttered) and the "WP4 descent (20 m)" line was removed
# because THIS (compound) run cruised at 50 m throughout and never descended to 20 m
# — that descent occurred only in the total-failure run. Honest depiction of the
# displayed flight: takeoff -> 50 m cruise -> final landing.

axA.set_xlim(ul_me[0], ul_me[-1])
axA.set_ylim(0, max(float(ul_alt_m.max()) * 1.12, 60))
axA.set_xlabel('Mission Elapsed Time (s)  [ULog reference]')
axA.set_ylabel('Altitude AGL (m)')
axA.set_title('UAV Altitude Profile — ULog\nTakeoff, sustained 50 m cruise, and landing', pad=6)
axA.grid(True, ls='--', lw=0.4, alpha=0.45)
axA.legend(loc='upper right', fontsize=8.5)

plt.savefig(os.path.join(OUT_DIR, 'l3_ulog_crossval.png'))
plt.close()

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print('=' * 65)
print('Level 3 analysis complete.')
print()
print('  Three-run RTK error comparison (flying period):')
print(f'    Baseline (L2)       μ = {np.mean(l2_err_fly):.4f} m  |  P95 = {np.percentile(l2_err_fly,95):.4f} m')
print(f'    Compound Disaster   μ = {np.mean(cd_err_fly):.4f} m  |  P95 = {np.percentile(cd_err_fly,95):.4f} m')
print(f'    Total Failure       μ = {np.mean(tf_err_fly):.4f} m  |  P95 = {np.percentile(tf_err_fly,95):.4f} m')
print()
print('  Engineering threshold results (compound disaster):')
print(f'    Approach ≤2.0 m : {pct_app:.1f}%  (target >90%)')
print(f'    Landing  ≤0.3 m : {pct_land:.1f}%  (target >80%)')
print()
print('  Figures saved to:', OUT_DIR)
for fn in sorted(os.listdir(OUT_DIR)):
    if fn.endswith('.png'):
        sz = os.path.getsize(os.path.join(OUT_DIR, fn)) / 1024
        print(f'    {fn}  ({sz:.0f} KB)')
print('=' * 65)
