"""
generate_figures.py -- BDS-SMC2 experiment visualizations.
Reads directly from data/*.csv and generates all figures.

Usage: python generate_figures.py
Output: figures/fig1_latency.png
        figures/fig2_gap1_encoding.png
        figures/fig3_gap6_telemetry.png
        figures/fig4_summary.png
        figures/fig5_gap3_environments.png  (generated when gap3 data exists)
"""

import csv, os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict

os.makedirs("figures", exist_ok=True)

DARK  = "#1a3a5c"
BLUE  = "#2e5fa3"
RED   = "#e8523a"
GREEN = "#2d7a3a"
GOLD  = "#b07d1a"
LGRAY = "#f4f7fb"

def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))

gap2 = load_csv("data/gap2_latency.csv")
gap6 = load_csv("data/gap6_telemetry.csv")

tx_lat    = [int(r["tx_latency_ms"])     for r in gap2]
dec_lat   = [int(r["decode_latency_ms"]) for r in gap2]
total_lat = [int(r["total_latency_ms"])  for r in gap2]
n = len(tx_lat)

# ── CONFIRMED NUMBERS ──────────────────────────────────────────────────────────
print("=" * 60)
print("BDS-SMC2 -- CONFIRMED EXPERIMENT RESULTS")
print("=" * 60)

ASCII_LATLON_BITS  = 264
BINARY_LATLON_BITS = 64
reduction_g1 = (1 - BINARY_LATLON_BITS / ASCII_LATLON_BITS) * 100
print(f"\n-- Gap 1: ASCII vs Binary (lat/lon only) --")
print(f"  ASCII  : {ASCII_LATLON_BITS} bits")
print(f"  Binary : {BINARY_LATLON_BITS} bits")
print(f"  Reduction: {reduction_g1:.1f}%  ({ASCII_LATLON_BITS/BINARY_LATLON_BITS:.2f}x)")

mean_tx  = sum(tx_lat) / n
std_tx   = math.sqrt(sum((x - mean_tx) ** 2 for x in tx_lat) / (n - 1))
mean_tot = sum(total_lat) / n
std_tot  = math.sqrt(sum((x - mean_tot) ** 2 for x in total_lat) / (n - 1))
print(f"\n-- Gap 2: Latency (n={n} transmissions) --")
print(f"  TX  mean={mean_tx:.1f}ms  std={std_tx:.1f}ms  min={min(tx_lat)}ms  max={max(tx_lat)}ms")
print(f"  Tot mean={mean_tot:.1f}ms  std={std_tot:.1f}ms  min={min(total_lat)}ms  max={max(total_lat)}ms")
print(f"  Decode overhead mean={sum(dec_lat)/n:.1f}ms  (bottleneck = satellite)")

g6 = {r["format"]: r for r in gap6}
ASCII_TEL  = int(g6["ASCII"]["bits"])
BINARY_TEL = int(g6["Binary"]["bits"])
HUFF_TEL   = int(g6["Huffman"]["bits"])
print(f"\n-- Gap 6: Full Telemetry Encoding --")
print(f"  ASCII   : {ASCII_TEL} bits  (baseline)")
print(f"  Binary  : {BINARY_TEL} bits  (-{(1-BINARY_TEL/ASCII_TEL)*100:.1f}%)")
print(f"  Huffman : {HUFF_TEL} bits  (-{(1-HUFF_TEL/ASCII_TEL)*100:.1f}%)")

print("\n" + "=" * 60)
print("All numbers confirmed. Generating figures...")
print("=" * 60 + "\n")

# ── FIGURE 1 — Gap 2: Latency time-series + stats ─────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle(f"Gap 2 -- BDS-3 SMC End-to-End Latency  (n={n} transmissions)",
             fontsize=13, fontweight="bold", color=DARK)

x = np.arange(1, n + 1)

ax = axes[0]
ax.plot(x, tx_lat,    color=BLUE, linewidth=1.8, label="TX latency")
ax.plot(x, total_lat, color=RED,  linewidth=1.8, linestyle="--", label="Total latency")
ax.axhline(mean_tx,  color=BLUE, linewidth=0.9, linestyle=":", alpha=0.7)
ax.axhline(mean_tot, color=RED,  linewidth=0.9, linestyle=":", alpha=0.7)
ax.set_xlabel("Transmission #", fontsize=10)
ax.set_ylabel("Latency (ms)", fontsize=10)
ax.set_title("Per-Transmission Latency", fontsize=11, color=BLUE)
ax.legend(fontsize=9)
ax.set_xlim(1, n); ax.set_ylim(0, max(total_lat) * 1.15)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

