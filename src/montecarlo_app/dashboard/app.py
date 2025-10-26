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

    show_percentiles = st.multiselect(
        "Percentiles to Show",
        options=[50, 90, 95, 99],
        default=settings["simulation"]["percentiles"],
    )

    currency = st.selectbox("Currency", options=["USD"], index=0)

    st.divider()
    st.header("ℹ️ About")
    st.info(
        "Monte Carlo simulates thousands of risk outcomes to estimate "
        "expected and tail losses. Use the controls above to adjust parameters."
    )

    # --- Stateful run/reset controls ---
    if "run" not in st.session_state:
        st.session_state.run = False

    if st.button("▶ Run Simulation", type="primary"):
        st.session_state.run = True

    if st.button("↺ Reset", type="secondary"):
        st.session_state.run = False


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
if st.session_state.run:
    # Prepare parameters (cached by _prepare_params)
    df_params = _prepare_params()

    # --- Filters (Domain / Scenarios) ---
    domain_options = ["All"] + sorted(df_params["Category"].dropna().unique().tolist())
    col_f1, col_f2 = st.columns([1, 3])
    domain_choice = col_f1.selectbox("Domain", options=domain_options, index=0, key="filter_domain")

    if domain_choice != "All":
        df_params_filtered = df_params[df_params["Category"] == domain_choice].copy()
    else:
        df_params_filtered = df_params.copy()

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

    # ---------- Simulation ----------
    port_samples, per_scn = simulate_portfolio(
        df_params_filtered, n_sims=int(n_sims), seed=int(seed)
    )

    # ---------- Summary stats ----------
    stats = summarize(port_samples)

    # ---------- KPI Cards ----------
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("EAL (mean)", f"${stats['mean']:,.0f}")
    k2.metric("Median", f"${stats['median']:,.0f}")
    # Prefer p95 if selected; else show p90
    if 95 in show_percentiles:
        k3.metric("p95 Loss", f"${stats['p95']:,.0f}")
    else:
        k3.metric("p90 Loss", f"${stats.get('p90', 0):,.0f}")
    k4.metric("Max Observed", f"${stats['max']:,.0f}")

    # ---------- Histogram (Portfolio Loss) ----------
    fig_hist = go.Figure()
    fig_hist.add_histogram(
        x=port_samples,
        nbinsx=50,
        name="Portfolio Loss",
        histnorm=None,
        hovertemplate="Annual Loss: $%{x:,.0f}<extra></extra>",
    )
    # Percentile lines
    for p in show_percentiles:
        pval = stats.get(f"p{p}")
        if pval is not None:
            fig_hist.add_shape(
                type="line",
                x0=pval, x1=pval,
                y0=0, y1=1,
                yref="paper",
                line=dict(width=2, dash="dot"),
            )
            fig_hist.add_annotation(
                x=pval, y=1, yref="paper",
                text=f"p{p}: ${pval:,.0f}",
                showarrow=False,
                xanchor="left", yanchor="bottom",
            )
    fig_hist.update_layout(
        title="🏦 Portfolio Annual Loss Distribution",
        xaxis_title=f"Annual Loss ({currency})",
        yaxis_title="Frequency",
        bargap=0.05,
        height=420,
        margin=dict(l=20, r=20, t=50, b=40),
    )
    st.plotly_chart(fig_hist, use_container_width=True, key="plot_portfolio_hist")

    # ---------- CDF (Portfolio) ----------
    sorted_losses = np.sort(port_samples)
    cdf = np.arange(1, len(sorted_losses) + 1) / len(sorted_losses)
    fig_cdf = go.Figure()
    fig_cdf.add_trace(go.Scatter(
        x=sorted_losses,
        y=cdf,
        mode="lines",
        name="CDF",
        hovertemplate="P(Loss ≤ $%{x:,.0f}) = %{y:.1%}<extra></extra>",
    ))
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
    st.plotly_chart(fig_cdf, use_container_width=True, key="plot_portfolio_cdf")

    # ---------- Scenario Comparison (Box / Violin) ----------
    st.subheader("🎯 Scenario Comparison (Distribution by Scenario)")

    # Helper: downsample for plotting only (keep charts responsive)
    def _downsample_for_viz(df, group_col="Risk_ID", n_per_group=2000, seed=42):
        if len(df) == 0:
            return df
        return (
            df.groupby(group_col, group_keys=False)
            .apply(lambda g: g.sample(min(len(g), n_per_group), random_state=seed))
            .reset_index(drop=True)
        )

    # Build per-scenario samples and stats
    from montecarlo_app.model.monte_carlo import simulate_scenario_row, summarize as _scn_summarize
    rng = np.random.default_rng(int(seed))
    long_rows = []
    per_scenario_stats = []

    for _, row in df_params_filtered.iterrows():
        scenario_seed = int(rng.integers(0, 2 ** 31 - 1))
        samples_scn = simulate_scenario_row(row, n_sims=int(n_sims), seed=scenario_seed)
        per_scenario_stats.append({
            "Risk_ID": row["Risk_ID"],
            "Category": row["Category"],
            **_scn_summarize(samples_scn),
        })
        long_rows.append(pd.DataFrame({
            "Risk_ID": row["Risk_ID"],
            "Category": row["Category"],
            "Annual_Loss": samples_scn,
        }))

    df_long = pd.concat(long_rows, ignore_index=True) if long_rows else pd.DataFrame(
        columns=["Risk_ID", "Category", "Annual_Loss"])
    df_stats = pd.DataFrame(per_scenario_stats) if per_scenario_stats else pd.DataFrame(
        columns=["Risk_ID", "Category", "mean", "median", "p90", "p95", "p99"])

    # Persisted toggles for comparison
    st.session_state.setdefault("scn_comp_type", "Box")
    st.session_state.setdefault("scn_sort_metric", "p95")

    comp_type = st.radio(
        "Comparison Type",
        options=["Box", "Violin"],
        horizontal=True,
        key="scn_comp_type",
    )
    sort_metric = st.selectbox(
        "Sort scenarios by",
        options=["Risk_ID", "p95", "mean", "median"],
        key="scn_sort_metric",
    )

    # Determine x-axis order
    if not df_stats.empty:
        if sort_metric == "Risk_ID":
            order = sorted(df_stats["Risk_ID"].tolist())
        else:
            order = df_stats.sort_values(sort_metric, ascending=True)["Risk_ID"].tolist()
    else:
        order = []

    # Downsample for plotting
    viz_rows = _downsample_for_viz(df_long, n_per_group=2000, seed=int(seed))
    st.caption(f"Scenario Comparison shows {len(viz_rows):,} points (sampled from {len(df_long):,}).")

    # Render comparison chart
    if viz_rows.empty or not order:
        st.warning(
            "No data available to plot scenario distributions. Try selecting more scenarios or increasing simulations.")
    else:
        if comp_type == "Box":
            fig_comp = px.box(
                viz_rows,
                x="Risk_ID",
                y="Annual_Loss",
                color="Category",
                category_orders={"Risk_ID": order},
                points=False,
            )
        else:  # Violin
            fig_comp = px.violin(
                viz_rows,
                x="Risk_ID",
                y="Annual_Loss",
                color="Category",
                category_orders={"Risk_ID": order},
                box=True,
                points=False,
            )

        fig_comp.update_layout(
            title="Scenario Loss Distributions",
            xaxis_title="Scenario (Risk_ID)",
            yaxis_title=f"Annual Loss ({currency})",
            height=480,
            margin=dict(l=20, r=20, t=50, b=40),
            legend_title_text="Category",
        )
        st.plotly_chart(fig_comp, use_container_width=True, key="plot_scenario_comp")

    # ---------- Risk Matrix Heatmap ----------
    st.subheader("🔥 Risk Matrix (Likelihood × Impact) — Colored by p95 Loss")

    # Cell metric toggle + readability options
    col_metric, col_rm1, col_rm2 = st.columns([1, 1, 1])
    metric_type = col_metric.radio(
        "Cell metric",
        options=["Mean p95", "Total p95"],
        horizontal=True,
        key="rm_metric_type",
    )
    show_labels = col_rm1.checkbox("Show labels (n & p95)", value=True, key="rm_show_labels")
    boost_contrast = col_rm2.checkbox("Boost contrast (5–95% autoscale)", value=True, key="rm_boost_contrast")

    # Merge stats back for Likelihood/Impact (and Owner for hover) context
    merge_cols = ["Risk_ID", "Likelihood", "Impact"]
    if "Owner" in df_params_filtered.columns:
        merge_cols.append("Owner")

    df_stats_ctx = df_stats.merge(
        df_params_filtered[merge_cols],
        on="Risk_ID",
        how="left",
    )

    # Axis orders (keep consistent with your mappings)
    like_order = ["Very Low", "Low", "Medium", "High", "Critical"]
    imp_order = ["Low", "Medium", "High", "Critical"]

    # Aggregate per (Likelihood, Impact)
    if not df_stats_ctx.empty:
        grouped = (
            df_stats_ctx
            .groupby(["Likelihood", "Impact"], as_index=False)
            .agg(
                p95_mean=("p95", "mean"),
                p95_sum=("p95", "sum"),
                n=("p95", "size"),
            )
        )
        grouped["p95_total"] = grouped["p95_sum"]
        grouped["p95_plot"] = grouped["p95_mean"] if metric_type == "Mean p95" else grouped["p95_total"]
    else:
        grouped = pd.DataFrame(columns=["Likelihood", "Impact", "p95_mean", "p95_total", "n", "p95_plot"])

    # Ensure full grid coverage
    grid = pd.MultiIndex.from_product([like_order, imp_order], names=["Likelihood", "Impact"]).to_frame(index=False)
    matrix_full = grid.merge(grouped, on=["Likelihood", "Impact"], how="left").fillna({"p95_mean": 0, "p95_total": 0, "p95_plot": 0, "n": 0})

    # Pivot to matrices
    z_mat = (
        matrix_full
        .pivot(index="Impact", columns="Likelihood", values="p95_plot")
        .reindex(index=imp_order, columns=like_order)
    )
    n_mat = (
        matrix_full
        .pivot(index="Impact", columns="Likelihood", values="n")
        .reindex(index=imp_order, columns=like_order)
    )

    # Mask empty cells so they render blank (not “0 USD” color)
    z_plot = z_mat.copy().astype(float)
    z_plot[n_mat.fillna(0).values == 0] = np.nan

    # Optional contrast boost (clip to 5th–95th pct of non-empty)
    valid_vals = z_plot.values[~np.isnan(z_plot.values)]
    if valid_vals.size > 0 and boost_contrast:
        zmin = float(np.percentile(valid_vals, 5))
        zmax = float(np.percentile(valid_vals, 95))
        if zmin == zmax:  # guard degenerate case
            zmin = None
            zmax = None
    else:
        zmin = None
        zmax = None

    # Optional labels inside cells (n + p95)
    if show_labels:
        def _fmt_cell(v, n):
            if (n or 0) <= 0 or v is None or (isinstance(v, float) and np.isnan(v)):
                return ""
            # Show millions with 1 decimal (works for Mean or Total)
            return f"n={int(n)}\n${v/1_000_000:,.1f}M"

        text_mat = z_plot.copy()
        for i in range(text_mat.shape[0]):
            for j in range(text_mat.shape[1]):
                text_mat.iat[i, j] = _fmt_cell(z_plot.iat[i, j], n_mat.iat[i, j])
        text_vals = text_mat.values
        texttemplate = "%{text}"
    else:
        text_vals = None
        texttemplate = None

    # Build per-cell list of top 3 scenarios for hover
    # (requires df_stats_ctx with Risk_ID, p95, and Owner if available)
    top_scenarios = []
    for imp in imp_order:
        row_data = []
        for like in like_order:
            subset = df_stats_ctx.query("Impact == @imp and Likelihood == @like")
            if subset.empty:
                row_data.append("")
            else:
                cols = ["Risk_ID", "p95"]
                owner_present = "Owner" in subset.columns
                if owner_present:
                    cols.append("Owner")
                tops_df = subset.nlargest(3, "p95")[cols].copy()
                # Format each scenario line
                lines = []
                for _, rr in tops_df.iterrows():
                    rid = rr.get("Risk_ID", "")
                    p95v = rr.get("p95", 0.0)
                    if owner_present:
                        owner = rr.get("Owner", "")
                        line = f"{rid} ({owner}, ${p95v/1_000_000:.1f}M)"
                    else:
                        line = f"{rid} (${p95v/1_000_000:.1f}M)"
                    lines.append(line)
                row_data.append("<br>".join(lines))
        top_scenarios.append(row_data)

    # Prepare customdata: [n, top_scenarios_as_html]
    custom_data = np.dstack([n_mat.values, np.array(top_scenarios)]).reshape(
        n_mat.shape[0], n_mat.shape[1], 2
    )

    # Heatmap
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
                f"{metric_type}: $%{{z:,.0f}}<br>"
                "Top Scenarios:<br>"
                "%{customdata[1]}<extra></extra>"
            ),
            customdata=custom_data,
        )
    )
    fig_heat.update_layout(
        title="Likelihood × Impact (cell color = p95; toggle Mean/Total above)",
        xaxis_title="Likelihood",
        yaxis_title="Impact",
        height=420,
        margin=dict(l=20, r=20, t=50, b=40),
        coloraxis=dict(colorscale="YlOrRd"),
    )

    st.plotly_chart(
        fig_heat,
        use_container_width=True,
        key=f"plot_risk_heatmap_{domain_choice}_{len(selected_scenarios)}_{int(show_labels)}_{int(boost_contrast)}_{metric_type.replace(' ', '_')}",
    )

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
        "rows": int(len(df_params_filtered)),
        "stats": {k: float(v) for k, v in stats.items()},
        "filters": {
            "domain": domain_choice,
            "scenarios": selected_scenarios,
        },
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
