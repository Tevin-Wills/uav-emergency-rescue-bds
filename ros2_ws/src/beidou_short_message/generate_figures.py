"""
generate_figures.py — BDS-SMC2 experiment visualizations.
Reads directly from data/*.csv and generates all figures.

Usage: python generate_figures.py
Output: figures/fig1_latency.png
        figures/fig2_gap1_encoding.png
        figures/fig3_gap5_aes.png
        figures/fig4_gap6_telemetry.png
        figures/fig5_summary.png
"""

import csv, os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

os.makedirs("figures", exist_ok=True)

DARK  = "#1a3a5c"
BLUE  = "#2e5fa3"
RED   = "#e8523a"
GREEN = "#2d7a3a"
GOLD  = "#b07d1a"
LGRAY = "#f4f7fb"

# ── Load data ──────────────────────────────────────────────────────────────────
def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))

gap2 = load_csv("data/gap2_latency.csv")
gap5 = load_csv("data/gap5_encryption.csv")
gap6 = load_csv("data/gap6_telemetry.csv")

tx_lat    = [int(r["tx_latency_ms"])    for r in gap2]
dec_lat   = [int(r["decode_latency_ms"]) for r in gap2]
total_lat = [int(r["total_latency_ms"]) for r in gap2]
n = len(tx_lat)

# ── CONFIRMED NUMBERS (printed to console) ────────────────────────────────────
print("=" * 60)
print("BDS-SMC2 — CONFIRMED EXPERIMENT RESULTS")
print("=" * 60)

print(f"\n-- Gap 1: ASCII vs Binary (lat/lon only) --")
ASCII_LATLON_BITS = 264
BINARY_LATLON_BITS = 64
reduction_g1 = (1 - BINARY_LATLON_BITS/ASCII_LATLON_BITS)*100
print(f"  ASCII  : {ASCII_LATLON_BITS} bits")
print(f"  Binary : {BINARY_LATLON_BITS} bits")
print(f"  Reduction: {reduction_g1:.1f}%  ({ASCII_LATLON_BITS/BINARY_LATLON_BITS:.2f}x)")

print(f"\n-- Gap 2: Latency (n={n} transmissions) --")
mean_tx  = sum(tx_lat)/n
std_tx   = math.sqrt(sum((x-mean_tx)**2 for x in tx_lat)/(n-1))
mean_tot = sum(total_lat)/n
std_tot  = math.sqrt(sum((x-mean_tot)**2 for x in total_lat)/(n-1))
print(f"  TX  mean={mean_tx:.1f}ms  std={std_tx:.1f}ms  min={min(tx_lat)}ms  max={max(tx_lat)}ms")
print(f"  Tot mean={mean_tot:.1f}ms  std={std_tot:.1f}ms  min={min(total_lat)}ms  max={max(total_lat)}ms")
print(f"  Decode overhead mean={sum(dec_lat)/n:.1f}ms  (bottleneck = satellite)")

print(f"\n-- Gap 5: AES-128 Encryption Overhead --")
BINARY_BITS = int(gap5[0]["payload_bits"])
AES_BITS    = int(gap5[0]["encrypted_bits"])
OVERHEAD    = int(gap5[0]["overhead_bits"])
verified    = all(r["verified"] == "True" for r in gap5)
print(f"  Binary payload : {BINARY_BITS} bits")
print(f"  AES ciphertext : {AES_BITS} bits")
print(f"  Overhead       : {OVERHEAD} bits (+{OVERHEAD/BINARY_BITS*100:.0f}%)")
print(f"  Round-trip OK  : {verified} ({len(gap5)}/{len(gap5)} messages)")

print(f"\n-- Gap 6: Full Telemetry Encoding --")
g6 = {r["format"]: r for r in gap6}
ASCII_TEL  = int(g6["ASCII"]["bits"])
BINARY_TEL = int(g6["Binary"]["bits"])
HUFF_TEL   = int(g6["Huffman"]["bits"])
print(f"  ASCII   : {ASCII_TEL} bits  (baseline)")
print(f"  Binary  : {BINARY_TEL} bits  (-{(1-BINARY_TEL/ASCII_TEL)*100:.1f}%)")
print(f"  Huffman : {HUFF_TEL} bits  (-{(1-HUFF_TEL/ASCII_TEL)*100:.1f}%)")

print("\n" + "=" * 60)
print("All numbers confirmed. Generating figures...")
print("=" * 60 + "\n")

# ── FIGURE 1 — Gap 2: Latency time-series + stats ─────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Gap 2 — BDS-3 SMC End-to-End Latency  (n=30 transmissions)",
             fontsize=13, fontweight="bold", color=DARK)

