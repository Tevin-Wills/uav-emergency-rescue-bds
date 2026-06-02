"""
Level 2 RTK Positioning — Analysis and Visualisation
=====================================================
Generates six publication-quality figures from the Level 2 PX4/Gazebo
simulation CSV log and the QGC ULog flight record.

Figures produced (saved to level2/):
  l2_error_over_time.png      — Full 1028 s error time series (4 status phases)
  l2_rtk_convergence.png      — First 60 s: convergence + CORRECTION_LOST event
  l2_error_distribution.png   — Error distribution: raw GNSS vs RTK-corrected
  l2_trajectory.png           — 2D top-down UAV trajectory (208 × 214 m area)
  l2_accuracy_summary.png     — Status pie, phase error bars, improvement summary
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

raw_mean = float(np.mean(raw_err))
rtk_mean = float(np.mean(rtk_err))
IMP_PCT  = (raw_mean - rtk_mean) / raw_mean * 100   # 96.7 %

# ENU conversion (base station from simulation config)
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
ul_gps_eph = gps_d.data['eph']          # reported horizontal accuracy estimate

ul_gt_t    = gt_d.data['timestamp'] / 1e6
ul_gt_lat  = gt_d.data['lat']
ul_gt_lon  = gt_d.data['lon']
ul_gt_alt  = gt_d.data['alt']

# Convert ULog positions to ENU (origin = first GT point)
UL_BASE_LAT = float(ul_gt_lat[0])
UL_BASE_LON = float(ul_gt_lon[0])
UL_M_LON    = 111320.0 * math.cos(math.radians(UL_BASE_LAT))

ul_gt_x  = (ul_gt_lon - UL_BASE_LON) * UL_M_LON
ul_gt_y  = (ul_gt_lat - UL_BASE_LAT) * 111320.0
ul_gps_x = (ul_gps_lon - UL_BASE_LON) * UL_M_LON
ul_gps_y = (ul_gps_lat - UL_BASE_LAT) * 111320.0

# Measured PX4 GPS error vs ground truth (interpolated)
gt_ix = interp1d(ul_gt_t, ul_gt_x, bounds_error=False, fill_value=np.nan)
gt_iy = interp1d(ul_gt_t, ul_gt_y, bounds_error=False, fill_value=np.nan)
px4_err_3d = np.sqrt((ul_gps_x - gt_ix(ul_gps_t))**2 +
                     (ul_gps_y - gt_iy(ul_gps_t))**2)
px4_err_mean = float(np.nanmean(px4_err_3d))
px4_eph_mean = float(np.mean(ul_gps_eph))   # 0.90 m reported

# Per-status masks
m_gnss = status == 'GNSS_ONLY'
m_float = status == 'RTK_FLOAT'
m_fixed = status == 'RTK_FIXED'
m_lost  = status == 'CORRECTION_LOST'

fixed_raw = raw_err[m_fixed]
fixed_rtk = rtk_err[m_fixed]

# CORRECTION_LOST peak
cl_t   = elapsed[m_lost]
cl_rtk = rtk_err[m_lost]
peak_t = float(cl_t[np.argmax(cl_rtk)])
peak_v = float(cl_rtk.max())

# ── Colour palette ────────────────────────────────────────────────────────────
STATUS_COLORS = {
    'GNSS_ONLY':       '#E67E22',
    'RTK_FLOAT':       '#F1C40F',
    'RTK_FIXED':       '#27AE60',
    'CORRECTION_LOST': '#8E44AD',
}
STATUS_LABELS = {
    'GNSS_ONLY':       'GNSS Only  (±1.50 m spec)',
    'RTK_FLOAT':       'RTK Float  (±0.25 m spec)',
    'RTK_FIXED':       'RTK Fixed  (±0.03 m spec)',
    'CORRECTION_LOST': 'Correction Lost',
}
C_RAW = '#C0392B'
C_RTK = '#2471A3'
C_GT  = '#1C2833'

# ── Global style ──────────────────────────────────────────────────────────────
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
def shade_status(ax, t, st, alpha=0.09):
    i = 0
    while i < len(st):
        s = st[i]; j = i
        while j < len(st) and st[j] == s:
            j += 1
        ax.axvspan(t[i], t[min(j, len(t)-1)],
                   color=STATUS_COLORS.get(s, '#BDC3C7'), alpha=alpha, linewidth=0)
        i = j

def status_patch_handles(present):
    return [mpatches.Patch(facecolor=STATUS_COLORS[s], alpha=0.55,
                           edgecolor='none', label=STATUS_LABELS[s])
            for s in STATUS_COLORS if s in present]

# ═══════════════════════════════════════════════════════════════════════════
# Figure 1 — Positioning Error Over Time
# ═══════════════════════════════════════════════════════════════════════════
print('[1/6] Generating: l2_error_over_time.png')

fig, ax = plt.subplots(figsize=(14, 5.8))
fig.subplots_adjust(bottom=0.24, top=0.88, left=0.08, right=0.97)

shade_status(ax, elapsed, status, alpha=0.09)

W = 30
raw_sm = np.convolve(raw_err, np.ones(W)/W, mode='same')
rtk_sm = np.convolve(rtk_err, np.ones(W)/W, mode='same')

ax.plot(elapsed, raw_err, color=C_RAW, lw=0.5, alpha=0.15, zorder=2)
ax.plot(elapsed, rtk_err, color=C_RTK, lw=0.5, alpha=0.15, zorder=2)
ax.plot(elapsed, raw_sm,  color=C_RAW, lw=2.0, alpha=0.95, zorder=3,
        label='Raw GNSS Error (3 s mean)')
ax.plot(elapsed, rtk_sm,  color=C_RTK, lw=2.0, alpha=0.95, zorder=3,
        label='RTK-Corrected Error (3 s mean)')

# Mean reference lines
ax.axhline(raw_mean, color=C_RAW, ls=':', lw=1.3, alpha=0.70, zorder=1)
ax.axhline(rtk_mean, color=C_RTK, ls=':', lw=1.3, alpha=0.70, zorder=1)

# Spec reference lines
ax.axhline(1.50, color=STATUS_COLORS['GNSS_ONLY'],       ls='--', lw=0.9, alpha=0.50, zorder=1)
ax.axhline(0.25, color=STATUS_COLORS['RTK_FLOAT'],        ls='--', lw=0.9, alpha=0.50, zorder=1)
ax.axhline(0.03, color=STATUS_COLORS['RTK_FIXED'],        ls='--', lw=0.9, alpha=0.50, zorder=1)

# CORRECTION_LOST spike annotation — arrow pointing to the peak
y_max = max(raw_err.max(), rtk_err.max()) * 1.12
ax.set_ylim(0, y_max)
ax.annotate(
    f'Correction Lost\nt = {peak_t:.0f} s\nErr = {peak_v:.2f} m',
    xy=(peak_t, peak_v),
    xytext=(peak_t + 40, peak_v * 0.80),
    fontsize=8.5, color=STATUS_COLORS['CORRECTION_LOST'],
    ha='left', va='center',
    arrowprops=dict(arrowstyle='->', color=STATUS_COLORS['CORRECTION_LOST'],
                    lw=1.2, connectionstyle='arc3,rad=-0.2'),
    bbox=dict(boxstyle='round,pad=0.32', facecolor='white',
              edgecolor=STATUS_COLORS['CORRECTION_LOST'], alpha=0.90, linewidth=0.9))

ax.set_xlim(0, DURATION)
ax.set_xlabel('Elapsed Time (s)', labelpad=6)
ax.set_ylabel('3D Positioning Error (m)')
ax.set_title(
    'RTK Positioning Error Over Time\n'
    'Level 2 — PX4 / Gazebo Simulation  |  QGC Autonomous Mission  |  208 × 214 m Coverage',
    pad=8)
ax.grid(True, ls='--', lw=0.4, alpha=0.45)

# Single combined legend — upper right
data_handles = [
    Line2D([0],[0], color=C_RAW, lw=2.0, label='Raw GNSS Error (3 s mean)'),
    Line2D([0],[0], color=C_RTK, lw=2.0, label='RTK-Corrected Error (3 s mean)'),
    Line2D([0],[0], color='#555555', ls=':', lw=1.3, alpha=0.8,
           label=f'Overall mean  (raw {raw_mean:.3f} m  |  RTK {rtk_mean:.3f} m)'),
]
ax.legend(handles=data_handles + status_patch_handles(set(status)),
          loc='upper right', fontsize=9.0, framealpha=0.93,
          title='Signal  /  RTK Fix Status', title_fontsize=9.0)

# Stats box in figure bottom margin — zero overlap with data
stats_text = (
    f'Samples: {N:,}   |   Duration: {DURATION:.0f} s   |   '
    f'Raw GNSS: μ = {raw_mean:.3f} m, σ = {np.std(raw_err):.3f} m   |   '
    f'RTK-Corrected: μ = {rtk_mean:.3f} m, σ = {np.std(rtk_err):.3f} m   |   '
    f'Accuracy improvement: {IMP_PCT:.1f}%'
)
fig.text(0.08, 0.04, stats_text, fontsize=8.8, va='bottom', ha='left',
         bbox=dict(boxstyle='round,pad=0.45', facecolor='#F8F9FA',
                   alpha=0.95, edgecolor='#CCCCCC'))

plt.savefig(os.path.join(OUT_DIR, 'l2_error_over_time.png'))
plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# Figure 2 — RTK Convergence (first 60 s)
# ═══════════════════════════════════════════════════════════════════════════
print('[2/6] Generating: l2_rtk_convergence.png')

WINDOW  = 60.0
m60     = elapsed <= WINDOW
e_w     = elapsed[m60]
re_w    = raw_err[m60]
rk_w    = rtk_err[m60]
st_w    = status[m60]

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(13, 7),
    gridspec_kw={'height_ratios': [5, 1], 'hspace': 0.06},
    sharex=True)
fig.subplots_adjust(left=0.09, right=0.97, top=0.90, bottom=0.10)

# ── Top panel ──
shade_status(ax1, e_w, st_w, alpha=0.11)
ax1.plot(e_w, re_w, color=C_RAW, lw=1.6, alpha=0.88, label='Raw GNSS Error')
ax1.plot(e_w, rk_w, color=C_RTK, lw=1.6, alpha=0.88, label='RTK-Corrected Error')

ax1.axhline(1.50, color=STATUS_COLORS['GNSS_ONLY'], ls='--', lw=1.0, alpha=0.65)
ax1.axhline(0.25, color=STATUS_COLORS['RTK_FLOAT'],  ls='--', lw=1.0, alpha=0.65)
ax1.axhline(0.03, color=STATUS_COLORS['RTK_FIXED'],  ls='--', lw=1.0, alpha=0.65)

ax1.text(59.2, 1.55, '± 1.50 m', color=STATUS_COLORS['GNSS_ONLY'],
         fontsize=8.0, ha='right', va='bottom')
ax1.text(59.2, 0.28, '± 0.25 m', color=STATUS_COLORS['RTK_FLOAT'],
         fontsize=8.0, ha='right', va='bottom')

y_top_c = max(float(rk_w.max()), float(re_w.max()), 8.0) * 1.10
ax1.set_ylim(0, y_top_c)

# Transition markers at all four phase changes
transitions = [
    (5.0,  'GNSS Only → RTK Float\n(t = 5 s)'),
    (15.0, 'RTK Float → RTK Fixed\n(t = 15 s)'),
    (45.0, 'RTK Fixed → Correction Lost\n(t = 45 s)'),
    (50.0, 'Correction Lost → RTK Fixed\n(t = 50 s)'),
]
label_y = y_top_c * 0.97
for t_tr, lbl in transitions:
    ax1.axvline(t_tr, color='#7F8C8D', ls=':', lw=1.2, zorder=1)
    ha = 'left'
    xoff = t_tr + 0.5
    # The t=50s label sits close to t=45s — shift it left
    if t_tr == 50.0:
        ha = 'right'
        xoff = t_tr - 0.5
    ax1.text(xoff, label_y, lbl,
             fontsize=7.8, color='#333333', va='top', ha=ha,
             bbox=dict(boxstyle='round,pad=0.26', facecolor='white',
                       alpha=0.88, edgecolor='#BBBBBB', linewidth=0.8))

ax1.set_ylabel('3D Positioning Error (m)')
ax1.set_xlim(0, WINDOW)
ax1.grid(True, ls='--', lw=0.4, alpha=0.5)
ax1.set_title(
    'RTK Fix Convergence — First 60 Seconds\n'
    'Level 2 PX4/Gazebo Simulation  |  Includes CORRECTION_LOST Event at t = 45 – 50 s',
    pad=8)

data_h = [Line2D([0],[0], color=C_RAW, lw=1.6, label='Raw GNSS Error'),
          Line2D([0],[0], color=C_RTK, lw=1.6, label='RTK-Corrected Error')]
ax1.legend(handles=data_h + status_patch_handles(set(st_w)),
           ncol=3, loc='upper left', fontsize=9.0, framealpha=0.93)

# ── Bottom panel: status strip ──
for s in ['GNSS_ONLY', 'RTK_FLOAT', 'RTK_FIXED', 'CORRECTION_LOST']:
    ax2.fill_between(e_w, 0, 1, where=(st_w == s),
                     color=STATUS_COLORS[s], alpha=0.88)

# Text labels inside each band (skip CORRECTION_LOST — it is too narrow at 5 s)
for s, txt, xc in [('GNSS_ONLY',  'GNSS Only',  2.5),
                   ('RTK_FLOAT',  'RTK Float',  10.0),
                   ('RTK_FIXED',  'RTK Fixed',  30.0),
                   ('RTK_FIXED',  'RTK Fixed',  55.0)]:
    ax2.text(xc, 0.5, txt, ha='center', va='center',
             fontsize=8.0, fontweight='bold', color='white')
# Small label for CORRECTION_LOST (narrow band)
ax2.text(47.5, 0.5, 'Lost', ha='center', va='center',
         fontsize=6.5, fontweight='bold', color='white')

ax2.set_xlim(0, WINDOW)
ax2.set_ylim(0, 1)
ax2.set_yticks([])
ax2.set_xlabel('Elapsed Time (s)')
ax2.spines['left'].set_visible(False)
ax2.tick_params(axis='x', bottom=True)

plt.savefig(os.path.join(OUT_DIR, 'l2_rtk_convergence.png'))
plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# Figure 3 — Error Distribution
# ═══════════════════════════════════════════════════════════════════════════
print('[3/6] Generating: l2_error_distribution.png')

fig, (axL, axR) = plt.subplots(1, 2, figsize=(14, 5.5))
fig.subplots_adjust(left=0.07, right=0.97, top=0.83, bottom=0.20, wspace=0.32)
fig.suptitle(
    'Positioning Error Distribution — Raw GNSS vs RTK-Corrected\n'
    'Level 2 PX4/Gazebo Simulation  |  Samples from RTK_FIXED Period Only',
    fontsize=12, fontweight='bold', y=0.97)

# Shared legend below both panels
legend_handles_dist = [
    mpatches.Patch(color='#888888', alpha=0.30, label='Histogram (normalised density)'),
    Line2D([0],[0], color='#888888', lw=2.2, label='KDE fit'),
    Line2D([0],[0], color='#888888', ls='--', lw=1.8, label='Mean'),
    Line2D([0],[0], color='#888888', ls=':',  lw=1.8, label='Median'),
    Line2D([0],[0], color='#555555', ls='-.', lw=1.4, label='95th percentile'),
]
fig.legend(handles=legend_handles_dist,
           loc='upper center', bbox_to_anchor=(0.5, 0.08),
           ncol=5, fontsize=9.5, framealpha=0.93, edgecolor='#CCCCCC')

for ax, data, color, title, xmax, nbins in [
    (axL, fixed_raw, C_RAW, 'Raw GNSS Positioning Error\n(RTK_FIXED period)', 8.0, 60),
    (axR, fixed_rtk, C_RTK, 'RTK-Corrected Positioning Error\n(RTK_FIXED period)', 0.5, 50),
]:
    bins = np.linspace(0, xmax, nbins)
    ax.hist(data, bins=bins, color=color, alpha=0.28, density=True)

    kde   = gaussian_kde(data, bw_method='scott')
    x_kde = np.linspace(0, xmax, 800)
    ax.plot(x_kde, kde(x_kde), color=color, lw=2.2)

    mean_v   = float(np.mean(data))
    median_v = float(np.median(data))
    p95_v    = float(np.percentile(data, 95))

    ax.axvline(mean_v,   color=color,     ls='--', lw=1.8)
    ax.axvline(median_v, color=color,     ls=':',  lw=1.8)
    ax.axvline(p95_v,    color='#555555', ls='-.', lw=1.4)

    ax.set_xlabel('3D Positioning Error (m)')
    ax.set_ylabel('Probability Density')
    ax.set_title(title, fontsize=11, fontweight='bold', pad=6)
    ax.set_xlim(0, xmax)
    ax.set_ylim(bottom=0)
    ax.grid(True, ls='--', lw=0.4, alpha=0.5)

    stats_txt = (f'n = {len(data):,} samples\n'
                 f'Mean    = {mean_v:.4f} m\n'
                 f'Std     = {float(np.std(data)):.4f} m\n'
                 f'Min     = {float(np.min(data)):.4f} m\n'
                 f'Max     = {float(np.max(data)):.4f} m\n'
                 f'P95     = {p95_v:.4f} m')

    # Raw GNSS: data starts at 0.07 m → KDE near-zero at x=0 → upper-LEFT safe
    # RTK: KDE peaks at x≈0.047 m, zero at x=0.25 m → upper-RIGHT safe
    if ax is axL:
        ax.text(0.03, 0.97, stats_txt, transform=ax.transAxes,
                fontsize=8.8, va='top', ha='left',
                bbox=dict(boxstyle='round,pad=0.42', facecolor='white',
                          alpha=0.93, edgecolor='#CCCCCC'))
    else:
        ax.text(0.97, 0.97, stats_txt, transform=ax.transAxes,
                fontsize=8.8, va='top', ha='right',
                bbox=dict(boxstyle='round,pad=0.42', facecolor='white',
                          alpha=0.93, edgecolor='#CCCCCC'))

plt.savefig(os.path.join(OUT_DIR, 'l2_error_distribution.png'))
plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# Figure 4 — UAV Trajectory
# ═══════════════════════════════════════════════════════════════════════════
print('[4/6] Generating: l2_trajectory.png')

fig, ax = plt.subplots(figsize=(9, 9))
fig.subplots_adjust(left=0.11, right=0.97, top=0.91, bottom=0.18)

step     = max(1, N // 1500)
gps_mask = ~np.isnan(raw_x)
rtk_mask = ~np.isnan(rtk_x)

ax.scatter(raw_x[gps_mask][::step], raw_y[gps_mask][::step],
           color=C_RAW, s=8, alpha=0.18, zorder=2)
ax.scatter(rtk_x[rtk_mask][::step], rtk_y[rtk_mask][::step],
           color=C_RTK, s=8, alpha=0.45, zorder=3)
ax.plot(gt_x, gt_y, color=C_GT, lw=1.6, zorder=4)

# Start marker
ax.plot(gt_x[0], gt_y[0], 'o', color='#8E44AD', ms=9, zorder=5)

# Home / end position label
ax.text(gt_x[0] + 4, gt_y[0] + 3, 'Home\n(takeoff/land)',
        fontsize=8.0, color='#8E44AD', va='bottom', ha='left')

ax.set_xlabel('East (m)  [relative to base station]')
ax.set_ylabel('North (m)  [relative to base station]')
ax.set_title(
    'UAV Flight Trajectory — Positioning Comparison\n'
    'Level 2 PX4/Gazebo Simulation  |  Autonomous QGC Mission  |  208 × 214 m Coverage Area',
    pad=8)
ax.set_aspect('equal', adjustable='datalim')
ax.grid(True, ls='--', lw=0.4, alpha=0.5)

legend_handles_traj = [
    Line2D([0],[0], color=C_GT, lw=1.8, label='Ground Truth Path'),
    mpatches.Patch(color=C_RTK, alpha=0.55,
                   label=f'RTK-Corrected  (μ err = {np.mean(fixed_rtk):.3f} m, RTK Fixed)'),
    mpatches.Patch(color=C_RAW, alpha=0.35,
                   label=f'Raw GNSS  (μ err = {raw_mean:.2f} m)'),
    Line2D([0],[0], marker='o', color='w', markerfacecolor='#8E44AD',
           ms=9, label='Home / Takeoff Point'),
]
ax.legend(handles=legend_handles_traj,
          loc='upper center', bbox_to_anchor=(0.5, -0.10),
          ncol=2, fontsize=9.5, framealpha=0.93, edgecolor='#CCCCCC')

plt.savefig(os.path.join(OUT_DIR, 'l2_trajectory.png'))
plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# Figure 5 — Accuracy Summary
# ═══════════════════════════════════════════════════════════════════════════
print('[5/6] Generating: l2_accuracy_summary.png')

fig = plt.figure(figsize=(15, 5.8))
fig.subplots_adjust(left=0.06, right=0.97, top=0.84, bottom=0.14, wspace=0.42)
fig.suptitle('RTK Positioning Performance Summary — Level 2 PX4/Gazebo Simulation',
             fontsize=12, fontweight='bold', y=0.97)

gs  = GridSpec(1, 3, figure=fig, wspace=0.42)
axA = fig.add_subplot(gs[0])
axB = fig.add_subplot(gs[1])
axC = fig.add_subplot(gs[2])

# ── Panel A: Grouped bar — raw vs RTK per phase ─────────────────────────────
categories = ['All Samples', 'RTK Float\n(5–15 s)', 'RTK Fixed\n(≥ 15 s)']
raw_m_A = [np.mean(raw_err), np.mean(raw_err[m_float]), np.mean(raw_err[m_fixed])]
rtk_m_A = [np.mean(rtk_err), np.mean(rtk_err[m_float]), np.mean(rtk_err[m_fixed])]

x = np.arange(len(categories)); w = 0.35
bar_c_rtk = [C_RTK, STATUS_COLORS['RTK_FLOAT'], STATUS_COLORS['RTK_FIXED']]
b1 = axA.bar(x - w/2, raw_m_A, w, color=C_RAW, alpha=0.82, edgecolor='white', label='Raw GNSS')
b2 = axA.bar(x + w/2, rtk_m_A, w, color=bar_c_rtk, alpha=0.85, edgecolor='white',
             label='RTK-Corrected')

y_top_A = max(raw_m_A) * 1.28
for bars, means in [(b1, raw_m_A), (b2, rtk_m_A)]:
    for bar, m in zip(bars, means):
        axA.text(bar.get_x() + bar.get_width()/2, m + y_top_A * 0.025,
                 f'{m:.3f}', ha='center', va='bottom', fontsize=8.5, fontweight='bold')

axA.set_xticks(x)
axA.set_xticklabels(categories, fontsize=9.5)
axA.set_ylabel('Mean 3D Positioning Error (m)')
axA.set_title('Mean Error by Fix Phase', pad=6)
axA.set_ylim(0, y_top_A)
axA.grid(True, axis='y', ls='--', lw=0.4, alpha=0.5)
axA.legend(fontsize=9.0, loc='upper right')

# ── Panel B: Fix status pie (4 slices) ─────────────────────────────────────
status_counts = {s: int(np.sum(status == s)) for s in STATUS_COLORS if np.sum(status == s) > 0}
pie_labels    = [f'{s}\n({c:,} · {c/N*100:.1f}%)' for s, c in status_counts.items()]
pie_colors    = [STATUS_COLORS[s] for s in status_counts]

def safe_pct(pct):
    return f'{pct:.1f}%' if pct >= 3.5 else ''

wedges, _, autotexts = axB.pie(
    list(status_counts.values()),
    colors=pie_colors, startangle=90,
    autopct=safe_pct, pctdistance=0.68,
    wedgeprops=dict(edgecolor='white', linewidth=1.8))
for at in autotexts:
    at.set_fontsize(9.5); at.set_fontweight('bold'); at.set_color('white')

axB.legend(wedges, pie_labels,
           loc='upper center', bbox_to_anchor=(0.5, -0.08),
           fontsize=8.5, ncol=1, framealpha=0.92, edgecolor='#CCCCCC')
axB.set_title(f'RTK Fix Status Distribution\n(n = {N:,}  |  {DURATION:.0f} s total)', pad=6)

# ── Panel C: RTK-corrected error per phase ──────────────────────────────────
phase_labels = ['GNSS Only\n(0–5 s)', 'RTK Float\n(5–15 s)',
                'RTK Fixed\n(≥ 15 s)', 'Corr. Lost\n(45–50 s)']
phase_masks  = [m_gnss, m_float, m_fixed, m_lost]
phase_colors = [STATUS_COLORS[s] for s in
                ['GNSS_ONLY','RTK_FLOAT','RTK_FIXED','CORRECTION_LOST']]
phase_means  = [np.mean(rtk_err[m]) if m.sum() > 0 else 0.0 for m in phase_masks]
phase_stds   = [np.std(rtk_err[m])  if m.sum() > 0 else 0.0 for m in phase_masks]

y_top_C = max(m + s for m, s in zip(phase_means, phase_stds)) * 1.38
bars_C = axC.bar(phase_labels, phase_means, yerr=phase_stds,
                 color=phase_colors, alpha=0.84, capsize=5,
                 error_kw=dict(elinewidth=1.4, capthick=1.4), edgecolor='white')

for bar, m, s in zip(bars_C, phase_means, phase_stds):
    axC.text(bar.get_x() + bar.get_width()/2, m + s + y_top_C * 0.03,
             f'{m:.3f} m', ha='center', va='bottom', fontsize=8.5, fontweight='bold')

axC.set_ylabel('RTK-Corrected Error (m)')
axC.set_title('RTK-Corrected Error per Phase\n(Error bars = ± 1 σ)', pad=6)
axC.set_ylim(0, y_top_C)
axC.grid(True, axis='y', ls='--', lw=0.4, alpha=0.5)

axC.text(0.97, 0.97,
         f'Overall improvement\n{raw_mean:.3f} m → {rtk_mean:.3f} m\n= {IMP_PCT:.1f}%',
         transform=axC.transAxes, fontsize=8.8, va='top', ha='right',
         bbox=dict(boxstyle='round,pad=0.40', facecolor='#EBF5FB',
                   edgecolor='#AED6F1', alpha=0.95))

plt.savefig(os.path.join(OUT_DIR, 'l2_accuracy_summary.png'))
plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# Figure 6 — QGC ULog Cross-Validation
# ═══════════════════════════════════════════════════════════════════════════
print('[6/6] Generating: l2_qgc_crossval.png')

fig = plt.figure(figsize=(15, 6.0))
fig.subplots_adjust(left=0.06, right=0.97, top=0.85, bottom=0.14, wspace=0.38)
fig.suptitle(
    'QGC ULog Cross-Validation — PX4/Gazebo Flight Data vs RTK Positioning System\n'
    'Level 2 Simulation  |  166 s Autonomous Mission',
    fontsize=12, fontweight='bold', y=0.98)

gs2 = GridSpec(1, 3, figure=fig, wspace=0.38)
axT = fig.add_subplot(gs2[0])     # trajectory from ULog
axB2 = fig.add_subplot(gs2[1])    # 3-way accuracy bar chart
axA2 = fig.add_subplot(gs2[2])    # altitude profile from ULog

# ── Panel 1: ULog GT trajectory + GPS scatter ────────────────────────────────
step_ul = max(1, len(ul_gps_t) // 800)
axT.scatter(ul_gps_x[::step_ul], ul_gps_y[::step_ul],
            color=C_RAW, s=8, alpha=0.25, zorder=2, label='PX4 GPS Positions')
axT.plot(ul_gt_x, ul_gt_y, color=C_GT, lw=1.8, zorder=4, label='Ground Truth Path')
axT.plot(ul_gt_x[0], ul_gt_y[0], 'o', color='#8E44AD', ms=8, zorder=5)

# Mission waypoints from ULog
nav_d = next(d for d in ulog.data_list if d.name == 'navigator_mission_item')
wp_lat = nav_d.data['latitude']
wp_lon = nav_d.data['longitude']
wp_x   = (wp_lon - UL_BASE_LON) * UL_M_LON
wp_y   = (wp_lat - UL_BASE_LAT) * 111320.0
axT.scatter(wp_x, wp_y, marker='^', color='#E74C3C', s=55, zorder=6,
            label='Mission Waypoints', edgecolors='white', linewidths=0.6)

axT.set_xlabel('East (m)  [ENU, ULog origin]')
axT.set_ylabel('North (m)  [ENU, ULog origin]')
axT.set_title('ULog Ground Truth Trajectory\n& PX4 GPS Positions', pad=6)
axT.set_aspect('equal', adjustable='datalim')
axT.grid(True, ls='--', lw=0.4, alpha=0.5)
axT.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12),
           ncol=1, fontsize=9.0, framealpha=0.93)

# ── Panel 2: 3-way accuracy bar chart ───────────────────────────────────────
labels_3 = ['Raw GNSS\n(simulated)', 'PX4 GPS\n(EPH reported)', 'RTK-Corrected\n(RTK Fixed)']
values_3  = [raw_mean, px4_eph_mean, float(np.mean(fixed_rtk))]
colors_3  = [C_RAW, '#E67E22', STATUS_COLORS['RTK_FIXED']]

bars_3 = axB2.bar(labels_3, values_3, color=colors_3, alpha=0.84,
                  edgecolor='white', width=0.5)
y_top_3 = max(values_3) * 1.30
for bar, v in zip(bars_3, values_3):
    axB2.text(bar.get_x() + bar.get_width()/2, v + y_top_3 * 0.025,
              f'{v:.3f} m', ha='center', va='bottom', fontsize=9.0, fontweight='bold')

axB2.set_ylabel('Positioning Error / Accuracy (m)')
axB2.set_title('Three-Way Accuracy Comparison\n(ULog EPH vs Raw GNSS vs RTK)', pad=6)
axB2.set_ylim(0, y_top_3)
axB2.grid(True, axis='y', ls='--', lw=0.4, alpha=0.5)

# Footnote explaining each metric
axB2.text(0.50, -0.22,
          'Raw GNSS: measured error vs GT (Level 2 CSV)\n'
          'PX4 GPS EPH: reported uncertainty estimate (ULog)\n'
          'RTK Fixed: measured error vs GT (Level 2 CSV)',
          transform=axB2.transAxes, fontsize=7.5, ha='center', va='top',
          color='#555555', style='italic')

# ── Panel 3: UAV altitude profile from ULog ─────────────────────────────────
ul_t_rel = ul_gt_t - ul_gt_t[0]
axA2.plot(ul_t_rel, ul_gt_alt, color=C_GT, lw=1.8, label='Ground Truth Altitude')

# Mark takeoff and landing
take_idx = np.argmax(ul_gt_alt > 2.0)
land_idx = len(ul_gt_alt) - 1 - np.argmax(ul_gt_alt[::-1] > 2.0)
axA2.axvline(ul_t_rel[take_idx], color='#27AE60', ls='--', lw=1.0, alpha=0.75)
axA2.axvline(ul_t_rel[land_idx], color='#E74C3C', ls='--', lw=1.0, alpha=0.75)
axA2.text(ul_t_rel[take_idx] + 1, 2.5, 'Takeoff', fontsize=8.0,
          color='#27AE60', va='bottom')
axA2.text(ul_t_rel[land_idx] - 1, 2.5, 'Land', fontsize=8.0,
          color='#E74C3C', va='bottom', ha='right')

axA2.set_xlabel('Elapsed Time (s)')
axA2.set_ylabel('Altitude (m AMSL)')
axA2.set_title('UAV Altitude Profile — ULog\n(Confirms mission execution)', pad=6)
axA2.set_xlim(0, ul_t_rel[-1])
axA2.set_ylim(bottom=0)
axA2.grid(True, ls='--', lw=0.4, alpha=0.5)

# Stats annotation (EPH vs RTK) — in empty upper-right area of altitude plot
note = (f'PX4 GPS EPH = {px4_eph_mean:.2f} m\n'
        f'RTK Fixed μ = {np.mean(fixed_rtk):.4f} m\n'
        f'RTK improvement vs EPH:\n'
        f'{(px4_eph_mean - np.mean(fixed_rtk))/px4_eph_mean*100:.1f}%')
axA2.text(0.97, 0.97, note, transform=axA2.transAxes,
          fontsize=8.5, va='top', ha='right',
          bbox=dict(boxstyle='round,pad=0.40', facecolor='#EBF5FB',
                    edgecolor='#AED6F1', alpha=0.95))

plt.savefig(os.path.join(OUT_DIR, 'l2_qgc_crossval.png'))
plt.close()

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print('=' * 58)
print('Level 2 analysis complete.')
print(f'Improvement percentage: {IMP_PCT:.2f}%')
print(f'  Raw GNSS mean error : {raw_mean:.4f} m')
print(f'  RTK-corrected mean  : {rtk_mean:.4f} m')
print(f'  PX4 GPS EPH (ULog)  : {px4_eph_mean:.4f} m')
print(f'  PX4 GPS actual err  : {px4_err_mean:.4f} m')
print()
for fn in sorted(os.listdir(OUT_DIR)):
    if fn.endswith('.png'):
        sz = os.path.getsize(os.path.join(OUT_DIR, fn)) / 1024
        print(f'  {fn}  ({sz:.0f} KB)')
print('=' * 58)
