"""
Generate progress figures from BDS-SMC2 CSV data.
Output: figures/fig1_latency.png, fig2_encoding.png
"""

import csv, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

os.makedirs("figures", exist_ok=True)

# ── FIGURE 1 — Gap 2: Latency across 30 transmissions ───────────────────────
tx_lat, total_lat = [], []
with open("data/gap2_latency.csv") as f:
    for row in csv.DictReader(f):
        tx_lat.append(int(row["tx_latency_ms"]))
        total_lat.append(int(row["total_latency_ms"]))

n = len(tx_lat)
x = np.arange(1, n + 1)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Gap 2 — BDS-3 SMC End-to-End Latency  (n=30 transmissions)",
             fontsize=13, fontweight="bold", color="#1a3a5c")

# Left: time-series
ax = axes[0]
ax.plot(x, tx_lat,    color="#2e5fa3", linewidth=1.6, label="TX latency (ESP32→satellite)")
ax.plot(x, total_lat, color="#e8523a", linewidth=1.6, linestyle="--", label="Total latency")
ax.axhline(np.mean(tx_lat),    color="#2e5fa3", linewidth=0.8, linestyle=":")
ax.axhline(np.mean(total_lat), color="#e8523a", linewidth=0.8, linestyle=":")
ax.set_xlabel("Transmission #", fontsize=10)
ax.set_ylabel("Latency (ms)", fontsize=10)
ax.set_title("Per-Transmission Latency", fontsize=11, color="#2e5fa3")
ax.legend(fontsize=9)
ax.set_xlim(1, n)
ax.set_ylim(0, max(total_lat) * 1.15)
ax.grid(axis="y", linestyle=":", alpha=0.5)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Right: statistics summary bar
ax2 = axes[1]
stats = {
    "TX\nMean":  np.mean(tx_lat),
    "TX\nMin":   min(tx_lat),
    "TX\nMax":   max(tx_lat),
    "TX\nStd":   np.std(tx_lat),
    "Total\nMean": np.mean(total_lat),
    "Total\nMin":  min(total_lat),
    "Total\nMax":  max(total_lat),
}
cols  = ["#2e5fa3"]*4 + ["#e8523a"]*3
bars  = ax2.bar(list(stats.keys()), list(stats.values()), color=cols, width=0.6, edgecolor="white")
for bar, val in zip(bars, stats.values()):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 40,
             f"{val:.0f} ms", ha="center", va="bottom", fontsize=8.5, color="#1a1a1a")
ax2.set_ylabel("ms", fontsize=10)
ax2.set_title("Summary Statistics", fontsize=11, color="#2e5fa3")
ax2.set_ylim(0, max(total_lat) * 1.25)
ax2.grid(axis="y", linestyle=":", alpha=0.5)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
blue_patch = mpatches.Patch(color="#2e5fa3", label="TX latency")
red_patch  = mpatches.Patch(color="#e8523a", label="Total latency")
ax2.legend(handles=[blue_patch, red_patch], fontsize=9)

plt.tight_layout()
plt.savefig("figures/fig1_latency.png", dpi=150, bbox_inches="tight")
plt.close()
print("[SAVED] figures/fig1_latency.png")

# ── FIGURE 2 — Gap 1/6: Encoding size comparison ────────────────────────────
formats = ["ASCII\n(MODE 0)", "Binary\n(MODE 1)", "Huffman\n(MODE 2)"]
bits    = [384, 128, 192]
colors_bar = ["#9e2a2b", "#2d7a3a", "#2e5fa3"]
pcts    = [0, 66.7, 50.0]

fig2, axes2 = plt.subplots(1, 2, figsize=(11, 5))
fig2.suptitle("Gaps 1 & 4 — Payload Encoding Efficiency Comparison",
              fontsize=13, fontweight="bold", color="#1a3a5c")

# Left: bit size bar chart
ax3 = axes2[0]
bars2 = ax3.bar(formats, bits, color=colors_bar, width=0.5, edgecolor="white")
for bar, bit, pct in zip(bars2, bits, pcts):
    label = f"{bit} bits" if pct == 0 else f"{bit} bits\n(−{pct:.0f}% vs ASCII)"
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 6,
             label, ha="center", va="bottom", fontsize=9, color="#1a1a1a")
ax3.axhline(560, color="#b07d1a", linewidth=1.2, linestyle="--", label="GSMC 560-bit limit")
ax3.set_ylabel("Payload size (bits)", fontsize=10)
ax3.set_title("Payload Size per Mode", fontsize=11, color="#2e5fa3")
ax3.set_ylim(0, 500)
ax3.legend(fontsize=9)
ax3.grid(axis="y", linestyle=":", alpha=0.5)
ax3.spines["top"].set_visible(False)
ax3.spines["right"].set_visible(False)

# Right: compression ratio doughnut for Binary (best mode)
ax4 = axes2[1]
saved = 384 - 128
wedge_sizes = [saved, 128]
wedge_cols  = ["#2d7a3a", "#c8d8ea"]
wedges, _ = ax4.pie(wedge_sizes, colors=wedge_cols, startangle=90,
                     wedgeprops=dict(width=0.5, edgecolor="white"))
ax4.text(0, 0, "66.7%\nsaved", ha="center", va="center",
         fontsize=14, fontweight="bold", color="#2d7a3a")
ax4.set_title("Binary MODE 1\nvs ASCII baseline", fontsize=11, color="#2e5fa3")
saved_patch = mpatches.Patch(color="#2d7a3a", label=f"Saved: {saved} bits")
kept_patch  = mpatches.Patch(color="#c8d8ea", label=f"Used: 128 bits")
ax4.legend(handles=[saved_patch, kept_patch], fontsize=9, loc="lower center")

plt.tight_layout()
plt.savefig("figures/fig2_encoding.png", dpi=150, bbox_inches="tight")
plt.close()
print("[SAVED] figures/fig2_encoding.png")

print("\n[DONE] Both figures saved to BDS-SMC2/figures/")
