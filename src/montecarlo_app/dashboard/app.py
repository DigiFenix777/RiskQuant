"""
Streamlit MVP — Cyber Risk Simulation Dashboard
- Loads your Excel risk register via existing ETL helpers
- Derives parameters, simulates portfolio
- Shows KPI cards + Histogram + CDF
- Exports CSV of portfolio samples and run manifest JSON

Run locally:
    streamlit run src/montecarlo_app/dashboard/app.py
"""

from __future__ import annotations
import json
from io import StringIO
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# Ensure we can import from src/
ROOT = Path(__file__).resolve().parents[3]  # .../RiskQuant
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from montecarlo_app.etl.risk_register_loader import (  # noqa: E402
    load_settings,
    load_risk_register,
    validate_required_columns,
    normalize_columns,
    validate_and_clean_values,
    load_mappings,
    derive_parameters,
)
from montecarlo_app.model.monte_carlo import (  # noqa: E402
    simulate_portfolio,
    summarize,
)

# ---------- UI: Header ----------
st.set_page_config(page_title="Cyber Risk Simulation Dashboard", layout="wide")
st.title("📊 Cyber Risk Simulation Dashboard")
st.caption("Quantify annual cyber loss with Monte Carlo. Adjust assumptions and see impact instantly.")

# ---------- Sidebar Controls ----------
with st.sidebar:
    st.header("⚙️ Model Settings")
    settings = load_settings()
    risk_register_path = settings["data"]["risk_register_path"]
    st.caption(f"Using risk register:\n{risk_register_path}")

    n_sims = st.number_input("Number of Simulations", min_value=1000, max_value=200000,
                             value=int(settings["simulation"]["runs"]), step=1000)
    seed = st.number_input("Random Seed", min_value=0, max_value=10**7,
                           value=int(settings["simulation"]["seed"]), step=1)
    show_percentiles = st.multiselect("Percentiles to Show",
                                      options=[50, 90, 95, 99],
                                      default=settings["simulation"]["percentiles"])
    currency = st.selectbox("Currency", options=["USD"], index=0)

    st.divider()
    st.header("ℹ️ About")
    st.info(
        "Monte Carlo simulates thousands of risk outcomes to estimate "
        "expected and tail losses. Use the controls above to adjust parameters."
    )

    run_btn = st.button("▶ Run Simulation", type="primary")


# ---------- Load + Prepare Data (on demand) ----------
@st.cache_data(show_spinner=False)
def _prepare_params():
    df_raw = load_risk_register(settings)
    validate_required_columns(df_raw)
    df = normalize_columns(df_raw)
    _issues = validate_and_clean_values(df)
    maps = load_mappings()
    df_params = derive_parameters(df, maps)

    # Derive Category from Risk_ID prefix (e.g., GOV-01 -> GOV)
    df_params = df_params.copy()
    df_params["Category"] = df_params["Risk_ID"].astype(str).str.split("-").str[0]
    return df_params

# ---------- Load + Prepare Data (on demand) ----------
@st.cache_data(show_spinner=False)
def _prepare_params():
    df_raw = load_risk_register(settings)
    validate_required_columns(df_raw)
    df = normalize_columns(df_raw)
    _issues = validate_and_clean_values(df)
    maps = load_mappings()
    df_params = derive_parameters(df, maps)

    # Derive Category from Risk_ID prefix (e.g., GOV-01 -> GOV)
    df_params = df_params.copy()
    df_params["Category"] = df_params["Risk_ID"].astype(str).str.split("-").str[0]
    return df_params