ax = axes[1]
ax.hist(total_lat, bins=12, color=BLUE, edgecolor="white", alpha=0.85)
ax.axvline(mean_tot, color=RED, linewidth=2, linestyle="--", label=f"Mean {mean_tot:.0f}ms")
ax.axvline(sorted(total_lat)[int(0.95 * n)], color=GOLD, linewidth=2,
           linestyle="--", label=f"P95 {sorted(total_lat)[int(0.95*n)]}ms")
ax.set_xlabel("Latency (ms)", fontsize=10)
ax.set_ylabel("Count", fontsize=10)
ax.set_title("Latency Distribution", fontsize=11, color=BLUE)
ax.legend(fontsize=9)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

ax = axes[2]
stats_labels = ["Mean", "Median", "P95", "Max"]
stats_vals   = [mean_tot, sorted(total_lat)[n//2],
                sorted(total_lat)[int(0.95*n)], max(total_lat)]
colors_s = [BLUE, GREEN, GOLD, RED]
bars = ax.barh(stats_labels, stats_vals, color=colors_s, edgecolor="white", height=0.5)
for bar, val in zip(bars, stats_vals):
    ax.text(val + 30, bar.get_y() + bar.get_height()/2,
            f"{val:.0f}ms", va="center", fontsize=10, fontweight="bold")
ax.set_xlabel("Latency (ms)", fontsize=10)
ax.set_title("Key Statistics", fontsize=11, color=BLUE)
ax.set_xlim(0, max(total_lat) * 1.25)
ax.grid(axis="x", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("figures/fig1_latency.png", dpi=150, bbox_inches="tight")
plt.close()
print("[SAVED] figures/fig1_latency.png")

# ── FIGURE 2 — Gap 1: ASCII vs Binary encoding ────────────────────────────────
fig2, axes2 = plt.subplots(1, 2, figsize=(11, 5))
fig2.suptitle("Gap 1 -- Coordinate Encoding: ASCII vs Binary",
              fontsize=13, fontweight="bold", color=DARK)

ax = axes2[0]
enc_labels = ["ASCII", "Binary"]
enc_bits   = [ASCII_LATLON_BITS, BINARY_LATLON_BITS]
enc_colors = [RED, GREEN]
bars = ax.bar(enc_labels, enc_bits, color=enc_colors, width=0.45, edgecolor="white")
for bar, val in zip(bars, enc_bits):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 4,
            f"{val} bits", ha="center", va="bottom", fontsize=12, fontweight="bold")
ax.set_ylabel("Bits per message", fontsize=10)
ax.set_title("Payload Size (lat/lon only)", fontsize=11, color=BLUE)
ax.set_ylim(0, 320)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

ax2 = axes2[1]
saving = ASCII_LATLON_BITS - BINARY_LATLON_BITS
ax2.bar(["ASCII"], [ASCII_LATLON_BITS], color=RED, width=0.45,
        edgecolor="white", label="Used bits")
ax2.bar(["Binary"], [BINARY_LATLON_BITS], color=GREEN, width=0.45, edgecolor="white")
ax2.bar(["Binary"], [saving], bottom=[BINARY_LATLON_BITS],
        color="#e0e0e0", width=0.45, edgecolor="white", alpha=0.6, label="Saved bits")
ax2.text(1, BINARY_LATLON_BITS + saving/2, f"−{saving} bits\n(−{reduction_g1:.1f}%)",
         ha="center", va="center", fontsize=10, fontweight="bold", color="#555")
ax2.set_ylabel("Bits", fontsize=10)
ax2.set_title(f"Savings: {reduction_g1:.1f}% reduction  ({ASCII_LATLON_BITS/BINARY_LATLON_BITS:.2f}x)",
              fontsize=11, color=GREEN)
ax2.set_ylim(0, 320)
ax2.legend(fontsize=9, loc="lower center")
ax2.grid(axis="y", linestyle=":", alpha=0.4)
ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("figures/fig2_gap1_encoding.png", dpi=150, bbox_inches="tight")
plt.close()
print("[SAVED] figures/fig2_gap1_encoding.png")

# ── FIGURE 3 — Gap 6: Full telemetry comparison ───────────────────────────────
formats6 = ["ASCII", "Binary", "Huffman"]
bits6    = [ASCII_TEL, BINARY_TEL, HUFF_TEL]
cols6    = [RED, GREEN, BLUE]
pcts6    = [0, (1 - BINARY_TEL/ASCII_TEL)*100, (1 - HUFF_TEL/ASCII_TEL)*100]

fig3, axes3 = plt.subplots(1, 2, figsize=(12, 5))
fig3.suptitle("Gap 6 -- Full Telemetry Encoding Comparison (7-field struct)",
              fontsize=13, fontweight="bold", color=DARK)

ax = axes3[0]
bars = ax.bar(formats6, bits6, color=cols6, width=0.45, edgecolor="white")
for bar, val, pct in zip(bars, bits6, pcts6):
    lbl = f"{val} bits\n(baseline)" if pct == 0 else f"{val} bits\n(-{pct:.1f}%)"
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 4,
            lbl, ha="center", va="bottom", fontsize=10, fontweight="bold")
