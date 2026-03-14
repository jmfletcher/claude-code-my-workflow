# Deep Audit Report — Repository Infrastructure

**Date:** 2026-03-14  
**Scope:** CLAUDE.md accuracy, skills/rules consistency, cross-document consistency, hook code quality, quality gates  
**Instruction:** Report only — do not fix

---

## Executive Summary

| Category | Genuine Bugs | False Alarms |
|----------|--------------|--------------|
| 1. CLAUDE.md accuracy | 3 | 2 |
| 2. Skills and Rules consistency | 2 | 1 |
| 3. Cross-document consistency | 3 | 2 |
| 4. Hook code quality | 2 | 0 |
| 5. Quality gates | 0 | 0 |
| **Total** | **10** | **5** |

---

## 1. CLAUDE.md Accuracy

### 1.1 Folder Structure

**Finding:** CLAUDE.md omits several directories that exist on disk.

| Path | In CLAUDE.md? | Exists? | Verdict |
|------|---------------|---------|---------|
| `guide/` | No | Yes | **Genuine bug** — directory not documented |
| `output/` | No (mentioned in Current Project State table only) | Yes | **Genuine bug** — not in folder structure diagram |
| `Preambles/` | No | Yes | **Genuine bug** — directory not documented |
| `Slides/` | No | Yes | **False alarm** — framework template; empty .gitkeep |
| `docs/` | No | Yes | **False alarm** — deployment output; may be gitignored |
| `scripts/R/` | No | Yes | **False alarm** — framework has R; project uses Python |

**Verdict:** 3 genuine bugs (guide, output, Preambles missing from structure).

### 1.2 File Counts

| Claim | Actual | Verdict |
|-------|--------|---------|
| data/input: 7 PDFs | 7 PDFs | ✓ Correct |
| data/processed: 5 CSVs | 5 CSVs | ✓ Correct |
| literature: 3 files | 3 .md + README | ✓ Correct (3 lit files) |
| Figures: 4 PNGs | 4 PNGs | ✓ Correct |
| reference/figures_attempt1: 4 PNGs | 4 PNGs | ✓ Correct |
| scripts/python: config.py, 01–04 | config.py + 01–04 | ✓ Correct |

**Verdict:** All file counts accurate.

### 1.3 Path Verification

| Path | Exists? | Verdict |
|------|---------|---------|
| `quality_reports/plans/` | Yes | ✓ |
| `quality_reports/specs/` | Yes | ✓ |
| `quality_reports/session_logs/` | Yes | ✓ |
| `quality_reports/merges/` | Yes | ✓ |
| `reference/report_attempt1.md` | Yes | ✓ |
| `reference/figures_attempt1/` | Yes | ✓ |
| `Quarto/report.qmd` | Yes | ✓ |
| `Quarto/emory-clean.scss` | Yes | ✓ |

**Verdict:** All explicitly listed paths exist.

### 1.4 Config Script Naming

**Finding:** `quality_reports/plans/2026-03-14_project-migration-plan.md` references `00_setup.py`; CLAUDE.md and implementation use `config.py`.

**Verdict:** **Genuine bug** — plan is stale; implementation chose config.py.

---

## 2. Skills and Rules Consistency

### 2.1 YAML Frontmatter

All 23 skills in `.claude/skills/*/SKILL.md` have valid YAML frontmatter (start with `---`, include `name`, `description`, close with `---`).

**Rules:** 18 of 19 rules have YAML frontmatter with `paths:`. `meta-governance.md` has no frontmatter (always-on rule).

**Verdict:** No issues.

### 2.2 Rules paths → Existing Directories

