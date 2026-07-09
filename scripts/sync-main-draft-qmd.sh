#!/usr/bin/env bash
# Regenerate manuscript/main-draft.qmd from main.qmd (draft PDF variant).
# Run from repo root after editing main.qmd:  bash scripts/sync-main-draft-qmd.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MAIN="$ROOT/manuscript/main.qmd"
DRAFT="$ROOT/manuscript/main-draft.qmd"
cp "$MAIN" "$DRAFT"
export ROOT
python3 << 'PY'
import os
from pathlib import Path
draft = Path(os.environ["ROOT"]) / "manuscript" / "main-draft.qmd"
text = draft.read_text(encoding="utf-8")
old = """    keep-tex: false
    include-in-header:
      - file: includes/pdf-header.tex"""
new = """    keep-tex: false
    output-file: main-draft.pdf
    include-in-header:
      - file: includes/pdf-header.tex
      - file: includes/draft-banner.tex"""
if old not in text:
    raise SystemExit("sync-main-draft-qmd: expected YAML block not found; update script if main.qmd changed")
draft.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Updated", draft)
PY
echo "Done."