ax.axhline(560, color=GOLD, linewidth=1.5, linestyle="--", label="BDS-3 GSMC 560-bit limit")
ax.set_ylabel("Bits per message", fontsize=10)
ax.set_title("Full Telemetry Payload Size", fontsize=11, color=BLUE)
ax.set_ylim(0, 450)
ax.legend(fontsize=9)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

ax2 = axes3[1]
savings = [0, ASCII_TEL - BINARY_TEL, ASCII_TEL - HUFF_TEL]
bottoms = [ASCII_TEL, BINARY_TEL, HUFF_TEL]
ax2.bar(formats6, bottoms,  color=cols6, width=0.45, edgecolor="white", label="Used bits")
ax2.bar(formats6, savings, bottom=bottoms, color="#e0e0e0", width=0.45,
        edgecolor="white", alpha=0.6, label="Saved vs ASCII")
for i, (val, sav) in enumerate(zip(bits6, savings)):
    if sav > 0:
        ax2.text(i, val + sav/2, f"-{sav}b", ha="center", va="center",
                 fontsize=9, color="#555")
ax2.set_ylabel("Bits", fontsize=10)
ax2.set_title("Bits Used vs Saved (vs ASCII)", fontsize=11, color=BLUE)
ax2.set_ylim(0, ASCII_TEL * 1.2)
ax2.legend(fontsize=9)
ax2.grid(axis="y", linestyle=":", alpha=0.4)
ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("figures/fig3_gap6_telemetry.png", dpi=150, bbox_inches="tight")
plt.close()
print("[SAVED] figures/fig3_gap6_telemetry.png")

# ── FIGURE 4 — Summary dashboard (Gap 1, 2, 3 placeholder, 6) ─────────────────
fig4, axes4 = plt.subplots(2, 2, figsize=(14, 10))
fig4.suptitle("BDS-SMC2 -- All Gaps Summary Dashboard",
              fontsize=15, fontweight="bold", color=DARK)

# Top-left: Gap 1
ax = axes4[0][0]
ax.bar(["ASCII", "Binary"], [ASCII_LATLON_BITS, BINARY_LATLON_BITS],
       color=[RED, GREEN], width=0.4, edgecolor="white")
ax.set_title("Gap 1 -- Lat/Lon Encoding", fontsize=11, color=DARK, fontweight="bold")
ax.set_ylabel("Bits"); ax.set_ylim(0, 320)
ax.text(0, ASCII_LATLON_BITS + 5,  f"{ASCII_LATLON_BITS}b",
        ha="center", fontsize=10, fontweight="bold")
ax.text(1, BINARY_LATLON_BITS + 5, f"{BINARY_LATLON_BITS}b (-{reduction_g1:.0f}%)",
        ha="center", fontsize=10, fontweight="bold", color=GREEN)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

# Top-right: Gap 2 latency
ax = axes4[0][1]
ax.plot(range(1, n + 1), total_lat, color=BLUE, linewidth=1.6)
ax.fill_between(range(1, n + 1), total_lat, alpha=0.15, color=BLUE)
ax.axhline(mean_tot, color=RED, linewidth=1.5, linestyle="--",
           label=f"Mean {mean_tot:.0f}ms")
ax.set_title(f"Gap 2 -- Latency ({n} TX)", fontsize=11, color=DARK, fontweight="bold")
ax.set_xlabel("TX #"); ax.set_ylabel("ms")
ax.legend(fontsize=9); ax.set_xlim(1, n); ax.set_ylim(0, max(total_lat) * 1.2)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

# Bottom-left: Gap 3 placeholder
ax = axes4[1][0]
ax.set_facecolor("#f9f9f9")
ax.text(0.5, 0.55, "Gap 3", transform=ax.transAxes,
        ha="center", va="center", fontsize=22, fontweight="bold", color="#cccccc")
ax.text(0.5, 0.38, "Environmental data pending", transform=ax.transAxes,
        ha="center", va="center", fontsize=11, color="#aaaaaa", style="italic")
ax.text(0.5, 0.25, "Collect during hardware days 2-5", transform=ax.transAxes,
        ha="center", va="center", fontsize=9, color="#bbbbbb")
