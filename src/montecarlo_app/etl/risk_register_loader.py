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

# --- Allowed sets & normalization helpers ---
ALLOWED = {
    "Likelihood": {"Very Low", "Low", "Medium", "High", "Critical"},
    "Impact": {"Low", "Medium", "High", "Critical"},
    "Status": {"Open", "In Progress", "Closed"},
}

# Common typo/synonym fixes (case-insensitive keys)
FIXUPS = {
    "likelihood": {
        "v low": "Very Low",
        "verylow": "Very Low",
        "med": "Medium",
        "medium ": "Medium",
        "mediuim": "Medium",
        "mod": "Medium",
        "hi": "High",
        "critical ": "Critical",
    },
    "impact": {
        "med": "Medium",
        "medium ": "Medium",
        "mod": "Medium",
        "crit": "Critical",
        "critical ": "Critical",
    },
    "status": {
        "inprogress": "In Progress",
        "in-progress": "In Progress",
        "wip": "In Progress",
        "opened": "Open",
        "close": "Closed",
    },
}

def _clean_token(value: str) -> str:
    if value is None:
        return value
    return " ".join(str(value).strip().split())  # trim + collapse whitespace

def _normalize_value(col: str, value: str) -> str:
    if value is None:
        return value
    v = _clean_token(value)
    key = v.lower().replace("-", "").replace("_", "").replace("  ", " ")
    fixes = FIXUPS.get(col.lower(), {})
    if key in fixes:
        return fixes[key]
    # Title-case common categorical values
    titled = v.title()
    return titled

def validate_and_clean_values(df: pd.DataFrame) -> list[str]:
    """Normalize categorical text and report any values still outside the allowed sets."""
    issues: list[str] = []

    # Normalize Likelihood / Impact / Status text
    for col in ("Likelihood", "Impact", "Status"):
        if col in df.columns:
            df[col] = df[col].map(lambda x: _normalize_value(col, x))

    # Validate against allowed sets
    for col, allowed in ALLOWED.items():
        if col in df.columns:
            bad_mask = ~df[col].isin(allowed) & df[col].notna()
            if bad_mask.any():
                bad_vals = sorted(df.loc[bad_mask, col].astype(str).unique().tolist())
                issues.append(f"{col}: unexpected values {bad_vals} (allowed: {sorted(allowed)})")

    return issues


def load_mappings() -> dict:
    """Load qualitative→numeric mappings from YAML."""
    m_path = project_root() / "src" / "montecarlo_app" / "config" / "mappings.yaml"
    with open(m_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def derive_parameters(df: pd.DataFrame, maps: dict) -> pd.DataFrame:
    """
    Using Likelihood/Impact columns, attach numeric parameters needed by the simulator:
    - Lambda_Min/Mode/Max
    - Loss_Min/Mode/Max
    """
    like_map = maps["likelihood_to_lambda"]
    imp_map  = maps["impact_to_loss"]

    def _like(row):
        cfg = like_map.get(row["Likelihood"])
        return pd.Series([cfg["min"], cfg["mode"], cfg["max"]], index=["Lambda_Min","Lambda_Mode","Lambda_Max"]) if cfg else pd.Series([None,None,None], index=["Lambda_Min","Lambda_Mode","Lambda_Max"])

    def _imp(row):
        cfg = imp_map.get(row["Impact"])
        return pd.Series([cfg["min"], cfg["mode"], cfg["max"]], index=["Loss_Min","Loss_Mode","Loss_Max"]) if cfg else pd.Series([None,None,None], index=["Loss_Min","Loss_Mode","Loss_Max"])

    df = df.copy()
    df[["Lambda_Min","Lambda_Mode","Lambda_Max"]] = df.apply(_like, axis=1)
    df[["Loss_Min","Loss_Mode","Loss_Max"]]       = df.apply(_imp, axis=1)
    return df


if __name__ == "__main__":
    settings = load_settings()
    df_raw = load_risk_register(settings)
    validate_required_columns(df_raw)
    df = normalize_columns(df_raw)

    issues = validate_and_clean_values(df)
    print("✅ Validation passed; columns normalized.")
    if issues:
        print("⚠️  Value issues detected:")
        for msg in issues:
            print("  -", msg)
    else:
        print("✅ Categorical values look good (Likelihood/Impact/Status).")

    mappings = load_mappings()
    df_params = derive_parameters(df, mappings)

    print("✅ Parameters derived (Lambda_*, Loss_*).")
    print(df_params[[
        "Risk_ID","Likelihood","Impact",
        "Lambda_Min","Lambda_Mode","Lambda_Max",
        "Loss_Min","Loss_Mode","Loss_Max"
    ]].head(5).to_string(index=False))


