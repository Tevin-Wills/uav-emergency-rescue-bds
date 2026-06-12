"""
gap3_analysis.py -- Gap 3: environmental reliability analysis.

Reads data/gap3_field_test.csv and produces:
  - Per-environment success rate table with 95% binomial CI
  - Chi-square test across all 4 environments
  - Pairwise Fisher's exact tests with Bonferroni correction
  - Per-location breakdown (for multi-location experiments)

Usage:
    python gap3_analysis.py                   # reads real data
    python gap3_analysis.py --demo            # synthetic data for all 4 environments
"""

import csv
import argparse
import os
import math
from collections import defaultdict

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "gap3_field_test.csv")

ENVIRONMENTS = ["open_sky", "light_canopy", "urban_canyon", "indoor"]


def load_data(path):
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "env":      r.get("environment", ""),
                "location": r.get("location_id", ""),
                "result":   r.get("result", ""),
                "latency":  int(r["latency_ms"]) if r.get("latency_ms", "-1").lstrip("-").isdigit() else -1,
            })
    return rows


def demo_data():
    import random
    rates = {"open_sky": 0.95, "light_canopy": 0.80, "urban_canyon": 0.60, "indoor": 0.25}
    rows = []
    for env in ENVIRONMENTS:
        locs = [f"{env[:2].upper()}-{i}" for i in range(1, 4)]
        for loc in locs:
            for _ in range(20):
                ok  = random.random() < rates[env]
                lat = random.randint(1200, 4000) if ok else -1
                rows.append({"env": env, "location": loc,
                             "result": "success" if ok else "fail", "latency": lat})
    return rows


def binomial_ci(k, n, z=1.96):
    """Wilson score interval."""
    if n == 0:
        return 0, 0, 0
    p_hat = k / n
    denom = 1 + z**2 / n
    centre = (p_hat + z**2 / (2 * n)) / denom
    margin = (z * math.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2))) / denom
    return p_hat, max(0, centre - margin), min(1, centre + margin)


def chi_square_2x4(counts):
    """Chi-square test on a 2-row (success/fail) x k-column (environments) table."""
    envs   = [e for e in ENVIRONMENTS if e in counts]
    k      = len(envs)
    if k < 2:
        return float("nan"), float("nan"), k - 1

    obs    = [[counts[e]["success"], counts[e]["fail"]] for e in envs]
    totals = [sum(col) for col in obs]
    row_s  = [sum(r[i] for r in obs) for i in range(2)]
    N      = sum(totals)

    chi2 = 0
    for j, col in enumerate(obs):
        for i, observed in enumerate(col):
            expected = (row_s[i] * totals[j]) / N if N > 0 else 0
            if expected > 0:
                chi2 += (observed - expected) ** 2 / expected

    df = k - 1
    try:
        from scipy.stats import chi2 as chi2_dist
        p = 1 - chi2_dist.cdf(chi2, df)
    except ImportError:
        p = float("nan")

    return chi2, p, df


def fisher_pairwise(counts):
    """Pairwise Fisher's exact tests with Bonferroni correction."""
    envs = [e for e in ENVIRONMENTS if e in counts]
    pairs = [(envs[i], envs[j]) for i in range(len(envs)) for j in range(i+1, len(envs))]
    n_comparisons = len(pairs)
    results = []

    for a, b in pairs:
        ca, cb = counts[a], counts[b]
        table  = [[ca["success"], cb["success"]], [ca["fail"], cb["fail"]]]
        try:
            from scipy.stats import fisher_exact
            _, p_raw = fisher_exact(table)
        except ImportError:
            p_raw = float("nan")
        p_bonf = min(1.0, p_raw * n_comparisons) if not math.isnan(p_raw) else float("nan")
        results.append((a, b, p_raw, p_bonf))

    return results, n_comparisons


