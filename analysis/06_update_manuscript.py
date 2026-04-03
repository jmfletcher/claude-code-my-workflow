"""
06_update_manuscript.py
=======================
Surgically patch manuscript/main.html with corrected results.

Changes driven by the week_in_year bug fix (chronological position 5, not 8):
  1. Position text: "position 8 of 9" → "position 5 of 9"
  2. Asymmetry description → symmetry
  3. Table 1 (sample characteristics): BCS70 Age 0-9 rates corrected
  4. Table 5 (robustness): R1/R2 specs redefined (symmetric windows)
  5. Life table: corrected excess deaths and LE reduction
  6. Abstract and conclusion: robustness narrative updated
  7. HMD comparison table: minor differences
"""

from __future__ import annotations
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

HTML_PATH = Path(__file__).resolve().parents[1] / "manuscript" / "main.html"


def replace_exact(html: str, old: str, new: str, count: int = 1) -> str:
    found = html.count(old)
    if found == 0:
        print(f"  WARNING: pattern not found:\n    {old!r}")
        return html
    result = html.replace(old, new, count)
    print(f"  Replaced {min(found,count)} occurrence(s): {old[:60]!r}")
    return result


def patch_html(html: str) -> str:
    print("Applying patches…")

    # ── 1. Position in cluster ─────────────────────────────────────────────────
    html = replace_exact(
        html,
        "The treated birth week sits at position 8 of 9 (seven control positions precede it, one follows), creating an asymmetric comparison group; robustness checks in Section 5.5 examine sensitivity to this choice.",
        "The treated birth week sits at position 5 of 9 (four control positions precede it, four follow), creating a symmetric comparison group; robustness checks in Section 5.5 examine sensitivity to control-window width.",
    )

    # ── 2. Abstract: robustness sensitivity claim ──────────────────────────────
    html = replace_exact(
        html,
        "but this result is sensitive to the choice of control window width: restricting to the four nearest control weeks renders the estimate statistically insignificant.",
        "and this result is robust to the choice of control window width: restricting to the three nearest control weeks on each side leaves the estimate statistically significant.",
    )

    # ── 3. Table 1 rows — BCS70 Age 0-9 ──────────────────────────────────────
    # Original: 1.470 (3.795) for control; 2.178 (5.080) for treated
    html = replace_exact(
        html,
        "1.470 (3.795)</td>\n<td style=\"text-align: right;\">413</td>\n<td style=\"text-align: right;\">2.178 (5.080)</td>",
        "0.455 (0.396)</td>\n<td style=\"text-align: right;\">413</td>\n<td style=\"text-align: right;\">0.525 (0.540)</td>",
    )

    # ── 4. Table 5 — Robustness specification labels and values ───────────────
    # R1: old label and values
    html = replace_exact(
        html,
        "<td style=\"text-align: left;\">R1: Narrow window (weeks 5–9)</td>\n<td style=\"text-align: right;\">0.039</td>\n<td style=\"text-align: left;\">(0.024)</td>\n<td style=\"text-align: right;\">0.105</td>\n<td style=\"text-align: right;\">3,270</td>",
        "<td style=\"text-align: left;\">R1: Symmetric narrow (weeks 2–8)</td>\n<td style=\"text-align: right;\">0.068</td>\n<td style=\"text-align: left;\">(0.031)</td>\n<td style=\"text-align: right;\">0.025</td>\n<td style=\"text-align: right;\">4,599</td>",
    )
    # R2: old label and values
    html = replace_exact(
        html,
        "<td style=\"text-align: left;\">R2: Narrow window (weeks 6–9)</td>\n<td style=\"text-align: right;\">0.024</td>\n<td style=\"text-align: left;\">(0.027)</td>\n<td style=\"text-align: right;\">0.383</td>\n<td style=\"text-align: right;\">2,616</td>",
        "<td style=\"text-align: left;\">R2: Tightest symmetric (weeks 3–7)</td>\n<td style=\"text-align: right;\">0.088</td>\n<td style=\"text-align: left;\">(0.036)</td>\n<td style=\"text-align: right;\">0.015</td>\n<td style=\"text-align: right;\">3,285</td>",
    )
    # Baseline N: 5,886 → 5,913
    html = replace_exact(
        html,
        "5,886</td>",
        "5,913</td>",
        count=10,  # may appear multiple times
    )
    # R3: Log outcome coefficient → 0.056 (p=0.035) was in original, now 0.025 (p=0.182)
    html = replace_exact(
        html,
        "<td style=\"text-align: left;\">R3: Log outcome (log rate)</td>\n<td style=\"text-align: right;\">0.056</td>\n<td style=\"text-align: left;\">(0.026)</td>\n<td style=\"text-align: right;\">0.035</td>",
        "<td style=\"text-align: left;\">R3: Log outcome (log rate)</td>\n<td style=\"text-align: right;\">0.025</td>\n<td style=\"text-align: left;\">(0.019)</td>\n<td style=\"text-align: right;\">0.182</td>",
    )

    # ── 5. Life table section ──────────────────────────────────────────────────
    html = replace_exact(
        html,
        "the estimates imply 7.7 excess deaths per 1,000 birth-cohort members in the treated week relative to the control weeks.",
        "the estimates imply 6.6 excess deaths per 1,000 birth-cohort members in the treated week relative to the control weeks.",
    )
    html = replace_exact(
        html,
        "The corresponding reduction in life expectancy at birth is approximately 3.4 months (0.28 years), and at age 10 it is 2.7 months.",
        "The corresponding reduction in life expectancy at birth is approximately 1.4 months (0.11 years), and at age 10 it is 1.1 months.",
    )
    html = replace_exact(
        html,
        "the implied reduction rises to 4.1 months.",
        "the implied reduction rises to approximately 1.8 months.",
    )
    html = replace_exact(
        html,
        "ages 60–69, which account for roughly 4.97 of the 7.73 excess deaths per 1,000",
        "ages 60–69, which account for roughly 4.03 of the 6.58 excess deaths per 1,000",
    )

    # ── 6. Robustness narrative ────────────────────────────────────────────────
    html = replace_exact(
        html,
        "Control window width (R1–R2). Using only weeks 5–9 (four control weeks, three preceding and one following the treated week) reduces the estimate to \\(\\hat\\beta = 0.039\\) ( \\(p = 0.105\\) ), no longer statistically significant. Restricting further to weeks 6–9 (three control weeks) gives \\(\\hat\\beta = 0.024\\) ( \\(p = 0.38\\) ). The monotonic attenuation as the window narrows suggests that the full-window baseline estimate is partly driven by systematic differences between the treated week and more distant control weeks, rather than by panel conditioning alone. The most distant weeks in the cluster are matched to births roughly seven to eight weeks earlier in the calendar year and may face systematically different seasonal mortality risks.",
        "Control window width (R1–R2). Because the treated week sits at position 5 of 9, the baseline comparison is already symmetric (four control weeks on each side). Narrowing to a symmetric window of three control weeks on each side (weeks 2–8, R1) increases the estimate to \\(\\hat\\beta = 0.068\\) ( \\(p = 0.025\\) ). Restricting further to a two-control-week-each-side window (weeks 3–7, R2) gives \\(\\hat\\beta = 0.088\\) ( \\(p = 0.015\\) ). The estimate does not attenuate as the window narrows; if anything, it strengthens, suggesting the baseline estimate is conservative and that distant control weeks slightly dilute rather than contaminate the comparison.",
    )

    # ── 7. Conclusion: robustness claim ───────────────────────────────────────
    html = replace_exact(
        html,
        "Second, restricting the comparison to the four nearest control weeks halves the estimate and renders it statistically insignificant; restricting to three nearest controls produces a near-zero estimate. This attenuation implies that the treated birth week differs from distant control weeks for reasons unrelated to survey participation — likely seasonal or cohort-composition effects that are not absorbed by the fixed effects.",
        "Second, restricting the comparison to symmetric narrow windows does not attenuate the estimate; the coefficient increases slightly as the comparison is confined to the weeks closest in calendar time to the treated week (R1: \\(\\hat\\beta = 0.068\\), R2: \\(\\hat\\beta = 0.088\\), both \\(p < 0.03\\)). This robustness to window narrowing is consistent with the symmetric design (four control weeks on each side) providing a clean comparison.",
    )
    html = replace_exact(
        html,
        "Together, these findings suggest that the positive pooled result reflects systematic differences in the composition of the comparison group rather than a genuine panel conditioning effect on mortality.",
        "Together, the positive pooled estimate and its robustness to window narrowing suggest that the treated birth weeks do show modestly elevated mortality relative to adjacent weeks — though causal attribution to panel conditioning remains uncertain.",
    )

    # ── 8. HMD Appendix table — BCS70 Age 0-9 ────────────────────────────────
    html = replace_exact(
        html,
        "1.470 (3.795)</td>\n<td style=\"text-align: right;\">1.542 (4.208)</td>\n<td style=\"text-align: right;\">0.95</td>",
        "0.455 (0.396)</td>\n<td style=\"text-align: right;\">1.542 (4.208)</td>\n<td style=\"text-align: right;\">0.30</td>",
    )

    # ── 9. Publication date ───────────────────────────────────────────────────
    html = replace_exact(
        html,
        'content="2026-04-02"',
        'content="2026-04-02"',  # keep as-is
    )

    return html


def main() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    original_len = len(html)

    html_new = patch_html(html)

    out_path = HTML_PATH  # overwrite in place
    out_path.write_text(html_new, encoding="utf-8")
    print(f"\nManuscript updated: {out_path}")
    print(f"  Original length: {original_len:,} chars")
    print(f"  New length:      {len(html_new):,} chars")


if __name__ == "__main__":
    main()
