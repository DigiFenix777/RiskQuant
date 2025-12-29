# RiskQuant White Paper

This folder contains the **RiskQuant White Paper**, which provides a deeper technical and conceptual explanation of the RiskQuant modeling framework and how to interpret its outputs.

If you are primarily interested in *how to use* the dashboard and interpret results at a scenario level, start with the demo documentation first. If you want to understand *why the model is structured the way it is*, how Monte Carlo applies to cyber risk, and how to interpret percentile-based outputs defensibly, this white paper is the right place.

---
![ENT HC Demo Dashboard](docs/images/README-WP.png)
## What the white paper covers

The white paper is intended to support both technical and non-technical stakeholders by explaining:

- **Why Monte Carlo simulation** is useful for cyber risk analysis
- The difference between **qualitative ratings** and **quantitative loss modeling**
- How **event frequency** and **loss severity** are modeled
- How to interpret **loss distributions** using percentiles (p50, p90, p95)
- Why **tail risk** matters for budgeting, insurance, and executive decision-making
- How RiskQuant’s modeling assumptions are calibrated using public sources

---

## How to use it

A recommended reading flow:

1. Read the Executive Overview to understand scope and intent  
2. Review the modeling framework section to understand assumptions and structure  
3. Use the percentile interpretation guidance as a reference while reviewing demo outputs  
4. Use the cited sources and methodology references for defensibility and transparency

---

## Related methodology reference

For a centralized description of the public sources used to support scenario calibration and assumptions:

📄 [Data Sources and Assumptions](../methodology/Data_Sources_and_Assumptions.md)

---

## Navigation

Return to the main project and demos:

📄 [Project Home](../../README.md)

📄 [Documentation Home](../README.md)

Jump directly to the demo scenarios:

📄 [SMB Demo](../demos/SMB/README.md)

📄 [Mid-Market Demo](../demos/Mid-Market/README.md)

📄 [Enterprise Healthcare Demo](../demos/Enterprise-Healthcare/README.md)
