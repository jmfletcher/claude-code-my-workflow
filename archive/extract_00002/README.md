# Archived IPUMS NHIS extract `nhis_00002`

Superseded by `nhis_00003` on May 20, 2026.

## Why archived

- `nhis_00002` did **not** include `MORTUCOD` (detailed underlying cause of death).
- `nhis_00003` adds `MORTUCOD` at columns 172-174 (3-byte integer, IPUMS NCHS-style cause recode) and shifts `MORTUCODLD`, `MORTWT`, `MORTWTSA` downstream by 3 bytes.
- All cause-specific Schlüter results use `nhis_00003`; only the earlier all-cause κ + `MORTUCODLD` 10-category intent split (PR #3 commits a-d) used `nhis_00002`.

## Files

- `nhis_00002.dat` -- 588 MB raw fixed-width data
- `nhis_00002.do`  -- Stata read-in
- `nhis_00002.cbk` -- codebook
- `nhis_00002.R`   -- R read-in stub

## Reproducibility

The IPUMS NHIS extracts are gitignored. To recover this archive, re-submit IPUMS cart number 2 for user `jmfletcher` (see IPUMS dashboard).

## What downstream scripts to use

- **Do not** point `scripts/nhis_coresident_minors.py` at this archive; it expects the `nhis_00003` column layout (MORTUCOD at 172-174).
- The legacy parquet (`nhis_with_coresident_minors.parquet`) is regenerated from `nhis_00003.dat` in the project root.
