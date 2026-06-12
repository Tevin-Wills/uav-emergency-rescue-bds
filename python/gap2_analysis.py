"""
gap2_analysis.py -- Gap 2: end-to-end latency analysis across sessions.

Reads data/gap2_latency.csv (all sessions combined) and produces:
  - Per-session descriptive stats table
  - One-way ANOVA across sessions (morning / midday / evening / baseline)
  - CDF plot saved to figures/fig_gap2_cdf.png
  - UAV positional error model (max drift at given speed)

Option B (2026-06-12): all three sessions (morning/midday/evening) are collected
with the 112-bit binary rescue payload. The original 30-TX ASCII-payload baseline
is archived in data/gap2_latency_ascii_baseline.csv and is NOT part of the
time-of-day ANOVA (different payload would confound it). Use --ascii-baseline to
append it as a separate group for a secondary payload-format comparison.

Usage:
    python gap2_analysis.py                   # reads real data
    python gap2_analysis.py --demo            # synthetic multi-session data
    python gap2_analysis.py --plot            # also save CDF figure
    python gap2_analysis.py --ascii-baseline  # include archived ASCII baseline as extra group
"""

import csv
import argparse
import os
import statistics
import math
from collections import defaultdict

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "gap2_latency.csv")
FIG_DIR   = os.path.join(os.path.dirname(__file__), "..", "figures")


def load_data(path):
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                lat = int(r["tx_latency_ms"])
                if lat > 0:
                    rows.append({
                        "tx_num":   int(r.get("tx_num", 0)),
                        "session":  r.get("session", "unknown"),
                        "weather":  r.get("weather", ""),
                        "latency":  lat,
                    })
            except (ValueError, KeyError):
                continue
    return rows


def demo_data():
    import random
    sessions = {"morning": 34, "midday": 33, "evening": 33}
    rows = []
    tx = 31
    means = {"morning": 2400, "midday": 2700, "evening": 2300}
    for sess, n in sessions.items():
        for _ in range(n):
            lat = max(800, int(random.gauss(means[sess], 900)))
            rows.append({"tx_num": tx, "session": sess, "weather": "clear", "latency": lat})
            tx += 1
    return rows


def descriptive_stats(latencies):
    if not latencies:
        return {}
    s = sorted(latencies)
    n = len(s)
    mean = statistics.mean(s)
    std  = statistics.stdev(s) if n > 1 else 0
    p95  = s[int(math.ceil(0.95 * n)) - 1]
    return {
        "n": n, "mean": mean, "std": std,
        "min": s[0], "median": statistics.median(s),
        "p95": p95, "max": s[-1],
    }


def anova_f(groups):
    """One-way ANOVA F-statistic and p-value (manual implementation)."""
    all_vals = [v for g in groups for v in g]
    grand_mean = statistics.mean(all_vals)
    k = len(groups)
    N = len(all_vals)

    ss_between = sum(len(g) * (statistics.mean(g) - grand_mean) ** 2 for g in groups)
    ss_within  = sum((v - statistics.mean(g)) ** 2 for g in groups for v in g)

    df_between = k - 1
    df_within  = N - k

    if ss_within == 0 or df_within == 0:
        return float("nan"), float("nan")

    ms_between = ss_between / df_between
    ms_within  = ss_within  / df_within
    F = ms_between / ms_within

    # Approximate p-value using scipy if available, else report F only
    try:
        from scipy.stats import f as f_dist
        p = 1 - f_dist.cdf(F, df_between, df_within)
    except ImportError:
        p = float("nan")

    return F, p


def uav_error_model(latency_ms, speeds_ms=(5, 10, 15)):
    """Max UAV positional error for given latency and UAV speeds."""
    return {s: round(s * latency_ms / 1000, 1) for s in speeds_ms}


