"""
Level 1 RTK Positioning — Analysis and Visualisation
=====================================================
Generates five publication-quality figures from the Level 1 standalone
simulation CSV log.

Figures produced (saved to level1/):
  l1_error_over_time.png      — Positioning error time series with status shading
  l1_rtk_convergence.png      — RTK status convergence window (first 60 s)
  l1_error_distribution.png   — Error distribution: raw GNSS vs RTK-corrected
  l1_trajectory.png           — UAV flight trajectory with positioning comparison
  l1_accuracy_summary.png     — Accuracy statistics summary

Usage:
    python3 analyse_level1.py
"""

import os
import csv
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec
from scipy.stats import gaussian_kde

# ── Paths ───────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR    = os.path.join(SCRIPT_DIR, '..', '..', 'logs', 'rtk_positioning', 'level1')
OUT_DIR    = os.path.join(SCRIPT_DIR, 'level1')
os.makedirs(OUT_DIR, exist_ok=True)

csvs = sorted(f for f in os.listdir(LOG_DIR) if f.startswith('rtk_level1') and f.endswith('.csv'))
if not csvs:
    raise FileNotFoundError(f'No Level 1 CSV found in {LOG_DIR}')
CSV_PATH = os.path.join(LOG_DIR, csvs[-1])
print(f'[analyse_level1] Reading: {CSV_PATH}')

# ── Load data ────────────────────────────────────────────────────────────────
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

# Improvement: correct formula from mean errors (not per-row CSV column)
raw_mean = np.mean(raw_err)
rtk_mean = np.mean(rtk_err)
IMP_PCT  = (raw_mean - rtk_mean) / raw_mean * 100   # ~95.8 %

# ENU conversion
BASE_LAT      = 39.981000
BASE_LON      = 116.344000
M_PER_DEG_LAT = 111320.0
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(BASE_LAT))

def wgs84_to_enu(lat, lon):
    return (lon - BASE_LON) * M_PER_DEG_LON, (lat - BASE_LAT) * M_PER_DEG_LAT

raw_x, raw_y = wgs84_to_enu(raw_lat, raw_lon)
rtk_x, rtk_y = wgs84_to_enu(rtk_lat, rtk_lon)

# ── Colour palette ───────────────────────────────────────────────────────────
STATUS_COLORS = {
    'GNSS_ONLY': '#E67E22',
    'RTK_FLOAT': '#F1C40F',
    'RTK_FIXED': '#27AE60',
}
STATUS_LABELS = {
    'GNSS_ONLY': 'GNSS Only  (±1.50 m spec)',
    'RTK_FLOAT': 'RTK Float  (±0.25 m spec)',
    'RTK_FIXED': 'RTK Fixed  (±0.03 m spec)',
}
C_RAW = '#C0392B'   # red  — raw GNSS
C_RTK = '#2471A3'   # blue — RTK corrected
C_GT  = '#1C2833'   # dark — ground truth

# ── Global rcParams ──────────────────────────────────────────────────────────
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

# ── Helpers ──────────────────────────────────────────────────────────────────
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
    return [mpatches.Patch(facecolor=STATUS_COLORS[s], alpha=0.55, edgecolor='none',
                           label=STATUS_LABELS[s])
            for s in STATUS_COLORS if s in present]

# ═══════════════════════════════════════════════════════════════════════════
# Figure 1 — Positioning Error Over Time
# ═══════════════════════════════════════════════════════════════════════════
print('[1/5] Generating: l1_error_over_time.png')

fig, ax = plt.subplots(figsize=(13, 5.8))
fig.subplots_adjust(bottom=0.24, top=0.88, left=0.08, right=0.98)

shade_status(ax, elapsed, status, alpha=0.09)

# Thin raw samples + 3 s rolling mean on top
W = 30
raw_sm = np.convolve(raw_err, np.ones(W)/W, mode='same')
rtk_sm = np.convolve(rtk_err, np.ones(W)/W, mode='same')

