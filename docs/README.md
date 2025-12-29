# RiskQuant Documentation

This directory contains the supporting documentation and demonstration materials for **RiskQuant**, a Monte Carlo–based cyber risk quantification dashboard.

The materials are organized to show **how RiskQuant is applied in realistic business contexts**, across different organizational sizes and maturity levels, using calibrated risk registers and scenario-driven analysis.

---

## How to use this documentation

Each demonstration scenario includes a **consistent set of supporting artifacts** designed for different audiences and use cases. Together, these artifacts allow readers to understand both the **inputs** (risk registers and assumptions) and the **outputs** (quantified financial risk and analysis).

Markdown files in this repository provide **navigation and context**.  
The authoritative content is contained in the accompanying PDF documents.

---

## Demonstration scenarios

### Small & Medium Business (SMB)
**Primary focus:** Phishing and credential compromise  
**Audience:** SMB leadership, IT managers, non-specialist stakeholders  

📁 `docs/demos/SMB/`

**Supporting artifacts:**
- **Risk Register – SMB (Visual).pdf**  
  User-friendly, color-coded risk register formatted for readability and discussion, using standard qualitative risk color mappings.
- **Risk Register – SMB (Visual).png**  
  Screenshot of the Excel-based risk register used as simulation input.
- **RiskQuant for SMB Demo.pdf**  
  Written product demonstration guide, including an Executive Summary and step-by-step walkthrough of the RiskQuant interface.
- **RiskQuant for SMB Demo Visual Companion.pdf**  
  Companion slide deck with annotated screenshots and section-numbered callouts aligned to the written demo.

📄 [SMB Demo](demos/SMB/README.md)

---

### Mid-Market
**Primary focus:** Vendor supply-chain compromise and SaaS platform failure  
**Audience:** IT managers, security generalists, GRC practitioners  

📁 `docs/demos/Mid-Market/`

**Supporting artifacts:**
- **Risk Register – Mid-Market (Visual).pdf**  
  Color-coded, presentation-ready risk register reflecting mid-market operational realities and domain-level risk.
- **Risk Register – Mid-Market (Visual).png**  
  Screenshot of the Excel-based risk register used as simulation input.
- **RiskQuant for Mid-Market Demo.pdf**  
  Product demonstration guide focused on value realization, domain comparison, and scenario aggregation.
- **RiskQuant for Mid-Market Demo Visual Companion.pdf**  
  Companion slide deck with annotated screenshots and section-numbered callouts aligned to the written demo.

📄 [Mid-Market Demo](demos/Mid-Market/README.md)

---

### Enterprise Healthcare
**Primary focus:** Portfolio-level cyber risk in regulated healthcare environments  
**Audience:** Security leadership, compliance teams, auditors, executives  

📁 `docs/demos/Enterprise-Healthcare/`

**Supporting artifacts:**
- **Risk Register – Enterprise Healthcare (Visual).pdf**  
  Presentation-ready risk register highlighting regulated data exposure, legacy system risk, and operational dependencies.
- **Risk Register – Enterprise Healthcare (Visual).png**  
  Screenshot of the Excel-based risk register used as simulation input.
- **RiskQuant for Enterprise Healthcare Demo.pdf**  
  Comprehensive demonstration guide covering portfolio analysis, scenario deep dives, and cross-domain synthesis.
- **RiskQuant for Enterprise Healthcare Demo Visual Companion.pdf**  
  Companion slide deck with annotated screenshots and section-numbered callouts aligned to the written demo.

📄 [Enterprise Healthcare Demo](demos/Enterprise-Healthcare/README.md)

---

## White paper

📁 `docs/whitepaper/`

The RiskQuant white paper provides a deeper technical and conceptual explanation of:

- Monte Carlo simulation in cyber risk analysis
- Loss frequency and severity modeling
- Percentile-based interpretation (p50, p90, p95)
- Design principles and implementation of the RiskQuant framework

📄 [White Paper](whitepaper/README.md)

---

## Data sources and modeling assumptions

📁 `docs/methodology/Data_Sources_and_Assumptions.md`

All demonstration scenarios are informed by **publicly available industry research and regulatory guidance**, which are explicitly cited within each document using white-paper notation (e.g., `[1]`, `[2]`).

A centralized explanation of how these sources are used to defend modeling assumptions and parameterization is provided for transparency and governance.

📄 Data Sources and Assumptions](methodology/Data_Sources_and_Assumptions.md)

---

## Relationship to the codebase

The documentation in this directory corresponds directly to the RiskQuant application located under:

📁 `src/montecarlo_app/`


Each demo uses:
- A dedicated risk register (provided in `data/input/`)
- The same simulation engine and visualization pipeline
- Assumptions calibrated to organizational size, maturity, and threat profile

The documents are intended to **explain how the application is used**, not to replace or abstract away the code itself.

---

## Intended use

All materials in this repository are provided for **educational and demonstration purposes**.  
They illustrate approaches to cyber risk quantification and decision support, not predictions of specific events or outcomes.

---

## Where to go next

- Start with the demo that best matches your organization size
- Review the white paper for technical depth
- Explore the codebase to understand how the models and visualizations are implemented
