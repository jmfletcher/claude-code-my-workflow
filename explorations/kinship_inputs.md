# Inputs for the Kinship-Matrix Replication of Villaveces (2025)

Reuses the **preprocessed** Zenodo data from the Villaveces team so we avoid the
heavy NCHS line-list preprocessing.

## Source

- Zenodo: [doi.org/10.5281/zenodo.11423744](https://doi.org/10.5281/zenodo.11423744)
  (concept), [13765716](https://zenodo.org/records/13765716) (this version).
- Single archive `data.zip` (~223 MB) with preprocessed deaths, births, and
  population tables.
- License: **CC-BY-4.0**.

## Local destination

`data_kinship/` (gitignored - file too big to track).
After unzip, expected (per Villaveces README):

- `data/NCHS/death/output/Allcause_deaths_1983-2021.RDS`
- `data/NCHS/death_child/output/NCHS_deaths_children_1983-2021.RDS`
- `data/NCHS/births/output/births_1968-2021.RDS`
- `data/NCHS/fertility/pop_1968.rds` (population, SEER)
- `data/data/pop/raw*` (CDC WONDER bridged-race pop 1990+)
- `data/grandparents/raw*` (ACS grandparents)
- `data/CDC/ICD-10_113_Cause/*` (state-level WONDER deaths)

All `.RDS` are serialized R objects. Python ingestion path: use
`pyreadr.read_r()` (pure-Python R serialization reader) to load them once and
cache as parquet.

## Variable shapes we need for the matrix engine

Given the math in `kinship_math.md`, we need per year `t`:

| Quantity | Shape | Source |
|---|---|---|
| `pf[a, t]`, `pm[a, t]` | single-year ages × years, female/male survival | derive from `Allcause_deaths_1983-2021.RDS` deaths + population |
| `ff[a, t]`, `fm[a, t]` | mother-age fertility (and father-age fertility) | `births_1968-2021.RDS` + population denominators |
| `N_{x,t}^{\text{children}}` | single-year child age × year | `NCHS_deaths_children_*` plus pop |

For Villaveces fixed boundaries:
- Calendar years: 2000 - 2021 (study window). Need fertility back to ~1983 to
  populate parents-by-age distribution of children alive 0-17 in 2000.
- Ages: 0 - 100 (open-ended last class).
- Race/eth groups: NH White, NH Black, NH AIAN, NH Asian, Hispanic (5 groups
  matching their figure 2).

## Sex of births

Villaveces (and the kinship literature) typically use a fixed female share at
birth `birth_female = 1/2.04 ≈ 0.49`. We follow that.

## Race/ethnicity bridging

The NHIS analytic frame uses bridged 5 categories matching `raceth5`. The
Villaveces inputs are already prepared at the same level of detail. We do not
need to rebridge.

## What we will NOT replicate

- The Bayesian Poisson resampling and HPC ranking (the paper produces
  credible intervals from many resampled mortality/natality replications).
  For a single-stack Python replication we use point estimates and quote
  uncertainty from the published intervals where needed.
- Grandparent caregiver loss layer (the "caregiver death" part of the title).
  Our scope is **parental orphanhood** only, as this is what the kinship
  matrix natively produces from the `m` block. Grandparent loss can be a
  later extension.
- State-level breakdowns. National + national-by-race/eth is enough for
  showing the NHIS calibration delta.

## Acceptance criteria for baseline replication

Following the math note's discussion of how matrix kinship differs from
multiplicative orphanhood:

| Metric | Villaveces published | Our kinship-matrix target |
|---|---|---|
| 2021 prevalent orphanhood + caregiver loss | ~2.91 M | ~2.91 M (combined) |
| 2021 prevalent **parental** orphanhood only | not headline; see Fig 2 | match within ±15 % |
| Rank order by race/eth | AIAN > Black > Hispanic ≈ White > Asian | match exactly |
| 2000 - 2021 incidence trend | +49.5 % | direction and magnitude within ±10 pp |

If the matrix kinship totals come in low because of the strict definition of
`parental` only and we strip grandparent loss, that is expected; we report
the parental-only number for the comparison and note this in the writeup.
