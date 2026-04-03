# Panel Conditioning in UK Cohort Studies

## Project identity

**Working title:** Panel conditioning in UK cohort studies (mortality comparison).

**Research question:** Do people born in birth weeks **selected for** major UK panel/cohort studies have **different mortality** than people born in **similar non-selected weeks**, as cohorts age? The three studies used a **week-of-birth** sampling frame—treating survey participation as a natural experiment of being “surveyed” vs not, holding calendar cohort roughly fixed.

**Design:** Compare mortality profiles (and clear reporting of **numerators and denominators** / at-risk populations) for **treated** (selected week(s)) vs **control** weeks using **administrative vital statistics** (counts by year and week of birth). Examine whether profiles **diverge** over age relative to controls.

**Principal investigator:** Jason Fletcher (adapt `CLAUDE.local.md` for affiliation if needed).

**Repository:** Working research project using the Claude Code academic workflow ([fork lineage](https://github.com/jmfletcher/claude-code-my-workflow/tree/Panel-Conditioning-in-UK)). This checkout is **project-first**, not a generic template.

---

## Deliverables (in priority order)

1. **End-to-end analysis pipeline** — reproducible code, documented denominators, versioned outputs.
2. **Preprint-ready manuscript** — clear tables and **publication-quality figures** (polished, consistent theme).
3. **Short slide deck** — main findings; source in Markdown; export PDF.

Planned locations (create as work proceeds):

| Artifact | Location |
|----------|----------|
| Analysis (R) | `analysis/` |
| Figures (from code) | `output/figures/` or `analysis/figures/` (pick one convention in first analysis plan; document in knowledge base) |
| Manuscript | `manuscript/` |
| Slides | `slides/` |
| Exploratory / scratch | `explorations/` |
| Prior partial work (reference only) | `Old Attempts and Results/`, `Data/`, `Papers/` |

---

## Workflow (non-negotiable)

- **Plan-first** for any non-trivial task (multi-step, multi-file, or ambiguous). Save plans to `quality_reports/plans/YYYY-MM-DD_description.md`; use `quality_reports/specs/` + `templates/requirements-spec.md` when requirements are fuzzy.
- **Contractor mode after approval:** implement → verify → review → fix → score (see `.claude/rules/orchestrator-protocol.md` and `orchestrator-research.md` for R/analysis).
- **Memory:** append `[LEARN:…]` entries to `MEMORY.md` when decisions or corrections should persist. Use `.claude/state/personal-memory.md` for machine-local notes (gitignored).
- **Quality gates:** default **80/100** to commit; aim higher for manuscript figures and tables.

**Collaboration cadence:** For the **first few sessions**, pause more often for confirmation (plan boundaries, identification narrative, figure conventions). Taper to standard contractor autonomy as patterns stabilize.

---

## Domain standards (summary)

- **Denominators:** Never silently merge treated/control populations; every rate or count series should trace to documented at-risk denominators (see `.claude/rules/knowledge-base-template.md`).
- **Figures:** Publication-ready: consistent fonts, colors, labels, legible legends; no placeholder styling in outputs intended for the manuscript.
- **Prior work:** Review `Old Attempts and Results/` for context; **do not** treat it as authoritative—rebuild analysis cleanly with explicit replication checks where possible.

---

## Pointers

| Resource | Purpose |
|----------|---------|
| `.claude/rules/knowledge-base-template.md` | Notation, cohorts, estimands, pitfalls |
| `.claude/WORKFLOW_QUICK_REF.md` | Non-negotiables and preferences |
| `MEMORY.md` | Cross-session learnings |
| `Bibliography_base.bib` | Shared citations (expand as needed) |
| `.claude/agents/domain-reviewer.md` | Substance review for manuscript/analysis claims |

---

## Commands (typical)

- **Python (primary):** `python3 analysis/script.py` from repo root; `pip install -r requirements.txt` to install deps.
- **Quarto (manuscript/slides):** `quarto render manuscript/main.qmd` or `quarto render slides/main.qmd`.
- **R (legacy/optional):** `Rscript path/to/script.R` from repo root.
- **Stata (reference only):** scripts in `Old Attempts and Results/Terrence/`; do not modify.
- **Git:** conventional commits; do not commit large raw data—document paths in `Data/` and ignore binaries via `.gitignore`.

---

## Out of scope unless added later

- Beamer lecture decks and Beamer↔Quarto **lecture** sync are **not** part of this project unless you create `Slides/` + paired Quarto lectures. Path-scoped rules that only match those paths stay dormant.
