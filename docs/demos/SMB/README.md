# SMB Demo — Phishing & Credential Compromise

**Audience:** Small and Medium Business (SMB) leadership, IT managers, and non-specialist stakeholders  
**Purpose:** Demonstrate how RiskQuant helps SMB organizations understand the potential financial impact of common cyber threats using Monte Carlo simulation

---
![SMB Demo Dashboard](docs/images/README-SMB.png)
## Overview

This demonstration focuses on one of the most common and impactful cyber risks faced by small and medium businesses: **phishing attacks leading to credential compromise**.

The objective of this demo is to help SMB audiences:
- Understand cyber risk in **financial terms**
- Learn how probabilistic outputs (p50, p90, p95) should be interpreted
- See how RiskQuant supports informed decision-making without requiring deep cybersecurity expertise

The scenario and assumptions are calibrated to reflect typical SMB environments, including limited dedicated security staff and constrained budgets.

---

## Scenario summary

**Primary scenario:**  
Phishing attack leading to credential compromise of user email accounts

**Key characteristics:**
- High-frequency, human-targeted attack vector
- Moderate to severe financial impact depending on scale and response
- Common precursor to fraud, data exposure, and operational disruption

---

## Supporting artifacts

This demo includes a **consistent set of supporting artifacts**, each designed for a specific purpose and audience.

### Risk register (visual)
- **Risk Register – SMB (Visual).pdf**  
  A user-friendly, presentation-ready version of the SMB risk register, color-coded by domain and using standard qualitative risk color mappings.
- **Risk Register – SMB (Visual).png**  
  A screenshot of the Excel-based risk register used as input to the RiskQuant simulation.

These artifacts help audiences understand the **inputs** used to drive the simulation before reviewing the outputs.

---

### Product demonstration guide
- **RiskQuant for SMB Demo.pdf**  

A written walkthrough of the RiskQuant application that includes:
- An Executive Summary
- A detailed Table of Contents
- Step-by-step guidance on using the interface
- Explanations of key visualizations and metrics

This document is designed for independent reading or asynchronous review.

---

### Visual companion
- **RiskQuant for SMB Demo Visual Companion.pdf**

A companion document containing:
- High-resolution screenshots of the RiskQuant dashboard
- Annotated callouts aligned to section numbers in the demonstration guide
- Visual references intended for live presentations or side-by-side viewing

---

## Modeling approach (high level)

This demo uses Monte Carlo simulation to estimate the **annualized financial impact** of the phishing scenario.

At a high level:
- Event frequency is modeled probabilistically
- Loss severity is modeled using bounded distributions
- Thousands of simulations generate a loss distribution
- Results are expressed as percentiles (e.g., p50, p90, p95)

The emphasis is on understanding **ranges of potential outcomes**, not predicting a single loss value.

For a deeper technical explanation, see the RiskQuant white paper.

---

## Data sources and assumptions


Scenario assumptions and loss ranges are informed by publicly available industry research and regulatory guidance. Sources are explicitly cited within the demonstration guide using white-paper notation (e.g., `[1]`, `[2]`).


A centralized explanation of how these sources are used to defend modeling assumptions is available here:

📄 [Data Sources and Assumptions](../../methodology/Data_Sources_and_Assumptions.md)

---

## Related materials

📄 [Mid-Market Demo](demos/Mid-Market/README.md)

📄 [Enterprise Healthcare Demo](demos/Enterprise-Healthcare/README.md)

📄 [White Paper](../../whitepaper/README.md)

---

## Intended use

This demo is provided for **educational and illustrative purposes**.  
It is intended to help SMB audiences understand cyber risk exposure and decision-making tradeoffs, not to predict specific events or outcomes.

--- 
## Navigation

Return to the main project and demos:

📄 [Project Home](../../README.md)

📄 [Documentation Home](../README.md)

Jump directly to the demo scenarios:

📄 [Mid-Market Demo](../demos/Mid-Market/README.md)

📄 [Enterprise Healthcare Demo](../demos/Enterprise-Healthcare/README.md)