# ---------- Simulation + Results ----------
if run_btn:
    # Prepare parameters
    df_params = _prepare_params()

    # --- Filters (Domain / Scenarios) ---
    domain_options = ["All"] + sorted(df_params["Category"].dropna().unique().tolist())
    col_f1, col_f2 = st.columns([1, 3])
    domain_choice = col_f1.selectbox("Domain", options=domain_options, index=0, key="domain")

    if domain_choice != "All":
        df_params_filtered = df_params[df_params["Category"] == domain_choice].copy()
    else:
        df_params_filtered = df_params.copy()

    scenario_options = df_params_filtered["Risk_ID"].tolist()
    selected_scenarios = col_f2.multiselect(
        "Scenarios (optional)",
        options=scenario_options,
        default=scenario_options,
        key="scenarios",
    )
    if not selected_scenarios:
        st.warning("No scenarios selected for this domain. Select at least one.")
        st.stop()

    df_params_filtered = df_params_filtered[df_params_filtered["Risk_ID"].isin(selected_scenarios)]

    # ---------- Simulation (must happen before KPI cards) ----------
    port_samples, per_scn = simulate_portfolio(df_params_filtered, n_sims=int(n_sims), seed=int(seed))

    # ---------- Summarize (defines `stats`) ----------
    stats = summarize(port_samples)

    # ---------- KPI Cards (now safe to use `stats`) ----------
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("EAL (mean)", f"${stats['mean']:,.0f}")
    k2.metric("Median", f"${stats['median']:,.0f}")
    if 95 in show_percentiles:
        k3.metric("p95 Loss", f"${stats['p95']:,.0f}")
    else:
        k3.metric("p90 Loss", f"${stats.get('p90', 0):,.0f}")
    k4.metric("Max Observed", f"${stats['max']:,.0f}")

    # ---------- Histogram ----------
    fig_hist = go.Figure()
    fig_hist.add_histogram(
        x=port_samples,
        nbinsx=50,
        name="Portfolio Loss",
        histnorm=None,
        hovertemplate="Annual Loss: $%{x:,.0f}<extra></extra>",
    )
    # Percentile lines
    x_max = float(np.max(port_samples))
    for p in show_percentiles:
        pval = stats.get(f"p{p}")
        if pval is not None:
            fig_hist.add_shape(
                type="line",
                x0=pval, x1=pval,
                y0=0, y1=1,
                yref="paper",
                line=dict(width=2, dash="dot")
            )
            fig_hist.add_annotation(
                x=pval, y=1, yref="paper",
                text=f"p{p}: ${pval:,.0f}",
                showarrow=False,
                xanchor="left", yanchor="bottom"
            )

    fig_hist.update_layout(
        title="🏦 Portfolio Annual Loss Distribution",
        xaxis_title=f"Annual Loss ({currency})",
        yaxis_title="Frequency",
        bargap=0.05,
        height=420,
        margin=dict(l=20, r=20, t=50, b=40),
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    # ---------- CDF ----------
    sorted_losses = np.sort(port_samples)
    cdf = np.arange(1, len(sorted_losses) + 1) / len(sorted_losses)
    fig_cdf = go.Figure()
    fig_cdf.add_trace(go.Scatter(
        x=sorted_losses, y=cdf, mode="lines",
        name="CDF", hovertemplate="P(Loss ≤ $%{x:,.0f}) = %{y:.1%}<extra></extra>"
    ))
    # Percentile markers
    for p in show_percentiles:
        pval = stats.get(f"p{p}")
        if pval is not None:
            fig_cdf.add_trace(go.Scatter(
                x=[pval], y=[p / 100],
                mode="markers+text",
                text=[f"p{p}"],
                textposition="top center",
                marker=dict(size=8),
                showlegend=False,
                hovertemplate=f"p{p}: $%{{x:,.0f}}<extra></extra>",
            ))
    fig_cdf.update_layout(
        title="📈 Cumulative Probability (CDF)",
        xaxis_title=f"Loss Threshold ({currency})",
        yaxis_title="Probability",
        height=420,
        margin=dict(l=20, r=20, t=50, b=40),
    )
    st.plotly_chart(fig_cdf, use_container_width=True)

    st.subheader("🎯 Scenario Comparison (Distribution by Scenario)")
    # Simulate each scenario individually to build a long DF for box/violin
    from montecarlo_app.model.monte_carlo import simulate_scenario_row, summarize

    rng = np.random.default_rng(int(seed))
    long_rows = []
    per_scenario_stats = []

    for _, row in df_params_filtered.iterrows():
        # independent reproducible seed per scenario
        scenario_seed = int(rng.integers(0, 2**31 - 1))
        samples_scn = simulate_scenario_row(row, n_sims=int(n_sims), seed=scenario_seed)
        stats_scn = summarize(samples_scn)
        per_scenario_stats.append({"Risk_ID": row["Risk_ID"], "Category": row["Category"], **stats_scn})
        # store some (or all) samples for visualization
        long_rows.append(pd.DataFrame({
            "Risk_ID": row["Risk_ID"],
            "Category": row["Category"],
            "Annual_Loss": samples_scn
        }))

    df_long = pd.concat(long_rows, ignore_index=True)
    df_stats = pd.DataFrame(per_scenario_stats)

    st.subheader("🔥 Risk Matrix (Likelihood × Impact) — Colored by p95 Loss")

    # Merge stats back onto params for Likelihood/Impact context
    df_stats_ctx = df_stats.merge(
        df_params_filtered[["Risk_ID", "Likelihood", "Impact"]],
        on="Risk_ID",
        how="left"
    )

    # Order the axes
    like_order = ["Very Low", "Low", "Medium", "High", "Critical"]
    imp_order = ["Low", "Medium", "High", "Critical"]

    # Aggregate: mean p95 per (Likelihood, Impact)
    matrix = (
        df_stats_ctx
        .groupby(["Likelihood", "Impact"], as_index=False)["p95"]
        .mean()
        .rename(columns={"p95": "p95_mean"})
    )

    # Ensure all category combinations exist (fill missing with 0)
    grid = pd.MultiIndex.from_product([like_order, imp_order], names=["Likelihood", "Impact"]).to_frame(index=False)
    matrix_full = grid.merge(matrix, on=["Likelihood", "Impact"], how="left").fillna({"p95_mean": 0})

    # Pivot to 2D
    mat = matrix_full.pivot(index="Impact", columns="Likelihood", values="p95_mean").reindex(index=imp_order, columns=like_order)

    # Heatmap
    fig_heat = go.Figure(data=go.Heatmap(
        z=mat.values,
        x=mat.columns.tolist(),
        y=mat.index.tolist(),
        coloraxis="coloraxis",
        hovertemplate="Likelihood=%{x}<br>Impact=%{y}<br>Mean p95: $%{z:,.0f}<extra></extra>"
    ))
    fig_heat.update_layout(
        title="Likelihood × Impact (cell color = mean p95 loss)",
        xaxis_title="Likelihood",
        yaxis_title="Impact",
        height=420,
        margin=dict(l=20, r=20, t=50, b=40),
        coloraxis=dict(colorscale="YlOrRd")
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # Toggle: Box or Violin
    comp_type = st.radio("Comparison Type", options=["Box", "Violin"], horizontal=True, index=0)
    sort_metric = st.selectbox("Sort scenarios by", options=["Risk_ID", "p95", "mean", "median"], index=1)

    # Sort order
    if sort_metric == "Risk_ID":
        order = sorted(df_stats["Risk_ID"].tolist())
    else:
        order = df_stats.sort_values(sort_metric, ascending=True)["Risk_ID"].tolist()

    if comp_type == "Box":
        fig_comp = px.box(
            df_long, x="Risk_ID", y="Annual_Loss", color="Category",
            category_orders={"Risk_ID": order},
            points=False
        )
    else:
        fig_comp = px.violin(
            df_long, x="Risk_ID", y="Annual_Loss", color="Category",
            category_orders={"Risk_ID": order}, box=True, points=False
        )

    fig_comp.update_layout(
        title="Scenario Loss Distributions",
        xaxis_title="Scenario (Risk_ID)",
        yaxis_title=f"Annual Loss ({currency})",
        height=480,
        margin=dict(l=20, r=20, t=50, b=40),
        legend_title_text="Category",
    )
    st.plotly_chart(fig_comp, use_container_width=True)


    # ---------- Downloads ----------
    st.subheader("Export")
    colA, colB = st.columns(2)

    # CSV of portfolio samples
    csv_buf = StringIO()
    pd.DataFrame({"annual_loss_usd": port_samples}).to_csv(csv_buf, index=False)
    colA.download_button(
        "⬇ Download Portfolio Samples (CSV)",
        data=csv_buf.getvalue().encode("utf-8"),
        file_name="portfolio_samples.csv",
        mime="text/csv",
    )

    # Run manifest (JSON)
    manifest = {
        "model_version": "mc-mvp-1",
        "n_sims": int(n_sims),
        "seed": int(seed),
        "percentiles": list(map(int, show_percentiles)),
        "risk_register_path": str(risk_register_path),
        "rows": int(len(df_params)),
        "stats": {k: float(v) for k, v in stats.items()},
    }
    colB.download_button(
        "📑 Download Run Manifest (JSON)",
        data=json.dumps(manifest, indent=2).encode("utf-8"),
        file_name="run_manifest.json",
        mime="application/json",
    )

else:
    st.info("Set parameters above and click **Run Simulation** to generate results.")
