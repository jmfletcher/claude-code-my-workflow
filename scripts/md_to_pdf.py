"""
Convert Paper/main.md to a PDF in Paper/main.pdf.
Includes Appendix A (tables from Paper/tables/*.csv) and Appendix B (figures from Figures/*.png).
Uses reportlab; run from project root or scripts/ with pdf_deps on path.
"""
import sys
import re
import csv
import os
from pathlib import Path

# Allow using deps installed with pip install --target ./pdf_deps
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEPS = SCRIPT_DIR / "pdf_deps"
if DEPS.exists():
    sys.path.insert(0, str(DEPS))

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image, KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def parse_front_matter(lines):
    """Return (front_matter_dict, rest_lines)."""
    if not lines or lines[0].strip() != "---":
        return {}, lines
    rest = lines[1:]
    fm = {}
    i = 0
    while i < len(rest) and rest[i].strip() != "---":
        line = rest[i]
        m = re.match(r"^(\w+):\s*[\"']?(.+?)[\"']?\s*$", line.strip())
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
        i += 1
    if i < len(rest) and rest[i].strip() == "---":
        i += 1
    return fm, rest[i:]

def md_para_to_reportlab(text):
    """Convert markdown paragraph to ReportLab-safe string. Preserves &lt; &gt; &amp;."""
    # Bold: **word** -> <b>word</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Protect existing HTML entities so we don't double-escape
    text = text.replace("&amp;", "\x00AMP\x00").replace("&lt;", "\x00LT\x00").replace("&gt;", "\x00GT\x00")
    # Escape for XML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Restore ReportLab tags (so <b> and </b> render as bold, not literal)
    text = text.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
    text = text.replace("&lt;i&gt;", "<i>").replace("&lt;/i&gt;", "</i>")
    # Restore protected entities
    text = text.replace("\x00AMP\x00", "&amp;").replace("\x00LT\x00", "&lt;").replace("\x00GT\x00", "&gt;")
    return text


def _format_number_cell(s):
    """Format a cell that may be a long float for readable table output."""
    s = str(s).strip()
    if not s or s in ("", ".", "-"):
        return s
    try:
        x = float(s)
    except ValueError:
        return s
    # Integer if whole and in reasonable range
    if abs(x) < 1e15 and x == int(x):
        return str(int(x))
    # Very small numbers: scientific (e.g. p-values, MSPE)
    if x != 0 and (abs(x) < 0.0001 or abs(x) >= 1e6):
        return f"{x:.2e}"
    # Coefficients, SEs, percents: fixed decimals, strip trailing zeros
    out = f"{x:.4f}"
    if "." in out:
        out = out.rstrip("0").rstrip(".")
    return out


