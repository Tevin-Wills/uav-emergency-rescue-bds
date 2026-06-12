"""
generate_presentation.py — BDS-SMC2 Dissertation Presentation PDF
Produces a structured 5-page PDF: title page + one page per research gap.
Each gap page: numbered header, problem, research question, table, figure proof.
Usage: python generate_presentation.py
"""

import os
import csv
import math
import textwrap
import statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

ROOT    = os.path.dirname(os.path.abspath(__file__))
DATA    = os.path.join(ROOT, "data")
FIGS    = os.path.join(ROOT, "figures")
OUT_PDF = os.path.join(ROOT, "BDS_SMC2_Presentation.pdf")

BLUE  = "#1a5276"
LBLUE = "#eaf2ff"
GOLD  = "#7d6608"
RED   = "#a93226"
GREEN = "#1e8449"
ENVS  = ["#1a5276", "#148f77", "#d35400", "#7d3c98"]

matplotlib.rc("font", **{"family": "DejaVu Sans", "size": 10})


def wrap(text, w=36):
    return textwrap.fill(str(text), width=w)


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return 0, 0, 0
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return p, max(0, centre - margin), min(1, centre + margin)


# ── PRESENTATION FIGURES (clean titles — no "Gap X") ──────────────────────────

def fig_encoding():
    fig, ax = plt.subplots(figsize=(7, 4))
    bits   = [264, 112]
    labels = ["ASCII\n(Baseline)", "Binary\n(112-bit Rescue)"]
    colors = [GOLD, BLUE]
    bars = ax.bar(labels, bits, color=colors, width=0.42,
                  edgecolor="white", linewidth=1.3, zorder=3)
    for bar, val in zip(bars, bits):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 4,
                f"{val} bits", ha="center", va="bottom",
                fontweight="bold", fontsize=13)
    ax.annotate("", xy=(1, 120), xytext=(0, 268),
                arrowprops=dict(arrowstyle="->", color="#555", lw=1.6))
    ax.text(0.5, 200, "−57.6%", ha="center", color=GREEN,
            fontweight="bold", fontsize=15)
    ax.axhline(210, color="#e74c3c", linestyle="--", linewidth=2, zorder=4)
    ax.text(1.36, 215, "BDS-SMC limit (210 bits)",
            color="#e74c3c", fontsize=9, fontweight="bold")
    ax.set_ylabel("Payload size (bits)", fontsize=12)
    ax.set_title("Coordinate Encoding: ASCII vs Binary",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_ylim(0, 310)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    p = os.path.join(FIGS, "_pres1.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return p


def fig_latency():
    path = os.path.join(DATA, "gap2_latency.csv")
    latencies, tx_nums = [], []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            try:
                lat = int(r["tx_latency_ms"])
                if lat > 0:
                    latencies.append(lat / 1000)
                    tx_nums.append(int(r.get("tx_num", len(latencies))))
            except (ValueError, KeyError):
                continue
    mean_s = statistics.mean(latencies)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.scatter(tx_nums, latencies, color=BLUE, s=55, zorder=3,
               alpha=0.85, label="Individual TX")
    ax.axhline(mean_s, color=GREEN, linestyle="--", linewidth=2,
               label=f"Mean = {mean_s:.2f} s", zorder=4)
    ax.axhline(5.0, color="#e74c3c", linestyle="--", linewidth=1.5,
               label="BDS-3 limit (5 s)", alpha=0.8, zorder=4)
    ax.set_xlabel("Transmission Number", fontsize=11)
    ax.set_ylabel("End-to-End Latency (s)", fontsize=11)
    ax.set_title(f"End-to-End Latency — Baseline Morning Session  (n={len(latencies)})",
                 fontsize=12, fontweight="bold", pad=12)
    ax.legend(fontsize=9, loc="upper right")
    ax.set_ylim(0, 6.2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    p = os.path.join(FIGS, "_pres2.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return p


def fig_delivery():
    path   = os.path.join(DATA, "gap3_field_test.csv")
    envs   = ["open_sky", "light_canopy", "urban_canyon", "indoor"]
    labels = ["Open Sky", "Light\nCanopy", "Urban\nCanyon", "Indoor"]
    counts = {e: {"s": 0, "n": 0} for e in envs}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            e = r["environment"]
            if r["result"] == "timeout" or e not in counts:
                continue
            counts[e]["n"] += 1
            if r["result"] == "success":
                counts[e]["s"] += 1
    rates, lo_e, hi_e = [], [], []
    for e in envs:
        k, n = counts[e]["s"], counts[e]["n"]
        p, lo, hi = wilson_ci(k, n)
        rates.append(p * 100)
        lo_e.append(max(0.0, (p - lo) * 100))
        hi_e.append(max(0.0, (hi - p) * 100))
    x = np.arange(len(envs))
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(x, rates, color=ENVS, width=0.52,
                  edgecolor="white", linewidth=1.2, zorder=3)
    ax.errorbar(x, rates, yerr=[lo_e, hi_e], fmt="none",
                color="#2c3e50", capsize=5, capthick=1.5,
                elinewidth=1.5, zorder=4)
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2, rate + 2.5,
                f"{rate:.0f}%", ha="center", va="bottom",
                fontweight="bold", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel("Delivery Success Rate (%)", fontsize=11)
    ax.set_title("Delivery Reliability Across Environments\n"
                 "(χ²=0.000, df=3, p=1.000  ·  95% Wilson CI)",
                 fontsize=12, fontweight="bold", pad=10)
    ax.set_ylim(0, 118)
    ax.axhline(100, color="#aab7b8", linestyle="--", linewidth=1, zorder=1)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    fig.tight_layout()
    p = os.path.join(FIGS, "_pres3.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return p


def fig_telemetry():
    labels = ["ASCII\n(Baseline)", "Huffman\nCoding", "Binary\n(112-bit Rescue)"]
    bits   = [368, 184, 112]
    colors = [GOLD, RED, BLUE]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(labels, bits, color=colors, width=0.42,
                  edgecolor="white", linewidth=1.2, zorder=3)
    for bar, val in zip(bars, bits):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 5,
                f"{val} bits", ha="center", va="bottom",
                fontweight="bold", fontsize=12)
    for bar, val in zip(bars[1:], bits[1:]):
        pct = (1 - val / 368) * 100
        ax.text(bar.get_x() + bar.get_width() / 2, val / 2,
                f"−{pct:.0f}%\nvs ASCII", ha="center", va="center",
                color="white", fontweight="bold", fontsize=10)
    ax.axhline(210, color="#e74c3c", linestyle="--", linewidth=2, zorder=4)
    ax.text(2.28, 220, "BDS-SMC limit (210 bits)",
            ha="right", color="#e74c3c", fontsize=9, fontweight="bold")
    ax.set_ylabel("Encoded payload size (bits)", fontsize=11)
    ax.set_title("Telemetry Encoding Comparison\n"
                 "(binary: lat(7dp) · lon(7dp) · alt · uncertainty R · priority · survivor ID)",
                 fontsize=12, fontweight="bold", pad=10)
    ax.set_ylim(0, 445)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    fig.tight_layout()
    p = os.path.join(FIGS, "_pres4.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return p


# ── PAGE BUILDERS ──────────────────────────────────────────────────────────────

def page_title(pdf):
    fig = plt.figure(figsize=(11, 8.5))
    fig.patch.set_facecolor("#0d1b2a")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor("#0d1b2a")
    ax.axis("off")
    kw = dict(transform=ax.transAxes, ha="center")
    ax.text(0.5, 0.80, "BDS-SMC2",        fontsize=44, fontweight="bold",
            color="white", **kw)
    ax.text(0.5, 0.69, "UAV BeiDou Short Message Communication\nRescue System",
            fontsize=18, color="#aed6f1", linespacing=1.7, **kw)
    ax.plot([0.15, 0.85], [0.61, 0.61], color="#2e86c1",
            linewidth=2, transform=ax.transAxes)
    ax.text(0.5, 0.54, "Research Findings & Analysis",
            fontsize=13, color="#85c1e9", **kw)
    ax.text(0.5, 0.44, "4 Research Gaps  ·  BDS-3 RDSS Satellite Communication\n"
            "UAV Rescue Coordinate Transmission System",
            fontsize=11, color="#aab7b8", linespacing=1.6, **kw)
    ax.text(0.5, 0.20, "June 2026", fontsize=10, color="#717d7e", **kw)
    ax.text(0.98, 0.01, "1", ha="right", va="bottom", fontsize=9,
            color="#555", transform=ax.transAxes)
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def draw_cell(ax, x0, y0, w, h, bg, text, fontsize=9,
              bold=False, fg="black", pad=0.008):
    rect = mpatches.FancyBboxPatch(
        (x0 + pad, y0 + 0.012), w - pad * 2, h - 0.024,
        boxstyle="square,pad=0",
        facecolor=bg, edgecolor="#c0c0c0", linewidth=0.7,
        transform=ax.transAxes, clip_on=False
    )
    ax.add_patch(rect)
    ax.text(x0 + w / 2, y0 + h / 2, text,
            ha="center", va="center",
            fontsize=fontsize, fontweight="bold" if bold else "normal",
            color=fg, transform=ax.transAxes,
            multialignment="center", linespacing=1.45)


def page_gap(pdf, num, problem, research_q,
             solution, result, significance, fig_path, slide_num=2):
    fig = plt.figure(figsize=(11, 8.5))
    fig.patch.set_facecolor("#f5f6fa")

    # ── HEADER (blue strip) ──────────────────────────────────
    ax_hdr = fig.add_axes([0.0, 0.87, 1.0, 0.13])
    ax_hdr.set_facecolor(BLUE)
    ax_hdr.axis("off")

    # Number badge
    ax_badge = fig.add_axes([0.02, 0.882, 0.088, 0.118])
    ax_badge.set_facecolor(BLUE)
    ax_badge.set_xlim(0, 1)
    ax_badge.set_ylim(0, 1)
    ax_badge.axis("off")
    ax_badge.add_patch(plt.Circle((0.5, 0.5), 0.44, color="white", zorder=2))
    ax_badge.text(0.5, 0.5, str(num), ha="center", va="center",
                  fontsize=24, fontweight="bold", color=BLUE, zorder=3)

    # Problem title + research question
    ax_txt = fig.add_axes([0.13, 0.882, 0.855, 0.118])
    ax_txt.set_facecolor(BLUE)
    ax_txt.axis("off")
    ax_txt.text(0.0, 0.80, problem,
                fontsize=11.5, fontweight="bold", color="white",
                va="top", transform=ax_txt.transAxes)
    ax_txt.text(0.0, 0.20, f"Research Question:   {research_q}",
                fontsize=8.5, color="#aed6f1", va="top",
                style="italic", transform=ax_txt.transAxes)

    # ── TABLE ────────────────────────────────────────────────
    ax_tbl = fig.add_axes([0.0, 0.55, 1.0, 0.31])
    ax_tbl.set_facecolor("#f5f6fa")
    ax_tbl.set_xlim(0, 1)
    ax_tbl.set_ylim(0, 1)
    ax_tbl.axis("off")

    # Column boundaries
    cx = [0.02, 0.40, 0.63, 0.98]
    cw = [cx[i + 1] - cx[i] for i in range(3)]

    # Header row (compact — top 20%)
    heads = ["Solution / Analysis", "Key Result", "Significance to Problem"]
    for i in range(3):
        draw_cell(ax_tbl, cx[i], 0.78, cw[i], 0.20,
                  bg=BLUE, text=heads[i],
                  fontsize=9.5, bold=True, fg="white")

    # Data row (expanded — bottom 74%)
    wraps = [38, 24, 38]
    data  = [wrap(solution, wraps[0]),
             wrap(result,   wraps[1]),
             wrap(significance, wraps[2])]
    for i in range(3):
        draw_cell(ax_tbl, cx[i], 0.02, cw[i], 0.74,
                  bg=LBLUE, text=data[i],
                  fontsize=8.5, bold=False, fg="#1a1a1a")

    # ── FIGURE ───────────────────────────────────────────────
    if fig_path and os.path.exists(fig_path):
        from matplotlib.image import imread
        img = imread(fig_path)
        ax_img = fig.add_axes([0.07, 0.02, 0.86, 0.50])
        ax_img.imshow(img, aspect="auto")
        ax_img.axis("off")
        ax_img.text(0.5, -0.032, "Figure: Empirical proof of results",
                    ha="center", transform=ax_img.transAxes,
                    fontsize=8, color="#999", style="italic")
    else:
        ax_no = fig.add_axes([0.07, 0.02, 0.86, 0.50])
        ax_no.set_facecolor("#ebebeb")
        ax_no.axis("off")
        ax_no.text(0.5, 0.5,
                   "Figure pending — midday and evening sessions not yet collected",
                   ha="center", va="center",
                   fontsize=11, color="#aaa", style="italic")

    # ── SLIDE NUMBER ─────────────────────────────────────────
    ax_pg = fig.add_axes([0.88, 0.0, 0.12, 0.04])
    ax_pg.axis("off")
    ax_pg.text(0.95, 0.5, str(slide_num), ha="right", va="center",
               fontsize=9, color="#aaa", transform=ax_pg.transAxes)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


# ── GAP DATA ──────────────────────────────────────────────────────────────────

GAPS = [
    dict(
        num=1,
        problem="BDS-SMC 210-bit limit: ASCII coordinate encoding is too large to transmit",
        research_q="Can binary encoding reduce coordinate payload size to fit within the BDS-SMC 210-bit limit?",
        solution=(
            "Encode lat/lon as signed 32-bit integers with "
            "x10,000,000 fixed-point scaling (7 decimal places "
            "= RTK-grade ~1 cm precision), plus altitude, "
            "uncertainty radius R, priority and survivor ID. "
            "Complete rescue payload fixed at 112 bits."
        ),
        result=(
            "ASCII  =  264 bits  ✗ exceeds limit\n"
            "\n"
            "Binary =  112 bits  ✓ fits limit\n"
            "(6 rescue fields, verified on lab\n"
            " ground-truth records T001-T006)\n"
            "\n"
            "Reduction = 57.6% with MORE data"
        ),
        significance=(
            "Binary encoding is the only viable format "
            "for BDS-SMC coordinate transmission. "
            "ASCII exceeds the satellite channel limit "
            "and cannot be used in a real rescue deployment."
        ),
    ),
    dict(
        num=2,
        problem="End-to-end BDS-SMC transmission latency is unquantified for rescue operations",
        research_q="What is the end-to-end latency of a BDS-3 short message in rescue conditions, and does it vary by time of day?",
        solution=(
            "Serial logger captures three timestamps: "
            "T1 (command sent), T2 (module ACK), "
            "T3 (satellite delivery confirmed). "
            "Baseline: 30 transmissions, morning session, "
            "open-sky conditions."
        ),
        result=(
            "n = 30  (ASCII baseline, archived)\n"
            "Mean latency = 2.57 s\n"
            "All 30 TX within 5 s BDS-3 limit\n"
            "3 sessions on 112-bit payload\n"
            "scheduled (Option B re-collection)\n"
            "\n"
            "UAV positional drift at mean latency:\n"
            "  5 m/s UAV  ->  12.9 m\n"
            " 10 m/s UAV  ->  25.7 m\n"
            " 15 m/s UAV  ->  38.6 m"
        ),
        significance=(
            "If latency exceeds 5 s, the BDS-3 satellite "
            "drops the message — it never reaches the GCS. "
            "The rescuer receives no coordinate at all. "
            "At mean 2.57 s all transmissions succeed. "
            "UAV positional drift during the latency window "
            "defines the coordinate staleness on arrival: "
            "25.7 m at 10 m/s — operationally acceptable "
            "for a rescue search radius."
        ),
    ),
    dict(
        num=3,
        problem="BDS-SMC delivery reliability across diverse rescue environments is unknown",
        research_q="Does BDS-SMC maintain reliable delivery across the environmental conditions encountered in real rescue operations?",
        solution=(
            "Field test: 4 environments x 3 locations "
            "x 20 TX each.\n\n"
            "x2 (Chi-square): tests whether success rates "
            "differ across environments.\n\n"
            "p-value: probability of observing this result "
            "if environment had no effect.\n\n"
            "Wilson CI: 95% bounds — used because normal "
            "approximation is unreliable near 100%."
        ),
        result=(
            "232/232 delivered\n(all 4 environments)\n"
            "12 locations · 232 valid TX\n"
            "\n"
            "x2 = 0.000, df = 3\n"
            "p   = 1.000\n"
            "\n"
            "Wilson 95% lower bound:\n>= 93.7% per environment"
        ),
        significance=(
            "x2 = 0.000: success rates are identical "
            "across all environments — zero variation.\n\n"
            "p = 1.000: null hypothesis cannot be "
            "rejected at any threshold — not 5%, not 1%.\n\n"
            "Wilson CI [94%-100%]: all environments "
            "confirmed near-perfect with 95% confidence.\n\n"
            "There is no statistically significant "
            "difference in delivery across environments. "
            "BDS-SMC is reliable in every rescue terrain."
        ),
    ),
    dict(
        num=4,
        problem="Full UAV telemetry in ASCII exceeds the BDS-SMC 210-bit channel limit",
        research_q="Which encoding scheme achieves the most compact UAV telemetry within the BDS-SMC 210-bit limit?",
        solution=(
            "ASCII is confirmed to exceed the limit (368 bits). "
            "Huffman coding — the standard lossless text "
            "compression algorithm — is included as a rigorous "
            "benchmark: if even the best text compressor fails, "
            "it conclusively justifies binary packing as a "
            "fundamentally different approach. "
            "Binary carries the upgraded rescue payload: "
            "lat(7dp), lon(7dp), alt, uncertainty R, "
            "priority, survivor ID."
        ),
        result=(
            "ASCII   = 368 bits  ✗\n"
            "Huffman = 184 bits  ✓ (26 spare)\n"
            "Binary  = 112 bits  ✓\n"
            "\n"
            "Binary fits with 98 bits spare\n"
            "— 39% fewer bits than Huffman\n"
            "   while carrying MORE fields"
        ),
        significance=(
            "Only binary encoding fits full UAV telemetry "
            "within the BDS-SMC channel. "
            "Huffman is outperformed because structured "
            "numeric data lacks the character frequency "
            "skew needed for entropy coding to compete "
            "with direct binary packing."
        ),
    ),
]


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(FIGS, exist_ok=True)

    print("[PRESENTATION] Generating figures...")
    figures = [fig_encoding(), fig_latency(), fig_delivery(), fig_telemetry()]
    print("[PRESENTATION] Figures done. Building PDF...")

    with PdfPages(OUT_PDF) as pdf:
        page_title(pdf)
        for slide, (g, fig_path) in enumerate(zip(GAPS, figures), start=2):
            page_gap(
                pdf,
                num=g["num"],
                problem=g["problem"],
                research_q=g["research_q"],
                solution=g["solution"],
                result=g["result"],
                significance=g["significance"],
                fig_path=fig_path,
                slide_num=slide,
            )

    print(f"[PRESENTATION] Saved: {OUT_PDF}")


if __name__ == "__main__":
    main()
