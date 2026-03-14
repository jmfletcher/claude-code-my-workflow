# Workflow Quick Reference

**Model:** Contractor (you direct, Claude orchestrates)
**Project:** Wisconsin Infant Mortality — Evidence, Disparities, Policy
**Language:** Python | **Output:** Quarto → PDF

---

## The Loop

```
Your instruction
    ↓
[PLAN] (if multi-file or unclear) → Show plan → Your approval
    ↓
[EXECUTE] Implement, verify, done
    ↓
[REPORT] Summary + what's ready
    ↓
Repeat
```

---

## I Ask You When

- **Design forks:** "Option A (fast) vs. Option B (robust). Which?"
- **Code ambiguity:** "Spec unclear on X. Assume Y?"
- **Data edge case:** "Suppressed count — impute as Total − White?"
- **Scope question:** "Also refactor Y while here, or focus on X?"

---

## I Just Execute When

- Code fix is obvious (bug, pattern application)
- Verification (running scripts, checking outputs)
- Documentation (logs, commits)
- Plotting (per established palette and standards)
- Rendering Quarto (after you approve content)

---

## Quality Gates (No Exceptions)

| Score | Action |
|-------|--------|
| >= 80 | Ready to commit |
| < 80  | Fix blocking issues |

---

## Non-Negotiables

- **Paths:** `pathlib.Path(__file__).resolve()` for relative paths in all Python scripts
- **Figure palette:** White=#2171b5, Black=#b2182b. 300 DPI. "(95% CI, Poisson-based)" in titles
- **CI method:** Poisson-based: rate ± 1.96 × (1000√D)/B. Do not change formula without discussion
- **Suppression:** WISH "X" → impute as Total − White; document in code and report
- **Attempt 1 is read-only:** Never modify files in `../Attempt 1/`

---

## Preferences

**Visual:** Publication-ready figures, consistent palette, 300 DPI PNG
**Reporting:** Concise bullets for summaries; detailed prose in the report
**Session logs:** Always (post-plan, incremental, end-of-session)
**Data:** CSVs as interchange format between scripts and Quarto

---

## Exploration Mode

For experimental work, use the **Fast-Track** workflow:
- Work in `explorations/` folder
- 60/100 quality threshold (vs. 80/100 for production)
- No plan needed — just a research value check (2 min)
- See `.claude/rules/exploration-fast-track.md`

---

## Next Step

You provide task → I plan (if needed) → Your approval → Execute → Done.
