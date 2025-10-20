"""
risk_register_loader.py
-----------------------
Load the risk register Excel file and print headers.
Resolves absolute paths automatically so it runs from anywhere.
"""

import yaml
import pandas as pd
from pathlib import Path


def project_root() -> Path:
    """Return the absolute path to the repo root (where .git/ lives)."""
    current = Path(__file__).resolve()
    # This file lives in .../src/montecarlo_app/etl/
    return current.parents[3]  # go up 3 levels to the project root


def load_settings() -> dict:
    """Read YAML configuration using absolute path."""
    settings_path = project_root() / "src/montecarlo_app/config/settings.yaml"
    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_risk_register(settings: dict) -> pd.DataFrame:
    """Load the Excel file defined in settings.yaml using absolute path."""
    data_path = project_root() / settings["data"]["risk_register_path"]
    if not data_path.exists():
        raise FileNotFoundError(f"❌ Risk register not found at: {data_path}")
    df = pd.read_excel(data_path)
    return df


if __name__ == "__main__":
    settings = load_settings()
    df = load_risk_register(settings)
    print("✅ Loaded Risk Register successfully!")
    print(f"File path: {project_root() / settings['data']['risk_register_path']}")
    print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    print("Column headers:")
    print(df.columns.tolist())
