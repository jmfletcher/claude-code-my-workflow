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
- **Replication edge case:** "Just missed tolerance. Investigate?"
- **Scope question:** "Also refactor Y while here, or focus on X?"

---

## I Just Execute When

- Code fix is obvious (bug, pattern application)
- Verification (tolerance checks, tests, compilation)
- Documentation (logs, commits)
- Plotting (per established standards)
- Deployment (after you approve, I ship automatically)

---

## Quality Gates (No Exceptions)

| Score | Action |
|-------|--------|
| >= 80 | Ready to commit |
| < 80  | Fix blocking issues |

---

## Non-Negotiables

- **Dataset paths:** All data under `datasets/{name}/`; shared code in `scripts/R/`
- **Author aliases:** Every merge documented in `author_aliases.csv` with notes
- **Pipeline SSOT:** raw → processed → output; never hand-edit metrics
- **Figure standards:** ggplot2 + project theme, PDF + PNG at 300 DPI, source data as RDS
- **Count reconciliation:** Raw PMIDs must match processed PMIDs before metrics
- **Seed convention:** `set.seed()` once at top for any stochastic code
- **Tolerance:** HHI/top-x hand-check within 1e-10; paper counts must match exactly

---

## Preferences

<!-- Fill in as you discover your working style -->

**Visual:** [How you want figures/plots handled]
**Reporting:** [Concise bullets? Detailed prose? Details on request?]
**Session logs:** Always (post-plan, incremental, end-of-session)
**Replication:** [How strict? Flag near-misses?]

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
