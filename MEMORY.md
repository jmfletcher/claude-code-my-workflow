# Project Memory

Corrections and learned facts that persist across sessions.
When a mistake is corrected, append a `[LEARN:category]` entry below.

---

<!-- Append new entries below. Most recent at bottom. -->

## Panel Conditioning (UK) — project defaults (updated 2026-04-02)

[LEARN:workflow] This fork prioritizes **manuscript + analysis + slides** over Beamer/Quarto lecture pairs. SSOT: `analysis/` → outputs → `manuscript/` and `slides/`; legacy folders are reference-only.

[LEARN:workflow] **Denominators** for treated vs control weeks must stay explicit in code and writing; domain-reviewer and r-code-conventions reinforce this.

[LEARN:workflow] **Collaboration cadence:** more frequent check-ins for the first several sessions; taper when the user signals.

[LEARN:documentation] Project identity lives in **`CLAUDE.md`**; upstream README remains a general workflow overview with a short fork banner at top.

[LEARN:workflow] **Python** is the primary analysis language; Stata scripts in `Old Attempts and Results/Terrence/` are reference only. Port with `statsmodels.OLS(cov_type="cluster")`.

[LEARN:data] Three treated birth weeks confirmed from `final.csv`: NSHD=group1 (3–9 Mar 1946), NCDS=group2 (3–9 Mar 1958), BCS70=group3 (5–11 Apr 1970). 9 weeks × 3 groups; `week_in_year` is cluster-relative (1–9), NOT ISO week.

[LEARN:data] Legacy `mortality age final.csv` has `age_needed` (0–70) for age-interval regressions (9,450 rows). Rate denominator not yet confirmed — pending `01_load_and_clean.py`.

[LEARN:files] Output convention: **`output/figures/`** (PDF + PNG) and **`output/tables/`** (CSV + LaTeX). Analysis scripts in `analysis/`. Manuscript in `manuscript/main.qmd`. Slides in `slides/main.qmd`.

[LEARN:workflow] Warren2022 WLS mortality paper: Warren, Halpern-Manners & **Helgertz** (2022), *SSM–Pop Health* vol 19, p.101233, DOI 10.1016/j.ssmph.2022.101233. Key null result: no panel conditioning effect on longevity. Direct comparison for UK analysis.

[LEARN:data] **Denominator confirmed**: `rate = total / N × 1000` where N ≈ 15,300 per birth week (fixed cohort birth count, not surviving population). `rate/total` ratio is ~constant (std=0.005). Important: denominator is static (birth count), not dynamic (survivors).

[LEARN:results] **First estimates from legacy data**: pooled cohort coef = **0.061** (SE=0.029, p=0.036). Age-interval pattern: elevated at ages 0–9 (β=0.070, p=0.014) and 60–69 (β=0.497, p=0.005); near-null at 30–49. Contrasts with WLS null result — needs careful interpretation.

[LEARN:workflow] **Quarto render requires**: nbformat, nbclient, ipykernel, jupyter-core. Add to requirements.txt. `matplotlib.use("Agg")` needed in scripts run from non-interactive shell.

[LEARN:files] **Slides folder**: macOS case-insensitive filesystem merged writes to `slides/` into existing `Slides/` directory. Use `Slides/` (capital S) as canonical. `Slides/main.qmd` is the presentation deck.

[LEARN:data] **ONS XLS structure confirmed (2026-04-02)**: Each data sheet = one calendar year of death registration (`Data 1970`–`Data 2013`, 44 sheets). Columns: `birth_week`, then `Total` (1970–1979) or `All` (1980+), then `January`–`December`. header_row=6. 135 birth weeks per sheet. Load with `pd.read_excel(..., header=6, engine="xlrd")`; rename Total/All → `deaths_total`.

