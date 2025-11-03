"""
monte_carlo.py
--------------
Minimal scenario-level simulator.
- Samples event frequency using Poisson with λ drawn from a triangular prior.
- Samples loss per event from a triangular distribution and sums per run.

Note: Controls, correlations, and portfolio aggregation come later.
"""

from __future__ import annotations

import numpy as np


def simulate_scenario_row(row, n_sims: int = 10000, seed: int | None = 42) -> np.ndarray:
    """
    Simulate annual loss distribution for one scenario (row from df_params).
    Returns: np.ndarray of length n_sims with total annual loss per run.
    """
    rng = np.random.default_rng(seed)

    # 1) Sample λ per simulation run from triangular(Lambda_Min, Lambda_Mode, Lambda_Max)
    lam = rng.triangular(row["Lambda_Min"], row["Lambda_Mode"], row["Lambda_Max"], n_sims)

    # 2) Sample event counts from Poisson(λ)
    freq = rng.poisson(lam)

    # 3) For each run, sample `freq[i]` loss events from triangular(Loss_Min, Loss_Mode, Loss_Max) and sum
    losses = np.zeros(n_sims, dtype=float)
    loss_min, loss_mode, loss_max = row["Loss_Min"], row["Loss_Mode"], row["Loss_Max"]

    # Efficient, readable loop over only runs that have events
    idxs = np.nonzero(freq)[0]
    for i in idxs:
        k = freq[i]
        # Sum k sampled losses for this simulation run
        losses[i] = rng.triangular(loss_min, loss_mode, loss_max, k).sum()

    return losses


def summarize(samples: np.ndarray, percentiles=(50, 90, 95, 99)) -> dict:
    """Quick stats for sanity checks."""
    out = {
        "mean": float(np.mean(samples)),
        "median": float(np.median(samples)),
        "stdev": float(np.std(samples, ddof=1)) if len(samples) > 1 else 0.0,
        "min": float(np.min(samples)) if len(samples) else 0.0,
        "max": float(np.max(samples)) if len(samples) else 0.0,
    }
    for p in percentiles:
        out[f"p{p}"] = float(np.percentile(samples, p))
    return out


def simulate_portfolio(df_params, n_sims: int = 10000, seed: int | None = 42):
    """
    Simulate portfolio annual loss by summing scenario losses per run.
    Returns:
      - portfolio_samples: np.ndarray shape (n_sims,)
      - scenario_summaries: list of (risk_id, stats_dict)
    """
    rng = np.random.default_rng(seed)
    portfolio = np.zeros(n_sims, dtype=float)
    scenario_summaries = []

    for _, row in df_params.iterrows():
        # Use a derived seed per scenario for reproducibility without coupling
        scenario_seed = None if seed is None else int(rng.integers(0, 2**31 - 1))
        samples = simulate_scenario_row(row, n_sims=n_sims, seed=scenario_seed)
        portfolio += samples
        scenario_summaries.append((row["Risk_ID"], summarize(samples)))

    return portfolio, scenario_summaries
