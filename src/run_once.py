# src/run_once.py
import csv
from pathlib import Path
import numpy as np
from sim import Scenario, simulate_annual_loss, summarize

def load_first_row(csv_path: Path) -> Scenario:
    with csv_path.open(newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    return Scenario(
        asset_id=row["asset_id"],
        asset_name=row["asset_name"],
        scenario=row["scenario"],
        aro=float(row["aro"]),
        impact_min=float(row["impact_min"]),
        impact_mode=float(row["impact_mode"]),
        impact_max=float(row["impact_max"]),
        control_reduction=float(row.get("control_reduction", 0.0) or 0.0),
    )

if __name__ == "__main__":
    path = Path("../data/input/assets.csv")
    s = load_first_row(path)
    samples = simulate_annual_loss(s, n_iter=50000, rng=np.random.default_rng(42))
    stats = summarize(samples)
    print(f"[{s.asset_id}] {s.asset_name} / {s.scenario}")
    print(stats)
