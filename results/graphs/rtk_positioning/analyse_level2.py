"""
Level 2 RTK Positioning — Analysis and Visualisation (segmented reanalysis)
===========================================================================
Generates six publication-quality figures from the Level 2 PX4/Gazebo
simulation CSV log and the QGC ULog flight record.

METHODOLOGICAL NOTE — why this analysis is segmented
----------------------------------------------------
The Level 2 logger ran for 1028 s, but the drone only left the ground at
t = 497 s and flew its autonomous waypoint mission at t = 785-948 s. The
RTK correction state machine (driven by `rtcm_correction_simulator_node`)
runs on its own clock from t = 0, so the GNSS->Float->Fixed convergence
(0-15 s) and the injected correction-loss event (45-50 s) both occur while
the vehicle is stationary on the ground, ~7 min before take-off.

Reporting a single blended "mission" statistic over the whole log therefore
fuses two physically distinct experiments. This script keeps them separate:

  INIT    (t < 50 s, stationary)  -> RTK initialization + correction-loss
                                      recovery (a state-machine demonstration;
                                      transition timing is SCRIPTED, see
                                      docs/simulation_assumptions.md).
  FLIGHT  (airborne, ~497-986 s)  -> the in-flight positioning accuracy
                                      result. 100 % RTK_FIXED throughout.
  MISSION (horizontal flight, ~785-948 s) -> the QGC waypoint leg; aligns
                                      with the 166 s ULog record used for
                                      cross-validation.

Headline result is the FLIGHT accuracy (cm-level, RTK Fixed), NOT the
whole-log mean. In-flight resilience to mid-mission correction loss is
delegated to Level 3 by design.

Figures produced (saved to level2/):
  l2_error_over_time.png      — Full session, INIT vs FLIGHT phases demarcated
  l2_rtk_convergence.png      — INIT sequence: convergence + loss recovery (stationary)
  l2_error_distribution.png   — In-flight error distribution: raw GNSS vs RTK
  l2_trajectory.png           — 2D flight trajectory (~210 x 215 m area)
  l2_accuracy_summary.png     — Error by segment, in-flight fix status, improvement
  l2_qgc_crossval.png         — QGC ULog cross-validation and 3-way accuracy comparison

Usage:
    python3 analyse_level2.py
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
from scipy.interpolate import interp1d
from pyulog import ULog

# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR    = os.path.join(SCRIPT_DIR, '..', '..', 'logs', 'rtk_positioning', 'level2')
ULOG_PATH  = os.path.join(SCRIPT_DIR, '..', '..', 'logs', 'qgc_mission_20260521.ulg')
OUT_DIR    = os.path.join(SCRIPT_DIR, 'level2')
os.makedirs(OUT_DIR, exist_ok=True)

csvs = sorted(f for f in os.listdir(LOG_DIR) if f.startswith('rtk_level2') and f.endswith('.csv'))
if not csvs:
    raise FileNotFoundError(f'No Level 2 CSV found in {LOG_DIR}')
CSV_PATH = os.path.join(LOG_DIR, csvs[-1])
print(f'[analyse_level2] CSV  : {CSV_PATH}')
print(f'[analyse_level2] ULog : {ULOG_PATH}')

# ── Load Level 2 CSV ─────────────────────────────────────────────────────────
with open(CSV_PATH) as f:
    rows = [r for r in csv.DictReader(f) if r['ros_time_sec'].strip()]

t0      = float(rows[0]['ros_time_sec'])
elapsed = np.array([float(r['ros_time_sec']) - t0           for r in rows])
gt_x    = np.array([float(r['ground_truth_x'])               for r in rows])
gt_y    = np.array([float(r['ground_truth_y'])               for r in rows])
gt_z    = np.array([float(r['ground_truth_z'])               for r in rows])
raw_err = np.array([float(r['raw_gnss_error_m'])             for r in rows])
rtk_err = np.array([float(r['rtk_error_m'])                  for r in rows])
status  = np.array([r['rtk_status_name'].strip()             for r in rows])
raw_lat = np.array([float(r['raw_gnss_lat']) if r['raw_gnss_lat'].strip() else np.nan for r in rows])
raw_lon = np.array([float(r['raw_gnss_lon']) if r['raw_gnss_lon'].strip() else np.nan for r in rows])
rtk_lat = np.array([float(r['rtk_lat'])      if r['rtk_lat'].strip()      else np.nan for r in rows])
rtk_lon = np.array([float(r['rtk_lon'])      if r['rtk_lon'].strip()      else np.nan for r in rows])

DURATION = elapsed[-1]
N        = len(rows)

# ── Segment masks (derived from the data, not hard-coded) ────────────────────
# FLIGHT  : airborne window — first to last sample with altitude > 2 m.
# MISSION : horizontal waypoint leg — horizontal displacement > 2 m from home.
# INIT    : scripted RTK initialization window (convergence + loss event),
#           which all occurs in the first 50 s while stationary on the ground.
ALT_THRESH   = 2.0
HORIZ_THRESH = 2.0
INIT_END     = 50.0          # scripted convergence (0-15 s) + loss event (45-50 s)

horiz   = np.sqrt(gt_x**2 + gt_y**2)
air_idx = np.where(gt_z > ALT_THRESH)[0]
T_TAKEOFF = float(elapsed[air_idx[0]])
T_LANDING = float(elapsed[air_idx[-1]])

m_init    = elapsed < INIT_END
m_flight  = (elapsed >= T_TAKEOFF) & (elapsed <= T_LANDING)
m_mission = horiz > HORIZ_THRESH
m_idle_fixed = (elapsed >= INIT_END) & (elapsed < T_TAKEOFF) & (status == 'RTK_FIXED')

T_MISSION_0 = float(elapsed[m_mission][0])
T_MISSION_1 = float(elapsed[m_mission][-1])

# ── Headline (FLIGHT) statistics ─────────────────────────────────────────────
raw_flight = raw_err[m_flight]
rtk_flight = rtk_err[m_flight]
raw_mean   = float(np.mean(raw_flight))             # in-flight raw GNSS
rtk_mean   = float(np.mean(rtk_flight))             # in-flight RTK (HEADLINE)
IMP_PCT    = (raw_mean - rtk_mean) / raw_mean * 100  # in-flight improvement (~98 %)
flight_fixed_pct = 100.0 * np.mean(status[m_flight] == 'RTK_FIXED')

# Whole-log mean retained ONLY for explicit comparison / disclosure
rtk_mean_wholelog = float(np.mean(rtk_err))

print(f'[analyse_level2] take-off t={T_TAKEOFF:.0f}s  landing t={T_LANDING:.0f}s  '
      f'mission t={T_MISSION_0:.0f}-{T_MISSION_1:.0f}s')
print(f'[analyse_level2] IN-FLIGHT  raw={raw_mean:.3f} m  RTK={rtk_mean:.4f} m  '
      f'improvement={IMP_PCT:.1f}%  RTK_FIXED={flight_fixed_pct:.1f}%')
print(f'[analyse_level2] (whole-log RTK mean for reference only = {rtk_mean_wholelog:.4f} m)')

# ENU conversion (round-trips through the simulation base station; the forward
# ENU->lat/lon and this inverse cancel, so raw_x/rtk_x share the ground-truth
# ENU frame regardless of the base coordinate — see simulation_assumptions.md).
BASE_LAT      = 39.981000
BASE_LON      = 116.344000
M_PER_DEG_LAT = 111320.0
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(BASE_LAT))

raw_x = (raw_lon - BASE_LON) * M_PER_DEG_LON
raw_y = (raw_lat - BASE_LAT) * M_PER_DEG_LAT
rtk_x = (rtk_lon - BASE_LON) * M_PER_DEG_LON
rtk_y = (rtk_lat - BASE_LAT) * M_PER_DEG_LAT

# ── Load QGC ULog ────────────────────────────────────────────────────────────
ulog    = ULog(ULOG_PATH)
gps_d   = next(d for d in ulog.data_list if d.name == 'vehicle_gps_position')
gt_d    = next(d for d in ulog.data_list if d.name == 'vehicle_global_position_groundtruth')

ul_gps_t   = gps_d.data['timestamp'] / 1e6
ul_gps_lat = gps_d.data['latitude_deg']
ul_gps_lon = gps_d.data['longitude_deg']
ul_gps_eph = gps_d.data['eph']          # reported horizontal accuracy estimate (1-sigma, m)

ul_gt_t    = gt_d.data['timestamp'] / 1e6
ul_gt_lat  = gt_d.data['lat']
ul_gt_lon  = gt_d.data['lon']
ul_gt_alt  = gt_d.data['alt']

UL_BASE_LAT = float(ul_gt_lat[0])
UL_BASE_LON = float(ul_gt_lon[0])
UL_M_LON    = 111320.0 * math.cos(math.radians(UL_BASE_LAT))

ul_gt_x  = (ul_gt_lon - UL_BASE_LON) * UL_M_LON
ul_gt_y  = (ul_gt_lat - UL_BASE_LAT) * 111320.0
ul_gps_x = (ul_gps_lon - UL_BASE_LON) * UL_M_LON
ul_gps_y = (ul_gps_lat - UL_BASE_LAT) * 111320.0

gt_ix = interp1d(ul_gt_t, ul_gt_x, bounds_error=False, fill_value=np.nan)
gt_iy = interp1d(ul_gt_t, ul_gt_y, bounds_error=False, fill_value=np.nan)
px4_err_3d = np.sqrt((ul_gps_x - gt_ix(ul_gps_t))**2 +
                     (ul_gps_y - gt_iy(ul_gps_t))**2)
px4_err_mean = float(np.nanmean(px4_err_3d))
px4_eph_mean = float(np.mean(ul_gps_eph))

# Per-status masks (used for the INIT figures)
m_gnss  = status == 'GNSS_ONLY'
m_float = status == 'RTK_FLOAT'
m_fixed = status == 'RTK_FIXED'
m_lost  = status == 'CORRECTION_LOST'

cl_t   = elapsed[m_lost]
cl_rtk = rtk_err[m_lost]
peak_t = float(cl_t[np.argmax(cl_rtk)]) if len(cl_t) else np.nan
peak_v = float(cl_rtk.max())            if len(cl_rtk) else np.nan

# ═══════════════════════════════════════════════════════════════════════════
# Publication style — Okabe-Ito colourblind-safe palette, baked in for
# reproducibility (no external style dependency). Generous sizing is retained
# deliberately: this is a report/presentation figure set, so detail visibility
# is prioritised over journal single-column compactness.
# ═══════════════════════════════════════════════════════════════════════════
# Okabe-Ito semantic assignments (distinguishable under all CVD types + grayscale)
OK_ORANGE   = '#E69F00'
OK_SKYBLUE  = '#56B4E9'
OK_GREEN    = '#009E73'
OK_YELLOW   = '#F0E442'
OK_BLUE     = '#0072B2'
OK_VERMIL   = '#D55E00'
OK_PURPLE   = '#CC79A7'
OK_BLACK    = '#000000'

C_RAW = OK_VERMIL    # raw / uncorrected GNSS error
C_RTK = OK_BLUE      # RTK-corrected error (the study subject)
C_GT  = '#1C2833'    # ground-truth path (near-black)

STATUS_COLORS = {
    'GNSS_ONLY':       OK_VERMIL,    # standard GNSS  (worst)
    'RTK_FLOAT':       OK_ORANGE,    # decimetre, partial
    'RTK_FIXED':       OK_GREEN,     # centimetre     (best)
    'CORRECTION_LOST': OK_PURPLE,    # link lost      (alarm)
}
STATUS_LABELS = {
    'GNSS_ONLY':       'GNSS Only  (metre-level, σ≈1.50 m)',
    'RTK_FLOAT':       'RTK Float  (decimetre, σ≈0.25 m)',
    'RTK_FIXED':       'RTK Fixed  (centimetre, σ≈0.03 m)',
    'CORRECTION_LOST': 'Correction Lost  (degraded, σ≈2.50 m)',
}
# Phase-region tints for the full-session timeline
REGION_INIT   = '#FBE9E7'   # pale vermillion  — initialization (stationary)
REGION_IDLE   = '#ECEFF1'   # pale grey        — pre-flight hold (stationary)
REGION_FLIGHT = '#E8F5E9'   # pale green       — autonomous flight

plt.rcParams.update({
    'font.family':        'sans-serif',
    'font.sans-serif':    ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size':          11,
    'axes.titlesize':     12,
    'axes.titleweight':   'bold',
    'axes.labelsize':     11,
    'axes.linewidth':     0.8,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'axes.axisbelow':     True,
    'xtick.labelsize':    10,
    'ytick.labelsize':    10,
    'xtick.direction':    'out',
    'ytick.direction':    'out',
    'legend.fontsize':    9.5,
    'legend.framealpha':  0.93,
    'legend.edgecolor':   '#CCCCCC',
    'figure.dpi':         150,
    'savefig.dpi':        300,
    'savefig.bbox':       'tight',
    'savefig.pad_inches': 0.18,
    'savefig.facecolor':  'white',
})

# ── Helpers ───────────────────────────────────────────────────────────────────
def panel_label(ax, letter, dx=-0.12, dy=1.04):
    """Bold A/B/C panel label in axes-fraction coordinates."""
    ax.text(dx, dy, letter, transform=ax.transAxes,
            fontsize=13, fontweight='bold', va='top', ha='left')

def shade_status(ax, t, st, alpha=0.10):
    i = 0
    while i < len(st):
        s = st[i]; j = i
        while j < len(st) and st[j] == s:
            j += 1
        ax.axvspan(t[i], t[min(j, len(t)-1)],
                   color=STATUS_COLORS.get(s, '#BDC3C7'), alpha=alpha, linewidth=0)
        i = j

def status_patch_handles(present):
    return [mpatches.Patch(facecolor=STATUS_COLORS[s], alpha=0.65,
                           edgecolor='none', label=STATUS_LABELS[s])
            for s in STATUS_COLORS if s in present]

def smooth(arr, w=30):
    return np.convolve(arr, np.ones(w) / w, mode='same')

# ═══════════════════════════════════════════════════════════════════════════
# Figure 1 — Full-session timeline: INITIALIZATION vs FLIGHT (nothing hidden)
# ═══════════════════════════════════════════════════════════════════════════
print('[1/6] Generating: l2_error_over_time.png')

fig, ax = plt.subplots(figsize=(14, 6.0))
fig.subplots_adjust(bottom=0.26, top=0.86, left=0.08, right=0.78)

# Phase regions across the WHOLE session — transparent about what is what
ax.axvspan(0, INIT_END,            color=REGION_INIT,   alpha=0.9, lw=0, zorder=0)
ax.axvspan(INIT_END, T_TAKEOFF,    color=REGION_IDLE,   alpha=0.9, lw=0, zorder=0)
ax.axvspan(T_TAKEOFF, T_LANDING,   color=REGION_FLIGHT, alpha=0.9, lw=0, zorder=0)
ax.axvspan(T_LANDING, DURATION,    color=REGION_IDLE,   alpha=0.9, lw=0, zorder=0)

# Log y-axis so the cm-level flight error AND the metre-level dropout are BOTH
# visible — a linear axis crushes the 0.047 m flight result onto the x-axis.
ax.set_yscale('log')

ax.plot(elapsed, raw_err, color=C_RAW, lw=0.5, alpha=0.18, zorder=2)
ax.plot(elapsed, rtk_err, color=C_RTK, lw=0.5, alpha=0.18, zorder=2)
ax.plot(elapsed, smooth(raw_err), color=C_RAW, lw=2.0, alpha=0.95, zorder=4,
        label='Raw GNSS error (3 s mean)')
ax.plot(elapsed, smooth(rtk_err), color=C_RTK, lw=2.2, alpha=0.95, zorder=5,
        label='RTK-corrected error (3 s mean)')

ax.set_ylim(0.01, max(float(raw_err.max()), 3.0) * 1.4)

# Phase boundary markers
ax.axvline(T_TAKEOFF, color=OK_GREEN, ls='--', lw=1.4, alpha=0.9, zorder=6)
ax.axvline(T_LANDING, color=OK_VERMIL, ls='--', lw=1.4, alpha=0.9, zorder=6)

# Engineering reference lines (RTK Fixed spec + GNSS spec), dotted, neutral
ax.axhline(0.03, color=OK_GREEN,  ls=':', lw=1.2, alpha=0.7, zorder=3)
ax.axhline(1.50, color=OK_VERMIL, ls=':', lw=1.2, alpha=0.5, zorder=3)

# Phase region labels along the top
ytxt = ax.get_ylim()[1] * 0.55
ax.text(INIT_END/2, ytxt, 'INITIALIZATION\n(stationary, scripted)',
        ha='center', va='center', fontsize=8.0, color=OK_VERMIL, fontweight='bold')
ax.text((INIT_END+T_TAKEOFF)/2, ytxt, 'Pre-flight hold\n(stationary)',
        ha='center', va='center', fontsize=8.0, color='#607D8B', fontweight='bold')
ax.text((T_TAKEOFF+T_LANDING)/2, ytxt, 'AUTONOMOUS FLIGHT',
        ha='center', va='center', fontsize=9.0, color=OK_GREEN, fontweight='bold')
ax.annotate('Take-off\nt = %.0f s' % T_TAKEOFF, xy=(T_TAKEOFF, 0.03),
            xytext=(T_TAKEOFF-150, 0.013), fontsize=8.0, color=OK_GREEN, ha='center',
            arrowprops=dict(arrowstyle='->', color=OK_GREEN, lw=1.0))

# Correction-loss event annotation (explicitly tagged as INIT)
if np.isfinite(peak_t):
    # Placed in the open band between the RTK (~0.05 m) and raw (~2.4 m) lines,
    # clear of the phase-region labels at the top and the take-off marker below.
    ax.annotate('Correction-loss test\n(initialization, t≈%.0f s)' % peak_t,
                xy=(peak_t, peak_v), xytext=(165, 0.32),
                fontsize=8.0, color=STATUS_COLORS['CORRECTION_LOST'], ha='left', va='center',
                arrowprops=dict(arrowstyle='->', color=STATUS_COLORS['CORRECTION_LOST'],
                                lw=1.1, connectionstyle='arc3,rad=0.2'),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor=STATUS_COLORS['CORRECTION_LOST'], alpha=0.95, lw=0.8),
                zorder=10)

ax.set_xlim(0, DURATION)
ax.set_xlabel('Elapsed time (s)', labelpad=6)
ax.set_ylabel('3D positioning error (m, log scale)')
ax.set_title(
    'Positioning Error Across the Full Level 2 Session\n'
    'PX4 / Gazebo  |  Initialization (stationary) and autonomous flight shown separately',
    pad=8)
ax.grid(True, which='both', ls='--', lw=0.4, alpha=0.4)
ax.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0), fontsize=9.0,
          title='Signal', title_fontsize=9.5)

stats_text = (
    f'IN-FLIGHT result (t = {T_TAKEOFF:.0f}–{T_LANDING:.0f} s, n = {m_flight.sum():,}):   '
    f'Raw GNSS μ = {raw_mean:.3f} m   |   RTK μ = {rtk_mean:.3f} m '
    f'({rtk_mean*100:.1f} cm)   |   improvement {IMP_PCT:.1f}%   |   RTK_FIXED {flight_fixed_pct:.0f}% of flight\n'
    f'Convergence and the correction-loss event occur during INITIALIZATION (t < {INIT_END:.0f} s, '
    f'stationary, scripted timing).   Whole-log mean ({rtk_mean_wholelog:.3f} m) is NOT used as the result.'
)
fig.text(0.08, 0.045, stats_text, fontsize=8.6, va='bottom', ha='left',
         bbox=dict(boxstyle='round,pad=0.45', facecolor='#F8F9FA',
                   alpha=0.95, edgecolor='#CCCCCC'))

plt.savefig(os.path.join(OUT_DIR, 'l2_error_over_time.png'))
plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# Figure 2 — RTK INITIALIZATION sequence (first 60 s, stationary)
# ═══════════════════════════════════════════════════════════════════════════
print('[2/6] Generating: l2_rtk_convergence.png')

WINDOW = 60.0
m60    = elapsed <= WINDOW
e_w, re_w, rk_w, st_w = elapsed[m60], raw_err[m60], rtk_err[m60], status[m60]

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(13, 7),
    gridspec_kw={'height_ratios': [5, 1], 'hspace': 0.08}, sharex=True)
fig.subplots_adjust(left=0.09, right=0.85, top=0.88, bottom=0.15)

shade_status(ax1, e_w, st_w, alpha=0.12)
ax1.plot(e_w, re_w, color=C_RAW, lw=1.8, alpha=0.9, marker='o', ms=2.5,
         markevery=8, label='Raw GNSS error')
ax1.plot(e_w, rk_w, color=C_RTK, lw=1.8, alpha=0.9, marker='s', ms=2.5,
         markevery=8, label='RTK-corrected error')

# Per-status noise-spec reference lines, labelled just OUTSIDE the right edge
# (blended transform: x in axes fraction, y in data) so the labels never cross
# the raw-error trace that fills the plot interior.
ax1.axhline(1.50, color=STATUS_COLORS['GNSS_ONLY'], ls=':', lw=1.1, alpha=0.7)
ax1.axhline(0.25, color=STATUS_COLORS['RTK_FLOAT'], ls=':', lw=1.1, alpha=0.7)
ax1.axhline(0.03, color=STATUS_COLORS['RTK_FIXED'], ls=':', lw=1.1, alpha=0.7)
_spec_tr = ax1.get_yaxis_transform()
ax1.text(1.015, 1.50, 'GNSS spec\n±1.50 m', transform=_spec_tr, color=STATUS_COLORS['GNSS_ONLY'],
         fontsize=8, va='center', ha='left', fontweight='bold', clip_on=False)
ax1.text(1.015, 0.25, 'Float spec\n±0.25 m', transform=_spec_tr, color=STATUS_COLORS['RTK_FLOAT'],
         fontsize=8, va='center', ha='left', fontweight='bold', clip_on=False)

y_top_c = max(float(rk_w.max()), float(re_w.max()), 8.0) * 1.12
ax1.set_ylim(0, y_top_c)

transitions = [
    (5.0,  'GNSS Only → RTK Float\n(t = 5 s)'),
    (15.0, 'RTK Float → RTK Fixed\n(t = 15 s)'),
    (45.0, 'Correction lost\n(t = 45 s)'),
    (50.0, 'Recovered → RTK Fixed\n(t = 50 s)'),
]
label_y = y_top_c * 0.965
for t_tr, lbl in transitions:
    ax1.axvline(t_tr, color='#7F8C8D', ls='--', lw=1.0, zorder=1)
    # Send the t=45 'Correction lost' label LEFT (into the clear RTK Fixed band)
    # and the t=50 'Recovered' label RIGHT, so the two never overlap.
    ha, xoff = ('right', t_tr - 0.6) if t_tr == 45.0 else ('left', t_tr + 0.6)
    ax1.text(xoff, label_y, lbl, fontsize=7.8, color='#333333', va='top', ha=ha,
             bbox=dict(boxstyle='round,pad=0.26', facecolor='white',
                       alpha=0.9, edgecolor='#BBBBBB', lw=0.7))

ax1.set_ylabel('3D positioning error (m)')
ax1.set_xlim(0, WINDOW)
ax1.grid(True, ls='--', lw=0.4, alpha=0.5)
ax1.set_title(
    'RTK Initialization Sequence — Convergence and Correction-Loss Recovery\n'
    'Level 2  |  Stationary, pre-flight (t < 50 s)  |  Transition timing is scripted '
    '(state-machine demonstration, not real ambiguity resolution)', pad=10)
# Raw/RTK key placed BELOW the status strip so it never covers the transition
# labels at the top of the plot. (Spec lines are labelled at the right edge.)
fig.legend(handles=[Line2D([0],[0], color=C_RAW, lw=1.8, marker='o', ms=4, label='Raw GNSS error'),
                    Line2D([0],[0], color=C_RTK, lw=1.8, marker='s', ms=4, label='RTK-corrected error')],
           loc='lower center', bbox_to_anchor=(0.47, 0.005), ncol=2, fontsize=9.5,
           framealpha=0.95, edgecolor='#CCCCCC')
panel_label(ax1, 'A', dx=-0.07, dy=1.02)

for s in ['GNSS_ONLY', 'RTK_FLOAT', 'RTK_FIXED', 'CORRECTION_LOST']:
    ax2.fill_between(e_w, 0, 1, where=(st_w == s), color=STATUS_COLORS[s], alpha=0.9)
for s, txt, xc in [('GNSS_ONLY', 'GNSS Only', 2.5), ('RTK_FLOAT', 'RTK Float', 10.0),
                   ('RTK_FIXED', 'RTK Fixed', 30.0), ('RTK_FIXED', 'RTK Fixed', 55.0)]:
    ax2.text(xc, 0.5, txt, ha='center', va='center', fontsize=8, fontweight='bold', color='white')
ax2.text(47.5, 0.5, 'Lost', ha='center', va='center', fontsize=6.5, fontweight='bold', color='white')
ax2.set_xlim(0, WINDOW); ax2.set_ylim(0, 1); ax2.set_yticks([])
ax2.set_ylabel('Fix status', fontsize=9)
ax2.set_xlabel('Elapsed time (s)')
ax2.spines['left'].set_visible(False)

plt.savefig(os.path.join(OUT_DIR, 'l2_rtk_convergence.png'))
plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# Figure 3 — In-flight error distribution (FLIGHT window)
# ═══════════════════════════════════════════════════════════════════════════
print('[3/6] Generating: l2_error_distribution.png')

fig, (axL, axR) = plt.subplots(1, 2, figsize=(14, 5.5))
fig.subplots_adjust(left=0.07, right=0.97, top=0.82, bottom=0.22, wspace=0.30)
fig.suptitle(
    'In-Flight Positioning Error Distribution — Raw GNSS vs RTK-Corrected\n'
    f'Level 2  |  Autonomous flight only (t = {T_TAKEOFF:.0f}–{T_LANDING:.0f} s, '
    f'100% RTK Fixed)',
    fontsize=12, fontweight='bold', y=0.98)

legend_handles_dist = [
    mpatches.Patch(color='#888888', alpha=0.30, label='Histogram (normalised density)'),
    Line2D([0],[0], color='#888888', lw=2.2, label='KDE fit'),
    Line2D([0],[0], color='#888888', ls='--', lw=1.8, label='Mean'),
    Line2D([0],[0], color='#888888', ls=':',  lw=1.8, label='Median'),
    Line2D([0],[0], color='#555555', ls='-.', lw=1.4, label='95th percentile'),
]
fig.legend(handles=legend_handles_dist, loc='lower center', bbox_to_anchor=(0.5, 0.0),
           ncol=5, fontsize=9.5, framealpha=0.93, edgecolor='#CCCCCC')

for ax, data, color, title, xmax, nbins, lab in [
    (axL, raw_flight, C_RAW, 'Raw GNSS positioning error\n(in-flight)', 8.0, 60, 'A'),
    (axR, rtk_flight, C_RTK, 'RTK-corrected positioning error\n(in-flight, RTK Fixed)', 0.5, 50, 'B'),
]:
    bins = np.linspace(0, xmax, nbins)
    ax.hist(data, bins=bins, color=color, alpha=0.30, density=True)
    kde = gaussian_kde(data, bw_method='scott')
    x_kde = np.linspace(0, xmax, 800)
    ax.plot(x_kde, kde(x_kde), color=color, lw=2.2)
    mean_v, median_v, p95_v = float(np.mean(data)), float(np.median(data)), float(np.percentile(data, 95))
    ax.axvline(mean_v,   color=color,     ls='--', lw=1.8)
    ax.axvline(median_v, color=color,     ls=':',  lw=1.8)
    ax.axvline(p95_v,    color='#555555', ls='-.', lw=1.4)
    ax.set_xlabel('3D positioning error (m)')
    ax.set_ylabel('Probability density')
    ax.set_title(title, fontsize=11, fontweight='bold', pad=6)
    ax.set_xlim(0, xmax); ax.set_ylim(bottom=0)
    ax.grid(True, ls='--', lw=0.4, alpha=0.5)
    stats_txt = (f'n = {len(data):,} samples\n'
                 f'Mean    = {mean_v:.4f} m\n'
                 f'Median  = {median_v:.4f} m\n'
                 f'Std     = {float(np.std(data)):.4f} m\n'
                 f'Min     = {float(np.min(data)):.4f} m\n'
                 f'Max     = {float(np.max(data)):.4f} m\n'
                 f'P95     = {p95_v:.4f} m')
    pos = (0.97, 0.97) if ax is axR else (0.97, 0.97)
    ax.text(pos[0], pos[1], stats_txt, transform=ax.transAxes, fontsize=8.8,
            va='top', ha='right', family='monospace',
            bbox=dict(boxstyle='round,pad=0.42', facecolor='white', alpha=0.93, edgecolor='#CCCCCC'))
    panel_label(ax, lab)

plt.savefig(os.path.join(OUT_DIR, 'l2_error_distribution.png'))
plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# Figure 4 — Flight trajectory
# ═══════════════════════════════════════════════════════════════════════════
print('[4/6] Generating: l2_trajectory.png')

fig, ax = plt.subplots(figsize=(9, 9))
fig.subplots_adjust(left=0.11, right=0.97, top=0.90, bottom=0.18)

fly = m_flight
step = max(1, fly.sum() // 1500)
gps_mask = fly & ~np.isnan(raw_x)
rtk_mask = fly & ~np.isnan(rtk_x)

ax.scatter(raw_x[gps_mask][::step], raw_y[gps_mask][::step],
           color=C_RAW, s=10, alpha=0.18, zorder=2, label='Raw GNSS (μ = %.2f m)' % raw_mean)
ax.scatter(rtk_x[rtk_mask][::step], rtk_y[rtk_mask][::step],
           color=C_RTK, s=10, alpha=0.5, zorder=3, label='RTK-corrected (μ = %.3f m)' % rtk_mean)
ax.plot(gt_x[fly], gt_y[fly], color=C_GT, lw=1.8, zorder=4, label='Ground-truth path')
ax.plot(gt_x[fly][0], gt_y[fly][0], 'o', color=OK_PURPLE, ms=11, zorder=5,
        label='Home (take-off / land)')

bbox_e = gt_x[fly].max() - gt_x[fly].min()
bbox_n = gt_y[fly].max() - gt_y[fly].min()
max_r  = horiz[fly].max()

ax.set_xlabel('East (m)  [ENU, relative to home]')
ax.set_ylabel('North (m)  [ENU, relative to home]')
ax.set_title(
    'UAV Flight Trajectory — Raw GNSS vs RTK-Corrected\n'
    f'Level 2 autonomous QGC mission  |  ≈{bbox_e:.0f} × {bbox_n:.0f} m area, '
    f'{max_r:.0f} m max range from home',
    pad=8)
ax.set_aspect('equal', adjustable='datalim')
ax.grid(True, ls='--', lw=0.4, alpha=0.5)
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.10), ncol=2, fontsize=9.5,
          framealpha=0.93, edgecolor='#CCCCCC')

plt.savefig(os.path.join(OUT_DIR, 'l2_trajectory.png'))
plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# Figure 5 — Performance summary (segment-aware, honest framing)
# ═══════════════════════════════════════════════════════════════════════════
print('[5/6] Generating: l2_accuracy_summary.png')

fig = plt.figure(figsize=(15, 5.8))
fig.subplots_adjust(left=0.06, right=0.97, top=0.82, bottom=0.18, wspace=0.34)
fig.suptitle('RTK Positioning Performance Summary — Level 2 PX4/Gazebo  |  In-flight result vs initialization',
             fontsize=12, fontweight='bold', y=0.97)
gs = GridSpec(1, 3, figure=fig, wspace=0.34)
axA, axB, axC = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])

# Panel A — mean RTK error by physical segment (init transient vs steady regimes)
seg_labels = ['Initialization\n(t<50 s, scripted)', 'Ground-idle\nFixed', 'In-flight\n(RTK Fixed)']
seg_data   = [rtk_err[m_init], rtk_err[m_idle_fixed], rtk_flight]
seg_means  = [float(np.mean(d)) for d in seg_data]
seg_stds   = [float(np.std(d))  for d in seg_data]
seg_cols   = [STATUS_COLORS['CORRECTION_LOST'], '#90A4AE', C_RTK]
y_top_A = max(m + s for m, s in zip(seg_means, seg_stds)) * 1.35
barsA = axA.bar(seg_labels, seg_means, yerr=seg_stds, color=seg_cols, alpha=0.85,
                capsize=5, error_kw=dict(elinewidth=1.4, capthick=1.4), edgecolor='white')
for bar, m, s in zip(barsA, seg_means, seg_stds):
    axA.text(bar.get_x() + bar.get_width()/2, m + s + y_top_A*0.03, f'{m:.3f} m',
             ha='center', va='bottom', fontsize=8.6, fontweight='bold')
axA.set_ylabel('Mean 3D positioning error (m)')
axA.set_title('Mean Error by Session Segment\n(error bars = ±1σ)', pad=6)
axA.set_ylim(0, y_top_A)
axA.grid(True, axis='y', ls='--', lw=0.4, alpha=0.5)
panel_label(axA, 'A')

# Panel B — fix-status composition DURING FLIGHT (replaces misleading whole-session pie)
flight_status_counts = {s: int(np.sum(status[m_flight] == s))
                        for s in STATUS_COLORS if np.sum(status[m_flight] == s) > 0}
labels_b = [f'{s.replace("_"," ")}\n({c:,} · {c/m_flight.sum()*100:.1f}%)'
            for s, c in flight_status_counts.items()]
colors_b = [STATUS_COLORS[s] for s in flight_status_counts]
wedges, _, autot = axB.pie(list(flight_status_counts.values()), colors=colors_b, startangle=90,
                           autopct=lambda p: f'{p:.0f}%' if p >= 3.5 else '',
                           pctdistance=0.7, wedgeprops=dict(edgecolor='white', linewidth=1.8))
for at in autot:
    at.set_fontsize(10); at.set_fontweight('bold'); at.set_color('white')
axB.legend(wedges, labels_b, loc='upper center', bbox_to_anchor=(0.5, -0.04),
           fontsize=9, framealpha=0.92, edgecolor='#CCCCCC')
axB.set_title(f'RTK Fix Status During Flight\n(n = {m_flight.sum():,}  |  '
              f'{T_LANDING-T_TAKEOFF:.0f} s airborne)', pad=6)
panel_label(axB, 'B', dx=-0.05)

# Panel C — in-flight improvement: raw vs RTK
cats = ['Raw GNSS', 'RTK-corrected']
vals = [raw_mean, rtk_mean]
cols = [C_RAW, C_RTK]
barsC = axC.bar(cats, vals, color=cols, alpha=0.85, edgecolor='white', width=0.55)
y_top_C = max(vals) * 1.25
for bar, v in zip(barsC, vals):
    axC.text(bar.get_x()+bar.get_width()/2, v + y_top_C*0.02, f'{v:.3f} m',
             ha='center', va='bottom', fontsize=9.5, fontweight='bold')
axC.set_ylabel('Mean in-flight error (m)')
axC.set_ylim(0, y_top_C)
axC.set_title('In-Flight Accuracy Improvement', pad=6)
axC.grid(True, axis='y', ls='--', lw=0.4, alpha=0.5)
axC.text(0.97, 0.95, f'{raw_mean:.3f} m → {rtk_mean:.3f} m\n= {IMP_PCT:.1f}% improvement\n'
                     f'({rtk_mean*100:.1f} cm, RTK Fixed)',
         transform=axC.transAxes, fontsize=9.2, va='top', ha='right',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#EBF5FB', edgecolor='#AED6F1', alpha=0.95))
panel_label(axC, 'C')

plt.savefig(os.path.join(OUT_DIR, 'l2_accuracy_summary.png'))
plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# Figure 6 — QGC ULog Cross-Validation
# ═══════════════════════════════════════════════════════════════════════════
print('[6/6] Generating: l2_qgc_crossval.png')

fig = plt.figure(figsize=(15, 6.0))
fig.subplots_adjust(left=0.06, right=0.97, top=0.84, bottom=0.16, wspace=0.34)
fig.suptitle(
    'QGC ULog Cross-Validation — PX4/Gazebo Flight Data vs RTK Positioning System\n'
    'Level 2  |  Independent ground-truth confirmation that the RTK module ran against a real PX4 flight',
    fontsize=12, fontweight='bold', y=0.98)
gs2 = GridSpec(1, 3, figure=fig, wspace=0.34)
axT, axB2, axA2 = fig.add_subplot(gs2[0]), fig.add_subplot(gs2[1]), fig.add_subplot(gs2[2])

step_ul = max(1, len(ul_gps_t) // 800)
axT.scatter(ul_gps_x[::step_ul], ul_gps_y[::step_ul], color=C_RAW, s=10, alpha=0.25,
            zorder=2, label='PX4 GPS positions')
axT.plot(ul_gt_x, ul_gt_y, color=C_GT, lw=1.8, zorder=4, label='Ground-truth path')
axT.plot(ul_gt_x[0], ul_gt_y[0], 'o', color=OK_PURPLE, ms=9, zorder=5)
nav_d = next(d for d in ulog.data_list if d.name == 'navigator_mission_item')
wp_x = (nav_d.data['longitude'] - UL_BASE_LON) * UL_M_LON
wp_y = (nav_d.data['latitude']  - UL_BASE_LAT) * 111320.0
axT.scatter(wp_x, wp_y, marker='^', color=OK_VERMIL, s=60, zorder=6,
            edgecolors='white', linewidths=0.6, label='Mission waypoints')
axT.set_xlabel('East (m)  [ENU, ULog origin]')
axT.set_ylabel('North (m)  [ENU, ULog origin]')
axT.set_title('ULog Ground-Truth Trajectory\n& PX4 GPS Positions', pad=6)
axT.set_aspect('equal', adjustable='datalim')
axT.grid(True, ls='--', lw=0.4, alpha=0.5)
axT.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=1, fontsize=9.0, framealpha=0.93)
panel_label(axT, 'A')

labels_3 = ['Raw GNSS\n(simulated)', 'PX4 GPS EPH\n(ULog reported)', 'RTK-corrected\n(in-flight)']
values_3 = [raw_mean, px4_eph_mean, rtk_mean]
colors_3 = [C_RAW, OK_ORANGE, STATUS_COLORS['RTK_FIXED']]
bars3 = axB2.bar(labels_3, values_3, color=colors_3, alpha=0.85, edgecolor='white', width=0.55)
y_top_3 = max(values_3) * 1.28
for bar, v in zip(bars3, values_3):
    axB2.text(bar.get_x()+bar.get_width()/2, v + y_top_3*0.02, f'{v:.3f} m',
              ha='center', va='bottom', fontsize=9.2, fontweight='bold')
axB2.set_ylabel('Positioning error / accuracy (m)')
axB2.set_title('Three-Way Accuracy Comparison\n(independent EPH cross-check)', pad=6)
axB2.set_ylim(0, y_top_3)
axB2.grid(True, axis='y', ls='--', lw=0.4, alpha=0.5)
axB2.text(0.5, -0.24,
          'Raw GNSS & RTK: measured error vs ground truth (CSV, in-flight)\n'
          'PX4 GPS EPH: PX4-reported horizontal accuracy estimate (1σ, ULog) — independent of our model',
          transform=axB2.transAxes, fontsize=7.6, ha='center', va='top', color='#555555', style='italic')
panel_label(axB2, 'B', dx=-0.05)

ul_t_rel = ul_gt_t - ul_gt_t[0]
axA2.plot(ul_t_rel, ul_gt_alt, color=C_GT, lw=1.8, label='Ground-truth altitude')
axA2.fill_between(ul_t_rel, ul_gt_alt.min(), ul_gt_alt, color=C_GT, alpha=0.07)
take_idx = int(np.argmax(ul_gt_alt > ul_gt_alt.min() + 2.0))
land_idx = len(ul_gt_alt) - 1 - int(np.argmax(ul_gt_alt[::-1] > ul_gt_alt.min() + 2.0))
axA2.axvline(ul_t_rel[take_idx], color=OK_GREEN,  ls='--', lw=1.0, alpha=0.8)
axA2.axvline(ul_t_rel[land_idx], color=OK_VERMIL, ls='--', lw=1.0, alpha=0.8)
axA2.text(ul_t_rel[take_idx]+1, ul_gt_alt.min()+3, 'Take-off', fontsize=8, color=OK_GREEN, va='bottom')
axA2.text(ul_t_rel[land_idx]-1, ul_gt_alt.min()+3, 'Land', fontsize=8, color=OK_VERMIL, va='bottom', ha='right')
axA2.set_xlabel('Elapsed time (s)  [ULog]')
axA2.set_ylabel('Altitude (m AMSL)')
axA2.set_title('UAV Altitude Profile — ULog\n(confirms a full mission was flown)', pad=6)
axA2.set_xlim(0, ul_t_rel[-1])
axA2.grid(True, ls='--', lw=0.4, alpha=0.5)
peak_alt = float(ul_gt_alt.max() - ul_gt_alt.min())
axA2.text(0.97, 0.05,
          f'PX4 GPS EPH = {px4_eph_mean:.2f} m\nRTK in-flight μ = {rtk_mean:.4f} m\n'
          f'RTK vs EPH: {(px4_eph_mean-rtk_mean)/px4_eph_mean*100:.0f}% tighter\n'
          f'Peak climb ≈ {peak_alt:.0f} m AGL',
          transform=axA2.transAxes, fontsize=8.4, va='bottom', ha='right',
          bbox=dict(boxstyle='round,pad=0.4', facecolor='#EBF5FB', edgecolor='#AED6F1', alpha=0.95))
panel_label(axA2, 'C')

plt.savefig(os.path.join(OUT_DIR, 'l2_qgc_crossval.png'))
plt.close()

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print('=' * 64)
print('Level 2 analysis complete (segmented reanalysis).')
print(f'  IN-FLIGHT (t={T_TAKEOFF:.0f}-{T_LANDING:.0f}s, n={m_flight.sum():,}):')
print(f'    Raw GNSS mean   : {raw_mean:.4f} m')
print(f'    RTK mean        : {rtk_mean:.4f} m  ({rtk_mean*100:.2f} cm)  [HEADLINE]')
print(f'    Improvement     : {IMP_PCT:.2f}%')
print(f'    RTK_FIXED       : {flight_fixed_pct:.1f}% of flight')
print(f'  Cross-check: PX4 GPS EPH (ULog) = {px4_eph_mean:.4f} m ; measured PX4 GPS err = {px4_err_mean:.4f} m')
print(f'  (whole-log RTK mean, reference only = {rtk_mean_wholelog:.4f} m)')
print()
for fn in sorted(os.listdir(OUT_DIR)):
    if fn.endswith('.png'):
        sz = os.path.getsize(os.path.join(OUT_DIR, fn)) / 1024
        print(f'  {fn}  ({sz:.0f} KB)')
print('=' * 64)