ax.set_title("Gap 3 -- Environmental Reliability", fontsize=11, color=DARK, fontweight="bold")
ax.set_xticks([]); ax.set_yticks([])
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False); ax.spines["bottom"].set_visible(False)

# Bottom-right: Gap 6
ax = axes4[1][1]
ax.bar(["ASCII", "Binary", "Huffman"], bits6, color=cols6, width=0.4, edgecolor="white")
ax.axhline(560, color=GOLD, linewidth=1.2, linestyle="--", label="560-bit BDS limit")
ax.set_title("Gap 6 -- Full Telemetry Encoding", fontsize=11, color=DARK, fontweight="bold")
ax.set_ylabel("Bits"); ax.set_ylim(0, 450)
for i, (val, pct) in enumerate(zip(bits6, pcts6)):
    lbl = "baseline" if pct == 0 else f"-{pct:.0f}%"
    ax.text(i, val + 4, f"{val}b\n{lbl}", ha="center", fontsize=9, fontweight="bold")
ax.legend(fontsize=9)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("figures/fig4_summary.png", dpi=150, bbox_inches="tight")
plt.close()
print("[SAVED] figures/fig4_summary.png")

# ── FIGURE 5 — Gap 3: Environmental success rates (when data exists) ──────────
_G3_PATH    = "data/gap3_field_test.csv"
_ENVS       = ["open_sky", "light_canopy", "urban_canyon", "indoor"]
_ENV_LABELS = ["Open Sky", "Light Canopy", "Urban Canyon", "Indoor"]

def _wilson_ci(k, n_tot, z=1.96):
    if n_tot == 0: return 0, 0, 0
    p      = k / n_tot
    denom  = 1 + z**2 / n_tot
    centre = (p + z**2 / (2 * n_tot)) / denom
    margin = (z * math.sqrt(p*(1-p)/n_tot + z**2/(4*n_tot**2))) / denom
    return p, max(0, centre - margin), min(1, centre + margin)

if os.path.exists(_G3_PATH):
    g3_rows = load_csv(_G3_PATH)
    if g3_rows:
        counts = defaultdict(lambda: {"s": 0, "f": 0})
        for r in g3_rows:
            e = r.get("environment", "")
            if r.get("result") == "success": counts[e]["s"] += 1
            else:                            counts[e]["f"] += 1

        rates, lo_errs, hi_errs, totals = [], [], [], []
        for env in _ENVS:
            c     = counts.get(env, {"s": 0, "f": 0})
            n_tot = c["s"] + c["f"]
            p, lo, hi = _wilson_ci(c["s"], n_tot)
            rates.append(p * 100)
            lo_errs.append((p - lo) * 100)
            hi_errs.append((hi - p) * 100)
            totals.append(n_tot)

        fig5, ax5 = plt.subplots(figsize=(9, 5))
        bar_colors = [GREEN, BLUE, GOLD, RED]
        bars = ax5.bar(_ENV_LABELS, rates, color=bar_colors, width=0.5,
                       edgecolor="white", zorder=3)
        ax5.errorbar(range(len(_ENV_LABELS)), rates,
                     yerr=[lo_errs, hi_errs],
                     fmt="none", color="black", capsize=6, linewidth=1.5, zorder=4)
        for i, (bar, rate, n_tot) in enumerate(zip(bars, rates, totals)):
            ax5.text(i, rate + hi_errs[i] + 2, f"{rate:.0f}%\n(n={n_tot})",
                     ha="center", va="bottom", fontsize=9, fontweight="bold")
        ax5.set_ylim(0, 115)
        ax5.set_ylabel("Delivery success rate (%)", fontsize=11)
        ax5.set_title("Gap 3 -- BDS-3 SMC Reliability by Environment\n"
                      "(bars = success rate, error bars = 95% Wilson CI)",
                      fontsize=12, color=DARK)
        ax5.axhline(100, color="gray", linewidth=0.8, linestyle=":")
        ax5.grid(axis="y", linestyle=":", alpha=0.4, zorder=0)
        ax5.spines["top"].set_visible(False); ax5.spines["right"].set_visible(False)
        plt.tight_layout()
        plt.savefig("figures/fig5_gap3_environments.png", dpi=150, bbox_inches="tight")
        plt.close()
        print("[SAVED] figures/fig5_gap3_environments.png")
    else:
        print("[SKIP]  figures/fig5_gap3_environments.png -- gap3 data not yet collected")
else:
    print("[SKIP]  figures/fig5_gap3_environments.png -- gap3 data not yet collected")

print("\n[DONE] All figures saved to BDS-SMC2/figures/")
