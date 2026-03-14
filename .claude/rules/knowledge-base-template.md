---
paths:
  - "Quarto/**/*.qmd"
  - "scripts/**/*.py"
---

# Project Knowledge Base: Wisconsin Infant Mortality

## Notation Registry

| Rule | Convention | Example | Anti-Pattern |
|------|-----------|---------|-------------|
| Rate units | Per 1,000 live births | "14.3 per 1,000" | "14.3 per thousand" or "0.0143" |
| CI notation | "95% CI" with Poisson label | "95% CI, Poisson-based" | "confidence interval" without method |
| Race categories | Non-Hispanic White, Non-Hispanic Black | "White", "Black" in figures | "Caucasian", "African American" |
| Geography names | State, Milwaukee, Dane, Rest of Wisconsin | — | "WI", "MKE", "rest of state" |

## Key Constants

| Constant | Value | Source |
|----------|-------|--------|
| NFP cost per life saved | $3.2M | Miller, 2015 |
| NFP lives per $1M | 0.31 | Miller, 2015 |
| Denmark campaign reduction | 17.2% | Altindag et al., 2022 |
| KMC neonatal mortality RR | 0.75 (meta: 0.68) | NEJM, 2021 |
| Milwaukee Black deaths/yr | ~55 | WISH 2019–2023 avg |
| Detectability formula | min averted = ceil(1.96√D) | Poisson assumption |

## Data Sources

| Source | Content | Years | Notes |
|--------|---------|-------|-------|
| WISH (DHS) | Births and infant deaths by race | 1999–2023 | "X" = suppressed (1–4) |
| Cap Times | Birth Equity Act coverage | March 2026 | Rep. Shelia Stubbs |
| CDC WONDER | County × race (optional) | 2017–2023 | Not used in main analysis |

## Report Structure

| # | Section | Core Question |
|---|---------|--------------|
| — | Executive Summary | What should policymakers know? |
| — | Introduction | Why does Wisconsin's disparity matter? |
| 1 | Literature Review | What interventions work and at what cost? |
| 2 | Data & Rates | Where are Black infant deaths concentrated? |
| 3 | Birth Equity Act | How do the 7 bills connect to evidence? |
| 4 | Conclusion | Why focus on Milwaukee? |

## Design Principles

| Principle | Evidence | Applied Where |
|-----------|----------|--------------|
| Milwaukee focus | Only county with ~55 Black deaths/yr | Tables 2–3, conclusion |
| Honest uncertainty | Wide CIs outside Milwaukee | All figures, Table 2 |
| Evidence candor | State when evidence is indirect | Section 3 (each bill) |
| Detectability framing | Poisson CI → min averted | Table 3 |

## Python Code Pitfalls

| Bug | Impact | Fix |
|-----|--------|-----|
| Integer division in rate calc | Wrong rate values | `float(deaths) / births * 1000` |
| Suppressed "X" read as NaN | Lost data rows | Read CSV with `dtype=str`, convert manually |
| CI lower bound < 0 | Impossible negative rate | `max(0, rate - ci_half)` |
| matplotlib default colors | Inconsistent palette | Always pass `color=RACE_COLORS[race]` |