def print_report(rows):
    # Exclude legacy OS-1 timeout rows from before the T3 bug fix
    rows = [r for r in rows if r["result"] != "timeout"]

    by_env = defaultdict(lambda: {"success": 0, "fail": 0, "latencies": [], "locations": set()})
    for r in rows:
        env = r["env"]
        if r["result"] == "success":
            by_env[env]["success"] += 1
            if r["latency"] > 0:
                by_env[env]["latencies"].append(r["latency"])
        else:
            by_env[env]["fail"] += 1
        by_env[env]["locations"].add(r["location"])

    print(f"\n{'Environment':<20} {'Locs':>5} {'Succ':>6} {'Total':>6} "
          f"{'Rate':>8} {'95% CI (Wilson)':>18} {'Avg Lat':>10}")
    print("-" * 78)

    for env in ENVIRONMENTS:
        c  = by_env.get(env)
        if not c:
            print(f"{env:<20}  -- no data --")
            continue
        n  = c["success"] + c["fail"]
        p, lo, hi = binomial_ci(c["success"], n)
        avg_lat = int(sum(c["latencies"]) / len(c["latencies"])) if c["latencies"] else -1
        locs = len(c["locations"])
        ci_str = f"[{lo*100:.1f}%, {hi*100:.1f}%]"
        print(f"{env:<20} {locs:>5} {c['success']:>6} {n:>6} "
              f"{p*100:>7.1f}% {ci_str:>18} {avg_lat:>9}ms")

    # Chi-square
    chi2, p_chi, df = chi_square_2x4(by_env)
    p_chi_str = f"{p_chi:.4f}" if not math.isnan(p_chi) else "install scipy"
    sig = "SIGNIFICANT" if (not math.isnan(p_chi) and p_chi < 0.05) else "not significant"
    print(f"\n[CHI-SQUARE] chi2={chi2:.3f}  df={df}  p={p_chi_str}  ({sig})")
    print("[CHI-SQUARE] H0: environment has no effect on delivery success rate")

    # Pairwise Fisher's exact with Bonferroni
    pairs, n_comp = fisher_pairwise(by_env)
    if pairs:
        print(f"\n[PAIRWISE FISHER'S EXACT] Bonferroni correction (n={n_comp} comparisons)")
        print(f"  {'Pair':<40} {'p_raw':>10} {'p_Bonferroni':>14} {'Sig':>5}")
        print("  " + "-" * 72)
        for a, b, p_raw, p_bonf in pairs:
            p_raw_str  = f"{p_raw:.4f}"  if not math.isnan(p_raw)  else "n/a"
            p_bonf_str = f"{p_bonf:.4f}" if not math.isnan(p_bonf) else "n/a"
            sig_mark   = "*" if (not math.isnan(p_bonf) and p_bonf < 0.05) else ""
            print(f"  {a} vs {b:<25} {p_raw_str:>10} {p_bonf_str:>14} {sig_mark:>5}")

    # Location breakdown if multi-location
    all_locations = set(r["location"] for r in rows if r["location"])
    if len(all_locations) > len(ENVIRONMENTS):
        by_loc = defaultdict(lambda: {"success": 0, "fail": 0})
        for r in rows:
            by_loc[r["location"]][r["result"]] += 1
        print(f"\n[LOCATION BREAKDOWN]")
        print(f"  {'Location':<12} {'Succ':>6} {'Total':>6} {'Rate':>8}")
        print("  " + "-" * 36)
        for loc in sorted(all_locations):
            c = by_loc[loc]
            n = c["success"] + c["fail"]
            rate = c["success"] / n * 100 if n else 0
            print(f"  {loc:<12} {c['success']:>6} {n:>6} {rate:>7.1f}%")


def main():
    parser = argparse.ArgumentParser(description="Gap 3 environmental reliability analysis")
    parser.add_argument("--input", default=DATA_FILE)
    parser.add_argument("--demo",  action="store_true", help="Use synthetic data")
    args = parser.parse_args()

    if args.demo:
        print("[DEMO] Using synthetic 4-environment data (20 TX x 3 locations each)")
        rows = demo_data()
    else:
        if not os.path.exists(args.input):
            print(f"[ERROR] {args.input} not found. Run field_test_logger.py first.")
            print("        Or use --demo to test with synthetic data.")
            return
        rows = load_data(args.input)

    print(f"\n[GAP 3 ANALYSIS] {len(rows)} transmissions loaded")
    print_report(rows)


if __name__ == "__main__":
    main()
