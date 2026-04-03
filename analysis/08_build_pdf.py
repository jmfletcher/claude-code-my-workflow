"""
08_build_pdf.py
===============
Build a self-contained print HTML (main_print.html) and PDF (main.pdf)
from main.html by:
  1. Embedding all figure PNGs as base64 data URIs
  2. Inlining jQuery
  3. Pre-rendering all LaTeX math to styled HTML (no MathJax dependency)
  4. Injecting print CSS for professional A4 layout
  5. Running Chrome headless to produce main.pdf
"""

from __future__ import annotations
import base64, re, ssl, subprocess, urllib.request
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
FIGURES    = ROOT / "output" / "figures"

# ── Math rendering table ──────────────────────────────────────────────────────

def _i(x):   return f'<i>{x}</i>'
def _sub(x): return f'<sub>{x}</sub>'

# β̂ using CSS superscript (avoids combining diacritics that break PDF fonts)
BHAT = '<i>β</i><sup style="font-size:0.65em;line-height:0;vertical-align:0.5em">^</sup>'
# Use plain ASCII minus to avoid U+2212 not found in PDF fonts
def _bhat(val: str) -> str:
    return f'{BHAT} = {val}'

MATH_INLINE = {
    # Greek
    r"\delta_y":   "δ" + _sub("y"),
    r"\eta_w":     "η" + _sub("w"),
    r"\gamma_a":   "γ" + _sub("a"),
    # beta-hat variants
    r"\hat\beta = -0.021":   _bhat("-0.021"),
    r"\hat\beta = 0.016":    _bhat("0.016"),
    r"\hat\beta = 0.020":    _bhat("0.020"),
    r"\hat\beta = 0.025":    _bhat("0.025"),
    r"\hat\beta = 0.056":    _bhat("0.056"),
    r"\hat\beta = 0.061":    _bhat("0.061"),
    r"\hat\beta = 0.068":    _bhat("0.068"),
    r"\hat\beta = 0.088":    _bhat("0.088"),
    r"\hat\beta = 0.101":    _bhat("0.101"),
    r"\hat{\beta} = -0.021": _bhat("-0.021"),
    r"\hat{\beta} = 0.061":  _bhat("0.061"),
    r"\hat{\beta} = 0.075":  _bhat("0.075"),
    r"\hat{\beta} = 0.130":  _bhat("0.130"),
    # p-values
    r"p &gt; 0.17":  _i("p") + " &gt; 0.17",
    r"p &lt; 0.05":  _i("p") + " &lt; 0.05",
    r"p = 0.001":    _i("p") + " = 0.001",
    r"p = 0.015":    _i("p") + " = 0.015",
    r"p = 0.024":    _i("p") + " = 0.024",
    r"p = 0.025":    _i("p") + " = 0.025",
    r"p = 0.035":    _i("p") + " = 0.035",
    r"p = 0.036":    _i("p") + " = 0.036",
    r"p = 0.047":    _i("p") + " = 0.047",
    r"p = 0.051":    _i("p") + " = 0.051",
    r"p = 0.36":     _i("p") + " = 0.36",
    r"p \geq 0.05":  _i("p") + " &ge; 0.05",
    # variables
    r"\text{rate}_{b,y,a}": "rate" + _sub("b,y,a"),
    r"\text{treated}_{b,y}": "treated" + _sub("b,y"),
    r"\text{rate}_{b,t} = (\text{deaths}_{b,t} / N_b) \times 1{,}000":
        "rate" + _sub("b,t") + " = (deaths" + _sub("b,t") + " / " +
        _i("N") + _sub("b") + ") &times; 1,000",
    r"N_b \approx 15{,}334": _i("N") + _sub("b") + " &asymp; 15,334",
    r"N_b":                   _i("N") + _sub("b"),
    r"N = 5{,}913":           _i("N") + " = 5,913",
    r"a":  _i("a"),
    r"b":  _i("b"),
    r"y":  _i("y"),
}