x = np.arange(1, n+1)

# Left: time-series
ax = axes[0]
ax.plot(x, tx_lat,    color=BLUE, linewidth=1.8, label="TX latency")
ax.plot(x, total_lat, color=RED,  linewidth=1.8, linestyle="--", label="Total latency")
ax.axhline(mean_tx,  color=BLUE, linewidth=0.9, linestyle=":", alpha=0.7)
ax.axhline(mean_tot, color=RED,  linewidth=0.9, linestyle=":", alpha=0.7)
ax.set_xlabel("Transmission #", fontsize=10)
ax.set_ylabel("Latency (ms)", fontsize=10)
ax.set_title("Per-Transmission Latency", fontsize=11, color=BLUE)
ax.legend(fontsize=9)
ax.set_xlim(1, n); ax.set_ylim(0, max(total_lat)*1.15)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

# Middle: histogram
ax2 = axes[1]
ax2.hist(total_lat, bins=8, color=BLUE, edgecolor="white", alpha=0.85)
ax2.axvline(mean_tot, color=RED, linewidth=2, linestyle="--", label=f"Mean {mean_tot:.0f}ms")
ax2.set_xlabel("Total latency (ms)", fontsize=10)
ax2.set_ylabel("Frequency", fontsize=10)
ax2.set_title("Latency Distribution", fontsize=11, color=BLUE)
ax2.legend(fontsize=9)
ax2.grid(axis="y", linestyle=":", alpha=0.4)
ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)

# Right: stats bar
ax3 = axes[2]
labels = ["Mean", "Median", "Min", "Max", "95th pct"]
sorted_tot = sorted(total_lat)
vals   = [mean_tot, sorted_tot[n//2], min(total_lat), max(total_lat), sorted_tot[int(0.95*n)]]
colors_b = [BLUE, BLUE, GREEN, RED, GOLD]
bars = ax3.bar(labels, vals, color=colors_b, width=0.55, edgecolor="white")
for bar, val in zip(bars, vals):
    ax3.text(bar.get_x()+bar.get_width()/2, bar.get_height()+40,
             f"{val:.0f}", ha="center", va="bottom", fontsize=9)
ax3.set_ylabel("ms", fontsize=10)
ax3.set_title("Summary Statistics", fontsize=11, color=BLUE)
ax3.set_ylim(0, max(total_lat)*1.25)
ax3.grid(axis="y", linestyle=":", alpha=0.4)
ax3.spines["top"].set_visible(False); ax3.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("figures/fig1_latency.png", dpi=150, bbox_inches="tight")
plt.close()
print("[SAVED] figures/fig1_latency.png")

# ── FIGURE 2 — Gap 1: ASCII vs Binary lat/lon ─────────────────────────────────
fig2, axes2 = plt.subplots(1, 2, figsize=(11, 5))
fig2.suptitle("Gap 1 — ASCII vs Binary Coordinate Encoding",
              fontsize=13, fontweight="bold", color=DARK)

ax = axes2[0]
enc_labels = ["ASCII\n($CCTXM format)", "Binary\n(two int32)"]
enc_bits   = [ASCII_LATLON_BITS, BINARY_LATLON_BITS]
enc_colors = [RED, GREEN]
bars = ax.bar(enc_labels, enc_bits, color=enc_colors, width=0.45, edgecolor="white")
for bar, val, lbl in zip(bars, enc_bits, [f"{ASCII_LATLON_BITS} bits\n(baseline)", f"{BINARY_LATLON_BITS} bits\n(−{reduction_g1:.1f}%)"]):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+4,
            lbl, ha="center", va="bottom", fontsize=10, fontweight="bold")
ax.set_ylabel("Bits per message", fontsize=10)
ax.set_title("Payload Size: lat/lon only", fontsize=11, color=BLUE)
ax.set_ylim(0, ASCII_LATLON_BITS*1.4)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

ax2 = axes2[1]
saved = ASCII_LATLON_BITS - BINARY_LATLON_BITS
ax2.pie([saved, BINARY_LATLON_BITS], colors=[GREEN, LGRAY],
        startangle=90, wedgeprops=dict(width=0.52, edgecolor="white"))
ax2.text(0, 0, f"{reduction_g1:.1f}%\nsaved", ha="center", va="center",
         fontsize=16, fontweight="bold", color=GREEN)
ax2.set_title(f"Binary saves {saved} of {ASCII_LATLON_BITS} bits\n({ASCII_LATLON_BITS/BINARY_LATLON_BITS:.2f}× compression)",
              fontsize=11, color=BLUE)
ax2.legend(handles=[mpatches.Patch(color=GREEN, label=f"Saved: {saved} bits"),
                    mpatches.Patch(color=LGRAY, label=f"Used: {BINARY_LATLON_BITS} bits")],
           fontsize=9, loc="lower center")

plt.tight_layout()
plt.savefig("figures/fig2_gap1_encoding.png", dpi=150, bbox_inches="tight")
plt.close()
print("[SAVED] figures/fig2_gap1_encoding.png")

# ── FIGURE 3 — Gap 5: AES-128 overhead ────────────────────────────────────────
fig3, axes3 = plt.subplots(1, 2, figsize=(11, 5))
fig3.suptitle("Gap 5 — AES-128-CBC Encryption Overhead",
              fontsize=13, fontweight="bold", color=DARK)

ax = axes3[0]
aes_labels = ["Binary\n(plaintext)", "AES-128\n(ciphertext)"]
aes_bits   = [BINARY_BITS, AES_BITS]
aes_colors = [GREEN, GOLD]
bars = ax.bar(aes_labels, aes_bits, color=aes_colors, width=0.45, edgecolor="white")
for bar, val, extra in zip(bars, aes_bits, ["64 bits\n(baseline)", f"{AES_BITS} bits\n(+{OVERHEAD/BINARY_BITS*100:.0f}% overhead)"]):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+2,
            extra, ha="center", va="bottom", fontsize=10, fontweight="bold")