ax.plot(elapsed, raw_err, color=C_RAW, lw=0.5, alpha=0.18, zorder=2)
ax.plot(elapsed, rtk_err, color=C_RTK, lw=0.5, alpha=0.18, zorder=2)
ax.plot(elapsed, raw_sm,  color=C_RAW, lw=2.0, alpha=0.95, zorder=3,
        label='Raw GNSS Error (3 s mean)')
ax.plot(elapsed, rtk_sm,  color=C_RTK, lw=2.0, alpha=0.95, zorder=3,
        label='RTK-Corrected Error (3 s mean)')

# Mean reference lines — dotted, no inline text (values are in the stats box below)
ax.axhline(raw_mean, color=C_RAW, ls=':', lw=1.3, alpha=0.70, zorder=1)
ax.axhline(rtk_mean, color=C_RTK, ls=':', lw=1.3, alpha=0.70, zorder=1)

# Spec reference lines — subtle dashed, values captured in legend via STATUS_LABELS
ax.axhline(1.50, color=STATUS_COLORS['GNSS_ONLY'], ls='--', lw=0.9, alpha=0.55, zorder=1)
ax.axhline(0.25, color=STATUS_COLORS['RTK_FLOAT'],  ls='--', lw=0.9, alpha=0.55, zorder=1)
ax.axhline(0.03, color=STATUS_COLORS['RTK_FIXED'],  ls='--', lw=0.9, alpha=0.55, zorder=1)

y_max = raw_err.max() * 1.12
ax.set_xlim(0, DURATION)
ax.set_ylim(0, y_max)
ax.set_xlabel('Elapsed Time (s)', labelpad=6)
ax.set_ylabel('3D Positioning Error (m)')
ax.set_title(
    'RTK Positioning Error Over Time\n'
    'Level 1 — Standalone ROS 2 Simulation  |  50 × 50 m Square Path  |  30 m AGL',
    pad=8)
ax.grid(True, ls='--', lw=0.4, alpha=0.45)

# Single combined legend — upper right, well above the data cloud
data_handles = [
    Line2D([0],[0], color=C_RAW, lw=2.0, label='Raw GNSS Error (3 s mean)'),
    Line2D([0],[0], color=C_RTK, lw=2.0, label='RTK-Corrected Error (3 s mean)'),
    Line2D([0],[0], color='#555555', ls=':', lw=1.3, alpha=0.8,
           label=f'Overall mean  (raw {raw_mean:.3f} m  |  RTK {rtk_mean:.3f} m)'),
]
all_handles = data_handles + status_patch_handles(set(status))
ax.legend(handles=all_handles, loc='upper right', fontsize=9.0,
          framealpha=0.93, edgecolor='#CCCCCC',
          title='Signal  /  RTK Fix Status', title_fontsize=9.0)

# Stats box placed in the bottom margin of the FIGURE (not inside axes)
# This completely avoids overlap with any data line.
stats_text = (
    f'Samples: {N:,}   |   Duration: {DURATION:.0f} s   |   '
    f'Raw GNSS: μ = {raw_mean:.3f} m, σ = {np.std(raw_err):.3f} m   |   '
    f'RTK-Corrected: μ = {rtk_mean:.3f} m, σ = {np.std(rtk_err):.3f} m   |   '
    f'Accuracy improvement: {IMP_PCT:.1f}%'
)
fig.text(0.08, 0.04, stats_text, fontsize=8.8, va='bottom', ha='left',
         color='#222222',
         bbox=dict(boxstyle='round,pad=0.45', facecolor='#F8F9FA',
                   alpha=0.95, edgecolor='#CCCCCC'))

plt.savefig(os.path.join(OUT_DIR, 'l1_error_over_time.png'))
plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# Figure 2 — RTK Convergence (first 60 s)
# ═══════════════════════════════════════════════════════════════════════════
print('[2/5] Generating: l1_rtk_convergence.png')

WINDOW  = 60.0
mask_60 = elapsed <= WINDOW
e_w     = elapsed[mask_60]
re_w    = raw_err[mask_60]
rk_w    = rtk_err[mask_60]
st_w    = status[mask_60]

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(12, 7),
    gridspec_kw={'height_ratios': [5, 1], 'hspace': 0.06},
    sharex=True)
