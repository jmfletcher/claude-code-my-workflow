---
paths:
  - "scripts/**/*.py"
  - "Figures/**"
---

# Replication-First Protocol

**Core principle:** Replicate original results (Attempt 1) to the dot BEFORE extending.

---

## Phase 1: Inventory & Baseline

Before writing any Python code:

- [ ] Read Attempt 1's outputs in `reference/`
- [ ] Inventory: data files, processed CSVs, figures, report
- [ ] Record gold standard numbers from Attempt 1:

```markdown
## Replication Targets: Attempt 1 Outputs

| Target | Source | Value | Notes |
|--------|--------|-------|-------|
| State White rate (2019-23 avg) | Table 1 | 4.45 | Per 1,000 |
| Milwaukee Black deaths/yr | Table 1 | 55 | Approximate |
```

- [ ] Store targets in `quality_reports/replication_targets.md`

---

## Phase 2: Implement & Execute

- [ ] Follow `python-code-conventions.md` for all Python coding standards
- [ ] Match Attempt 1 specification exactly (formulas, palette, suppression handling)
- [ ] Save all outputs as CSV and PNG

### Common Python Pitfalls

| Issue | Trap | Fix |
|-------|------|-----|
| Integer division | `deaths / births` returns 0 if both int | `float(deaths) / births` |
| Suppressed "X" | Read as NaN or string | Handle explicitly before conversion |
| CI lower bound | Can go negative | `max(0, rate - ci_half)` |
| Rest of WI | Must be State − Milwaukee − Dane | Compute separately for births AND deaths |

---

## Phase 3: Verify Match

### Tolerance Thresholds

| Type | Tolerance | Rationale |
|------|-----------|-----------|
| Integers (N, counts) | Exact match | No reason for any difference |
| Rates (per 1,000) | < 0.01 | Rounding in display |
| CI bounds | < 0.1 | Float precision |

### If Mismatch

**Do NOT proceed to extensions.** Isolate which step introduces the difference, check common causes, and document the investigation.

---

## Phase 4: Only Then Extend

After replication is verified:

- [ ] Commit replication scripts: "Replicate Attempt 1 outputs — all targets match"
- [ ] Now extend with improvements (better figures, Quarto report, etc.)
