"""
Streamlit MVP — Cyber Risk Simulation Dashboard
- Loads your Excel risk register via existing ETL helpers
- Derives parameters, simulates portfolio
- Shows KPI cards + Histogram + CDF + Scenario Comparison + Risk Matrix
- Exports CSV of portfolio samples and run manifest JSON

Run locally:
    streamlit run src/montecarlo_app/dashboard/app.py
"""

from __future__ import annotations

import json
import os
import sys
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------- UI: Page Setup ----------
st.set_page_config(page_title="Cyber Risk Simulation Dashboard", layout="wide")
st.title("📊 Cyber Risk Simulation Dashboard")
st.caption("Quantify annual cyber loss with Monte Carlo. Adjust assumptions and see impact instantly.")

# Ensure we can import from src/
ROOT = Path(__file__).resolve().parents[3]  # .../RiskQuant
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from montecarlo_app.etl.risk_register_loader import (  # noqa: E402
    derive_parameters,
    load_mappings,
    load_risk_register,
    load_settings,
    normalize_columns,
    validate_and_clean_values,
    validate_required_columns,
)
from montecarlo_app.model.monte_carlo import (  # noqa: E402
    simulate_portfolio,
    simulate_scenario_row,
    summarize,
)

# ---------- Sidebar Controls ----------
with st.sidebar:
    # Brand Header
    st.markdown("## 🧮 RiskQuant")
    st.divider()

    # Load baseline settings.yaml
    settings = load_settings()

    # =======================
    # Configure Simulation
    # =======================
    st.subheader("⚙️ Configure Simulation")

    n_sims = st.number_input(
        "Number of Simulations",
        min_value=1000,
        max_value=200000,
        value=int(settings["simulation"]["runs"]),
        step=1000,
    )
    seed = st.number_input(
        "Random Seed",
        min_value=0,
        max_value=10**7,
        value=int(settings["simulation"]["seed"]),
        step=1,
    )

    with st.expander("Advanced Settings", expanded=False):
        show_percentiles = st.multiselect(
            "Percentiles to Show",
            options=[50, 90, 95, 99],
            default=settings["simulation"]["percentiles"],
        )
        currency = st.selectbox("Currency", options=["USD"], index=0)

    # Fallbacks if Advanced not opened
    if "show_percentiles" not in locals():
        show_percentiles = settings["simulation"]["percentiles"]
    if "currency" not in locals():
        currency = "USD"

    st.divider()

    # =======================
    # Input Data
    # =======================
    st.subheader("📥 Input Data")

    with st.expander("📂 Data Source", expanded=False):

        def _list_register_files():
            root = ROOT / "data" / "input"
            root.mkdir(parents=True, exist_ok=True)
            return sorted([p for p in root.glob("*.xlsx") if p.is_file()])

        register_files = _list_register_files()
        options = [p.stem for p in register_files]

        # Default to the file referenced in settings.yaml when present
        default_stem = None
        try:
            current_rel = settings["data"]["risk_register_path"]
            current_abs = (ROOT / current_rel).resolve()
            if current_abs.exists():
                default_stem = current_abs.stem
        except Exception:
            default_stem = None

        default_index = options.index(default_stem) if default_stem in options else (0 if options else None)

        selected_name = st.selectbox(
            "Select Risk Register",
            options,
            index=default_index,
            key="risk_register_choice",
        )

        def _clear_data_cache() -> None:
            try:
                st.cache_data.clear()
            except Exception:
                pass

        st.button("🔄 Reload data", on_click=_clear_data_cache)

        # Override settings with selected file
        settings_selected = dict(settings)
        settings_selected.setdefault("data", dict(settings.get("data", {})))

        chosen_path = None
        if selected_name and register_files:
            stems = {p.stem: p for p in register_files}
            chosen_path = stems.get(selected_name)

        if chosen_path is not None:
            rel_path = chosen_path.resolve().relative_to(ROOT)
            settings_selected["data"]["risk_register_path"] = str(rel_path)

        # Display actual path used
        risk_register_path_display = settings_selected["data"]["risk_register_path"]
        st.caption(f"Using risk register:\n{risk_register_path_display}")

    # Fallback if expander not opened
    if "settings_selected" not in locals():
        settings_selected = settings
        risk_register_path_display = settings["data"]["risk_register_path"]

    st.divider()

    # =======================
    # Quantify Risk
    # =======================
    st.subheader("🚀 Quantify Risk")

    if "run" not in st.session_state:
        st.session_state.run = False

    if st.button("▶ Run Simulation", key="run_btn", type="primary", use_container_width=True):
        st.session_state.run = True
    if st.button("↺ Reset", key="reset_btn", type="secondary", use_container_width=True):
        st.session_state.run = False


# ---------- Data Prep (cached) ----------
@st.cache_data(show_spinner=False)
def _prepare_params(_settings) -> pd.DataFrame:
    df_raw = load_risk_register(_settings)
    validate_required_columns(df_raw)
    df = normalize_columns(df_raw)
    _issues = validate_and_clean_values(df)
    maps = load_mappings()
    df_params = derive_parameters(df, maps)

    # Derive Category from Risk_ID prefix (e.g., GOV-01 -> GOV)
    df_params = df_params.copy()
    df_params["Category"] = df_params["Risk_ID"].astype(str).str.split("-").str[0]

    # Ensure numeric dtypes for MC parameter columns (FutureWarning-safe)
    for col in ["Lambda_Min", "Lambda_Mode", "Lambda_Max", "Loss_Min", "Loss_Mode", "Loss_Max"]:
        if col in df_params.columns:
            df_params[col] = pd.to_numeric(df_params[col], errors="coerce")
    return df_params


