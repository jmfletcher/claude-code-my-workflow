#!/usr/bin/env bash
# Render a markdown report to PDF via pandoc -> HTML -> headless Chrome.
#
# Usage:
#   scripts/render_report_pdf.sh <input.md> [output.pdf]
#
# Defaults to quality_reports/report_nhis_calibrated_orphanhood.md ->
# quality_reports/pdf/report.pdf.
#
# Requirements:
#   - pandoc       (`brew install pandoc`)
#   - Google Chrome installed in /Applications/Google Chrome.app
#
# No LaTeX dependency. Output PDF retains tables, blockquotes, code blocks,
# and the project style (see quality_reports/pdf/style.css).

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$PROJECT_ROOT"

INPUT="${1:-quality_reports/report_nhis_calibrated_orphanhood.md}"
OUTPUT="${2:-quality_reports/pdf/$(basename "$INPUT" .md).pdf}"

mkdir -p "$(dirname "$OUTPUT")"
HTML_TMP="${OUTPUT%.pdf}.html"
CSS="quality_reports/pdf/style.css"

if [[ ! -f "$CSS" ]]; then
  echo "[render_report_pdf] missing $CSS" >&2; exit 1
fi
if [[ ! -f "$INPUT" ]]; then
  echo "[render_report_pdf] missing $INPUT" >&2; exit 1
fi

TITLE="$(head -1 "$INPUT" | sed 's/^# *//' | sed 's/ *$//')"

echo "[render_report_pdf] $INPUT -> $OUTPUT"

pandoc "$INPUT" \
  --from gfm+pipe_tables+smart \
  --to html5 \
  --standalone \
  --metadata title="$TITLE" \
  --css "$CSS" \
  --embed-resources \
  -o "$HTML_TMP"

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [[ ! -x "$CHROME" ]]; then
  echo "[render_report_pdf] Chrome not found at $CHROME" >&2; exit 1
fi

"$CHROME" \
  --headless=new \
  --disable-gpu \
  --no-sandbox \
  --no-pdf-header-footer \
  --print-to-pdf="$OUTPUT" \
  --print-to-pdf-no-header \
  "file://$PROJECT_ROOT/$HTML_TMP" 2>&1 | tail -1

if [[ -f "$OUTPUT" ]]; then
  SIZE=$(stat -f "%z" "$OUTPUT")
  PAGES=$(file "$OUTPUT" | sed -E 's/.*, ([0-9]+) pages?.*/\1/')
  printf "[render_report_pdf] wrote %s (%d bytes, %s pages)\n" \
         "$OUTPUT" "$SIZE" "$PAGES"
fi