[LEARN:data] **Denominator refined**: Cell-by-cell comparison of ONS deaths vs legacy rates gives implied N mean = 15,334 (SD = 1,215) per birth week. This variation reflects real differences in births by week/year. Script uses constant N=15,334; regression is invariant to this scale since `C(week_in_year)` absorbs level differences.

[LEARN:data] **Legacy `final.csv` is cross-sectional**: 135 rows = one per birth week (birth year × week_in_year × group), collapsed over all death years. NOT comparable to raw ONS death counts per (birth_week × death_year). The correct regression comparator is `mortality age final.csv` (9,450 rows = 135 birth weeks × 70 ages).

[LEARN:data] **ONS → age-aggregated validation**: After reading raw ONS deaths and aggregating to (birth_week × age), we get exactly 5,913 rows matching the legacy `mortality age final.csv` non-missing count. Row-count match confirmed ✅. Rate means: legacy 1.689, ONS 1.751 (3.7% diff from variable N).

[LEARN:pipeline] **Script outputs**: `01_clean_long.csv` (5,940 rows: birth_week × death_year), `01_age_aggregated.csv` (5,913 rows: birth_week × age, same structure as legacy). Use age_aggregated for regressions that replicate legacy Stata results.

[LEARN:data] **Legacy data artifact — age-0 infant mortality**: Legacy `mortality age final.csv` has rate=0.0 for all age=0 cells (BCS70 1970–1972 births). Fresh ONS data correctly shows ~16–19 per 1,000 infant deaths at age 0. This is a deliberate or incidental suppression in the legacy analysis. For the panel conditioning question (adult survey participation), infant mortality is largely irrelevant, but using fresh data gives more faithful representation.

[LEARN:data] **`year` in legacy regression = BIRTH year (not death year)**. The Stata regression uses `C(year)` as birth-year fixed effects (values 1944–1972). When replicating with fresh data, use `birth_year` as the FE, NOT `birth_year + age` (death year). Using death year as the FE gives completely wrong estimates.

[LEARN:pipeline] **Replication validation (ages 10–59)**: Fresh ONS data yields estimates within 0.01 of legacy for ages 10–19, 20–29, 30–39, 40–49, 50–59 ✅. Pooled estimate: 0.057 (fresh) vs 0.061 (legacy) — 7% diff, same sign/significance. Age 0–9 and 60–69 differ due to legacy artifact and data truncation. **Use legacy estimates as canonical until denominator denominator provenance is fully resolved.**

[LEARN:pipeline] **Full pipeline now complete and validated**: 00 → 01 → 02 → 03 → 04 → manuscript. `04_main_tables.py` generates LaTeX tables + JSON results summary. `04_results_summary.json` provides machine-readable estimates for manuscript inline references. `manuscript/main.qmd` reads directly from `04_results_summary.json`.

[LEARN:results] **By-cohort estimates reveal key heterogeneity** (added 2026-04-02): NSHD 1946 β=0.130 (p=0.028); NCDS 1958 β=−0.021 (p=0.36, null — consistent with Warren 2022 WLS); BCS70 1970 β=0.075 (p<0.001). The pooled positive result is driven by NSHD and BCS70, not NCDS. Each cohort covers a different age window (NSHD: 22–69, NCDS: 10–57, BCS70: 0–45), so cross-cohort differences partly reflect life-stage coverage, not only true heterogeneity. NSHD age 30–39 is anomalously negative (β=−0.095, p=0.0005); NCDS age 30–39 also negative (β=−0.122, p=0.006). Both warrant scrutiny.

[LEARN:pipeline] `02_by_cohort_coef.csv` produced by `run_by_cohort()` in `02_replicate_stata.py`. `04_table3_by_cohort.csv` + `fig04_by_cohort_coefs.png` are the corresponding output artifacts. Age bins are cohort-specific (defined in `COHORT_AGE_BINS` dict) to match each cohort's observation window.

