# Manuscript (`main.qmd`)

## Circulation

- **2026-04-06:** Draft sent to **Eric Grodsky** for feedback and to **Tommy Jaine** for LFS. Next session: incorporate comments when ready.
- **2026-07-09:** Report sent to **Erin G. (Wisconsin State Journal)** as part of a story she is working on. Sent after the cross-state companion report was finalized (16-school reporting threshold; MMSD White–Black r = 0.23).

---

## Selection brief (Introduction + 5 figures)

A short draft PDF with the same *Draft* banner as `main-draft.pdf` is built from `selection-brief.qmd`:

- **Output:** `main-selection-brief.pdf`
- **Content:** full **Introduction** (with in-text citations), plus main-report **Figures 1, 3, 9, 12, 20** (as numbered in the full PDF): gap trends, decomposition, MMSD Black vs. peers, school race scatter, and appendix E ED vs. non-ED school scatter.
- **Layout:** each figure is on its own **landscape** page, scaled to near full page. The **reference list** is omitted (`suppress-bibliography: true`); in-text parenthetical citations remain. **Figures 12 and 20** are scaled with `scale=2.25` in `adjustbox` (over two times the native PDF size before any max-dimension cap) and the figure notes are re-typeset in a wrapped `parbox` under the image. Update the hard-coded correlation text in `selection-brief.qmd` if you regenerate figures and the printed correlations change.

```bash
quarto render manuscript/selection-brief.qmd --to pdf
```

---

## Cross-state companion report (`cross-state.qmd` → `cross-state.pdf`)

Replicates main-report Figure 12 (school-level White vs. Black / White vs. Hispanic
ELA scatter) for **CA, TX, IL, NY, OH, GA, NC, NJ** plus Wisconsin, to test whether
MMSD's weak White–Black school correlation is an outlier. Pipeline:

```bash
python3 analysis/13_download_states.py     # raw files -> Data/raw/states/
python3 analysis/14_load_states.py         # -> output/data/panel_school_race_multistate.parquet
python3 analysis/15_multistate_school_scatter.py  # -> fig12_{st}_*.png + correlations CSV
python3 analysis/16_place_correlation_dotplot.py  # -> fig13 place-level dot plot (report Fig 1)
quarto render manuscript/cross-state.qmd --to pdf
```

The correlation tables in `cross-state.qmd` are hard-coded from
`output/tables/multistate_school_correlations.csv` — refresh them if figures are
regenerated. Per-state source quirks are in `DATA.md`.

**Reporting threshold:** correlations from subsamples with fewer than **16 schools**
are never reported (MIN_N_CORR in script 15; MIN_SCHOOLS in script 16) — do not cite
point estimates for Evanston, Ithaca, Berkeley, Chapel Hill-Carrboro, Princeton,
Newark, or Athens (OH).

---

## Draft PDF (`main-draft.pdf`)

The draft build adds a centered *Draft* banner at the top of each page via `includes/draft-banner.tex`.

**Render:**

```bash
quarto render manuscript/main-draft.qmd --to pdf
```

**After you edit `main.qmd`**, refresh `main-draft.qmd` so it stays in sync:

```bash
bash scripts/sync-main-draft-qmd.sh
```

Then render `main-draft.qmd` again. Shared LaTeX preamble lives in `includes/pdf-header.tex`.

## Archived PDFs

See `archive/README.md` for timestamped copies of `main.pdf`.
