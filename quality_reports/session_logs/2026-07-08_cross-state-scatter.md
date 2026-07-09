# Session Log — 2026-07-08 — Cross-State School Scatter (Figure 12 in Other States)

## Goal

Test whether MMSD's weak school-level White–Black proficiency correlation (r ≈ 0.18,
Figure 12 of the main report) is an outlier nationally, by replicating the figure with
school-level by-race data from other states' DOE report-card downloads (SEDA is
district-level only for race breakdowns, so unusable for this question).

Plan: `.cursor/plans/cross-state_school_scatter_ab96011b.plan.md` (approved by user).

## What was built

| Artifact | Description |
|---|---|
| `analysis/13_download_states.py` | Per-state downloaders (CA, TX, IL, NY, OH, GA, NC, NJ) to `Data/raw/states/{st}/`; `--state` flag isolates failures |
| `analysis/14_load_states.py` | Per-state loaders → common long schema; output `output/data/panel_school_race_multistate.parquet` (1.9M rows) + QC report `output/tables/multistate_qc.txt` |
| `analysis/15_multistate_school_scatter.py` | Fig-12-style two-panel scatter per state (incl. WI from existing Forward panel); `output/figures/fig12_{st}_school_scatter.{pdf,png}` + `output/tables/multistate_school_correlations.csv` |
| `manuscript/cross-state.qmd` → `cross-state.pdf` | 12-page companion report: data sources, summary correlation tables, 9 state figures, limitations |
| `DATA.md` | New cross-state section: URL patterns, formats, per-state quirks, manual-download notes for FL/MI/MN/MA |
| `MEMORY.md` | Two `[LEARN]` entries (data quirks; substantive finding) |

## Coverage

- **Scripted + loaded (8 states + WI):** CA, TX, IL, NY, OH, GA, NC, NJ — pooled 2–3
  most recent years each (TX 2 years; IL 2 years — 2023 file lacks pooled by-race rates).
- **Manual-only (documented, not loaded):** FL (Akamai blocks scripts), MI (Power BI
  export only), MN (portal timeouts), MA (ASP.NET form export).
- NY required `brew install mdbtools` to export the 1.5 GB Access report-card databases.

## QC

- Statewide n-weighted means from school rows reproduce published magnitudes
  (e.g., CA 2024 ELA White ≈ 61%, Black ≈ 27%; NY school-row sums match the
  state row within suppression loss — verified grade 3 White 2024: 62,785 vs 63,219).
- Caught and fixed: NY statewide pseudo-school row (`111111111111`) doubling counts;
  NC LEA/SEA/SBE aggregate rows inflating N ~4x; CA 2023 schema difference;
  IL 2025 `Type`→`Level` rename; OH 2025 column-name change; TX 2023 form-param change.
- Correlations for subsamples with < 5 schools are reported as "—".

## Headline result

Statewide school-level White–Black ELA correlations: 0.58–0.76 in all eight comparison
states (WI 0.46 is the lowest). No state's overall pattern resembles MMSD's r ≈ 0.18 —
but the college-town analogs do: Evanston −0.24, Ithaca 0.03, Athens–Clarke 0.33
(counter-examples: Chapel Hill-Carrboro 0.58, College Station 0.63). White–Hispanic
correlations are strong everywhere (0.5–0.8), including all college towns — the same
asymmetry as Wisconsin. Interpretation: the MMSD pattern looks characteristic of
high-SES college-town districts rather than Madison-specific; MMSD is unusual mainly
in scale (41 schools with published Black rates).

## Open items

- FL/MI/MN/MA manual downloads if broader coverage is wanted.
- TX 2024-25 STAAR (TAPR 2025 vintage) not yet on the CGI endpoint; revisit.
- Consider a compact cross-state summary figure (dot plot of correlations by state)
  if this report graduates into the main manuscript.


---
**Context compaction (auto) at 13:16**
Check git log and quality_reports/plans/ for current state.

---

## Addendum (same day): place-level dot plot + QC pass

### New figure

- `analysis/16_place_correlation_dotplot.py` → `output/figures/fig13_place_correlation_dotplot.{pdf,png}`:
  one row per place (statewide samples + named districts), White–Black r in red,
  White–Hispanic r in blue, ordered by the B–W correlation, n≥25-school reliability
  screen. Added to `cross-state.qmd` ("Correlations at a glance").

