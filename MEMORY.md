# Project Memory

Corrections and learned facts that persist across sessions.
When a mistake is corrected, append a `[LEARN:category]` entry below.

---

<!-- Append new entries below. Most recent at bottom. -->

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

---

## Data Monopolies Project (Bootstrap)

[LEARN:project] Data Monopolies measures authorship concentration (HHI, top-x share) in papers citing longitudinal datasets. First dataset: REGARDS via PubMed collection 46426411.

[LEARN:project] Author identity: PubMed strings + manual alias table per dataset. Never merge without documented entry in author_aliases.csv.

[LEARN:project] Language: R primary (rentrez, tidyverse). Python only when clearly needed.

[LEARN:project] Pipeline SSOT: raw/ → processed/ → output/. Never hand-edit metrics without rerunning scripts.

[LEARN:project] Bootstrap check-ins active for sessions 1–3. Checkpoint after config, download QC, first metrics. See bootstrap-checkins.md.

[LEARN:project] REGARDS source: https://www.ncbi.nlm.nih.gov/myncbi/browse/collection/46426411/ (911 papers expected as of June 2026).

[LEARN:project] Top-x default values: 1, 3, 5, 10. Configurable per dataset in config.yaml.

[LEARN:project] Publication-ready figures required: ggplot2 + project theme, PDF + PNG at 300 DPI, source data as RDS.

[LEARN:project] My NCBI collections (46426411) cannot be paginated via simple HTTP POST. Automated fallback: Entrez `"NS041588"[Grant Number]` yields 894 PMIDs vs 911 curated. Manual export to raw/pmid_list.csv for exact match.

[LEARN:project] REGARDS pilot results (2026-06-23): 893 papers, HHI=0.693 (post-Judd merge), Top-3=71.9%. Top author: Judd SE (345). Domain-specific HHI much higher in niche areas (caregiving HHI=2.7) than main CHD cluster (0.74).

[LEARN:project] HHI can exceed 1 with author-level paper-shares on multi-author papers — especially in small-N years/domains. Top-x share remains [0,1]. Use faceted plots for temporal trends.

[LEARN:aliases] 18 merges applied from alias_suggestions.csv Combine-with column (2026-06-23). Same?=Y without combine target = same last name only, not merged. Judd S target line corrected 14→24 (Judd SE).

[LEARN:project] Post-merge REGARDS: HHI=0.743, Top-3=74.9%, 3487 authors. Top: Judd SE (345), Safford MM (306), Howard VJ (296).
