"""
generate_figures.py — Dissertation-ready figures for Gap 1, Gap 3, Gap 6.
Saves all figures to figures/ directory.
Usage: python generate_figures.py
"""

import csv
import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

OUT_DIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUT_DIR, exist_ok=True)

COLORS = {
    "ascii":        "#7d6608",
    "binary":       "#1a5276",
    "huffman":      "#a93226",
    "environments": ["#1a5276", "#148f77", "#d35400", "#7d3c98"],
}

matplotlib.rc("font", **{"family": "DejaVu Sans", "size": 11})


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return 0, 0, 0
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2*n)) / denom
    margin = (z * math.sqrt(p*(1-p)/n + z**2/(4*n**2))) / denom
    return p, max(0, centre - margin), min(1, centre + margin)


def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [SAVED] {path}")


# ── GAP 1: Coordinate encoding ────────────────────────────────

def fig_gap1():
    formats = ["ASCII\n(Baseline)", "Binary\n(112-bit Rescue)"]
    bits    = [264, 112]
    colors  = [COLORS["ascii"], COLORS["binary"]]

    fig, ax = plt.subplots(figsize=(6, 4.5))
    bars = ax.bar(formats, bits, color=colors, width=0.45, edgecolor="white", linewidth=1.2)

    for bar, val in zip(bars, bits):
        ax.text(bar.get_x() + bar.get_width()/2, val + 4, f"{val} bits",
                ha="center", va="bottom", fontweight="bold", fontsize=12)

    reduction = (1 - bits[1]/bits[0]) * 100
    ax.annotate("", xy=(1, bits[1]+8), xytext=(0, bits[0]+8),
                arrowprops=dict(arrowstyle="->", color="#555", lw=1.5))
    ax.text(0.5, (bits[0]+bits[1])/2 + 20, f"−{reduction:.1f}%",
            ha="center", color="#1e8449", fontweight="bold", fontsize=14)

    ax.set_ylabel("Payload size (bits)", fontsize=12)
    ax.set_title("Gap 1: Rescue Payload Encoding — ASCII vs Binary\n"
                 "(112-bit payload: lat·lon at 7dp, alt, uncertainty R, priority, survivor ID)",
                 fontsize=12, fontweight="bold", pad=12)
    ax.set_ylim(0, 310)
    ax.spines[["top","right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    save(fig, "gap1_encoding_comparison.png")


# ── GAP 3: Success rate by environment ───────────────────────

def fig_gap3_success():
    data_path = os.path.join(os.path.dirname(__file__), "data", "gap3_field_test.csv")
    envs_order = ["open_sky", "light_canopy", "urban_canyon", "indoor"]
    labels     = ["Open Sky", "Light\nCanopy", "Urban\nCanyon", "Indoor"]
    counts     = {e: {"s": 0, "n": 0} for e in envs_order}

    with open(data_path, newline="") as f:
        for r in csv.DictReader(f):
            e = r["environment"]
            if r["result"] == "timeout" or e not in counts:
                continue
            counts[e]["n"] += 1
            if r["result"] == "success":
                counts[e]["s"] += 1

    rates, lo_err, hi_err = [], [], []
    for e in envs_order:
        k, n = counts[e]["s"], counts[e]["n"]
        p, lo, hi = wilson_ci(k, n)
        rates.append(p * 100)
        lo_err.append(max(0.0, (p - lo) * 100))
        hi_err.append(max(0.0, (hi - p) * 100))

    x = np.arange(len(envs_order))
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(x, rates, color=COLORS["environments"], width=0.55,
                  edgecolor="white", linewidth=1.2, zorder=3)
    ax.errorbar(x, rates, yerr=[lo_err, hi_err], fmt="none",
                color="#2c3e50", capsize=6, capthick=1.8, elinewidth=1.8, zorder=4)

    for bar, rate, lo, hi in zip(bars, rates,
                                  [r - e for r, e in zip(rates, lo_err)],
                                  [r + e for r, e in zip(rates, hi_err)]):
        n = counts[envs_order[list(x).index(bar.get_x() + bar.get_width()/2)]]["n"] if False else ""
        ax.text(bar.get_x() + bar.get_width()/2, rate + 2.5,
                f"{rate:.0f}%", ha="center", va="bottom", fontweight="bold", fontsize=12)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_ylabel("Delivery Success Rate (%)", fontsize=12)
    ax.set_title("Gap 3: BDS-SMC Delivery Reliability Across Environments\n"
                 "(n=57–61 per environment · error bars = 95% Wilson CI)",
                 fontsize=12, fontweight="bold", pad=12)
    ax.set_ylim(0, 118)
    ax.axhline(100, color="#aab7b8", linestyle="--", linewidth=1, zorder=1)
    ax.spines[["top","right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    fig.tight_layout()
    save(fig, "gap3_success_rate.png")


def fig_gap3_locations():
    data_path = os.path.join(os.path.dirname(__file__), "data", "gap3_field_test.csv")
    loc_data, env_map = {}, {}
    env_color = {e: c for e, c in zip(
        ["open_sky","light_canopy","urban_canyon","indoor"], COLORS["environments"])}

    with open(data_path, newline="") as f:
        for r in csv.DictReader(f):
            if r["result"] == "timeout":
                continue
            loc = r["location_id"]
            if loc not in loc_data:
                loc_data[loc] = {"s": 0, "n": 0}
                env_map[loc] = r["environment"]
            loc_data[loc]["n"] += 1
            if r["result"] == "success":
                loc_data[loc]["s"] += 1

    locs   = sorted(loc_data.keys())
    rates  = [loc_data[l]["s"]/loc_data[l]["n"]*100 for l in locs]
    colors = [env_color[env_map[l]] for l in locs]

    fig, ax = plt.subplots(figsize=(11, 4.5))
    bars = ax.bar(locs, rates, color=colors, width=0.6, edgecolor="white",
                  linewidth=1.1, zorder=3)

    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width()/2, rate + 1.2,
                f"{rate:.0f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    legend_patches = [
        mpatches.Patch(color=env_color[e], label=e.replace("_"," ").title())
        for e in ["open_sky","light_canopy","urban_canyon","indoor"]
    ]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=10, framealpha=0.8)
    ax.set_ylabel("Success Rate (%)", fontsize=11)
    ax.set_title("Gap 3: Per-Location Delivery Success (12 locations · 3 per environment)",
                 fontsize=12, fontweight="bold", pad=10)
    ax.set_ylim(0, 118)
    ax.axhline(100, color="#aab7b8", linestyle="--", linewidth=1, zorder=1)
    ax.spines[["top","right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    fig.tight_layout()
    save(fig, "gap3_location_breakdown.png")


# ── GAP 6: Telemetry compression ─────────────────────────────

def fig_gap6():
    formats = ["ASCII\n(Baseline)", "Huffman\nCoding", "Binary\n(Proposed)"]
    bits    = [368, 184, 112]
    colors  = [COLORS["ascii"], COLORS["huffman"], COLORS["binary"]]
    limit   = 210

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(formats, bits, color=colors, width=0.45,
                  edgecolor="white", linewidth=1.2, zorder=3)

    for bar, val in zip(bars, bits):
        ax.text(bar.get_x() + bar.get_width()/2, val + 5,
                f"{val} bits", ha="center", va="bottom", fontweight="bold", fontsize=12)

    ascii_bits = 368
    for bar, val in zip(bars[1:], bits[1:]):
        pct = (1 - val/ascii_bits)*100
        ax.text(bar.get_x() + bar.get_width()/2, val/2,
                f"−{pct:.0f}%\nvs ASCII", ha="center", va="center",
                color="white", fontweight="bold", fontsize=11)

    ax.axhline(limit, color="#e74c3c", linestyle="--", linewidth=2, zorder=4)
    ax.text(2.27, limit + 8, f"BDS-SMC limit ({limit} bits)",
            ha="right", color="#e74c3c", fontsize=10, fontweight="bold")

    ax.set_ylabel("Encoded payload size (bits)", fontsize=12)
    ax.set_title("Gap 6: Full Telemetry Encoding Comparison\n"
                 "(binary: lat(7dp) · lon(7dp) · alt · uncertainty(R) · priority · survivor ID)",
                 fontsize=12, fontweight="bold", pad=12)
    ax.set_ylim(0, 430)
    ax.spines[["top","right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    fig.tight_layout()
    save(fig, "gap6_telemetry_comparison.png")


if __name__ == "__main__":
    print("\n[FIGURES] Generating dissertation figures...\n")
    fig_gap1()
    fig_gap3_success()
    fig_gap3_locations()
    fig_gap6()
    print(f"\n[FIGURES] All saved to: {OUT_DIR}")
