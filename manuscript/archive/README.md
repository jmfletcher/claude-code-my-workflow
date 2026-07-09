# Manuscript PDF archive

Timestamped copies of `manuscript/main.pdf` live here before replacing the working PDF with a fresh Quarto render.

**When to archive**

- Before any substantive edit to `main.qmd` when you may want to compare outputs.
- After completing a milestone (e.g., before sending a draft to a coauthor).
- On a **regular cadence** (e.g., weekly or at end of each work session that changes the manuscript), so you retain a trail of compiled versions without relying on git for large binaries.

**How to archive and rebuild**

From the repo root:

```bash
STAMP=$(date +%Y-%m-%d_%H%M)
cp manuscript/main.pdf "manuscript/archive/main_${STAMP}.pdf"
quarto render manuscript/main.qmd --to pdf
```

If the Python engine is unavailable in your environment, use `quarto render manuscript/main.qmd --to pdf --no-execute` only when code chunks are unchanged and outputs are already current.

**Retention**

Delete old snapshots as needed; they are not intended for git (add `manuscript/archive/*.pdf` to `.gitignore` if you track the folder but not binaries).