[LEARN:results] **Cause-of-death results** (added 2026-04-02, `05_cause_of_death.py`): Pooled: cancer β=0.025 (p=0.047), respiratory β=0.020 (p=0.051), other β=0.016 (p=0.047); cardiovascular β=−0.009 (null); external β=0.008 (null). By cohort: NSHD elevated mortality concentrated in **respiratory** (β=0.057, p<0.001) and **other**; NCDS null across all causes; BCS70 elevated in **cancer** (β=0.044, p<0.001) and external. The BCS70 cancer result at young ages (0–45) is unexpected and warrants scrutiny — may reflect data artefacts or small-cell noise.

[LEARN:results] **Robustness checks reveal fragility** (added 2026-04-02, `06_robustness.py`): Baseline β=0.060 (p=0.024). (1) Narrow control window (weeks 5–9 only, 4 controls): β=0.039, p=0.105 — INSIGNIFICANT. (2) Very narrow (weeks 6–9, 3 controls): β=0.024, p=0.38 — NULL. (3) Log outcome: β=0.056, p=0.035 — holds. (4) Drop NSHD: β=0.028, p=0.21 — null. (5) Drop NCDS: β=0.101, p=0.001. (6) Drop BCS70: β=0.052, p=0.17 — null. (7) Death-year FE: β=−0.014, p=0.84 — COMPLETE NULL. **Conclusion: the positive pooled result is sensitive to control window width and FE specification. Likely reflects systematic differences between distant control weeks and the treated week rather than a true panel conditioning effect.** Manuscript must present this honestly.

[LEARN:manuscript] **Methodological clarifications (2026-04-02)**: (1) week_in_year FEs are cluster-position FEs (1–9), not absolute calendar weeks. They are identified from the 4–5 non-target birth years within each cohort group. Treated week is always at position 8. (2) APC issue: age + birth-year FEs are jointly identified because each cohort group spans 5 birth years, so age and birth year provide independent variation. Calendar-year (period) FEs are omitted by design. (3) An RD alternative (linear/polynomial in birth-week position, discontinuity at treated week) is noted as a future extension. (4) WLS = 1/3 random sample of 1957 Wisconsin HS graduates (not half). (5) Bib entries now filled for Papers/: Crossley2014_survey_saving, Zwane2011_surveyed_behavior, Axinn2015_frequent_measurement.

[LEARN:pipeline] **Full pipeline (as of 2026-04-02)**: `00_data_overview.py` → `01_load_and_clean.py` → `02_replicate_stata.py` → `03_figures.py` → `04_main_tables.py` → `05_cause_of_death.py` → `06_robustness.py` → `manuscript/main.qmd` (renders to PDF). All scripts run from repo root.

[LEARN:results] The treated week is at position 8 of 9 in each cluster (7 control weeks BEFORE, 1 AFTER). This asymmetry means the baseline result may reflect a trend in mortality across weeks within the cluster rather than a treated-vs-control contrast. Narrow-window robustness checks address this.

[LEARN:data] ONS cause-of-death XLS has three ICD revision periods: ICD-8 (1970–1978), ICD-9 (1979–2000), ICD-10 (2001–2013). Columns change across revisions; harmonised to 5 categories (cancer, cardiovascular, respiratory, external, other). Column names contain soft-hyphens (`\xad`); strip with `.replace("\xad", "-")`. Script: `05_cause_of_death.py`; outputs: `05_cause_long.csv`, `05_cause_age_agg.csv`, `05_cause_coef_pooled.csv`, `05_cause_coef_by_cohort.csv`, `fig05_cause_coefs.png`.

[LEARN:workflow] `Bibliography_base.bib` removed from protect-files hook (was blocking bib edits). `settings.json` remains protected.

## Workflow Patterns

[LEARN:workflow] Requirements specification phase catches ambiguity before planning → reduces rework 30-50%. Use spec-then-plan for complex/ambiguous tasks (>1 hour or >3 files).