DISPLAY_MATH_SRC = (
    r"\[\text{rate}_{b,y,a} = \alpha + \beta \cdot \text{treated}_{b,y}"
    r"  + \gamma_a + \delta_y + \eta_w + \varepsilon_{b,y,a}\]"
)
DISPLAY_MATH_HTML = (
    '<div style="text-align:center; margin:1em 0; font-size:1.05em; font-style:italic">'
    "rate<sub style='font-style:normal'>b,y,a</sub>"
    " = &alpha; + &beta; &middot; treated<sub style='font-style:normal'>b,y</sub>"
    " + &gamma;<sub style='font-style:normal'>a</sub>"
    " + &delta;<sub style='font-style:normal'>y</sub>"
    " + &eta;<sub style='font-style:normal'>w</sub>"
    " + &epsilon;<sub style='font-style:normal'>b,y,a</sub>"
    "</div>"
)


def prerender_math(html: str) -> str:
    def _render_inner(inner: str) -> str:
        """Translate a captured LaTeX inner string to HTML."""
        # Longest-key-first to avoid partial matches
        for latex, rendered in sorted(MATH_INLINE.items(), key=lambda x: -len(x[0])):
            if inner == latex:
                return rendered
        # Fallback: strip backslashes / braces
        fallback = re.sub(r"[\\{}]", "", inner)
        fallback = fallback.replace("text", "").replace("hat", "")
        return fallback

    # Inline math: <span class="math inline">\(...\)</span>
    def _replace_inline_span(m: re.Match) -> str:
        inner = m.group(1)
        return f'<span class="math-rendered">{_render_inner(inner)}</span>'

    html = re.sub(
        r'<span class="math inline">\\?\((.+?)\\?\)</span>',
        _replace_inline_span,
        html,
        flags=re.DOTALL
    )

    # Also handle bare \(...\) not wrapped in a span (raw LaTeX in paragraph text)
    def _replace_bare_inline(m: re.Match) -> str:
        inner = m.group(1)
        return f'<span class="math-rendered">{_render_inner(inner)}</span>'

    # NOTE: no re.DOTALL here — bare \(...\) in HTML text is always on one line;
    # using DOTALL would cause \( inside inlined jQuery to eat the print CSS block.
    html = re.sub(
        r'\\\((.+?)\\\)',
        _replace_bare_inline,
        html,
    )

    # Display math
    html = re.sub(
        r'<span class="math display">.*?</span>',
        DISPLAY_MATH_HTML,
        html,
        flags=re.DOTALL,
    )

    # Remove the MathJax script tags (they're large and no longer needed)
    html = re.sub(
        r'<script[^>]*type="text/javascript"[^>]*>.*?</script>',
        "",
        html,
        flags=re.DOTALL,
    )
    # Remove MathJax config script
    html = re.sub(
        r'<script>\s*window\.MathJax.*?</script>',
        "",
        html,
        flags=re.DOTALL,
    )

    return html


# ── Print CSS ─────────────────────────────────────────────────────────────────

PRINT_CSS = """
<style media="print">
@page {
  size: A4;
  margin: 25mm 20mm 25mm 20mm;
}
body {
  font-family: "Times New Roman", serif !important;
  font-size: 11pt !important;
  line-height: 1.5 !important;
  color: #000 !important;
}
#quarto-sidebar, .sidebar, #TOC, nav.quarto-secondary-nav,
.quarto-sidebar-toggle, #quarto-margin-sidebar,
.quarto-banner, .quarto-title-meta, .quarto-title-block > .quarto-title-meta,
header#title-block-header .quarto-title-meta, #quarto-document-content > .page-columns > div:first-child,
.nav-footer, .quarto-secondary-nav, .fixed-top { display: none !important; }
.page-columns { display: block !important; }
.page-columns .page-full { max-width: 100% !important; width: 100% !important; }
main.content { max-width: 100% !important; width: 100% !important;
               margin: 0 !important; padding: 0 !important; }
#quarto-content { max-width: 100% !important; }
figure img { max-width: 100% !important; height: auto !important;
             page-break-inside: avoid; }
figure { page-break-inside: avoid; margin: 1em auto; text-align: center; }
table { font-size: 9.5pt !important; page-break-inside: avoid; }
h1, h2, h3 { page-break-after: avoid; }
p { orphans: 3; widows: 3; }
a { color: #000 !important; text-decoration: none !important; }
.math-rendered { font-style: italic; }
</style>
<style media="screen,print">
.math-rendered sub, .math-rendered sup { font-size: 0.75em; }
</style>
"""


