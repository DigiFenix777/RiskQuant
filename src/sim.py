# src/sim.py
from dataclasses import dataclass
import numpy as np

@dataclass
class Scenario:
    asset_id: str
    asset_name: str
    scenario: str
    aro: float                  # expected incidents/year (λ)
    impact_min: float           # USD
    impact_mode: float          # USD
    impact_max: float           # USD
    control_reduction: float = 0.0  # 0.0 - 1.0

def simulate_annual_loss(s: Scenario, n_iter: int = 50000, rng: np.random.Generator | None = None) -> np.ndarray:
    """
    Returns an array of simulated annual losses (USD) for one scenario.
    Frequency: Poisson(λ = aro). Impact: Triangular(min, mode, max).
    Control reduction is applied multiplicatively to loss (clamped 0..1).
    """
    rng = rng or np.random.default_rng()
    # Sample number of incidents each year
    incidents = rng.poisson(lam=max(s.aro, 0.0), size=n_iter)
    # Sample loss per incident
    impact = rng.triangular(left=s.impact_min, mode=s.impact_mode, right=s.impact_max, size=n_iter)
    # Annual loss = incidents * impact (vectorized by resampling impact for each incident approximation)
    # Approximate by scaling impact by incidents (fast & simple for MVP)
    gross_loss = incidents * impact
    reduction = np.clip(1.0 - float(s.control_reduction), 0.0, 1.0)
    return gross_loss * reduction

def summarize(losses: np.ndarray) -> dict:
    q = np.percentile(losses, [50, 90, 95])
    return {
        "mean": float(losses.mean()),
        "p50": float(q[0]),
        "p90": float(q[1]),
        "p95": float(q[2]),
        "max": float(losses.max())
    }
