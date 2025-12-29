# Enterprise Healthcare Demo — Portfolio Cyber Risk in Regulated Environments

**Audience:** Healthcare security leadership, compliance teams, auditors, and executive stakeholders  
**Purpose:** Demonstrate how RiskQuant supports enterprise-scale cyber risk analysis, portfolio synthesis, and decision-making in regulated healthcare environments

---

## Overview

This demonstration focuses on **enterprise healthcare organizations**, where cyber risk is shaped by a combination of regulated data, complex identity systems, legacy platforms, and operational dependencies.

The demo illustrates how RiskQuant can be used to:
- Quantify financial exposure across multiple, related cyber scenarios
- Analyze portfolio-level risk rather than isolated events
- Support executive and board-level discussions using probabilistic outcomes
- Connect technical failures to regulatory, operational, and financial impact

The assumed audience includes security, compliance, audit, and leadership teams with familiarity in cybersecurity and regulatory requirements.

---

## Scenario summary

**Primary scenarios analyzed:**
- Multi-state exposure of protected health information (PHI)
- Cloud identity compromise impacting clinical or administrative systems
- PII exposure from legacy credentialing platforms
- Operational disruption due to backup or recovery failure in legacy systems

**Key characteristics:**
- Regulated data and compliance exposure
- Interdependencies between identity, access, and operational systems
- Tail-risk events with significant financial and reputational consequences

Scenarios are calibrated to reflect the complexity and scale of regional healthcare organizations operating across multiple jurisdictions.

---

## Supporting artifacts

This demo includes a **consistent set of supporting artifacts**, designed to support both executive and technical review.

### Risk register (visual)
- **Risk Register – Enterprise Healthcare (Visual).pdf**  
  A presentation-ready, color-coded risk register highlighting regulated data exposure, legacy systems, and cross-domain risk using standard qualitative risk color mappings.
- **Risk Register – Enterprise Healthcare (Visual).png**  
  A screenshot of the Excel-based risk register used as input to the RiskQuant simulation.

These artifacts provide transparency into how enterprise healthcare risks are documented and structured prior to quantitative analysis.

---

### Product demonstration guide
- **RiskQuant for Enterprise Healthcare Demo.pdf**

A comprehensive demonstration guide that includes:
- An Executive Summary and detailed Table of Contents
- Portfolio-level simulation and analysis
- Scenario-specific deep dives
- Cross-scenario synthesis and interpretation
- Discussion of financial, regulatory, and operational implications

This document is designed to support both independent review and facilitated executive discussions.

---

### Visual companion
- **RiskQuant for Enterprise Healthcare Demo Visual Companion.pdf**

A companion document containing:
- High-resolution screenshots of the RiskQuant dashboard
- Annotated callouts aligned to section numbers in the demonstration guide
- Visual references to support presentations, briefings, and technical walkthroughs

---

## Modeling approach (high level)

This demo applies Monte Carlo simulation across **multiple scenarios** to estimate enterprise-wide cyber risk exposure.

At a high level:
- Loss frequency and severity are modeled per scenario
- Scenarios are aggregated to form a portfolio view
- Percentiles (p50, p90, p95) are used to express uncertainty and tail risk
- Results support comparison, prioritization, and strategic decision-making

The emphasis is on **portfolio insight and risk concentration**, not point estimates or single-event prediction.

For a detailed technical explanation of the modeling framework, see the RiskQuant white paper.

---

## Data sources and assumptions


Scenario assumptions and loss ranges are informed by publicly available industry research and regulatory guidance. Sources are explicitly cited within the demonstration guide using white-paper notation (e.g., `[1]`, `[2]`).


A centralized explanation of how these sources are used to defend modeling assumptions and parameterization is available here:

📄 [Data Sources and Assumptions](../../methodology/Data_Sources_and_Assumptions.md)

---

## Related materials

📄 [SMB Demo](demos/SMB/README.md)

📄 [Mid-Market Demo](../Mid-Market/README.md)

📄 [White Paper](../../whitepaper/README.md)

---

## Intended use

This demo is provided for **educational and illustrative purposes**.  
It demonstrates approaches to enterprise cyber risk quantification and decision support in regulated environments and does not predict specific events or outcomes.

--- 

## Return

📄 [Docs Home](../../README.md)

---
