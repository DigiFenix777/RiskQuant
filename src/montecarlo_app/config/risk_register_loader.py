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


REQUIRED_HEADERS = {
    "Risk ID": "Risk_ID",
    "Risk Description": "Risk_Description",
    "Regulatory Impact": "Regulatory_Impact",
    "Likelihood": "Likelihood",
    "Impact": "Impact",
    "Risk Rating": "Risk_Rating",              # derived/metadata
    "Mitigation/Control": "Control_Description",
    "Responsible Party": "Owner",
    "Status": "Status",
}

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename human-friendly headers to stable internal names."""
    rename_map = {k: v for k, v in REQUIRED_HEADERS.items() if k in df.columns}
    return df.rename(columns=rename_map)

def validate_required_columns(df: pd.DataFrame) -> None:
    """Raise a clear error if any expected columns are missing."""
    missing = [k for k in REQUIRED_HEADERS if k not in df.columns and REQUIRED_HEADERS[k] not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )

def print_preview(df: pd.DataFrame, n: int = 5) -> None:
    """Show a tiny preview for sanity without spamming console."""
    print("Preview (first rows):")
    print(df.head(n).to_string(index=False))

if __name__ == "__main__":
    settings = load_settings()
    df_raw = load_risk_register(settings)
    validate_required_columns(df_raw)
    df = normalize_columns(df_raw)

    print("✅ Validation passed; columns normalized.")
    print(f"Normalized columns: {list(df.columns)}")
    print_preview(df, n=5)

