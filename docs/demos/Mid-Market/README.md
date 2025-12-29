# Mid-Market Demo — Vendor Supply-Chain Compromise & SaaS Platform Failure

**Audience:** Mid-market IT managers, security generalists, GRC practitioners, and business leadership  
**Purpose:** Demonstrate how RiskQuant helps mid-market organizations quantify cyber risk, compare domains, and support more effective budgeting and prioritization decisions

---
![Mid-Market Demo Dashboard](../../images/README-MM.png)
## Overview

This demonstration focuses on cyber risks commonly faced by mid-market organizations, where security responsibilities are often shared across IT, compliance, and third-party service providers.

The demo highlights how RiskQuant can be used to:
- Quantify the **financial impact** of vendor-related cyber incidents
- Compare risk across domains such as Governance, Compliance, and Security
- Support more informed decision-making when resources and staff are limited

While this demo introduces more cyber and operational context than the SMB scenario, it assumes that many mid-market organizations rely on a combination of internal generalists and external service providers rather than large, dedicated security teams.

---

## Scenario summary

**Primary scenarios:**
- Vendor data exposure due to third-party platform compromise
- Credential or API abuse involving a vendor-managed SaaS service

**Key characteristics:**
- Cascading impacts from third-party failures
- Shared responsibility across organizational and vendor boundaries
- Financial impacts that extend beyond immediate technical recovery (e.g., downtime, contractual exposure, regulatory considerations)

The scenarios are calibrated to reflect typical mid-market operational realities, including dependency on SaaS platforms and managed service providers.

---

## Supporting artifacts

This demo includes a **consistent set of supporting artifacts**, each designed to clarify the relationship between inputs, assumptions, and outputs.

### Risk register (visual)
- **Risk Register – Mid-Market (Visual).pdf**  
  A presentation-ready, color-coded risk register highlighting vendor dependencies and domain-level risk using standard qualitative risk color mappings.
- **Risk Register – Mid-Market (Visual).png**  
  A screenshot of the Excel-based risk register used as input to the RiskQuant simulation.

These artifacts provide visibility into how mid-market risks are documented and categorized prior to simulation.

---

### Product demonstration guide
- **RiskQuant for Mid-Market Demo.pdf**

A written demonstration guide that includes:
- An Executive Summary and detailed Table of Contents
- Guidance on configuring and running simulations
- Domain comparison and scenario aggregation analysis
- Interpretation of probabilistic outputs for budgeting and prioritization

This document is designed for both technical and non-technical stakeholders involved in risk decision-making.

---

### Visual companion
- **RiskQuant for Mid-Market Demo Visual Companion.pdf**

A companion document containing:
- Annotated screenshots of the RiskQuant dashboard
- Visual references aligned to section numbers in the demonstration guide
- Supporting visuals for live walkthroughs, briefings, or workshops

---

## Modeling approach (high level)

This demo uses Monte Carlo simulation to estimate **annualized financial risk** across multiple related scenarios.

At a high level:
- Individual scenarios are modeled independently
- Results are aggregated to understand combined exposure
- Domain-level comparisons highlight concentration of risk
- Percentiles (p50, p90, p95) are used to express uncertainty and tail risk

The emphasis is on understanding **relative risk and prioritization**, not predicting exact outcomes.

For a deeper technical explanation, see the RiskQuant white paper.

---

## Data sources and assumptions


Scenario assumptions and loss ranges are informed by publicly available industry research and regulatory guidance. Sources are cited explicitly within the demonstration guide using white-paper notation (e.g., `[1]`, `[2]`).


A centralized explanation of how these sources are used to defend modeling assumptions is available here:

📄 [Data Sources and Assumptions](../../methodology/Data_Sources_and_Assumptions.md)

---

## Related materials

📄 [SMB Demo](demos/SMB/README.md)

📄 [Enterprise Healthcare Demo](demos/Enterprise-Healthcare/README.md)

📄 [White Paper](../../whitepaper/README.md)

---

## Intended use

This demo is provided for **educational and illustrative purposes**.  
It is intended to help mid-market organizations better understand cyber risk exposure, third-party dependencies, and decision-making tradeoffs—not to predict specific events or losses.

--- 
## Navigation

Return to the main project and demos:

📄 [Project Home](../../README.md)

📄 [Documentation Home](../README.md)

Jump directly to the demo scenarios:

📄 [SMB Demo](../demos/SMB/README.md)

📄 [Enterprise Healthcare Demo](../demos/Enterprise-Healthcare/README.md)
