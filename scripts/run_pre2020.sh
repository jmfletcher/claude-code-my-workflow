#!/usr/bin/env bash
# Run full pipeline with data through 2019 (excluding COVID-19) and write to results_pre2020/
set -e
cd "$(dirname "$0")/.."
export OUTPUT_SUBDIR=results_pre2020
export END_YEAR=2019
export MPLCONFIGDIR="$PWD/.mpl_config"

echo "=== Pre-2020 pipeline (data through 2019, no COVID) ==="
python3 scripts/python/00_data_loading.py
python3 scripts/python/01_descriptive.py
python3 scripts/python/02_within_poland_did.py
python3 scripts/python/03_cross_country_did.py
python3 scripts/python/04_synthetic_control.py
echo "=== Building PDF ==="
python3 scripts/md_to_pdf.py
echo "=== Done. Outputs in $OUTPUT_SUBDIR/ ==="
