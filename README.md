# Data Monopolies

**Measuring authorship concentration in longitudinal study citation networks.**

For each major longitudinal/survey dataset, this project downloads all papers citing that dataset, extracts co-authors, and computes authorship concentration measures — the Herfindahl-Hirschman Index (HHI) and top-x author shares.

**PI:** Jason Fletcher, University of Wisconsin–Madison  
**Branch:** `Data-Monopolies`  
**Last Updated:** 2026-06-23

---

## Research Question

Who publishes using shared longitudinal datasets? How concentrated is that authorship — do a few investigators dominate, or is access diffuse?

We apply standard economics concentration measures (HHI, top-x share) to co-authorship networks around major datasets.

---

## Datasets

| Dataset | Source | Status | Papers |
|---------|--------|--------|--------|
| [REGARDS](datasets/REGARDS/) | [PubMed 46426411](https://www.ncbi.nlm.nih.gov/myncbi/browse/collection/46426411/) | Config scaffolded | 911 expected |
| MIDUS | TBD | Planned | — |
| Wisconsin Longitudinal Study | TBD | Planned | — |
| MESA | TBD | Planned | — |

---

## Quick Start

```bash
# Clone and checkout branch
git clone https://github.com/jmfletcher/claude-code-my-workflow.git
cd claude-code-my-workflow
git checkout Data-Monopolies

# Run REGARDS pipeline (once implemented)
Rscript datasets/REGARDS/scripts/run_pipeline.R
```

---

## Project Structure

```
datasets/{name}/          # One folder per dataset
├── config.yaml           # Source URL, metadata, top-x values
├── raw/                  # Downloaded PubMed records
├── processed/            # papers_authors.csv, author_aliases.csv
├── output/               # monopoly_metrics.csv, figures/
└── scripts/              # Dataset-specific pipeline

scripts/R/                # Shared utilities (fetch, parse, compute)
quality_reports/          # Plans, session logs, reviews
.claude/                  # Workflow rules, skills, agents
```

---

## Metrics

| Metric | Definition |
|--------|------------|
| **HHI** | \(\sum_i s_i^2\) where \(s_i\) = author *i*'s paper share |
| **Top-x share** | Fraction of papers co-authored by the top *x* authors |

See `.claude/rules/authorship-monopoly-metrics.md` for full definitions.

---

## Workflow

This project uses the [Claude Code academic workflow](https://github.com/jmfletcher/claude-code-my-workflow) (forked from [pedrohcgs/claude-code-my-workflow](https://github.com/pedrohcgs/claude-code-my-workflow)):

- **Plan first** for non-trivial tasks
- **Contractor mode** after plan approval
- **Quality gates** at 80/100
- **Bootstrap check-ins** during first 3 sessions

See [CLAUDE.md](CLAUDE.md) for project configuration and [`.claude/rules/`](.claude/rules/) for detailed protocols.

---

## Key Commands

| Command | Purpose |
|---------|---------|
| `/data-monopoly REGARDS` | Full pipeline for a dataset |
| `/data-analysis [goal]` | General R analysis |
| `/review-r [file]` | R code review |

---

## Author Identity

Authors are identified via PubMed strings (`{LastName} {Initials}`) with manual alias merges for known duplicates. Every merge is documented in `author_aliases.csv` with rationale.

---

## License

MIT — see [LICENSE](LICENSE).