def print_stats_table(rows):
    by_session = defaultdict(list)
    for r in rows:
        by_session[r["session"]].append(r["latency"])

    all_lat = [r["latency"] for r in rows]
    all_stats = descriptive_stats(all_lat)

    print(f"\n{'Session':<12} {'N':>5} {'Mean':>8} {'Std':>8} {'Min':>6} "
          f"{'Med':>6} {'P95':>6} {'Max':>6}")
    print("-" * 65)

    for sess, lats in sorted(by_session.items()):
        st = descriptive_stats(lats)
        print(f"{sess:<12} {st['n']:>5} {st['mean']:>8.0f} {st['std']:>8.0f} "
              f"{st['min']:>6} {st['median']:>6.0f} {st['p95']:>6} {st['max']:>6}")

    print("-" * 65)
    print(f"{'ALL':<12} {all_stats['n']:>5} {all_stats['mean']:>8.0f} "
          f"{all_stats['std']:>8.0f} {all_stats['min']:>6} "
          f"{all_stats['median']:>6.0f} {all_stats['p95']:>6} {all_stats['max']:>6}")

    # ANOVA
    groups = [lats for lats in by_session.values() if len(lats) > 1]
    if len(groups) >= 2:
        F, p = anova_f(groups)
        sig = "SIGNIFICANT" if (not math.isnan(p) and p < 0.05) else "not significant"
        p_str = f"{p:.4f}" if not math.isnan(p) else "install scipy for p-value"
        print(f"\n[ANOVA] F={F:.3f}  p={p_str}  ({sig} at alpha=0.05)")
        print("[ANOVA] Null hypothesis: session has no effect on latency")
    else:
        print("\n[ANOVA] Need >= 2 sessions. Add morning/midday/evening data.")

    # UAV error model at mean latency
    mean_lat = all_stats["mean"]
    p95_lat  = all_stats["p95"]
    print(f"\n[UAV ERROR MODEL] At mean latency {mean_lat:.0f}ms:")
    for speed, err in uav_error_model(mean_lat).items():
        print(f"  UAV @ {speed:2d} m/s -> max positional error = {err}m")
    print(f"[UAV ERROR MODEL] At 95th-pct latency {p95_lat:.0f}ms:")
    for speed, err in uav_error_model(p95_lat).items():
        print(f"  UAV @ {speed:2d} m/s -> max positional error = {err}m")


def save_cdf(rows, out_path):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[PLOT] matplotlib not found. Run: pip install matplotlib")
        return

    by_session = defaultdict(list)
    for r in rows:
        by_session[r["session"]].append(r["latency"])

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    for (sess, lats), color in zip(sorted(by_session.items()), colors):
        s = sorted(lats)
        cdf = [(i + 1) / len(s) for i in range(len(s))]
        ax.plot(s, cdf, label=f"{sess} (n={len(s)})", color=color, linewidth=2)

    ax.axvline(x=1000, color="gray", linestyle="--", alpha=0.5, label="1s")
    ax.axvline(x=5000, color="red",  linestyle="--", alpha=0.5, label="5s (BDS-3 limit)")
    ax.set_xlabel("End-to-end latency (ms)", fontsize=12)
    ax.set_ylabel("Cumulative probability", fontsize=12)
    ax.set_title("BDS-3 SMC Latency CDF by Session (Gap 2)", fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"[PLOT] CDF saved to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Gap 2 latency analysis")
    parser.add_argument("--input", default=DATA_FILE)
    parser.add_argument("--demo",  action="store_true", help="Use synthetic multi-session data")
    parser.add_argument("--plot",  action="store_true", help="Save CDF figure")
    parser.add_argument("--ascii-baseline", action="store_true",
                        help="Append archived ASCII-payload baseline as a separate group "
                             "(payload-format comparison — NOT part of the time-of-day ANOVA claim)")
    args = parser.parse_args()

    if args.demo:
        print("[DEMO] Using synthetic multi-session data (30 baseline + 100 new TX)")
        existing = load_data(args.input) if os.path.exists(args.input) else []
        rows = existing + demo_data()
    else:
        if not os.path.exists(args.input):
            print(f"[ERROR] {args.input} not found. Run with --demo to test.")
            return
        rows = load_data(args.input)

    if args.ascii_baseline:
        archive = os.path.join(os.path.dirname(DATA_FILE), "gap2_latency_ascii_baseline.csv")
        if os.path.exists(archive):
            old = load_data(archive)
            for r in old:
                r["session"] = "ascii_baseline"
            rows += old
            print(f"[INFO] Appended {len(old)} archived ASCII-baseline rows as group 'ascii_baseline'")
        else:
            print(f"[WARN] {archive} not found — skipping ASCII baseline")

    print(f"\n[GAP 2 ANALYSIS] {len(rows)} transmissions loaded")
    print_stats_table(rows)

    if args.plot:
        fig_path = os.path.join(FIG_DIR, "fig_gap2_cdf.png")
        save_cdf(rows, fig_path)


if __name__ == "__main__":
    main()
