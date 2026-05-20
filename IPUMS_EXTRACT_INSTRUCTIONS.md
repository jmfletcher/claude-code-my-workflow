# Updating the IPUMS NHIS extract to add detailed cause of death

Your current extract (`nhis_00002.dat`) carries only `MORTUCODLD`, the
10-category leading-cause recode. We want to add `MORTUCOD`, the detailed
ICD-10 underlying cause of death, which is published by IPUMS for
samples 1986-2004 only.

## Steps

1. Log in at [https://nhis.ipums.org](https://nhis.ipums.org) and open
   "My data extracts".
2. Click **Revise** on the extract that produced `nhis_00002.dat`.
   (If it has been retired, "Clone" it.)
3. Under **Select Variables -> Person -> Mortality** add:
   - `MORTUCOD` -- Underlying cause of death (ICD-10).
   - Optionally also `MORTDIAB`, `MORTHYPR`, `MORTHIPFX` if you want
     multiple-cause flags for diabetes / hypertension / hip fracture
     sensitivity checks. They are flags (Y/N) so they cannot stand in
     for `MORTUCOD` but are useful additional covariates.
4. Confirm samples 1986-2004 are included (they should already be in the
   extract). For other samples `MORTUCOD` will be coded `9999` ("NIU")
   and we will treat those as missing.
5. Submit the extract. IPUMS will queue it; when it is finished IPUMS
   emails you a download link.
6. Download:
   - `nhis_00002.dat` (the data, overwrites the 588 MB file)
   - `nhis_00002.do`  (the Stata command file, overwrites it)
   - `nhis_00002.cbk` (the codebook, overwrites it)
   Place all three at the project root, replacing the existing files.
7. Open the new `nhis_00002.do` and find the line that says
   ```
   readstr mortucod  XXX-YYY   (or:  str4 mortucod ...)
   ```
   Note the **start and end column positions** (1-indexed). These are
   the bytes to add to `scripts/nhis_coresident_minors.py`.
8. Edit `scripts/nhis_coresident_minors.py`:
   - In `_colspecs()` find the comment marker
     `# TODO[mortucod]: ADD HERE WHEN MORTUCOD IS IN THE EXTRACT`.
   - Replace it with one tuple line, using the column positions you
     read in step 7. The column type for `mortucod` is `string`
     (4-character ICD-9 or ICD-10 code):
     ```python
     ("mortucod", <START>, <END>, "string", None),
     ```
   - Keep the rest of the spec table consistent: if `mortucod` was
     inserted before `mortwt`/`mortwtsa`, shift their start/end columns
     accordingly (re-read from the new `nhis_00002.do`).
9. Rerun the analytic build:
   ```
   python scripts/nhis_coresident_minors.py
   ```
   This regenerates `nhis_with_coresident_minors.parquet` with the new
   `mortucod` column.
10. Run the cause-specific Schlüter analysis (already drafted and waiting):
    ```
    python scripts/run_schluter_mortucod.py
    ```
    Outputs land in
    `results/kinship/schluter_drugs_firearms/mortucod_*.csv` and
    print a side-by-side comparison of:
    - Naive (kids per living adult)
    - All-cause kappa (already in PR #3)
    - Intent-stratified (`MORTUCODLD` codes 4 vs 10, already in PR #3)
    - **`MORTUCOD` ICD-10 drug-specific** (NHIS 1999-2004)
    - **`MORTUCOD` ICD-9 drug-specific** (NHIS 1986-1998)

## Why two ICD eras

NHIS-LMF 1986-1998 carries ICD-9 underlying cause codes. NHIS-LMF
1999-2004 carries ICD-10. The Schlüter target uses ICD-10 (NCHS
1999-2020), so the cleanest comparison is the NHIS 1999-2004 ICD-10
subset. We will also report the NHIS 1986-1998 ICD-9 subset (mapped to
the equivalent E-code ranges) as a sensitivity check on the
"effect is constant over time" assumption.

## Crosswalk used by `scripts/run_schluter_mortucod.py`

### ICD-10 (NHIS 1999-2004, NCHS 1999-2020)

| Cause | Intent | ICD-10 codes |
|---|---|---|
| Drug | accidental | X40-X44 |
| Drug | suicide | X60-X64 |
| Drug | assault | X85 |
| Drug | undetermined | Y10-Y14 |
| Firearm | accidental | W32-W34 |
| Firearm | suicide | X72-X74 |
| Firearm | assault | X93-X95 |
| Firearm | undetermined | Y22-Y24 |
| Firearm | legal | Y35.0 |

### ICD-9 (NHIS 1986-1998 only)

| Cause | Intent | ICD-9 codes |
|---|---|---|
| Drug | accidental | E850-E858 |
| Drug | suicide | E950.0-E950.5 |
| Drug | assault | E962.0 |
| Drug | undetermined | E980.0-E980.5 |
| Firearm | accidental | E922 |
| Firearm | suicide | E955.0-E955.4 |
| Firearm | assault | E965.0-E965.4 |
| Firearm | undetermined | E985.0-E985.4 |
| Firearm | legal | E970 |

The two-era split treats ICD-9 NHIS as a separate sensitivity sample;
no comparability-ratio bridge is applied.
