# src/plot.py
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

def save_histogram(samples: np.ndarray, out_path: Path, title: str, bins: int = 50) -> None:
    """
    Save a histogram (PNG) of the provided samples.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=120)
    ax.hist(samples, bins=bins)
    ax.set_title(title)
    ax.set_xlabel("Annual loss (USD)")
    ax.set_ylabel("Frequency")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
