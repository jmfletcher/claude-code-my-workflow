# Constitutional Governance — Data Monopolies

**Immutable principles vs. flexible preferences for this project.**

---

## Article I: Pipeline Single Source of Truth

**Principle:** Data flows `raw/` → `processed/` → `output/`. Scripts are authoritative; derived files are never hand-edited.

**Why:** Prevents silent corruption of metrics and ensures reproducibility.

**Exceptions:** `author_aliases.csv` may be hand-edited (it is the dedup authority), but every edit must include a documented rationale in the `notes` column.

---

## Article II: Author Alias Authority

**Principle:** `datasets/{name}/processed/author_aliases.csv` is the authoritative deduplication table. No author merges without an alias entry.

**Why:** Author name ambiguity is the largest source of measurement error in bibliometric concentration metrics.

**Exceptions:** Exploratory alias candidates in `explorations/` before graduation to production.

---

## Article III: Plan-First Threshold

**Principle:** Enter plan mode for: new dataset onboarding, new metric definitions, or any task touching >2 files.

**Why:** Prevents mid-implementation pivots on methodological decisions.

**Exceptions:** Typo fixes, single-file alias additions with ≤5 rows, exploration folder fast-track (see `exploration-fast-track.md`).

---

## Article IV: Quality Gate

**Principle:** Nothing commits below 80/100. Pipeline count mismatches block commit regardless of score.

**Why:** Technical debt in data pipelines compounds silently.

**Exceptions:** WIP branches explicitly tagged; exploration folder (60/100 threshold).

---

## Article V: Dataset Isolation

**Principle:** Each dataset is self-contained under `datasets/{name}/`. Shared logic lives only in `scripts/R/`.

**Why:** Enables parallel work on REGARDS, MIDUS, WLS, MESA without cross-contamination.

**Exceptions:** Cross-dataset comparison outputs go in repo-root `output/` with explicit dataset list in filename.

---

## User Preferences (Override Anytime)

- Top-x values (default: 1, 3, 5, 10)
- Figure color palette (institutional vs colorblind-safe)
- Whether to report normalized HHI alongside raw
- Comment verbosity in R scripts
- Checkpoint frequency during bootstrap period

---

## Amendment Process

When deviating from an article, ask:

> "Are you **amending Article X** (permanent change) or **overriding for this task** (one-time exception)?"

Document amendments in session log with `[CONSTITUTIONAL AMENDMENT]` tag.
