# Workflow Quick Reference

**Model:** Contractor (you direct, Claude orchestrates)

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
- **Comparison group choice:** "Use Milwaukee as comparison, or all non-MMSD districts?"
- **Scope question:** "Also refactor Y while here, or focus on X?"

---

## I Just Execute When

- Code fix is obvious (bug, pattern application)
- Verification (tolerance checks, tests, compilation)
- Documentation (logs, commits)
- Plotting (per established standards below)
- Deployment (after you approve, I ship automatically)

---

## Quality Gates (No Exceptions)

| Score | Action |
|-------|--------|
| >= 80 | Ready to commit |
| >= 90 | Required for manuscript figures and tables |
| < 80  | Fix blocking issues |

---

## Non-Negotiables

**Path convention:**
```python
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]  # repo root
DATA_DIR = ROOT / "Data"
OUTPUT_DIR = ROOT / "output"
```
No hardcoded absolute paths anywhere.

**Figure standards:**
- White background, minimum 9pt font, consistent font family (Helvetica or DejaVu Sans)
- Save every figure as both PDF and PNG (150 DPI minimum for PNG)
- Suppressed or missing subgroup values must be visually distinguished from zero (hollow marker, dashed line, or caption note)

**Color palette (colorblind-safe, race groups):**
```python
RACE_COLORS = {
    "White":                  "#1b7837",
    "Black or African American": "#762a83",
    "Hispanic":               "#f1a340",
    "Asian":                  "#2166ac",
    "American Indian":        "#d7191c",
    "Two or More Races":      "#878787",
}
```

**Suppression rule:**
- DPI cells with N < 10 → replace with `NaN` (never impute)
- Log every suppressed cell: `output/tables/suppression_log.csv` with columns `[school_id, district_id, race_group, grade, subject, year]`

**Denominator rule:**
- Always carry `n_tested` alongside `pct_proficient` in every intermediate and output dataset
- Never plot a proficiency rate without documenting or annotating N

---

## Preferences

**Visual:** Figures as specified above. Consistent axis labels and titles. Legends inside plot frame when space allows. Grid lines: light gray horizontal only.

**Reporting:** Concise bullet-point summaries. Details on request. Flag suppression rates and coverage gaps proactively.

**Session logs:** Always — post-plan entry, incremental updates during long tasks, end-of-session summary. Save to `quality_reports/session_logs/YYYY-MM-DD_task-name.md`.

**Replication:** Scripts must be runnable from repo root with no arguments. All random seeds set explicitly if any stochastic step exists.

**Check-in cadence:** More frequent check-ins during first few sessions; taper as patterns stabilize.

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
