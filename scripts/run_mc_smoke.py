"""
run_mc_smoke.py
---------------
Loads your risk register, derives parameters, runs a small simulation
for the FIRST scenario only, and prints summary stats.
"""
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import sys

ROOT = Path(__file__).resolve().parents[1]  # repo root: .../RiskQuant
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from montecarlo_app.etl.risk_register_loader import (
    load_settings,
    load_risk_register,
    validate_required_columns,
    normalize_columns,
    validate_and_clean_values,
    load_mappings,
    derive_parameters,
)
from montecarlo_app.model.monte_carlo import simulate_scenario_row, summarize


def main():
    settings = load_settings()
    df_raw = load_risk_register(settings)
    validate_required_columns(df_raw)
    df = normalize_columns(df_raw)
    issues = validate_and_clean_values(df)
    if issues:
        print("⚠️  Value issues detected:", issues)

    maps = load_mappings()
    df_params = derive_parameters(df, maps)

    # Pick the first scenario as a smoke test
    row = df_params.iloc[0]
    samples = simulate_scenario_row(row, n_sims=10000, seed=42)
    stats = summarize(samples)

    print("\n🎲 Scenario:", row['Risk_ID'], "-", row['Risk_Description'][:60], "...")
    print("   Likelihood:", row['Likelihood'], "Impact:", row['Impact'])
    print("   λ ~ Triangular(", row['Lambda_Min'], row['Lambda_Mode'], row['Lambda_Max'], ")")
    print("   Loss ~ Triangular(", row['Loss_Min'], row['Loss_Mode'], row['Loss_Max'], ")")
    print("\n📊 Summary (USD):")
    for k in ["mean", "median", "p90", "p95", "p99", "min", "max", "stdev"]:
        if k in stats:
            print(f"  {k:>6}: {stats[k]:,.0f}")


 # --- NEW: Portfolio run across all scenarios ---
    from montecarlo_app.model.monte_carlo import simulate_portfolio
    port_samples, per_scn = simulate_portfolio(df_params, n_sims=10000, seed=42)
    port_stats = summarize(port_samples)

    print("\n🏦 Portfolio Summary (all scenarios)")
    for k in ["mean", "median", "p90", "p95", "p99", "min", "max", "stdev"]:
        if k in port_stats:
            print(f"  {k:>6}: {port_stats[k]:,.0f}")

    # Optional: show top 3 scenarios by p95 (not causal, just indicative)
    top3 = sorted(per_scn, key=lambda kv: kv[1].get("p95", 0.0), reverse=True)[:3]
    print("\nTop 3 scenarios by p95 (indicative):")
    for rid, s in top3:
        print(f"  {rid}: p95={s['p95']:,.0f}, mean={s['mean']:,.0f}")


    print("\nTop 3 scenarios by p95 (indicative):")
    for rid, s in top3:
        print(f"  {rid}: p95={s['p95']:,.0f}, mean={s['mean']:,.0f}")

    # --- Export artifacts ---
    outputs = Path(__file__).resolve().parents[1] / "data" / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    # 1) CSV of portfolio samples (one column)
    csv_path = outputs / "portfolio_samples.csv"
    np.savetxt(csv_path, port_samples, delimiter=",", header="annual_loss_usd", comments="")
    print(f"\n💾 Saved samples CSV → {csv_path}")

    # 2) Quick histogram (PNG)
    png_path = outputs / "portfolio_hist.png"
    plt.figure()
    plt.hist(port_samples, bins=50)
    plt.xlabel("Annual Loss (USD)")
    plt.ylabel("Frequency")
    plt.title("Portfolio Annual Loss Distribution")
    plt.tight_layout()
    plt.savefig(png_path, dpi=144)
    plt.close()
    print(f"🖼️ Saved histogram PNG → {png_path}")


if __name__ == "__main__":
    main()