# ---------- Helper: normalize per_scn into standard shapes ----------
def normalize_per_scn(per_scn_obj):
    """
    Normalize per_scn into one (or both) canonical forms:
      A) Samples DF:  columns ['Risk_ID', 'Annual_Loss']
      B) Summary DF:  columns ['Risk_ID', 'mean', 'median', 'p95']
    Handles: dicts, lists/tuples of (rid, samples), DataFrames with varied col names,
             dict values that are dicts (e.g., {'samples': [...]}), numpy arrays.
    """

    empty_samples = pd.DataFrame(columns=["Risk_ID", "Annual_Loss"])
    empty_summary = pd.DataFrame(columns=["Risk_ID", "mean", "median", "p95"])

    if per_scn_obj is None:
        return empty_samples, empty_summary

    # -------- Case: dict ----------
    if isinstance(per_scn_obj, dict):
        rows = []
        sum_rows = []
        for rid, val in per_scn_obj.items():
            rid = str(rid)
            # val might be: array-like, dict with 'samples', dict with stats, etc.
            if isinstance(val, dict):
                # samples?
                if "samples" in val and val["samples"] is not None:
                    arr = np.asarray(val["samples"]).flatten()
                    rows.extend([(rid, float(v)) for v in arr])
                # summary?
                has_stats = any(k in val for k in ("mean", "median", "p95"))
                if has_stats:
                    mean = float(val.get("mean", np.nan))
                    median = float(val.get("median", np.nan))
                    p95 = float(val.get("p95", np.nan))
                    sum_rows.append((rid, mean, median, p95))
            else:
                # assume array-like samples
                arr = np.asarray(val).flatten()
                rows.extend([(rid, float(v)) for v in arr])

        samples_df = pd.DataFrame(rows, columns=["Risk_ID", "Annual_Loss"]) if rows else empty_samples
        summary_df = pd.DataFrame(sum_rows, columns=["Risk_ID", "mean", "median", "p95"]) if sum_rows else empty_summary
        # dtype hygiene
        if not samples_df.empty:
            samples_df["Annual_Loss"] = pd.to_numeric(samples_df["Annual_Loss"], errors="coerce")
        if not summary_df.empty:
            for c in ["mean", "median", "p95"]:
                summary_df[c] = pd.to_numeric(summary_df[c], errors="coerce")
        return samples_df, summary_df

    # -------- Case: list/tuple of (rid, samples|dict) ----------
    if isinstance(per_scn_obj, (list, tuple)):
        rows = []
        sum_rows = []
        for item in per_scn_obj:
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue
            rid, val = item[0], item[1]
            rid = str(rid)
            if isinstance(val, dict):
                if "samples" in val and val["samples"] is not None:
                    arr = np.asarray(val["samples"]).flatten()
                    rows.extend([(rid, float(v)) for v in arr])
                has_stats = any(k in val for k in ("mean", "median", "p95"))
                if has_stats:
                    mean = float(val.get("mean", np.nan))
                    median = float(val.get("median", np.nan))
                    p95 = float(val.get("p95", np.nan))
                    sum_rows.append((rid, mean, median, p95))
            else:
                arr = np.asarray(val).flatten()
                rows.extend([(rid, float(v)) for v in arr])

        samples_df = pd.DataFrame(rows, columns=["Risk_ID", "Annual_Loss"]) if rows else empty_samples
        summary_df = pd.DataFrame(sum_rows, columns=["Risk_ID", "mean", "median", "p95"]) if sum_rows else empty_summary
        if not samples_df.empty:
            samples_df["Annual_Loss"] = pd.to_numeric(samples_df["Annual_Loss"], errors="coerce")
        if not summary_df.empty:
            for c in ["mean", "median", "p95"]:
                summary_df[c] = pd.to_numeric(summary_df[c], errors="coerce")
        return samples_df, summary_df

    # -------- Case: DataFrame (samples or summary, with varied column names) ----------
    if isinstance(per_scn_obj, pd.DataFrame):
        df = per_scn_obj.copy()
        # unify names
        rename_map = {}
        for c in df.columns:
            lc = str(c).lower()
            if lc in ("scenario", "riskid", "risk_id"):
                rename_map[c] = "Risk_ID"
            elif lc in ("loss", "annual_loss", "loss_usd", "value"):
                rename_map[c] = "Annual_Loss"
        if rename_map:
            df = df.rename(columns=rename_map)

        cols = set(df.columns)
        # samples form
        if {"Risk_ID", "Annual_Loss"}.issubset(cols):
            df["Risk_ID"] = df["Risk_ID"].astype(str)
            df["Annual_Loss"] = pd.to_numeric(df["Annual_Loss"], errors="coerce")
            return df, empty_summary
        # summary form
        need = {"Risk_ID", "mean", "median", "p95"}
        if need.issubset(cols):
            out = df[list(need)].copy()
            out["Risk_ID"] = out["Risk_ID"].astype(str)
            for c in ["mean", "median", "p95"]:
                out[c] = pd.to_numeric(out[c], errors="coerce")
            return empty_samples, out

    # Fallback
    return empty_samples, empty_summary