# ── Main builder ─────────────────────────────────────────────────────────────

def build(src: Path, out_html: Path, out_pdf: Path) -> None:
    with open(src, encoding="utf-8") as f:
        html = f.read()

    # 1. Embed figures as base64
    def embed_image(m: re.Match) -> str:
        rel = m.group(1)
        img_path = (src.parent / rel).resolve()
        if img_path.exists():
            data = base64.b64encode(img_path.read_bytes()).decode()
            ext  = img_path.suffix.lstrip(".").replace("jpg", "jpeg")
            return f'src="data:image/{ext};base64,{data}"'
        print(f"  WARNING: image not found: {img_path}")
        return m.group(0)

    html = re.sub(r'src="(\.\./output/figures/[^"]+)"', embed_image, html)
    n_figs = len(re.findall(r'src="data:image/', html))
    print(f"  Embedded {n_figs} figures")

    # 2. Inline jQuery (small)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(
            "https://cdn.jsdelivr.net/npm/jquery@3.5.1/dist/jquery.min.js",
            timeout=20, context=ctx
        ) as r:
            jquery = r.read().decode("utf-8")
        jquery_tag = f"<script>{jquery}</script>"
        html = re.sub(
            r'<script[^>]*jquery[^>]*></script>',
            lambda _: jquery_tag,
            html,
            flags=re.IGNORECASE
        )
        print(f"  Inlined jQuery ({len(jquery)//1024} KB)")
    except Exception as e:
        print(f"  jQuery inline failed: {e}")

    # 3. Remove remaining CDN scripts (polyfill, requirejs, mathjax)
    html = re.sub(r'<script[^>]*cdnjs\.cloudflare\.com[^>]*></script>\s*', "", html)
    html = re.sub(r'<script[^>]*cdn\.jsdelivr\.net/npm/requirejs[^>]*></script>\s*', "", html)
    html = re.sub(r'<script[^>]*cdn\.jsdelivr\.net/npm/mathjax[^>]*></script>\s*', "", html)
    html = re.sub(r'<script type="application/javascript">define\(\'jquery.*?</script>\s*', "", html)

    # 4. Pre-render math
    html = prerender_math(html)
    print("  Math pre-rendered")

    # 5. Inject print CSS just before </head>
    html = html.replace("</head>", PRINT_CSS + "\n</head>", 1)

    # Write self-contained HTML
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    size_kb = out_html.stat().st_size // 1024
    print(f"  Saved {out_html.name} ({size_kb} KB)")

    # 6. Render PDF with Chrome headless
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    result = subprocess.run(
        [
            chrome,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=15000",
            f"--print-to-pdf={out_pdf}",
            "--no-pdf-header-footer",
            "--print-to-pdf-no-header",
            f"file://{out_html}",
        ],
        capture_output=True, text=True
    )
    if out_pdf.exists():
        pdf_kb = out_pdf.stat().st_size // 1024
        print(f"  Generated {out_pdf.name} ({pdf_kb} KB)")
    else:
        print(f"  ERROR: PDF not created. stderr: {result.stderr[:300]}")


if __name__ == "__main__":
    print("Building self-contained PDF...")
    build(
        src      = MANUSCRIPT / "main.html",
        out_html = MANUSCRIPT / "main_print.html",
        out_pdf  = MANUSCRIPT / "main.pdf",
    )
    print("Done.")
