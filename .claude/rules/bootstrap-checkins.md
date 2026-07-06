# Bootstrap Check-ins — Early Session Cadence

**During the first 3 sessions, checkpoint with the user more frequently than standard contractor mode.**

---

## Why Bootstrap Check-ins

The user is learning how the workflow operates. More frequent checkpoints build trust, surface misunderstandings early, and establish patterns for future autonomous work.

---

## Session 1: Configuration Adaptation (This Session)

**Checkpoint after:**
- All config files updated (CLAUDE.md, rules, skills, scaffold)
- Verification checklist complete
- Summary presented for user review

**Ask user:**
- Does the folder structure make sense?
- Any missing rules or preferences?
- Ready to proceed to REGARDS download?

---

## Session 2: REGARDS Download + QC

**Checkpoint after:**
- PubMed collection downloaded
- Count reconciliation complete (911 papers ± documented exclusions)
- `papers_authors.csv` generated
- Initial alias suggestions flagged for review

**Ask user:**
- Review alias suggestions — which merges are correct?
- Any papers that shouldn't be in the collection?
- Confirm top-x values (default: 1, 3, 5, 10)

---

## Session 3: First Metrics + Figures

**Checkpoint after:**
- HHI and top-x metrics computed
- 2–3 publication-ready figures generated
- QC checks pass
- Session log written

**Ask user:**
- Do metrics match expectations?
- Figure quality acceptable?
- Ready to switch to standard contractor mode?

---

## After Session 3

Revert to standard contractor mode per `orchestrator-protocol.md`:
- Plan → approve → implement autonomously
- Check in only for ambiguity or decisions
- Present summary when quality gate met

---

## Checkpoint Format

Each checkpoint includes:

```markdown
## Bootstrap Checkpoint #N — [Phase Name]

**Completed:**
- [List of completed items]

**Open decisions:**
- [Questions requiring user input]

**Next step (if approved):**
- [What happens next]

**Blockers:**
- [Anything preventing progress, or "None"]
```

---

## Tracking

Record checkpoint completion in:
- Session log: `quality_reports/session_logs/YYYY-MM-DD_bootstrap-N.md`
- MEMORY.md: `[LEARN:bootstrap] Checkpoint N complete — [key decision made]`

After checkpoint 3, append to MEMORY.md:

```
[LEARN:bootstrap] Bootstrap period complete. Standard contractor mode active.
```
