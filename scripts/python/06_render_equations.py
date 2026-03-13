"""
06_render_equations.py
Render LaTeX equations as PNG images for embedding in the PDF.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import FIGURES_DIR

EQ_DIR = FIGURES_DIR / "equations"
EQ_DIR.mkdir(exist_ok=True)


def render_equation(latex_str, filename, fontsize=14, dpi=200):
    """Render a LaTeX equation string to a PNG image."""
    fig, ax = plt.subplots(figsize=(0.1, 0.1))
    ax.axis("off")
    text = ax.text(0.5, 0.5, f"${latex_str}$",
                   transform=ax.transAxes,
                   fontsize=fontsize,
                   ha="center", va="center",
                   usetex=False)

    fig.savefig(EQ_DIR / filename,
                bbox_inches="tight",
                pad_inches=0.15,
                dpi=dpi,
                facecolor="white",
                edgecolor="none",
                transparent=False)
    plt.close()
    print(f"  Saved {filename}")


if __name__ == "__main__":
    print("Rendering equations as images...")

    render_equation(
        r"\ln(m_{at}) = \alpha_a + \gamma_t + \beta \cdot (\mathrm{Treated}_a \times \mathrm{Post}_t) + \varepsilon_{at}",
        "eq1_baseline_did.png",
        fontsize=16,
    )

    render_equation(
        r"\ln(m_{at}) = \alpha_a + \gamma_t + \delta \cdot (a \times t) + \beta \cdot (\mathrm{Treated}_a \times \mathrm{Post}_t) + \varepsilon_{at}",
        "eq2_age_trends.png",
        fontsize=16,
    )

    render_equation(
        r"\ln(m_{cat}) = \mu_c + \alpha_a + \gamma_t + \beta \cdot (\mathrm{Poland}_c \times \mathrm{Elderly}_a \times \mathrm{Post}_t) + \mathrm{[two\text{-}way\ interactions]} + \varepsilon_{cat}",
        "eq3_triple_diff.png",
        fontsize=15,
    )

    print("Done.")