fig.subplots_adjust(left=0.09, right=0.97, top=0.90, bottom=0.10)

# ── Top: error time series ──
shade_status(ax1, e_w, st_w, alpha=0.11)
ax1.plot(e_w, re_w, color=C_RAW, lw=1.6, alpha=0.88, label='Raw GNSS Error')
ax1.plot(e_w, rk_w, color=C_RTK, lw=1.6, alpha=0.88, label='RTK-Corrected Error')

# Spec reference lines
ax1.axhline(1.50, color=STATUS_COLORS['GNSS_ONLY'], ls='--', lw=1.0, alpha=0.65)
ax1.axhline(0.25, color=STATUS_COLORS['RTK_FLOAT'],  ls='--', lw=1.0, alpha=0.65)
ax1.axhline(0.03, color=STATUS_COLORS['RTK_FIXED'],  ls='--', lw=1.0, alpha=0.65)

# Spec labels — only the two that have enough vertical clearance from each other.
# The ±0.03 m line is too close to ±0.25 m at this y-scale; its value is in the legend.
ax1.text(59.0, 1.55, '± 1.50 m spec',
         color=STATUS_COLORS['GNSS_ONLY'], fontsize=8.0, ha='right', va='bottom')
ax1.text(59.0, 0.28, '± 0.25 m spec',
         color=STATUS_COLORS['RTK_FLOAT'],  fontsize=8.0, ha='right', va='bottom')

y_top_conv = max(float(re_w.max()), 7.0) * 1.10
ax1.set_ylim(0, y_top_conv)

# Phase transition markers — vertical dotted lines with boxed labels at top
for t_tr, label_txt in [(5.0, 'GNSS Only → RTK Float\n(t = 5 s)'),
                         (15.0, 'RTK Float → RTK Fixed\n(t = 15 s)')]:
    ax1.axvline(t_tr, color='#7F8C8D', ls=':', lw=1.2, zorder=1)
    ax1.text(t_tr + 0.6, y_top_conv * 0.97, label_txt,
             fontsize=8.2, color='#333333', va='top', ha='left',
             bbox=dict(boxstyle='round,pad=0.28', facecolor='white',
                       alpha=0.88, edgecolor='#BBBBBB', linewidth=0.8))

ax1.set_ylabel('3D Positioning Error (m)')
ax1.set_xlim(0, WINDOW)
ax1.grid(True, ls='--', lw=0.4, alpha=0.5)
ax1.set_title(
    'RTK Fix Convergence — First 60 Seconds\n'
    'Level 1 Standalone Simulation  |  GNSS Only → RTK Float → RTK Fixed',
    pad=8)

# Legend — data lines + status patches
data_h = [Line2D([0],[0], color=C_RAW, lw=1.6, label='Raw GNSS Error'),
          Line2D([0],[0], color=C_RTK, lw=1.6, label='RTK-Corrected Error')]
ax1.legend(handles=data_h + status_patch_handles({'GNSS_ONLY','RTK_FLOAT','RTK_FIXED'}),
           ncol=3, loc='upper left', fontsize=9.0, framealpha=0.93)

# ── Bottom: fix-status strip ──
for s in ['GNSS_ONLY', 'RTK_FLOAT', 'RTK_FIXED']:
    ax2.fill_between(e_w, 0, 1, where=(st_w == s),
                     color=STATUS_COLORS[s], alpha=0.88)

# Direct text labels centred in each band — avoids a legend on the strip
for s, txt, xc in [('GNSS_ONLY', 'GNSS Only',  2.5),
                   ('RTK_FLOAT', 'RTK Float',  10.0),
                   ('RTK_FIXED', 'RTK Fixed',  37.0)]:
    ax2.text(xc, 0.5, txt, ha='center', va='center',
             fontsize=8.5, fontweight='bold', color='white')

ax2.set_xlim(0, WINDOW)
ax2.set_ylim(0, 1)
ax2.set_yticks([])
ax2.set_xlabel('Elapsed Time (s)')
ax2.spines['left'].set_visible(False)
ax2.tick_params(axis='x', bottom=True)

