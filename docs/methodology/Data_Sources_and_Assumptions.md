# Data Sources and Modeling Assumptions

This document describes the publicly available sources and high-level assumptions used to inform the modeling scenarios demonstrated in **RiskQuant**.

RiskQuant is a **quantitative cyber risk demonstration tool**. The sources listed here are used to calibrate assumptions related to event frequency, impact severity, and tail-risk behavior for educational and illustrative purposes. They are not used to predict specific incidents or outcomes.

---

## Purpose of this document

This document serves three purposes:

1. **Transparency**  
   To clearly identify the external sources used to support modeling assumptions.

2. **Defensibility**  
   To explain how widely cited industry and regulatory materials inform scenario calibration.

3. **Consistency**  
   To provide a centralized reference so assumptions remain aligned across all demo scenarios and supporting documents.

Each demo guide and the white paper explicitly cite sources using white-paper notation (e.g., `[1]`, `[2]`). This document explains *how* those sources are used in aggregate.

---

## Categories of assumptions

RiskQuant scenarios rely on three broad categories of assumptions:

- **Event frequency**  
  How often a given type of cyber event is expected to occur over a one-year period.

- **Loss severity**  
  The financial impact associated with an event, expressed as a bounded range rather than a single value.

- **Tail risk**  
  Low-probability, high-impact outcomes that materially influence upper percentiles (e.g., p95).

Monte Carlo simulation is used to explore the interaction of these assumptions across thousands of simulated outcomes.

---

## Primary data sources

### Verizon Data Breach Investigations Report (DBIR) — 2024

**Used to inform:**
- Relative frequency of attack types
- Prevalence of identity-based compromise
- Common initial access vectors (e.g., phishing, credential misuse)

The DBIR provides large-scale empirical context on *how* organizations are breached, which supports relative likelihood assumptions across scenarios.

**Reference:**  
Verizon. *2024 Data Breach Investigations Report*.

---

### IBM Cost of a Data Breach — 2024

**Used to inform:**
- Median breach cost ranges
- Industry-specific cost considerations
- Cost escalation factors for regulated data

IBM’s report is used to bound **loss severity distributions**, particularly for moderate and severe outcomes, rather than to establish exact loss values.

**Reference:**  
IBM Security. *Cost of a Data Breach Report 2024*.

---

### NetDiligence Cyber Claims Study — 2023

**Used to inform:**
- Tail-risk severity
- Legal, forensic, and response cost baselines
- Loss behavior beyond median outcomes

NetDiligence data is particularly useful for understanding **upper-percentile behavior** (e.g., p90–p95), where claims experience diverges significantly from averages.

**Reference:**  
NetDiligence. *Cyber Claims Study 2023*.

---

### HHS 405(d) and HC3 Advisories

**Used to inform:**
- Identity compromise trends in healthcare
- Third-party and vendor exposure patterns
- Common failure modes in access control and monitoring

These advisories provide domain-specific context for healthcare scenarios, particularly in enterprise environments.

**Reference:**  
U.S. Department of Health & Human Services, Health Sector Cybersecurity Coordination Center (HC3).

---

### OCR Enforcement History

**Used to inform:**
- Governance and access control failures
- Audit logging and monitoring deficiencies
- Regulatory exposure resulting from systemic control gaps

Historical enforcement actions are used to contextualize **governance and compliance scenarios**, not to estimate fines or penalties directly.

**Reference:**  
HHS Office for Civil Rights enforcement actions and resolution agreements.

---

## Assumption calibration approach

### Frequency assumptions
Event frequency assumptions are calibrated using:
- Relative prevalence observed in industry reports
- Scenario context (organization size, maturity, domain)
- Bounded ranges rather than fixed rates

Frequency is modeled probabilistically to reflect uncertainty and variability.

---

### Severity assumptions
Loss severity assumptions are:
- Expressed as bounded ranges (minimum, most likely, maximum)
- Informed by industry cost studies and claims data
- Adjusted for organizational context (e.g., SMB vs enterprise)

Severity modeling emphasizes **plausible ranges**, not precise forecasts.

---

### Tail-risk considerations
Upper percentiles (e.g., p95) are intentionally highlighted because:
- They capture low-probability, high-impact outcomes
- They are often most relevant for executive and board-level discussions
- They better reflect the financial risk of systemic failures

Tail risk is informed primarily by claims studies and regulatory exposure patterns.

---

## Important limitations

- All scenarios are **illustrative**, not predictive
- Real-world outcomes depend on organization-specific controls, detection, response, and governance
- Public reports aggregate across industries and geographies and may not reflect any single organization’s experience
- RiskQuant does not model attacker intent, correlation, or dynamic control effectiveness in its current form

These limitations are intentional and are discussed further in the white paper.

---

## Relationship to demo scenarios

The same sources and assumption categories are used across:
- SMB demonstration scenarios
- Mid-Market demonstration scenarios
- Enterprise Healthcare demonstration scenarios

What varies between demos is **calibration**, not methodology. Assumptions are adjusted to reflect organizational scale, complexity, and regulatory exposure.

---

## Relationship to the white paper

The RiskQuant white paper provides:
- A deeper technical explanation of the simulation methodology
- Mathematical and conceptual justification for Monte Carlo modeling
- Expanded discussion of uncertainty and percentile interpretation

This document should be read as a **supporting methodological reference**, not a substitute for the white paper.

---

## Disclaimer

All materials in this repository are provided for **educational and demonstration purposes only**.  
They illustrate approaches to cyber risk quantification and decision support and do not predict specific events, losses, or regulatory outcomes.