def csv_to_table_data(csv_path, format_numbers=True):
    """Read a CSV file; return list of rows (each row is list of strings). Optionally format numeric cells."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            cells = [str(cell).strip() for cell in row]
            if format_numbers:
                cells = [_format_number_cell(c) for c in cells]
            rows.append(cells)
    return rows


def parse_markdown_table(block_text):
    """If block_text looks like a markdown table (| a | b |), return list of rows; else None."""
    lines = [ln.strip() for ln in block_text.strip().split("\n") if ln.strip()]
    if len(lines) < 2:
        return None
    rows = []
    for line in lines:
        if not line.startswith("|") or "|" not in line[1:]:
            return None
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if not cells:
            return None
        # Skip separator row |---|---|
        if re.match(r"^[\s\-:]+$", "".join(cells)):
            continue
        rows.append(cells)
    return rows if len(rows) >= 1 else None


def _escape_table_cell(text):
    """Escape for use inside a ReportLab Paragraph in a table cell."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def make_table_flowable(data, col_widths=None, table_width=6.5 * inch, cell_style=None):
    """Build a ReportLab Table flowable from list of rows. First row = header.
    Uses Paragraph in each cell so text wraps and does not overflow."""
    if not data:
        return None
    ncols = len(data[0])
    if col_widths is None:
        col_widths = [table_width / ncols] * ncols
    # Wrap each cell in a Paragraph so text wraps within the column
    if cell_style is None:
        from reportlab.lib.styles import getSampleStyleSheet
        _styles = getSampleStyleSheet()
        cell_style = ParagraphStyle(
            name="TableCell",
            parent=_styles["Normal"],
            fontSize=8,
            leading=10,
            alignment=1,  # CENTER
        )
    wrapped = []
    for r, row in enumerate(data):
        wrapped_row = []
        for cell in row:
            safe = _escape_table_cell(cell)
            wrapped_row.append(Paragraph(safe, cell_style))
        wrapped.append(wrapped_row)
    t = Table(wrapped, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _table_col_widths(stem, ncols, table_width):
    """Return list of column widths (in points) for a given table to avoid overflow."""
    default_w = table_width / ncols
    # Tables with long first column(s) or many narrow numeric columns
    if stem == "table4_cross_country_did" and ncols == 7:
        # Set, Spec, Sex, coef, se, pval, n
        w = table_width / 7
        return [1.0 * inch, 1.0 * inch, 0.7 * inch] + [w] * 4
    if stem == "table5_synthetic_control" and ncols == 7:
        # Config, N Donors, Pre-MSPE, Avg Gap, Avg Gap %, MSPE Ratio, P-value
        return [1.4 * inch, 0.65 * inch, 0.9 * inch, 0.9 * inch, 0.85 * inch, 0.9 * inch, 0.7 * inch]
    return [default_w] * ncols


# Short captions for tables (keyed by filename stem)
TABLE_CAPTIONS = {
    "table1_summary_statistics": "Table 1. Summary statistics: pre- and post-policy mortality (per 1,000), percent change, and average deaths and exposure by age group (Poland).",
    "table2_robustness_bandwidth": "Table 2. Within-Poland DiD robustness to age bandwidth.",
    "table3_within_poland_did": "Table 3. Within-Poland DiD and TWFE estimates by sex.",
    "table4_cross_country_did": "Table 4. Cross-country simple DiD and triple-difference by comparator set and sex.",
    "table5_synthetic_control": "Table 5. Synthetic control: average post-treatment gap, MSPE ratio, placebo p-value.",
    "tableA1_placebo_dates": "Table A1. Placebo treatment dates (pre-period only).",
    "tableA2_age_trends": "Table A2. TWFE with and without age-specific linear trends.",
    "tableA3_power_calculation": "Table A3. Power calculations by design and effect size.",
    "tableA4_cause_specific": "Table A4. Cause-specific mortality: pre/post changes for treated vs control ages.",
}

# Figure number and caption by filename stem (fig1_*, fig2_*, ...)
FIGURE_CAPTIONS = {
    "fig1_poland_mortality_by_age": "Figure 1. Poland: age-specific mortality rates, 2000–2023.",
    "fig2_treated_vs_control_ratio": "Figure 2. Poland: relative mortality of treated vs control age groups.",
    "fig3_cross_country_elderly": "Figure 3. Elderly mortality: Poland vs Visegrad countries.",
    "fig4_parallel_trends": "Figure 4. Parallel trends: Poland vs Visegrad average (normalized to 2010).",
    "fig5_cause_specific": "Figure 5. Poland: cause-specific elderly mortality (ages 75+).",
    "fig6_log_mortality_profiles": "Figure 6. Log-mortality age profiles.",
    "fig7_event_study": "Figure 7. Within-Poland event study (coefficients by year relative to policy).",
    "fig8_robustness_bandwidth": "Figure 8. Within-Poland DiD by age bandwidth.",
    "fig9_cross_country_es": "Figure 9. Cross-country event study.",
    "fig10_trends": "Figure 10. Elderly mortality: Poland vs comparators.",
    "fig11_synthetic_control": "Figure 11. Synthetic control: actual vs synthetic Poland.",
    "fig12_placebo": "Figure 12. Placebo distribution (synthetic control).",
    "figA1_placebo_dates": "Figure A1. Placebo treatment dates.",
    "figA2_cause_specific_did": "Figure A2. Cause-specific mortality: treated vs control ages.",
}

# Multi-variant sub-labels (suffix -> letter)
VARIANT_LABELS = ["a", "b", "c", "d", "e", "f", "g", "h"]


def _figure_sort_key(path):
    """Order: fig1, fig2, ... fig8 (single), then fig9_*, fig10_*, fig11_*, fig12_* by name."""
    name = path.stem.lower()
    # Extract leading figN
    for i in range(1, 13):
        prefix = f"fig{i}_"
        if name == f"fig{i}" or name.startswith(prefix):
            # fig9_cross_country_es_Visegrad -> (9, "cross_country_es_visegrad")
            suffix = name[len(prefix):] if name.startswith(prefix) else ""
            return (i, suffix)
    return (99, name)


def _make_scaled_image(path, max_width, max_height):
    """Return an Image flowable scaled to fit inside (max_width, max_height), aspect ratio preserved."""
    # kind='proportional' scales to fit within width x height without stretching
    img = Image(
        str(path),
        width=max_width,
        height=max_height,
        kind="proportional",
    )
    img.hAlign = "CENTER"
    return img

def main():
    output_subdir = os.environ.get("OUTPUT_SUBDIR", "").strip()
    if output_subdir:
        base = PROJECT_ROOT / output_subdir
        md_path = base / "Paper" / "main.md"
        pdf_path = base / "Paper" / "main.pdf"
        tables_dir = base / "Paper" / "tables"
        figures_dir = base / "Figures"
    else:
        base = PROJECT_ROOT
        md_path = base / "Paper" / "main.md"
        pdf_path = base / "Paper" / "main.pdf"
        tables_dir = base / "Paper" / "tables"
        figures_dir = base / "Figures"
    if not md_path.exists():
        print("Not found:", md_path)
        sys.exit(1)

    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    fm, rest = parse_front_matter(lines)
    title = fm.get("title", "Free Prescription Drugs and Mortality: Evidence from Poland")
    author = fm.get("author", "Jason Fletcher et al.")
    date = fm.get("date", "DRAFT")
    acknowledgement = fm.get("acknowledgement", "")

    # Rebuild body and split into blocks (## section, ### subsection, paragraphs)
    body = "\n".join(rest)
    # Normalize: \n\n\n -> \n\n
    body = re.sub(r"\n{3,}", "\n\n", body)
    blocks = []
    current = []
    for line in body.split("\n"):
        if line.strip().startswith("## "):
            if current:
                blocks.append(("\n".join(current), None))
            current = []
            blocks.append((line.strip()[3:], "h1"))
        elif line.strip().startswith("### "):
            if current:
                blocks.append(("\n".join(current), None))
            current = []
            blocks.append((line.strip()[4:], "h2"))
        else:
            current.append(line)
    if current:
        blocks.append(("\n".join(current), None))

    # ReportLab doc
    # Extra bottom margin on all pages to reserve space for the page-1 footnote
    # (on later pages the space is simply empty — a minor trade-off for simplicity)
    bottom_margin = 1.6 * inch if acknowledgement else inch
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=bottom_margin,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="PaperTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="PaperAuthor",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="H1",
        parent=styles["Heading1"],
        fontSize=14,
        spaceBefore=14,
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="H2",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Caption",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#333333"),
        spaceAfter=8,
        spaceBefore=4,
    ))
    styles.add(ParagraphStyle(
        name="Blockquote",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        leftIndent=0.4 * inch,
        rightIndent=0.3 * inch,
        textColor=colors.HexColor("#333333"),
        spaceBefore=6,
        spaceAfter=6,
        borderColor=colors.HexColor("#999999"),
        borderWidth=0,
        borderPadding=0,
    ))
    story = []

    # Title block
    story.append(Paragraph(md_para_to_reportlab(title), styles["PaperTitle"]))
    story.append(Paragraph(md_para_to_reportlab(author), styles["PaperAuthor"]))
    story.append(Paragraph(md_para_to_reportlab(date), styles["PaperAuthor"]))
    story.append(Spacer(1, 0.2 * inch))

    # Prepare acknowledgement for page-1 footnote (drawn by canvas callback)
    acknowledgement = fm.get("acknowledgement", "")
    _ack_footnote_text = ""
    if acknowledgement:
        _ack_footnote_text = re.sub(
            r'(https?://\S+)',
            r'<link href="\1"><u>\1</u></link>',
            md_para_to_reportlab(acknowledgement),
        )
        _ack_footnote_text = "&#8224; " + _ack_footnote_text

    for content, kind in blocks:
        if kind == "h1":
            story.append(Paragraph(md_para_to_reportlab(content), styles["H1"]))
        elif kind == "h2":
            story.append(Paragraph(md_para_to_reportlab(content), styles["H2"]))
        else:
            for para in content.split("\n\n"):
                para = para.strip()
                if not para:
                    continue
                # Blockquote: lines starting with >
                if para.startswith(">"):
                    bq_lines = []
                    for ln in para.split("\n"):
                        bq_lines.append(re.sub(r"^>\s?", "", ln))
                    bq_text = " ".join(bq_lines).strip()
                    story.append(Paragraph(md_para_to_reportlab(bq_text), styles["Blockquote"]))
                    story.append(Spacer(1, 4))
                    continue
                # Inline image: ![alt](path)
                img_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", para.strip())
                if img_match:
                    img_alt = img_match.group(1)
                    img_path_str = img_match.group(2)
                    # Resolve relative to Figures dir or project root
                    img_path = figures_dir / img_path_str
                    if not img_path.exists():
                        img_path = base / img_path_str
                    if not img_path.exists():
                        img_path = base / "Figures" / img_path_str
                    if img_path.exists():
                        try:
                            img = _make_scaled_image(img_path, 5.0 * inch, 1.5 * inch)
                            story.append(img)
                            story.append(Spacer(1, 6))
                        except Exception:
                            story.append(Paragraph(f"[Image: {img_alt}]", styles["Normal"]))
                    else:
                        story.append(Paragraph(f"[Image not found: {img_path_str}]", styles["Caption"]))
                    story.append(Spacer(1, 4))
                    continue
                table_rows = parse_markdown_table(para)
                if table_rows:
                    ncols = len(table_rows[0])
                    col_widths = [6.5 * inch / ncols] * ncols
                    t = make_table_flowable(table_rows, col_widths=col_widths, table_width=6.5 * inch)
                    if t:
                        story.append(t)
                        story.append(Spacer(1, 8))
                else:
                    story.append(Paragraph(md_para_to_reportlab(para), styles["Normal"]))
                    story.append(Spacer(1, 4))

    # ---------- Appendix A: Tables ----------
    table_order = [
        "table1_summary_statistics.csv",
        "table2_robustness_bandwidth.csv",
        "table3_within_poland_did.csv",
        "table4_cross_country_did.csv",
        "table5_synthetic_control.csv",
        "tableA1_placebo_dates.csv",
        "tableA2_age_trends.csv",
        "tableA3_power_calculation.csv",
        "tableA4_cause_specific.csv",
    ]
    if tables_dir.exists():
        story.append(PageBreak())
        story.append(Paragraph("Appendix A: Tables", styles["H1"]))
        story.append(Spacer(1, 0.15 * inch))
    table_width = 6.5 * inch
    table_cell_style = ParagraphStyle(
        name="TableCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        alignment=1,
    )
    for fname in table_order:
            path = tables_dir / fname
            if not path.exists():
                continue
            stem = path.stem
            caption = TABLE_CAPTIONS.get(stem, f"Table: {stem}")
            story.append(Paragraph(md_para_to_reportlab(caption), styles["Caption"]))
            try:
                data = csv_to_table_data(path)
                if data:
                    ncols = len(data[0])
                    # Per-table column widths to avoid crowding (optional overrides)
                    col_widths = _table_col_widths(stem, ncols, table_width)
                    t = make_table_flowable(data, col_widths=col_widths, cell_style=table_cell_style)
                    story.append(t)
                    story.append(Spacer(1, 0.2 * inch))
            except Exception as e:
                story.append(Paragraph(f"[Table load error: {path.name}]", styles["Normal"]))
                story.append(Spacer(1, 0.1 * inch))

    # ---------- Appendix B: Figures ----------
    # Consistent bounding box so all figures scale to fit and don't overflow or look tiny
    max_fig_width = 5.5 * inch
    max_fig_height = 4.25 * inch
    if figures_dir.exists():
        story.append(PageBreak())
        story.append(Paragraph("Appendix B: Figures", styles["H1"]))
        story.append(Spacer(1, 0.2 * inch))
        image_extensions = (".png", ".jpg", ".jpeg")
        fig_paths = []
        for ext in image_extensions:
            fig_paths.extend(figures_dir.glob(f"*{ext}"))
        # Exclude equation images (those live in equations/ subfolder)
        fig_paths = [p for p in fig_paths if "equations" not in str(p)]
        fig_paths = sorted(set(fig_paths), key=_figure_sort_key)

        # Group figures by their base caption key for a/b/c labeling
        from collections import defaultdict
        base_key_counter = defaultdict(int)
        fig_base_keys = []
        for path in fig_paths:
            stem = path.stem
            matched_key = None
            for key in sorted(FIGURE_CAPTIONS.keys(), key=len, reverse=True):
                if stem == key or stem.startswith(key + "_") or stem.startswith(key):
                    matched_key = key
                    break
            fig_base_keys.append(matched_key)
            if matched_key:
                base_key_counter[matched_key] += 1

        variant_idx = defaultdict(int)  # track which variant we're on per base key
        for i, path in enumerate(fig_paths):
            if i > 0:
                story.append(PageBreak())
            stem = path.stem
            base_key = fig_base_keys[i]

            if base_key and base_key in FIGURE_CAPTIONS:
                base_caption = FIGURE_CAPTIONS[base_key]
                if base_key_counter[base_key] > 1 and stem != base_key:
                    # Multi-variant: use a/b/c/d labels
                    idx = variant_idx[base_key]
                    variant_idx[base_key] += 1
                    subletter = VARIANT_LABELS[idx] if idx < len(VARIANT_LABELS) else str(idx + 1)
                    suffix = stem[len(base_key):].lstrip("_").replace("_", " ").replace(",", ", ").strip()
                    # Insert letter into the figure number
                    num_match = re.match(r"(Figure\s+\w+\.?)", base_caption)
                    if num_match:
                        caption = f"{num_match.group(1).rstrip('.')}{subletter}. {base_caption[num_match.end():].strip().rstrip('.')}"
                    else:
                        caption = f"{base_caption.rstrip('.')} ({subletter})"
                    if suffix:
                        caption = f"{caption} — {suffix}."
                    else:
                        caption = f"{caption}."
                elif stem == base_key:
                    caption = base_caption
                else:
                    suffix = stem[len(base_key):].lstrip("_").replace("_", " ").strip()
                    caption = f"{base_caption.rstrip('.')} ({suffix})." if suffix else base_caption
            else:
                caption = f"Figure: {stem}."

            caption_para = Paragraph(md_para_to_reportlab(caption), styles["Caption"])
            try:
                img = _make_scaled_image(path, max_fig_width, max_fig_height)
                block = KeepTogether([
                    caption_para,
                    Spacer(1, 0.08 * inch),
                    img,
                    Spacer(1, 0.2 * inch),
                ])
                story.append(block)
            except Exception as e:
                story.append(Paragraph(f"[Image not embedded: {path.name}]", styles["Normal"]))
                story.append(Spacer(1, 0.1 * inch))

    # Page callbacks: draw acknowledgement footnote at bottom of page 1
    from reportlab.platypus import Frame
    from reportlab.lib.enums import TA_LEFT

    ack_footnote_style = ParagraphStyle(
        name="FootnoteAck",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#444444"),
        alignment=TA_LEFT,
    )

    def _draw_first_page_footer(canvas, doc_obj):
        if not _ack_footnote_text:
            return
        canvas.saveState()
        page_w, page_h = letter
        left_m = inch
        right_m = inch
        usable_w = page_w - left_m - right_m
        footnote_y_top = inch - 0.1 * inch  # just above the bottom margin

        # Draw separator line
        canvas.setStrokeColor(colors.HexColor("#999999"))
        canvas.setLineWidth(0.5)
        canvas.line(left_m, footnote_y_top + 4, left_m + 2.0 * inch, footnote_y_top + 4)

        # Render footnote paragraph into a frame at the bottom
        p = Paragraph(_ack_footnote_text, ack_footnote_style)
        pw, ph = p.wrap(usable_w, 2 * inch)
        p.drawOn(canvas, left_m, footnote_y_top - ph)
        canvas.restoreState()

    def _draw_later_pages(canvas, doc_obj):
        pass

    doc.build(story, onFirstPage=_draw_first_page_footer, onLaterPages=_draw_later_pages)
    print("PDF written to:", pdf_path)

if __name__ == "__main__":
    main()
