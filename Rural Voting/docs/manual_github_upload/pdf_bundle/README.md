# Rural voting manuscript — PDF bundle (manual GitHub upload)

This folder is a **self-contained snapshot** of the rendered manuscript for uploading to GitHub without using `git push` from the command line.

## Contents

| File | Purpose |
|------|--------|
| `paper.pdf` | Journal-style PDF (Quarto → LaTeX). **Primary artifact to archive or share.** |
| `paper.html` | Same document as HTML; figures are embedded. Useful for quick review in a browser. |

## Refresh this folder from your project

From the repository root:

```bash
bash scripts/package_pdf_bundle_for_github.sh
```

That script copies the latest `docs/manuscript/paper.pdf` and `docs/manuscript/paper.html` into this directory.

## Upload to GitHub (web UI)

1. Open your repo and branch (e.g. `Rural-Counties-and-Voting`).
2. Navigate to the path where you want these files (for example `docs/manuscript/` or a folder like `docs/manual_github_upload/pdf_bundle/`).
3. **Add file → Upload files**, drag `paper.pdf` and optionally `paper.html`, commit.

**Note:** GitHub shows a **50 MB** warning per file; these files are typically a few MB each.

## Rebuilding the PDF from source

Full reproduction requires the Quarto source (`paper.qmd`), bibliography, and generated tables/figures under `output/`. If you restore `docs/manuscript/paper.qmd` in this repo, run:

```bash
quarto render docs/manuscript/paper.qmd
```

Then rerun `scripts/package_pdf_bundle_for_github.sh` to refresh this bundle.
