#!/usr/bin/env bash
# Copy rendered manuscript PDF/HTML into docs/manual_github_upload/pdf_bundle/ for manual GitHub upload.
# Usage: from repo root — bash scripts/package_pdf_bundle_for_github.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/docs/manuscript"
DST="$ROOT/docs/manual_github_upload/pdf_bundle"

mkdir -p "$DST"
for f in paper.pdf paper.html; do
  if [[ ! -f "$SRC/$f" ]]; then
    echo "Missing: $SRC/$f — render the manuscript first (e.g. quarto render docs/manuscript/paper.qmd)." >&2
    exit 1
  fi
  cp -f "$SRC/$f" "$DST/"
  echo "Copied $f -> $DST/"
done
echo "Done. Upload contents of: $DST"