| Rule | Path | Exists? | Verdict |
|------|------|---------|---------|
| pdf-processing.md | `master_supporting_docs/**` | No | **Genuine bug** — directory does not exist |
| quality-gates.md | `Slides/**/*.tex` | Slides/ exists | ✓ |
| quality-gates.md | `Quarto/**/*.qmd` | Yes | ✓ |
| quality-gates.md | `scripts/**/*.R` | scripts/R/ exists | ✓ |
| quality-gates.md | `scripts/**/*.py` | Yes | ✓ |
| python-code-conventions.md | `Figures/**/*.py` | Yes (pattern; no .py in Figures) | ✓ |

**Verdict:** 1 genuine bug — `pdf-processing.md` references non-existent `master_supporting_docs/`.

### 2.3 Contradictions Between Rules

No contradictions found. All rules agree on language (Python), output format (Quarto PDF), figure palette (#2171b5, #b2182b), and CI method (Poisson).

**Verdict:** No issues.

### 2.4 Templates Referenced

Rules reference `templates/quality-report.md`, `templates/session-log.md`, etc. All exist in `templates/`.

**Verdict:** No issues.

---

## 3. Cross-Document Consistency

### 3.1 Language & Output Format

| Document | Language | Output Format | Verdict |
|----------|----------|---------------|---------|
| CLAUDE.md | Python | Quarto → PDF | ✓ |
| MEMORY.md | Python | Quarto → PDF | ✓ |
| WORKFLOW_QUICK_REF.md | Python | Quarto → PDF | ✓ |
| Plan (2026-03-14) | Mixed (says R then Python) | Quarto PDF | **Genuine bug** — internal contradiction |

**Plan contradiction:** Plan states "Goal: Redo the project using Attempt 2's workflow infrastructure... build a proper R-based, Quarto-compatible analysis" but then "Design Decision 1: Language: Python (Kept)". Phase 3 says "Integrate R-generated figures" but project uses Python-generated figures.

**Verdict:** 1 genuine bug — plan has internal contradictions.

### 3.2 Figure Palette & CI Method

| Document | White | Black | CI Method | Verdict |
|----------|-------|-------|-----------|---------|
| CLAUDE.md | #2171b5 | #b2182b | Poisson: rate ± 1.96 × (1000√D)/B | ✓ |
| MEMORY.md | #2171b5 | #b2182b | Same | ✓ |
| WORKFLOW_QUICK_REF.md | #2171b5 | #b2182b | Same | ✓ |
| Plan | Not specified | Not specified | Not specified | **False alarm** — plan is high-level |

**Verdict:** 1 false alarm — plan omits palette but core docs agree.

### 3.3 Feature Counts (Guide vs. Reality)

| Document | Agents | Skills | Rules | Hooks |
|----------|--------|--------|-------|-------|
| guide/workflow-guide.qmd | 10 | 22 | 18 | 7 |
| Actual (on disk) | 11 | 23 | 19 | 7 |

**Verdict:** **Genuine bug** — guide has stale counts (10 vs 11 agents, 22 vs 23 skills, 18 vs 19 rules).

### 3.4 Guide: R vs. Python

**Finding:** Guide says "The `/data-analysis` skill also generates R scripts (saved to `scripts/R/`)". The project's `data-analysis` skill is Python-focused and saves to `scripts/python/`.

**Verdict:** **False alarm** — guide is generic template; project has customized data-analysis for Python.

---

## 4. Hook Code Quality

### 4.1 Python Hooks — Error Handling

| Hook | Fail-open pattern? | try/except in __main__? | Verdict |
|------|--------------------|------------------------|---------|
| log-reminder.py | Yes (exit 0 on exception) | Yes | ✓ |
| pre-compact.py | Yes | Yes | ✓ |
| post-compact-restore.py | Yes | Yes | ✓ |
| verify-reminder.py | Yes | Yes | ✓ |
| context-monitor.py | Yes | Yes | ✓ |

**Verdict:** All Python hooks have proper fail-open pattern.

### 4.2 Shell Hooks — Error Handling

| Hook | Issue | Verdict |
|------|-------|---------|
| protect-files.sh | No `set -e`; relies on `jq` without checking if installed/available | **Genuine bug** — if `jq` missing, script may fail silently or produce wrong output |
| protect-files.sh | No explicit error handling for malformed JSON input | **Genuine bug** — malformed JSON could cause `jq` to fail |

**notify.sh:** Uses `2>/dev/null` which suppresses errors; exits 0. Fail-open behavior is acceptable for notifications.

**Verdict:** 2 genuine bugs in protect-files.sh (jq dependency, JSON parsing).

### 4.3 Other Hook Quality Checks

- Python hooks use `from __future__ import annotations` ✓
- Hash length `[:8]` consistent across hooks ✓
- State stored in `~/.claude/sessions/<hash>/` ✓
- No `/tmp/` usage ✓

---

## 5. Quality Gates

**Question:** Does `.claude/rules/quality-gates.md` reference the correct file types (.py, .qmd)?

**Finding:** Yes. The `paths:` frontmatter includes:
- `scripts/**/*.py` ✓
- `Quarto/**/*.qmd` ✓

Content includes scoring rubrics for:
- Python Scripts (.py) ✓
- Quarto Slides (.qmd) ✓

**Verdict:** No issues.

---

## 6. Additional Findings

### 6.1 verify-reminder.py — Missing .py Extension

**Finding:** `VERIFY_EXTENSIONS` in verify-reminder.py includes `.tex`, `.qmd`, `.R` but NOT `.py`. This project is Python-based; editing Python scripts should trigger a verification reminder.

**Verdict:** **Genuine bug** — Python scripts do not get a reminder to run/verify after edit.

### 6.2 data-analysis Skill — output/diagnostics/

**Finding:** data-analysis skill says "Save all diagnostic figures to `output/diagnostics/`". Directory does not exist.

**Verdict:** **False alarm** — skill says to create output dirs with `os.makedirs(..., exist_ok=True)`; directory would be created on first use.

---

## 7. Summary Table

| # | Severity | Category | Finding | Verdict |
|---|----------|-----------|---------|---------|
| 1 | Medium | CLAUDE.md | guide/, output/, Preambles/ missing from folder structure | Genuine bug |
| 2 | Low | CLAUDE.md | Plan references 00_setup.py; actual is config.py | Genuine bug |
| 3 | Medium | Rules | pdf-processing.md: master_supporting_docs/ does not exist | Genuine bug |
| 4 | Medium | Cross-doc | Plan: R vs. Python contradictions | Genuine bug |
| 5 | Medium | Cross-doc | Guide: stale counts (10→11 agents, 22→23 skills, 18→19 rules) | Genuine bug |
| 6 | Medium | Hooks | protect-files.sh: jq dependency; no check if installed | Genuine bug |
| 7 | Low | Hooks | protect-files.sh: no handling for malformed JSON | Genuine bug |
| 8 | Low | Hooks | verify-reminder.py: .py not in VERIFY_EXTENSIONS | Genuine bug |
| 9 | Low | CLAUDE.md | Slides/, docs/, scripts/R/ not in structure | False alarm |
| 10 | Low | Cross-doc | Plan omits palette | False alarm |
| 11 | Low | Cross-doc | Guide says R scripts; project uses Python | False alarm |
| 12 | Low | Skills | output/diagnostics/ missing | False alarm |

---

## 8. Recommendations (Report Only — No Fixes Applied)

1. **CLAUDE.md:** Add guide/, output/, Preambles/ to folder structure diagram.
2. **Plan:** Update to remove R references; align with config.py (not 00_setup.py).
3. **pdf-processing.md:** Either create master_supporting_docs/ or remove/scope the rule for projects that use it.
4. **Guide:** Update counts to 11 agents, 23 skills, 19 rules.
5. **protect-files.sh:** Add jq availability check; handle JSON parse errors gracefully.
6. **verify-reminder.py:** Add `.py` to VERIFY_EXTENSIONS with action "run script to verify output".

---

*End of report. No fixes were applied per instructions.*
