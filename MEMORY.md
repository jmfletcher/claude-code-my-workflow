# Project Memory — Wisconsin Mortality Project

Corrections and learned facts that persist across sessions.
When a mistake is corrected, append a `[LEARN:category]` entry below.

---

<!-- Append new entries below. Most recent at bottom. -->

## Project Context

[LEARN:project] This is a mortality analysis project (not a lecture/slides project). Primary workflow: Python data analysis (pandas, numpy, matplotlib), life tables, publication-ready figures. The Beamer/Quarto/Slides infrastructure from the template is NOT the focus.

[LEARN:project] Key paper to replicate: Roberts et al. (2019) BMC Public Health — "Contributors to Wisconsin's persistent black-white gap in life expectancy." We replicate LE trends only (Figures 1-2), not cause decomposition.

[LEARN:data] Population file is fixed-width CDC bridged-race format. Positions: Year(1-4), State(5-6), FIPS(7-11), spaces, Race(14), Origin(15), Sex(16), Age(17-18), Population(19-26). Must use pd.read_fwf() with explicit colspecs.

[LEARN:data] Mortality CSV columns: deathmonth, race, racer3, sex, age, ICD codes (7/8/9/10 depending on era), deathyear, countyrs (county FIPS), hispanic, mannerdeath. Race: 1=White, 2=Black. Sex: 1=Male, 2=Female.

[LEARN:data] Milwaukee County FIPS = 55079. Dane County FIPS = 55025. All WI counties use 55xxx prefix.

[LEARN:methods] Roberts et al. uses 3-year pooled data (e.g., "2015" = 2014–2016), abridged life tables with 19 age groups (<1, 1-4, 5-9, ..., 80-84, 85+). We replicate LE trends only — no cause-of-death decomposition.

[LEARN:scope] Project scope: life expectancy gaps only (no Arriaga cause decomposition). Geographic extension: statewide WI, Milwaukee County, Dane County, rest of WI (state minus Milwaukee minus Dane).

[LEARN:data] Analysis restricted to 2005-2017 data only. 3-year windows span center years 2006-2016 (underlying data 2005-2017). All 2005+ mortality records have Hispanic origin coded, so non-Hispanic filter is exact.

[LEARN:methods] Pooling: both deaths AND population are SUMMED across the 3-year window. The ratio sum(D)/sum(N) gives the average annual rate. Earlier bug used mean(pop) which inflated rates by ~3x.

[LEARN:tools] Project uses Python (not R). Core stack: pandas, numpy, matplotlib, geopandas. Scripts go in scripts/python/. Intermediate data saved as parquet/pickle.

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
