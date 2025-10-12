# src/run_portfolio.py
from pathlib import Path
import csv
import numpy as np
from sim import simulate_annual_loss, summarize
from run_all import load_scenarios   # reuse the loader you already wrote
from plot import save_histogram

def simulate_portfolio(input_csv: Path, n_iter: int = 50000, seed: int = 42) -> np.ndarray:
    """
    Simulate portfolio annual loss by summing scenario losses element-wise.
    Uses a shared RNG so all scenarios have the same number of trials.
    """
    rng = np.random.default_rng(seed)
    scenarios = load_scenarios(input_csv)
    if not scenarios:
        return np.zeros(n_iter)

    losses_per_scenario = []
    for s in scenarios:
        losses = simulate_annual_loss(s, n_iter=n_iter, rng=rng)
        losses_per_scenario.append(losses)

    # Sum across scenarios for each iteration to form portfolio loss distribution
    portfolio_losses = np.sum(losses_per_scenario, axis=0)
    return portfolio_losses

if __name__ == "__main__":
    input_path = Path("../data/input/assets.csv")
    output_csv = Path("../data/output/portfolio_summary.csv")
    output_png = Path("../data/output/portfolio_loss_distribution.png")

    portfolio_losses = simulate_portfolio(input_path, n_iter=50000, seed=42)
    stats = summarize(portfolio_losses)

    # Write a one-row CSV with portfolio stats
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["mean", "p50", "p90", "p95", "max"])
        writer.writeheader()
        writer.writerow(stats)

    # Save histogram PNG
    save_histogram(
        portfolio_losses,
        output_png,
        title=f"Portfolio Annual Loss Distribution (n={len(portfolio_losses):,})"
    )

    print("✅ Portfolio simulation complete.")
    print(f"📁 Summary CSV: {output_csv}")
    print(f"🖼️ Histogram PNG: {output_png}")
    print(f"📊 Stats: {stats}")