### QC pass (user-requested): school counts and grade coverage

**Grade coverage — no high-school contamination found.**
- CA/TX/NY/OH/NC/NJ loaders pull per-grade rows for grades 3–8 only; buildings named
  "X High School" that appear are junior/senior-high configurations that genuinely
  house grades 7–8 (verified grade coverage is concentrated in 06–08), or 8-12
  buildings housing an 8th grade (e.g. Pepperell High GA, confirmed via NCES: grades
  8–12). IL IAR and GA Milestones EOG are administered in grades 3–8 only by
  construction (GA files verified ASSMT_CD == "EOG").
- Tested-count sums align with cohort sizes: CA 2025 W+B+H grades 3-8 ELA ≈ 1.98M,
  TX ≈ 1.89M, NC ≈ 585K, GA ≈ 676K — all consistent with enrollment shares. NY (770K)
  and NJ (377K) run lower, consistent with NY opt-outs and NJ small-cell suppression.
- School counts per state are plausible vs. NCES public-school totals (schools with
  any grade 3-8 ELA rate: CA 7.5K, TX 6.8K, IL 2.9K, NY 3.6K, OH 2.5K, GA 1.8K,
  NC 2.1K, NJ 1.9K).

**Bug found and fixed: school renames split scatter points.**
- Scripts 09/10/15 pooled schools grouping by NAME columns in addition to codes.
  Schools renamed across years appeared as two dots (WI: 106 school codes with >1
  name, incl. 3 in MMSD — Falk→Milele Chikasa Anana, Glendale→Dr Virginia Henderson,
  Randall). NY schools with missing district names were also silently dropped by
  `pivot_table` (~60 schools).
- Fix: group by codes/IDs only; attach most-recent name for labels; pivot on ID alone.
- Effect: MMSD White–Black r 0.18 → **0.23** (n 41 → 38); MMSD White–Hispanic
  0.65 → 0.63; WI overall B–W unchanged at 0.46; all other states' overall
  correlations moved < 0.02. Qualitative conclusions unchanged.
- Updated: figs 09/A10/12(all states)/13, correlation CSV, cross-state.qmd tables
  and narrative, MEMORY.md; re-rendered main.pdf (archived prior copy) and
  cross-state.pdf.

### Addendum (2026-07-09): reporting threshold raised to 16 schools

User-requested revision: remove places with <16 schools from the cross-state
write-up. `MIN_N_CORR` in script 15 raised 5 → 16 (figure notes and CSV now show
"—" for small subsamples). Under this screen every college-town analog except
Athens–Clarke County (18 schools) drops out — including Evanston (15), College
Station (15), Chapel Hill-Carrboro (11), Ithaca (5), Berkeley (4) — as does
Newark. Report rewritten accordingly: the abstract, finding 2, the
interpretation section, and the limitations no longer cite point estimates from
sub-16 districts; the college-town interpretation is now framed as a hypothesis
resting on Athens–Clarke alone, with the analogs' small size itself presented as
evidence of MMSD's unusual scale. cross-state.pdf re-rendered.

The place-level dot plot (report Figure 1, `fig13_place_correlation_dotplot`) was
then aligned to the same threshold: screen lowered 25 → 16 schools, adding
Athens–Clarke County (B–W 0.33, H–W 0.61) and College Station (H–W panel only,
0.62) — 20 places shown.

### Project close-out (2026-07-09)

Report sent to **Erin G. (Wisconsin State Journal)** as part of a story she is
working on. Project paused. State of the world at close:

- `manuscript/main.pdf` — main Wisconsin report (current, post school-dedup fix).
- `manuscript/cross-state.pdf` — cross-state companion (16-school reporting
  threshold throughout; MMSD White–Black r = 0.23, n = 38).
- Circulation to date: Eric Grodsky (feedback), Tommy Jaine (LFS), Erin G. (WSJ).
- Open items unchanged: FL/MI/MN/MA manual downloads; TX 2024-25 TAPR when posted;
  Grodsky feedback integration when received.