# =====================================================================
# ======================== Simulation + Results =======================
# =====================================================================
if st.session_state.run:
    # Prepare parameters (cached)
    df_params = _prepare_params(settings_selected)

    # --- Filters (Domain / Scenarios) ---
    domain_options = ["All"] + sorted(df_params["Category"].dropna().unique().tolist())
    col_f1, col_f2 = st.columns([1, 3])
    domain_choice = col_f1.selectbox("Domain", options=domain_options, index=0, key="filter_domain")

    df_params_filtered = (
        df_params[df_params["Category"] == domain_choice].copy() if domain_choice != "All" else df_params.copy()
    )

    scenario_options = df_params_filtered["Risk_ID"].tolist()
    selected_scenarios = col_f2.multiselect(
        "Scenarios (optional)",
        options=scenario_options,
        default=scenario_options,
        key="filter_scenarios",
    )
    if not selected_scenarios:
        st.warning("No scenarios selected for this domain. Select at least one.")
        st.stop()
    df_params_filtered = df_params_filtered[df_params_filtered["Risk_ID"].isin(selected_scenarios)]

    # ============================
    # Explore Risk Register Data (UX block v4)
    # ============================
    import os

    import pandas as pd

    # --- Resolve active dataset name
    try:
        _active_dataset = (
            selected_name
            if "selected_name" in locals() and selected_name
            else os.path.basename(str(risk_register_path_display))
        )
    except Exception:
        _active_dataset = "Unknown dataset"

    # --- Build a domain-scoped base (so unchecking the toggle shows ALL domain rows, not only selected)
    if domain_choice == "All":
        df_params_domain = df_params.copy()
    else:
        df_params_domain = df_params[df_params["Category"] == domain_choice].copy()

    # --- Section header (match ~14px like "Scenarios (optional)")
    st.markdown(
        """
        <style>
          .rq-ref-header { font-size:14px; font-weight:600; margin: 0.4rem 0 0.25rem 0; }
        </style>
        <p class="rq-ref-header">Explore Risk Register Data</p>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(f"Active data: {_active_dataset}", expanded=False):
        # Desired columns and order
        desired_cols = [
            "Risk_ID",
            "Asset",
            "Scenario",
            "Likelihood",
            "Impact",
            "Risk Rating",
            "Loss_Min",
            "Loss_Mode",
            "Loss_Max",
            "Owner",
            "Notes",
        ]

        # Map labels → actual columns (handle underscores)
        colmap = {}
        for c in desired_cols:
            if c in df_params_domain.columns:
                colmap[c] = c
            elif c.replace(" ", "_") in df_params_domain.columns:
                colmap[c] = c.replace(" ", "_")
            elif c == "Risk Rating" and "Risk_Rating" in df_params_domain.columns:
                colmap[c] = "Risk_Rating"

        present_labels = [c for c in desired_cols if c in colmap]

        # Toggle: limit to currently selected scenarios, or show all within domain
        only_sel = st.checkbox("Show only currently selected scenarios", value=True, key="ref_only_sel_v4")
        if only_sel:
            base_df = df_params_domain[df_params_domain["Risk_ID"].isin(selected_scenarios)].copy()
        else:
            base_df = df_params_domain.copy()

        ref_df = base_df[[colmap[c] for c in present_labels]].copy()
        # Normalize headers back to friendly labels
        inv_map = {v: k for k, v in colmap.items()}
        ref_df = ref_df.rename(columns=inv_map)

        # ----- Colors (more saturated + auto contrast) -----
        # Category colors for Risk_ID cell background
        cat_color = {
            "CMP": "#F06292",  # deeper pink
            "GOV": "#E53935",  # deep red
            "OPS": "#1E88E5",  # vivid blue
            "SEC": "#64B5F6",  # stronger light blue
        }
        # Risk heat colors (closer to your matrix)
        risk_heat = {
            "Very Low": "#C8EFC3",
            "Low": "#93E18A",
            "Medium": "#FFD166",
            "High": "#FF9F50",
            "Critical": "#E53935",  # deep red (white text for contrast)
        }

        def _hex_to_rgb(hex_color: str):
            hex_color = hex_color.lstrip("#")
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

        def _luminance(hex_color: str) -> float:
            r, g, b = _hex_to_rgb(hex_color)

            def _conv(c):
                c = c / 255.0
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

            R, G, B = _conv(r), _conv(g), _conv(b)
            return 0.2126 * R + 0.7152 * G + 0.0722 * B

        def _auto_text_color(bg_hex: str) -> str:
            # WCAG-ish contrast: use black on light backgrounds, white on dark
            try:
                return "black" if _luminance(bg_hex) > 0.45 else "white"
            except Exception:
                return "black"

        def _risk_id_style(row):
            styles = ["" for _ in row.index]
            if "Risk_ID" in row.index:
                rid = str(row["Risk_ID"])
                prefix = rid.split("-")[0] if "-" in rid else ""
                bg = cat_color.get(prefix)
                if bg:
                    color = _auto_text_color(bg)
                    idx = list(row.index).index("Risk_ID")
                    styles[idx] = f"background-color: {bg}; color: {color};"
            return styles

        def _heat_cell(val):
            if pd.isna(val):
                return ""
            txt = str(val)
            bg = risk_heat.get(txt)
            if not bg:
                return ""
            color = _auto_text_color(bg)
            return f"background-color: {bg}; color: {color};"

        show_df = ref_df.copy()
        styler = show_df.style

        # Row-wise style for Risk_ID by Category
        styler = styler.apply(_risk_id_style, axis=1)

        # Heat cells for Likelihood / Impact / Risk Rating
        for col in ["Likelihood", "Impact", "Risk Rating"]:
            if col in show_df.columns:
                styler = styler.applymap(_heat_cell, subset=pd.IndexSlice[:, [col]])

        # Currency formatting for loss columns
        for c in ["Loss_Min", "Loss_Mode", "Loss_Max"]:
            if c in show_df.columns:
                styler = styler.format({c: lambda x: f"${x:,.0f}" if pd.notna(x) else "—"})

        # Do NOT force a global text color; rely on theme + per-cell contrast
        st.dataframe(styler, use_container_width=True)

        st.caption(
            "View scenario inputs and qualitative ratings from the active risk register. "
            "Updates automatically with your current domain and scenario selections."
        )
    # ============================
    # End UX block v4
    # ============================

    # ---------- Simulation ----------
    port_samples, per_scn = simulate_portfolio(df_params_filtered, n_sims=int(n_sims), seed=int(seed))
    per_samples, per_summary = normalize_per_scn(per_scn)

    # ---------- Summary stats ----------
    stats = summarize(port_samples)

    # ---------- KPI Cards ----------
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("EAL (mean)", f"${stats['mean']:,.0f}")
    k2.metric("Median", f"${stats['median']:,.0f}")
    k3.metric(
        "p95 Loss" if 95 in show_percentiles else "p90 Loss",
        f"${stats['p95' if 95 in show_percentiles else 'p90']:,.0f}",
    )
    k4.metric("Max Observed", f"${stats['max']:,.0f}")

    # -----------------------------------------------------------------
    # Histogram (Portfolio Loss) + Insights
    # -----------------------------------------------------------------
    st.session_state.setdefault("show_hist_insights", False)
    hcol1, hcol2 = st.columns([1, 0.3])
    with hcol1:
        st.markdown("## 🏦 Portfolio Annual Loss Distribution")
    with hcol2:
        if st.button("ℹ️ Data Insights", key="hist_insights_btn"):
            st.session_state.show_hist_insights = not st.session_state.show_hist_insights

    if st.session_state.get("show_hist_insights", False):
        with st.expander("🧠 Data Insights — Portfolio Annual Loss Distribution", expanded=True):
            _mean = f"${stats.get('mean', 0):,.0f}"
            _median = f"${stats.get('median', 0):,.0f}"
            _p95 = f"${stats.get('p95', 0):,.0f}"
            _max = f"${stats.get('max', 0):,.0f}"

            st.markdown("#### What it is")
            st.write(
                "Distribution of **annualized portfolio loss** from Monte Carlo simulations. "
                "Each bar shows how often a loss value appears across all runs."
            )
            st.markdown("#### Who it’s for")
            st.write(
                "Cyber risk analysts, managers, and decision-makers who need a quick view of "
                "typical vs. tail losses to inform risk appetite, budgeting, and control decisions."
            )
            st.markdown("#### How to use it")
            st.write(
                "Compare **central tendency** (EAL, Median) with **tail percentiles** (e.g., p95). "
                "Use this to set thresholds, evaluate controls or insurance, and communicate exposure."
            )
            st.markdown("#### Definitions")
            st.markdown(
                f"""
- **EAL (mean):** Expected Annual Loss — arithmetic average of simulated annual losses. **Current:** **{_mean}**
- **Median:** 50th percentile — half of simulated outcomes are at or below this value. **Current:** **{_median}**
- **p95 Loss:** 95th percentile — tail risk indicator; 95% of outcomes are ≤ this number. **Current:** **{_p95}**
- **Max Observed:** Largest annual loss observed in the simulated sample. **Current:** **{_max}**
                """
            )
            st.info(
                "💡 **Tips**\n\n"
                """- Adjust simulation runs, percentiles, and scenario filters to see 
                how the distribution and tail change.\n"""
                "- Compare baseline vs. with-control scenarios to demonstrate reduction in tail risk.\n"
                "- Use the p95 to discuss tail exposure with leadership; use EAL for budgeting."
            )
            st.button(
                "Close",
                key="hist_insights_close_btn",
                on_click=lambda: st.session_state.update(show_hist_insights=False),
            )

    fig_hist = go.Figure()
    fig_hist.add_histogram(
        x=port_samples,
        nbinsx=50,
        name="Portfolio Loss",
        histnorm=None,
        hovertemplate="Annual Loss: $%{x:,.0f}<extra></extra>",
    )
    for p in show_percentiles:
        pval = stats.get(f"p{p}")
        if pval is not None:
            fig_hist.add_shape(
                type="line",
                x0=pval,
                x1=pval,
                y0=0,
                y1=1,
                yref="paper",
                line=dict(width=2, dash="dot"),
            )
            fig_hist.add_annotation(
                x=pval,
                y=1,
                yref="paper",
                text=f"p{p}: ${pval:,.0f}",
                showarrow=False,
                xanchor="left",
                yanchor="bottom",
            )
    fig_hist.update_layout(
        title=None,
        xaxis_title=f"Annual Loss ({currency})",
        yaxis_title="Frequency",
        bargap=0.05,
        height=420,
        margin=dict(l=20, r=20, t=20, b=40),
    )
    st.plotly_chart(fig_hist, use_container_width=True, key="plot_portfolio_hist")

    # -----------------------------------------------------------------
    # CDF (Portfolio) + Insights
    # -----------------------------------------------------------------
    st.session_state.setdefault("show_cdf_insights", False)
    c1, c2 = st.columns([1, 0.3])
    with c1:
        st.markdown("## 📈 Cumulative Probability (CDF)")
    with c2:
        if st.button("ℹ️ Data Insights", key="cdf_insights_btn"):
            st.session_state.show_cdf_insights = not st.session_state.show_cdf_insights

    if st.session_state.get("show_cdf_insights", False):
        with st.expander("🧠 Data Insights — Cumulative Probability (CDF)", expanded=True):
            _median = f"${stats.get('median', 0):,.0f}"
            _p90 = stats.get("p90")
            _p95 = stats.get("p95")
            _p90_s = f"${_p90:,.0f}" if _p90 is not None else "—"
            _p95_s = f"${_p95:,.0f}" if _p95 is not None else "—"
            _plist = ", ".join([f"p{int(p)}" for p in show_percentiles])

            st.markdown("#### What it is")
            st.write(
                "The **Cumulative Distribution Function (CDF)** shows the probability that annual loss will be "
                "**≤ a given threshold**. Right = larger losses; up = higher probability."
            )
            st.markdown("#### Who it’s for")
            st.write(
                "Analysts & leaders setting **risk appetite** and **budget thresholds**, and discussing **tail risk**."
            )
            st.markdown("#### How to use it")
            st.write(
                "Pick a threshold on the x-axis and read up to get **P(Loss ≤ threshold)**. "
                """Or pick a probability (e.g., 95%), read left to the curve, 
                then down to the **loss at that confidence**."""
            )
            st.markdown("#### Definitions")
            st.markdown(
                f"""
                    - **Median (p50):** 50% of outcomes are ≤ this value. **Current:** **{_median}**
                    - **p90:** 90% of outcomes are ≤ this value (conservative budgeting). **Current:** **{_p90_s}**
                    - **p95:** 95% of outcomes are ≤ this value (tail-risk marker). **Current:** **{_p95_s}**
                    - **Displayed percentiles:** {_plist or "—"}
                """
            )
            st.info(
                "💡 **Tips**\n\n"
                "- Use **p95** for tail exposure with leadership; **Median/EAL** for expected outcomes.\n"
                "- Steeper curve near your threshold ⇒ small control changes can materially change risk.\n"
                "- Compare baseline vs. with-control CDFs to show tail-risk reduction."
            )
            st.button(
                "Close",
                key="cdf_insights_close_btn",
                on_click=lambda: st.session_state.update(show_cdf_insights=False),
            )

    sorted_losses = np.sort(port_samples)
    cdf = np.arange(1, len(sorted_losses) + 1) / len(sorted_losses)
    fig_cdf = go.Figure()
    fig_cdf.add_trace(
        go.Scatter(
            x=sorted_losses,
            y=cdf,
            mode="lines",
            name="CDF",
            hovertemplate="P(Loss ≤ $%{x:,.0f}) = %{y:.1%}<extra></extra>",
        )
    )
    for p in show_percentiles:
        pval = stats.get(f"p{p}")
        if pval is not None:
            fig_cdf.add_trace(
                go.Scatter(
                    x=[pval],
                    y=[p / 100],
                    mode="markers+text",
                    text=[f"p{p}"],
                    textposition="top center",
                    marker=dict(size=8),
                    showlegend=False,
                    hovertemplate=f"p{p}: $%{{x:,.0f}}<extra></extra>",
                )
            )
    fig_cdf.update_layout(
        title=None,
        xaxis_title=f"Loss Threshold ({currency})",
        yaxis_title="Probability",
        height=420,
        margin=dict(l=20, r=20, t=20, b=40),
    )
    st.plotly_chart(
        fig_cdf,
        use_container_width=True,
        key=(
            f"plot_portfolio_cdf_{domain_choice}_{len(selected_scenarios)}"
            f"_{int(st.session_state.get('show_cdf_insights', False))}"
        ),
    )

    # ---------- Scenario Comparison (Distribution by Scenario) ----------

    # --- Header + toggle button (place this immediately above the Scenario Comparison expander) ---
    st.session_state.setdefault("show_scenario_insights", False)

    c1, c2 = st.columns([1, 0.3])
    with c1:
        st.markdown("## 📦 Distribution by Scenario")
    with c2:
        # Explicit key avoids state collisions (Streamlit 1.51+)
        if st.button("ℹ️ Data Insights", key="scenario_insights_btn"):
            st.session_state.show_scenario_insights = not st.session_state.show_scenario_insights

    if st.session_state.get("show_scenario_insights", False):
        with st.expander("🧠 Data Insights — Distribution by Scenario", expanded=True):
            st.markdown("""
    **What it is**  
    A comparison of simulated annual loss distributions for each scenario. Switch between **Box**, **Violin**, 
    and **Bar** to explore central tendency (P50/median), spread (IQR), and tail risk (outliers/long tails).

    **Who it’s for**  
    • GRC/risk analysts prioritizing scenarios  
    • Leaders deciding where to invest limited budget

    **How to use it**  
    1. **Median (P50)** ≈ “typical” outcome; **P95** ≈ “bad but plausible” tail.  
    2. Wide violins/boxes = more uncertainty; tall bars = higher expected loss.  
    3. Compare scenarios with similar medians but very different tails—those with higher **P95** may deserve
   earlier attention.


    **Definitions**  
    • **P50 (Median):** 50% of simulations are ≤ this value.  
    • **P95:** 95% of simulations are ≤ this value (tail).  
    • **IQR:** Middle 50% of outcomes (Q1–Q3).  
    • **Outliers:** Unusually large losses—watch clustering in the upper tail.

    **Tips**  
    • Sort by **P95** to surface tail-heavy scenarios.  
    • Use category colors (GOV, CMP, OPS, SEC) to spot themes.  
    • Re-run with more iterations to stabilize noisy tails.
    """)

    #   st.subheader("🎯 Scenario Comparison (Distribution by Scenario)")

    # Controls row
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([0.45, 0.35, 0.20])

    # Current samples/summary availability
    has_samples = not per_samples.empty

    # If no row-level samples, offer fast local generation to enable Box/Violin
    if not has_samples:
        st.markdown(
            "> ℹ️ No row-level samples were returned by the simulator. "
            "You can generate per-scenario samples (fast) to enable Box/Violin."
        )
        gen_col1, gen_col2 = st.columns([0.5, 0.5])
        with gen_col1:
            enable_local_sampling = st.checkbox(
                "Generate per-scenario samples (approx.)",
                value=False,
                help="Uses current parameters to sample each scenario locally so Box/Violin can render.",
                key="comp_enable_local_sampling",
            )
        with gen_col2:
            local_nsims = st.slider(
                "Samples per scenario",
                min_value=1000,
                max_value=min(int(n_sims), 20000),
                value=min(5000, int(n_sims)),
                step=500,
                key="comp_local_nsims",
                disabled=not enable_local_sampling,
            )

        if enable_local_sampling:
            # 1) Generate samples (Risk_ID, Annual_Loss)
            rows = []
            for _, r in df_params_filtered.iterrows():
                arr = simulate_scenario_row(r, n_sims=int(local_nsims), seed=int(seed))
                rid = str(r["Risk_ID"])
                rows.extend([(rid, float(v)) for v in arr])
            per_samples = pd.DataFrame(rows, columns=["Risk_ID", "Annual_Loss"])

            # 2) Merge labels so Category/Owner are present for coloring/hover
            label_cols = ["Risk_ID"] + [c for c in ["Category", "Owner"] if c in df_params_filtered.columns]
            labels = df_params_filtered[label_cols].drop_duplicates("Risk_ID")
            per_samples = per_samples.merge(labels, on="Risk_ID", how="left")

    # Re-evaluate after optional generation
    has_samples = not per_samples.empty

    # Comparison controls (always enabled to avoid sticky state)
    comp_type = col_ctrl1.radio(
        "Comparison Type",
        options=["Box", "Violin"],
        horizontal=True,
        index=0,
        key="comp_type_control",
    )
    y_metric = col_ctrl2.selectbox(
        "Metric (used when no samples → bar)",
        options=["p95", "median", "mean"],
        index=0,
        key="comp_y_metric",
    )
    sort_metric = col_ctrl3.selectbox(
        "Sort by",
        options=["Risk_ID", "p95", "median", "mean"],
        index=0,
        key="comp_sort_metric",
    )

    # Build per-scenario stats from whatever we have
    if has_samples:
        df_stats_comp = (
            per_samples.groupby("Risk_ID")["Annual_Loss"]
            .agg(
                mean="mean",
                median="median",
                p95=lambda s: np.percentile(s.dropna().values, 95) if s.notna().any() else np.nan,
            )
            .reset_index()
        )
    else:
        df_stats_comp = per_summary.copy()

    # Merge labels for color/hover
    label_cols = ["Risk_ID"] + [c for c in ["Category", "Owner"] if c in df_params_filtered.columns]
    labels = df_params_filtered[label_cols].drop_duplicates("Risk_ID")
    df_stats_comp = df_stats_comp.merge(labels, on="Risk_ID", how="left")
    df_samples_comp = per_samples.merge(labels, on="Risk_ID", how="left") if has_samples else pd.DataFrame()

    # Sort order
    if sort_metric in ["p95", "median", "mean"]:
        order = (
            df_stats_comp[["Risk_ID", sort_metric]]
            .dropna(subset=[sort_metric])
            .sort_values(by=sort_metric, ascending=False)["Risk_ID"]
            .tolist()
        )
    else:
        order = sorted(df_stats_comp["Risk_ID"].dropna().unique().tolist())

    # Guard
    if df_stats_comp.empty or df_stats_comp["Risk_ID"].isna().all():
        st.warning("No per-scenario stats available to plot. Try running the simulation or broadening filters.")
    else:
        if has_samples and not df_samples_comp.empty:
            # Box/Violin with row-level samples
            dfp = df_samples_comp.dropna(subset=["Risk_ID", "Annual_Loss"]).copy()
            dfp["Annual_Loss"] = pd.to_numeric(dfp["Annual_Loss"], errors="coerce")
            if comp_type == "Box":
                fig_comp = px.box(
                    dfp,
                    x="Risk_ID",
                    y="Annual_Loss",
                    color="Category" if "Category" in dfp.columns else None,
                    category_orders={"Risk_ID": order},
                    points=False,
                )
                fig_comp.update_traces(quartilemethod="inclusive")
                y_label = "Annual Loss (USD)"
            else:
                fig_comp = px.violin(
                    dfp,
                    x="Risk_ID",
                    y="Annual_Loss",
                    color="Category" if "Category" in dfp.columns else None,
                    category_orders={"Risk_ID": order},
                    box=True,
                    points=False,
                )
                y_label = "Annual Loss (USD)"
            # Avoid undefined legend labels; only show legend if Category exists
            fig_comp.update_traces(
                name="Annual Loss",
                selector=dict(name=None),
                showlegend=("Category" in dfp.columns),
                hovertemplate="Scenario=%{x}<br>Loss=$%{y:,.0f}<extra></extra>",
            )
        else:
            # No samples → bar of metric
            dfp = df_stats_comp.dropna(subset=["Risk_ID", y_metric]).copy()
            dfp[y_metric] = pd.to_numeric(dfp[y_metric], errors="coerce")
            dfp = dfp.sort_values(by=y_metric, ascending=False, na_position="last")
            fig_comp = px.bar(
                dfp,
                x="Risk_ID",
                y=y_metric,
                color="Category" if "Category" in dfp.columns else None,
                category_orders={"Risk_ID": order},
            )
            fig_comp.update_traces(
                name=y_metric.upper(),
                selector=dict(name=None),
                showlegend=("Category" in dfp.columns),
                hovertemplate=f"Scenario=%{{x}}<br>{y_metric}=$%{{y:,.0f}}<extra></extra>",
            )
            y_label = f"{y_metric} (USD)"

        fig_comp.update_layout(
            title="",
            xaxis_title="Scenario",
            yaxis_title=y_label,
            height=420,
            margin=dict(l=20, r=20, t=20, b=40),
        )
        st.plotly_chart(
            fig_comp,
            use_container_width=True,
            key=(
                f"plot_comp_{'samples' if has_samples else 'summary'}"
                f"_{comp_type}_{y_metric}_{domain_choice}_{len(selected_scenarios)}"
            ),
        )

    # ---------- Risk Matrix (Likelihood × Impact) ----------
    # --- Header + toggle button (place this immediately above the Risk Matrix expander) ---
    st.session_state.setdefault("show_matrix_insights", False)

    c1, c2 = st.columns([1, 0.3])
    with c1:
        st.markdown("## 🧮 Risk Matrix (Likelihood × Impact)")
    with c2:
        if st.button("ℹ️ Data Insights", key="matrix_insights_btn"):
            st.session_state.show_matrix_insights = not st.session_state.show_matrix_insights

    if st.session_state.get("show_matrix_insights", False):
        with st.expander("🧠 Data Insights — Risk Matrix (Likelihood × Impact)", expanded=True):
            st.markdown("""
    **What it is**  
    A qualitative map of **Likelihood × Impact** showing which scenarios are most concerning at a glance. 
    It complements the quantitative charts by offering a quick triage view.

    **Who it’s for**  
    • Executives and managers who need a simple, common-language view  
    • Analysts aligning portfolio risk to governance processes

    **How to use it**  
    1. Start triage in the **upper right** (High × High).  
    2. Cross-check these with the **quantitative tails** (P95) for budget planning.  
    3. Use labels and contrast toggles to improve readability during reviews.

    **Definitions & Caveats**  
    • **Likelihood:** Expected frequency (mapped from ARO/λ).  
    • **Impact:** Consequence of a single loss event (mapped from min/mode/max).  
    • **Caveat:** The grid is **ordinal**, not monetary—always validate with Monte Carlo results.

    **Tips**  
    • Keep qualitative→quantitative mappings in sync to avoid drift.  
    • When two items land in the same cell, use **P95** or **EAL** to break ties.  
    • Track movement over time (controls, incidents) to show improvement.
    """)

    #    st.subheader("🔥 Risk Matrix (Likelihood × Impact) — Colored by p95 Loss)")

    # Build a per-scenario summary we can aggregate into cells
    if not per_summary.empty:
        df_stats_src = per_summary.copy()
    else:
        # derive from samples if needed
        if not per_samples.empty:
            df_stats_src = (
                per_samples.groupby("Risk_ID")["Annual_Loss"]
                .agg(
                    mean="mean",
                    median="median",
                    p95=lambda s: np.percentile(s.dropna().values, 95) if s.notna().any() else np.nan,
                )
                .reset_index()
            )
        else:
            df_stats_src = pd.DataFrame(columns=["Risk_ID", "mean", "median", "p95"])

    # Merge Likelihood / Impact / Category for matrix + hover
    merge_cols = ["Risk_ID"] + [c for c in ["Likelihood", "Impact", "Category"] if c in df_params_filtered.columns]
    ctx = df_stats_src.merge(
        df_params_filtered[merge_cols].drop_duplicates("Risk_ID"),
        on="Risk_ID",
        how="left",
    )

    # Fixed axis orders
    like_order = ["Very Low", "Low", "Medium", "High", "Critical"]
    imp_order = ["Low", "Medium", "High", "Critical"]

    # Aggregate per cell
    if not ctx.empty:
        grouped = ctx.groupby(["Likelihood", "Impact"], as_index=False).agg(
            p95_mean=("p95", "mean"),
            p95_sum=("p95", "sum"),
            n=("p95", "size"),
        )
    else:
        grouped = pd.DataFrame(columns=["Likelihood", "Impact", "p95_mean", "p95_sum", "n"])

    # Choose metric shown (toggle mean vs total)
    metric_type = st.radio(
        "Cell metric",
        options=["Mean p95", "Total p95"],
        horizontal=True,
        index=0,
        key="rm_metric_type",
    )
    grouped["p95_plot"] = grouped["p95_mean"] if metric_type == "Mean p95" else grouped["p95_sum"]

    # Full grid so empty combos render as blank
    grid = pd.MultiIndex.from_product([like_order, imp_order], names=["Likelihood", "Impact"]).to_frame(index=False)
    matrix_full = grid.merge(grouped, on=["Likelihood", "Impact"], how="left").fillna(
        {"p95_mean": 0, "p95_sum": 0, "p95_plot": 0, "n": 0}
    )

    # Pivot for heatmap
    z_mat = matrix_full.pivot(index="Impact", columns="Likelihood", values="p95_plot").reindex(
        index=imp_order, columns=like_order
    )
    n_mat = matrix_full.pivot(index="Impact", columns="Likelihood", values="n").reindex(
        index=imp_order, columns=like_order
    )

    # Mask empty cells (avoid “0 USD” tiles)
    z_plot = z_mat.copy().astype(float)
    z_plot[n_mat.fillna(0).values == 0] = np.nan

    # Optional contrast boost
    boost_contrast = st.checkbox("Boost contrast", value=True, key="rm_boost_contrast")

    # Optional labels
    show_labels = st.checkbox("Show labels", value=True, key="rm_show_labels")
    if show_labels:

        def _fmt(v, n):
            if (n or 0) <= 0 or v is None or (isinstance(v, float) and np.isnan(v)):
                return ""
            return f"n={int(n)}\n${v / 1_000_000:,.1f}M"

        text_mat = z_plot.copy()
        for i in range(text_mat.shape[0]):
            for j in range(text_mat.shape[1]):
                text_mat.iat[i, j] = _fmt(z_plot.iat[i, j], n_mat.iat[i, j])
        text_vals = text_mat.values
        texttemplate = "%{text}"
    else:
        text_vals = None
        texttemplate = None

    # Color range clipping (contrast)
    valid_vals = z_plot.values[~np.isnan(z_plot.values)]
    zmin = zmax = None
    if boost_contrast and valid_vals.size > 0:
        lo, hi = float(np.percentile(valid_vals, 5)), float(np.percentile(valid_vals, 95))
        if lo < hi:
            zmin, zmax = lo, hi

    # Render heatmap
    fig_heat = go.Figure(
        data=go.Heatmap(
            z=z_plot.values,
            x=z_plot.columns.tolist(),
            y=z_plot.index.tolist(),
            coloraxis="coloraxis",
            zmin=zmin,
            zmax=zmax,
            text=text_vals,
            texttemplate=texttemplate,
            hovertemplate=(
                "Likelihood=%{x}<br>"
                "Impact=%{y}<br>"
                "Scenarios: %{customdata[0]}<br>"
                f"{metric_type}: $%{{z:,.0f}}<extra></extra>"
            ),
            customdata=np.dstack([n_mat.values]).reshape(n_mat.shape[0], n_mat.shape[1], 1),
        )
    )
    fig_heat.update_layout(
        title="",
        xaxis_title="Likelihood",
        yaxis_title="Impact",
        height=420,
        margin=dict(l=20, r=20, t=20, b=40),
        coloraxis=dict(colorscale="YlOrRd"),
    )
    st.plotly_chart(
        fig_heat,
        use_container_width=True,
        key=f"plot_risk_heatmap_{domain_choice}_{len(selected_scenarios)}_{metric_type.replace(' ', '_')}",
    )

    # -----------------------------------------------------------------
    # Downloads
    # -----------------------------------------------------------------
    st.subheader("Export")
    colA, colB = st.columns(2)

    csv_buf = StringIO()
    pd.DataFrame({"annual_loss_usd": port_samples}).to_csv(csv_buf, index=False)
    colA.download_button(
        "⬇ Download Portfolio Samples (CSV)",
        data=csv_buf.getvalue().encode("utf-8"),
        file_name="portfolio_samples.csv",
        mime="text/csv",
    )

    manifest = {
        "model_version": "mc-mvp-1",
        "n_sims": int(n_sims),
        "seed": int(seed),
        "percentiles": list(map(int, show_percentiles)),
        "risk_register_path": str(risk_register_path_display),
        "rows": int(len(df_params_filtered)),
        "stats": {k: float(v) for k, v in stats.items()},
        "filters": {"domain": domain_choice, "scenarios": selected_scenarios},
        "risk_matrix": {
            "metric_type": metric_type,
            "boost_contrast": bool(boost_contrast),
            "show_labels": bool(show_labels),
        },
    }
    colB.download_button(
        "📑 Download Run Manifest (JSON)",
        data=json.dumps(manifest, indent=2).encode("utf-8"),
        file_name="run_manifest.json",
        mime="application/json",
    )
else:
    st.info("Set parameters in the sidebar and click **Run Simulation** to generate results.")
