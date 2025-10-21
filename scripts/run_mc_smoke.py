"""
run_mc_smoke.py
---------------
Loads your risk register, derives parameters, runs a small simulation
for the FIRST scenario only, and prints summary stats.
"""
from pathlib import Path
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


if __name__ == "__main__":
    # Optional: ensure working directory is repo root in your Run Configuration
    # or rely on your loader's project_root() logic.
    main()