plt.savefig(os.path.join(OUT_DIR, 'l1_rtk_convergence.png'))
plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# Figure 3 — Error Distribution
# ═══════════════════════════════════════════════════════════════════════════
print('[3/5] Generating: l1_error_distribution.png')

fixed_mask = status == 'RTK_FIXED'
raw_fixed  = raw_err[fixed_mask]
rtk_fixed  = rtk_err[fixed_mask]

fig, (axL, axR) = plt.subplots(1, 2, figsize=(14, 5.5))
fig.subplots_adjust(left=0.07, right=0.97, top=0.83, bottom=0.20, wspace=0.32)
fig.suptitle(
    'Positioning Error Distribution — Raw GNSS vs RTK-Corrected\n'
    'Level 1 Standalone Simulation  |  Samples from RTK_FIXED Period Only',
    fontsize=12, fontweight='bold', y=0.97)

# Shared legend below both panels
legend_handles = [
    mpatches.Patch(color='#888888', alpha=0.30, label='Histogram (normalised density)'),
    Line2D([0],[0], color='#888888', lw=2.2, label='KDE fit'),
    Line2D([0],[0], color='#888888', ls='--', lw=1.8, label='Mean'),
    Line2D([0],[0], color='#888888', ls=':',  lw=1.8, label='Median'),
    Line2D([0],[0], color='#555555', ls='-.', lw=1.4, label='95th percentile'),
]
fig.legend(handles=legend_handles,
           loc='upper center', bbox_to_anchor=(0.5, 0.08),
           ncol=5, fontsize=9.5, framealpha=0.93, edgecolor='#CCCCCC')

