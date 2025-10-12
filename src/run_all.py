# src/run_all.py
import csv
from pathlib import Path
import numpy as np
from sim import Scenario, simulate_annual_loss, summarize

def load_scenarios(csv_path: Path) -> list[Scenario]:
    scenarios = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scenarios.append(
                Scenario(
                    asset_id=row["asset_id"],
                    asset_name=row["asset_name"],
                    scenario=row["scenario"],
                    aro=float(row["aro"]),
                    impact_min=float(row["impact_min"]),
                    impact_mode=float(row["impact_mode"]),
                    impact_max=float(row["impact_max"]),
                    control_reduction=float(row.get("control_reduction", 0.0) or 0.0),
                )
            )
    return scenarios


def run_batch(input_csv: Path, output_csv: Path, n_iter: int = 50000):
    rng = np.random.default_rng(42)
    scenarios = load_scenarios(input_csv)
    results = []

    for s in scenarios:
        losses = simulate_annual_loss(s, n_iter=n_iter, rng=rng)
        stats = summarize(losses)
        results.append({
            "asset_id": s.asset_id,
            "asset_name": s.asset_name,
            "scenario": s.scenario,
            **stats,
        })
        print(f"✅ Simulated: {s.asset_id} {s.asset_name} / {s.scenario}")

    # Write summary CSV
    fieldnames = ["asset_id", "asset_name", "scenario", "mean", "p50", "p90", "p95", "max"]
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n📁 Saved results to {output_csv}")


if __name__ == "__main__":
    input_path = Path("../data/input/assets.csv")
    output_path = Path("../data/output/results_summary.csv")
    run_batch(input_path, output_path)