[LEARN:workflow] Spec-then-plan protocol: AskUserQuestion (3-5 questions) → create `quality_reports/specs/YYYY-MM-DD_description.md` with MUST/SHOULD/MAY requirements → declare clarity status (CLEAR/ASSUMED/BLOCKED) → get approval → then draft plan.

[LEARN:workflow] Context survival before compression: (1) Update MEMORY.md with [LEARN] entries, (2) Ensure session log current (last 10 min), (3) Active plan saved to disk, (4) Open questions documented. The pre-compact hook displays checklist.

[LEARN:workflow] Plans, specs, and session logs must live on disk (not just in conversation) to survive compression and session boundaries. Quality reports only at merge time.

## Documentation Standards

[LEARN:documentation] When adding new features, update BOTH README and guide immediately to prevent documentation drift. Stale docs break user trust.

[LEARN:documentation] Always document new templates in README's "What's Included" section with purpose description. Template inventory must be complete and accurate.

[LEARN:documentation] Guide must be generic (framework-oriented) not prescriptive. Provide templates with examples for multiple workflows (LaTeX, R, Python, Jupyter), let users customize. No "thou shalt" rules.

[LEARN:documentation] Date fields in frontmatter and README must reflect latest significant changes. Users check dates to assess currency.

## Design Philosophy

[LEARN:design] Framework-oriented > Prescriptive rules. Constitutional governance works as a TEMPLATE with examples users customize to their domain. Same for requirements specs.

[LEARN:design] Quality standard for guide additions: useful + pedagogically strong + drives usage + leaves great impression + improves upon starting fresh + no redundancy + not slow. All 7 criteria must hold.

[LEARN:design] Generic means working for any academic workflow: pure LaTeX (no Quarto), pure R (no LaTeX), Python/Jupyter, any domain (not just econometrics). Test recommendations across use cases.

## File Organization

[LEARN:files] Specifications go in `quality_reports/specs/YYYY-MM-DD_description.md`, not scattered in root or other directories. Maintains structure.

[LEARN:files] Templates belong in `templates/` directory with descriptive names. Currently have: session-log.md, quality-report.md, exploration-readme.md, archive-readme.md, requirements-spec.md, constitutional-governance.md.

## Constitutional Governance

[LEARN:governance] Constitutional articles distinguish immutable principles (non-negotiable for quality/reproducibility) from flexible user preferences. Keep to 3-7 articles max.

[LEARN:governance] Example articles: Primary Artifact (which file is authoritative), Plan-First Threshold (when to plan), Quality Gate (minimum score), Verification Standard (what must pass), File Organization (where files live).

[LEARN:governance] Amendment process: Ask user if deviating from article is "amending Article X (permanent)" or "overriding for this task (one-time exception)". Preserves institutional memory.

## Skill Creation

[LEARN:skills] Effective skill descriptions use trigger phrases users actually say: "check citations", "format results", "validate protocol" → Claude knows when to load skill.

[LEARN:skills] Skills need 3 sections minimum: Instructions (step-by-step), Examples (concrete scenarios), Troubleshooting (common errors) → users can debug independently.

[LEARN:skills] Domain-specific examples beat generic ones: citation checker (psychology), protocol validator (biology), regression formatter (economics) → shows adaptability.

## Memory System

[LEARN:memory] Two-tier memory solves template vs working project tension: MEMORY.md (generic patterns, committed), personal-memory.md (machine-specific, gitignored) → cross-machine sync + local privacy.

[LEARN:memory] Post-merge hooks prompt reflection, don't auto-append → user maintains control while building habit.

## Meta-Governance

[LEARN:meta] Repository dual nature requires explicit governance: what's generic (commit) vs specific (gitignore) → prevents template pollution.

[LEARN:meta] Dogfooding principles must be enforced: plan-first, spec-then-plan, quality gates, session logs → we follow our own guide.

[LEARN:meta] Template development work (building infrastructure, docs) doesn't create session logs in quality_reports/ → those are for user work (slides, analysis), not meta-work. Keeps template clean for users who fork.