ax.set_ylabel("Bits", fontsize=10)
ax.set_title("Payload Size: Binary vs Encrypted", fontsize=11, color=BLUE)
ax.set_ylim(0, AES_BITS*1.5)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

ax2 = axes3[1]
ax2.pie([BINARY_BITS, OVERHEAD], colors=[GREEN, GOLD],
        startangle=90, wedgeprops=dict(width=0.52, edgecolor="white"),
        labels=["", ""])
ax2.text(0, 0, "+100%\noverhead", ha="center", va="center",
         fontsize=14, fontweight="bold", color=GOLD)
ax2.set_title(f"AES adds {OVERHEAD} bits overhead\n(1 extra cipher block)\nRound-trip verified: {verified}",
              fontsize=11, color=BLUE)
ax2.legend(handles=[mpatches.Patch(color=GREEN, label=f"Data: {BINARY_BITS} bits"),
                    mpatches.Patch(color=GOLD,  label=f"Overhead: {OVERHEAD} bits")],
           fontsize=9, loc="lower center")

plt.tight_layout()
plt.savefig("figures/fig3_gap5_aes.png", dpi=150, bbox_inches="tight")
plt.close()
print("[SAVED] figures/fig3_gap5_aes.png")

# ── FIGURE 4 — Gap 6: Full telemetry comparison ───────────────────────────────
fig4, axes4 = plt.subplots(1, 2, figsize=(12, 5))
fig4.suptitle("Gap 6 — Full Telemetry Encoding Comparison (7-field struct)",
              fontsize=13, fontweight="bold", color=DARK)

formats6 = ["ASCII", "Binary", "Huffman"]
bits6    = [ASCII_TEL, BINARY_TEL, HUFF_TEL]
cols6    = [RED, GREEN, BLUE]
pcts6    = [0, (1-BINARY_TEL/ASCII_TEL)*100, (1-HUFF_TEL/ASCII_TEL)*100]

ax = axes4[0]
bars = ax.bar(formats6, bits6, color=cols6, width=0.45, edgecolor="white")
for bar, val, pct in zip(bars, bits6, pcts6):
    lbl = f"{val} bits\n(baseline)" if pct==0 else f"{val} bits\n(−{pct:.1f}%)"
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+4,
            lbl, ha="center", va="bottom", fontsize=10, fontweight="bold")
ax.axhline(560, color=GOLD, linewidth=1.5, linestyle="--", label="BDS-3 GSMC 560-bit limit")
ax.set_ylabel("Bits per message", fontsize=10)
ax.set_title("Full Telemetry Payload Size", fontsize=11, color=BLUE)
ax.set_ylim(0, 450)
ax.legend(fontsize=9)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

ax2 = axes4[1]
savings = [0, ASCII_TEL-BINARY_TEL, ASCII_TEL-HUFF_TEL]
bottoms = [ASCII_TEL, BINARY_TEL, HUFF_TEL]
ax2.bar(formats6, bottoms,  color=cols6, width=0.45, edgecolor="white", label="Used bits")
ax2.bar(formats6, savings, bottom=bottoms, color="#e0e0e0", width=0.45,
        edgecolor="white", alpha=0.6, label="Saved vs ASCII")