for ax, data, color, title, xmax, nbins in [
    (axL, raw_fixed, C_RAW, 'Raw GNSS Positioning Error\n(RTK_FIXED period)',   8.0, 60),
    (axR, rtk_fixed, C_RTK, 'RTK-Corrected Positioning Error\n(RTK_FIXED period)', 0.5, 50),
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

    if ax is axL:
        # Raw GNSS panel: KDE is near-zero at x=0 (data starts at 0.18 m)
        # → stats box safe at upper-LEFT
        ax.text(0.03, 0.97, stats_txt, transform=ax.transAxes,
                fontsize=8.8, va='top', ha='left',
                bbox=dict(boxstyle='round,pad=0.42', facecolor='white',
                          alpha=0.93, edgecolor='#CCCCCC'))
    else:
        # RTK panel: KDE peaks at x≈0.046 m — upper-LEFT is directly behind the peak.
        # KDE at x=0.25 m is essentially 0 → stats box safe at upper-RIGHT.
        ax.text(0.97, 0.97, stats_txt, transform=ax.transAxes,
                fontsize=8.8, va='top', ha='right',
                bbox=dict(boxstyle='round,pad=0.42', facecolor='white',
                          alpha=0.93, edgecolor='#CCCCCC'))

plt.savefig(os.path.join(OUT_DIR, 'l1_error_distribution.png'))
plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# Figure 4 — UAV Trajectory
# ═══════════════════════════════════════════════════════════════════════════
print('[4/5] Generating: l1_trajectory.png')

fig, ax = plt.subplots(figsize=(8, 9))
fig.subplots_adjust(left=0.12, right=0.97, top=0.91, bottom=0.18)

step     = max(1, N // 1200)
gps_mask = ~np.isnan(raw_x)
rtk_mask = ~np.isnan(rtk_x)

# Layer order: raw (bottom) → RTK (middle) → GT (top)
ax.scatter(raw_x[gps_mask][::step], raw_y[gps_mask][::step],
           color=C_RAW, s=10, alpha=0.18, zorder=2)
ax.scatter(rtk_x[rtk_mask][::step], rtk_y[rtk_mask][::step],
           color=C_RTK, s=10, alpha=0.48, zorder=3)
ax.plot(gt_x, gt_y, color=C_GT, lw=2.0, zorder=4)
ax.plot(gt_x[0], gt_y[0], 'o', color='#8E44AD', ms=9, zorder=5)

# Corner markers — derived from actual GT data extents, labels offset outside the corner
gx_min, gx_max = float(gt_x.min()), float(gt_x.max())
gy_min, gy_max = float(gt_y.min()), float(gt_y.max())
corners = [
    (gx_min, gy_min, 'SW', -7, -12),
    (gx_max, gy_min, 'SE', +4, -12),
    (gx_max, gy_max, 'NE', +4,  +5),
    (gx_min, gy_max, 'NW', -7,  +5),
]
for cx, cy, lbl, dx, dy in corners:
    ax.plot(cx, cy, 's', color=C_GT, ms=6, zorder=4)
    ax.text(cx + dx * 0.18, cy + dy * 0.18, lbl,
            fontsize=8.5, color=C_GT, fontweight='bold',
            ha='right' if dx < 0 else 'left',
            va='top'   if dy < 0 else 'bottom')

ax.set_xlabel('East (m)  [relative to base station]')
ax.set_ylabel('North (m)  [relative to base station]')
ax.set_title(
    'UAV Flight Trajectory — Positioning Comparison\n'
    'Level 1 Standalone Simulation  |  50 × 50 m Square Pattern  |  30 m AGL',
    pad=8)
ax.set_aspect('equal', adjustable='datalim')
ax.grid(True, ls='--', lw=0.4, alpha=0.5)

# Legend BELOW the axes — completely avoids the data area
legend_handles_traj = [
    Line2D([0],[0], color=C_GT,  lw=2.0,  label='Ground Truth Path'),
    mpatches.Patch(color=C_RTK, alpha=0.55, label=f'RTK-Corrected  (μ err = {rtk_mean:.2f} m)'),
    mpatches.Patch(color=C_RAW, alpha=0.35, label=f'Raw GNSS  (μ err = {raw_mean:.2f} m)'),
    Line2D([0],[0], marker='o', color='w', markerfacecolor='#8E44AD',
           ms=9, label='Start / End'),
]
ax.legend(handles=legend_handles_traj,
          loc='upper center', bbox_to_anchor=(0.5, -0.10),
          ncol=2, fontsize=9.5, framealpha=0.93, edgecolor='#CCCCCC')

plt.savefig(os.path.join(OUT_DIR, 'l1_trajectory.png'))
plt.close()

# ═══════════════════════════════════════════════════════════════════════════
# Figure 5 — Accuracy Summary
# ═══════════════════════════════════════════════════════════════════════════
print('[5/5] Generating: l1_accuracy_summary.png')

float_mask = status == 'RTK_FLOAT'

fig = plt.figure(figsize=(15, 5.8))
fig.subplots_adjust(left=0.06, right=0.97, top=0.84, bottom=0.14, wspace=0.40)
fig.suptitle('RTK Positioning Performance Summary — Level 1 Standalone Simulation',
             fontsize=12, fontweight='bold', y=0.97)

gs  = GridSpec(1, 3, figure=fig, wspace=0.40)
axA = fig.add_subplot(gs[0])
axB = fig.add_subplot(gs[1])
axC = fig.add_subplot(gs[2])

# ── Panel A: Grouped bar — raw GNSS vs RTK-corrected per phase ─────────────
categories = ['All Samples', 'RTK Float\n(5–15 s)', 'RTK Fixed\n(≥ 15 s)']
raw_m = [np.mean(raw_err), np.mean(raw_err[float_mask]), np.mean(raw_err[fixed_mask])]
rtk_m = [np.mean(rtk_err), np.mean(rtk_err[float_mask]), np.mean(rtk_err[fixed_mask])]

x = np.arange(len(categories))
w = 0.35
bar_colors_rtk = [C_RTK, STATUS_COLORS['RTK_FLOAT'], STATUS_COLORS['RTK_FIXED']]

b1 = axA.bar(x - w/2, raw_m, w, color=C_RAW, alpha=0.82, edgecolor='white', label='Raw GNSS')
b2 = axA.bar(x + w/2, rtk_m, w, color=bar_colors_rtk, alpha=0.85, edgecolor='white',
             label='RTK-Corrected')

y_top_A = max(raw_m) * 1.28
for bars, means in [(b1, raw_m), (b2, rtk_m)]:
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

# ── Panel B: Fix status pie ─────────────────────────────────────────────────
status_counts = {s: int(np.sum(status == s)) for s in STATUS_COLORS if np.sum(status == s) > 0}
pie_labels    = [f'{s}\n({c:,} samples, {c/N*100:.1f}%)' for s, c in status_counts.items()]
pie_colors    = [STATUS_COLORS[s] for s in status_counts]

def safe_pct(pct):
    return f'{pct:.1f}%' if pct >= 4.0 else ''

wedges, _, autotexts = axB.pie(
    list(status_counts.values()),
    colors=pie_colors, startangle=90,
    autopct=safe_pct, pctdistance=0.68,
    wedgeprops=dict(edgecolor='white', linewidth=1.8))
for at in autotexts:
    at.set_fontsize(9.5)
    at.set_fontweight('bold')
    at.set_color('white')

# Legend placed below the pie with explicit line-wrap labels
axB.legend(wedges, pie_labels,
           loc='upper center', bbox_to_anchor=(0.5, -0.08),
           fontsize=8.5, ncol=1, framealpha=0.92, edgecolor='#CCCCCC')
axB.set_title(f'RTK Fix Status Distribution\n(n = {N:,}  |  {DURATION:.0f} s total)', pad=6)

# ── Panel C: RTK-corrected error per fix phase ──────────────────────────────
phase_labels = ['GNSS Only\n(0–5 s)', 'RTK Float\n(5–15 s)', 'RTK Fixed\n(≥ 15 s)']
phase_masks  = [status == 'GNSS_ONLY', status == 'RTK_FLOAT', status == 'RTK_FIXED']
phase_colors = [STATUS_COLORS[s] for s in ['GNSS_ONLY', 'RTK_FLOAT', 'RTK_FIXED']]
phase_means  = [np.mean(rtk_err[m]) if m.sum() > 0 else 0.0 for m in phase_masks]
phase_stds   = [np.std(rtk_err[m])  if m.sum() > 0 else 0.0 for m in phase_masks]

y_top_C = max(m + s for m, s in zip(phase_means, phase_stds)) * 1.40
bars_C = axC.bar(phase_labels, phase_means, yerr=phase_stds,
                 color=phase_colors, alpha=0.84, capsize=5,
                 error_kw=dict(elinewidth=1.4, capthick=1.4), edgecolor='white')

for bar, m, s in zip(bars_C, phase_means, phase_stds):
    axC.text(bar.get_x() + bar.get_width()/2, m + s + y_top_C * 0.03,
             f'{m:.3f} m', ha='center', va='bottom', fontsize=9.0, fontweight='bold')

axC.set_ylabel('RTK-Corrected Error (m)')
axC.set_title('RTK-Corrected Error by Phase\n(Error bars = ± 1 σ)', pad=6)
axC.set_ylim(0, y_top_C)
axC.grid(True, axis='y', ls='--', lw=0.4, alpha=0.5)

axC.text(0.97, 0.97,
         f'Overall improvement\n'
         f'{raw_mean:.3f} m  →  {rtk_mean:.3f} m\n'
         f'= {IMP_PCT:.1f}% reduction',
         transform=axC.transAxes, fontsize=8.8, va='top', ha='right',
         bbox=dict(boxstyle='round,pad=0.40', facecolor='#EBF5FB',
                   edgecolor='#AED6F1', alpha=0.95))

plt.savefig(os.path.join(OUT_DIR, 'l1_accuracy_summary.png'))
plt.close()

# ── Summary ──────────────────────────────────────────────────────────────────
print()
print('=' * 58)
print('Level 1 analysis complete.')
print(f'Improvement percentage: {IMP_PCT:.2f}%')
print(f'  Raw GNSS mean error : {raw_mean:.4f} m')
print(f'  RTK-corrected mean  : {rtk_mean:.4f} m')
print()
for fn in sorted(os.listdir(OUT_DIR)):
    if fn.endswith('.png'):
        sz = os.path.getsize(os.path.join(OUT_DIR, fn)) / 1024
        print(f'  {fn}  ({sz:.0f} KB)')
print('=' * 58)