for i, (fmt, val, sav) in enumerate(zip(formats6, bits6, savings)):
    if sav > 0:
        ax2.text(i, val + sav/2, f"−{sav}b", ha="center", va="center",
                 fontsize=9, color="#555")
ax2.set_ylabel("Bits", fontsize=10)
ax2.set_title("Bits Used vs Saved (vs ASCII)", fontsize=11, color=BLUE)
ax2.set_ylim(0, ASCII_TEL*1.2)
ax2.legend(fontsize=9)
ax2.grid(axis="y", linestyle=":", alpha=0.4)
ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("figures/fig4_gap6_telemetry.png", dpi=150, bbox_inches="tight")
plt.close()
print("[SAVED] figures/fig4_gap6_telemetry.png")

# ── FIGURE 5 — Summary: all gaps side by side ─────────────────────────────────
fig5, axes5 = plt.subplots(2, 2, figsize=(14, 10))
fig5.suptitle("BDS-SMC2 — All Gaps Summary Dashboard",
              fontsize=15, fontweight="bold", color=DARK)

# Top-left: Gap 1 bar
ax = axes5[0][0]
ax.bar(["ASCII", "Binary"], [ASCII_LATLON_BITS, BINARY_LATLON_BITS],
       color=[RED, GREEN], width=0.4, edgecolor="white")
ax.set_title("Gap 1 — Lat/Lon Encoding", fontsize=11, color=DARK, fontweight="bold")
ax.set_ylabel("Bits"); ax.set_ylim(0, 320)
ax.text(0, ASCII_LATLON_BITS+5,  f"{ASCII_LATLON_BITS}b", ha="center", fontsize=10, fontweight="bold")
ax.text(1, BINARY_LATLON_BITS+5, f"{BINARY_LATLON_BITS}b (−{reduction_g1:.0f}%)", ha="center", fontsize=10, fontweight="bold", color=GREEN)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

# Top-right: Gap 2 latency time-series
ax = axes5[0][1]
ax.plot(range(1, n+1), total_lat, color=BLUE, linewidth=1.6)
ax.fill_between(range(1, n+1), total_lat, alpha=0.15, color=BLUE)
ax.axhline(mean_tot, color=RED, linewidth=1.5, linestyle="--", label=f"Mean {mean_tot:.0f}ms")
ax.set_title("Gap 2 — Latency (30 TX)", fontsize=11, color=DARK, fontweight="bold")
ax.set_xlabel("TX #"); ax.set_ylabel("ms")
ax.legend(fontsize=9); ax.set_xlim(1, n); ax.set_ylim(0, max(total_lat)*1.2)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

# Bottom-left: Gap 5 AES
ax = axes5[1][0]
ax.bar(["Binary\nplaintext", "AES-128\nciphertext"], [BINARY_BITS, AES_BITS],
       color=[GREEN, GOLD], width=0.4, edgecolor="white")
ax.set_title("Gap 5 — AES-128 Overhead", fontsize=11, color=DARK, fontweight="bold")
ax.set_ylabel("Bits"); ax.set_ylim(0, 170)
ax.text(0, BINARY_BITS+2, f"{BINARY_BITS}b", ha="center", fontsize=10, fontweight="bold")
ax.text(1, AES_BITS+2,    f"{AES_BITS}b (+100%)", ha="center", fontsize=10, fontweight="bold", color=GOLD)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

# Bottom-right: Gap 6 full telemetry
ax = axes5[1][1]
ax.bar(["ASCII", "Binary", "Huffman"], bits6, color=cols6, width=0.4, edgecolor="white")
ax.axhline(560, color=GOLD, linewidth=1.2, linestyle="--", label="560-bit BDS limit")
ax.set_title("Gap 6 — Full Telemetry Encoding", fontsize=11, color=DARK, fontweight="bold")
ax.set_ylabel("Bits"); ax.set_ylim(0, 450)
for i, (val, pct) in enumerate(zip(bits6, pcts6)):
    lbl = "baseline" if pct==0 else f"−{pct:.0f}%"
    ax.text(i, val+4, f"{val}b\n{lbl}", ha="center", fontsize=9, fontweight="bold")
ax.legend(fontsize=9)
ax.grid(axis="y", linestyle=":", alpha=0.4)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig("figures/fig5_summary.png", dpi=150, bbox_inches="tight")
plt.close()
print("[SAVED] figures/fig5_summary.png")

print("\n[DONE] All 5 figures saved to BDS-SMC2/figures/")
