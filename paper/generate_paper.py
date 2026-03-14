"""
Generate a publication-ready PDF paper for the Wisconsin Mortality Project.

Uses fpdf2 to produce a formatted academic paper with embedded figures
and tables, since no LaTeX distribution is available on this machine.
"""

from fpdf import FPDF
from pathlib import Path
import csv
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "Figures"
TABLE_DIR = ROOT / "output" / "tables"
OUT_PDF = ROOT / "paper" / "wisconsin_mortality_paper.pdf"


def ascii_safe(text):
    """Replace Unicode characters with ASCII equivalents for core PDF fonts."""
    return (text
            .replace("\u2013", "--")
            .replace("\u2014", " -- ")
            .replace("\u0394", "Delta ")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2018", "'")
            .replace("\u2019", "'")
            .replace("\u2212", "-")
            .replace("\u2026", "..."))


class Paper(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="letter")
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 5, "Fletcher -- Wisconsin Black-White Life Expectancy Gaps",
                      align="L")
            self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_heading(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(0, 0, 0)
        self.ln(4)
        self.cell(0, 8, ascii_safe(title), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def subsection_heading(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(40, 40, 40)
        self.ln(2)
        self.cell(0, 7, ascii_safe(title), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5, ascii_safe(text.strip()))
        self.ln(2)

    def add_figure(self, img_path, caption, width=160):
        if not Path(img_path).exists():
            self.body_text(f"[Figure not found: {img_path}]")
            return
        x = (self.w - width) / 2
        self.image(str(img_path), x=x, w=width)
        self.ln(2)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 4.5, ascii_safe(caption))
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def add_table(self, headers, rows, col_widths=None, caption=None,
                  font_size=9):
        if caption:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(60, 60, 60)
            self.multi_cell(0, 4.5, ascii_safe(caption))
            self.set_text_color(0, 0, 0)
            self.ln(2)
        if col_widths is None:
            usable = self.w - self.l_margin - self.r_margin
            col_widths = [usable / len(headers)] * len(headers)
        self.set_font("Helvetica", "B", font_size)
        self.set_fill_color(230, 230, 230)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, ascii_safe(h), border=1, fill=True,
                      align="C")
        self.ln()
        self.set_font("Helvetica", "", font_size)
        for row in rows:
            for i, val in enumerate(row):
                align = "L" if i == 0 else "C"
                self.cell(col_widths[i], 5.5, ascii_safe(str(val)), border=1,
                          align=align)
            self.ln()
        self.ln(4)


def load_csv(path):
    with open(path) as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)
    return headers, rows


def fmt(val, decimals=2):
    try:
        return f"{float(val):.{decimals}f}"
    except (ValueError, TypeError):
        return str(val)


# Load bootstrap CIs if available (from analysis.py Phase 2B)
gap_ci_df = None
le_ci_df = None
if (TABLE_DIR / "gap_ci.csv").exists():
    with open(TABLE_DIR / "gap_ci.csv") as f:
        gap_ci_df = pd.read_csv(f)
if (TABLE_DIR / "le_with_ci.csv").exists():
    with open(TABLE_DIR / "le_with_ci.csv") as f:
        le_ci_df = pd.read_csv(f)
change_ci_df = None
if (TABLE_DIR / "change_ci.csv").exists():
    with open(TABLE_DIR / "change_ci.csv") as f:
        change_ci_df = pd.read_csv(f)

def fmt_gap_ci(center_year, geography, sex, point_est):
    """Format gap as 'X.X (95% CI lo–hi)' when CIs available. sex is 'Male' or 'Female'."""
    if gap_ci_df is None:
        return fmt(point_est)
    row = gap_ci_df[(gap_ci_df["center_year"] == center_year) &
                    (gap_ci_df["geography"] == geography) &
                    (gap_ci_df["sex_label"] == sex)]
    if len(row) == 0:
        return fmt(point_est)
    r = row.iloc[0]
    return f"{float(point_est):.1f} (95% CI {float(r['gap_lo']):.1f}–{float(r['gap_hi']):.1f})"

def fmt_le_ci(center_year, geography, race_label, sex_label, point_est):
    """Format e0 with 95% CI when available."""
    if le_ci_df is None:
        return fmt(point_est)
    row = le_ci_df[(le_ci_df["center_year"] == center_year) &
                   (le_ci_df["geography"] == geography) &
                   (le_ci_df["race_label"] == race_label) &
                   (le_ci_df["sex_label"] == sex_label)]
    if len(row) == 0:
        return fmt(point_est)
    r = row.iloc[0]
    return f"{float(r['e0_lo']):.1f}–{float(r['e0_hi']):.1f}"


# ======================================================================
# BUILD THE PAPER
# ======================================================================
pdf = Paper()
pdf.set_margins(25, 20, 25)

# ------------------------------------------------------------------
# TITLE PAGE
# ------------------------------------------------------------------
pdf.add_page()
pdf.ln(30)
pdf.set_font("Helvetica", "B", 20)
pdf.multi_cell(0, 10,
    "Geographic Variation in the Black-White\n"
    "Life Expectancy Gap in Wisconsin,\n"
    "2005-2017",
    align="C")
pdf.ln(8)

pdf.set_font("Helvetica", "", 12)
pdf.cell(0, 7, "Jason Fletcher", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "I", 11)
pdf.cell(0, 7, "University of Wisconsin-Madison", align="C",
         new_x="LMARGIN", new_y="NEXT")
pdf.ln(6)
pdf.set_font("Helvetica", "", 10)
pdf.cell(0, 6, "Working Paper -- March 2026", align="C",
         new_x="LMARGIN", new_y="NEXT")
pdf.ln(15)

# ---- Abstract ----
pdf.set_font("Helvetica", "B", 11)
pdf.cell(0, 7, "Abstract", new_x="LMARGIN", new_y="NEXT")
pdf.ln(1)
pdf.set_font("Helvetica", "", 10)
pdf.multi_cell(0, 5, ascii_safe(
    "Racial disparities in life expectancy persist across the United States, "
    "but state-level averages can mask important geographic heterogeneity. "
    "This paper examines the Black-White life expectancy gap in Wisconsin "
    "from 2005 to 2017, disaggregating the state into Milwaukee County, "
    "Dane County (Madison), and the rest of the state. Because Milwaukee "
    "is home to about two-thirds of Wisconsin's Black population and "
    "exhibits very poor Black mortality outcomes, statewide statistics are "
    "heavily influenced by conditions in a single county. I construct "
    "abridged life tables by race, sex, geography, and period, validate "
    "statewide estimates against prior work, and apply a formal "
    "decomposition that expresses the statewide gap as the sum of "
    "geography-specific contributions (population share times local gap), "
    "along with a composition term and residual. For males in 2015\u20132017, "
    "Milwaukee accounts for about 70 percent of the 7.9-year statewide gap, "
    "and the geographic concentration of Black Wisconsinites in Milwaukee "
    "adds roughly 2.6 years to the gap relative to a scenario in which "
    "Black and White residents share the same distribution across regions. "
    "Counterfactual exercises show that if Black Milwaukeeans had the same "
    "age-specific mortality as Black residents in the rest of Wisconsin, "
    "the statewide male gap would fall from 7.9 to about 4.2 years. In Dane "
    "County, a large male gap (8.5 years) reflects both exceptionally high "
    "White life expectancy and evidence of worsening Black male mortality, "
    "although the latter is estimated with substantial uncertainty because "
    "of the small Black population. Bootstrap confidence intervals quantify "
    "this uncertainty and highlight that the strongest and most precisely "
    "estimated contribution to the statewide gap arises from Milwaukee's "
    "combination of concentrated Black population and severe local "
    "mortality disadvantage."
))
pdf.ln(3)
pdf.set_font("Helvetica", "B", 9)
pdf.cell(20, 5, "Keywords: ")
pdf.set_font("Helvetica", "", 9)
pdf.cell(0, 5, "life expectancy, racial disparities, Wisconsin, "
         "geographic variation, counterfactual analysis",
         new_x="LMARGIN", new_y="NEXT")

# Acknowledgment footnote on title page (kept compact so it fits on page 1)
pdf.ln(3)
pdf.set_font("Helvetica", "I", 7)
pdf.multi_cell(
    0,
    3.5,
    ascii_safe(
        "Acknowledgments: I thank Grace Stallworth for project assistance and "
        "the Herb Kohl Public Service Research Competition for funding. This "
        "report used Claude/Cursor for assistance with data management, "
        "analysis, and summaries. I am responsible for any errors."
    ),
)


# ------------------------------------------------------------------
# 1. INTRODUCTION
# ------------------------------------------------------------------
pdf.add_page()
pdf.section_heading("1. Introduction")

pdf.body_text(
    "The Black-White gap in life expectancy is one of the most persistent "
    "health disparities in the United States. Although this gap has narrowed "
    "nationally over recent decades, substantial variation remains across "
    "states and localities (Harper et al. 2014; Riddell et al. 2018). "
    "State-level analyses, while informative, can obscure important "
    "within-state heterogeneity driven by residential segregation, "
    "differential access to health care, economic inequality, and other "
    "social determinants of health."
)

pdf.body_text(
    "Wisconsin is a particularly instructive case. The state consistently "
    "ranks among the worst for Black-White disparities across a range of "
    "social and economic indicators. The Milwaukee metropolitan area has "
    "been repeatedly identified as one of the most racially segregated in "
    "the nation. Roberts et al. (2019) documented a persistent statewide "
    "Black-White life expectancy gap in Wisconsin that showed little "
    "improvement between 1999 and 2016, in contrast to national trends of "
    "convergence. Critically, however, their analysis was conducted at "
    "the state level."
)

pdf.body_text(
    "A state-level analysis of Wisconsin is misleading for a specific, "
    "quantifiable reason: Milwaukee County alone contains about two-thirds "
    "of the state's Black population (67 percent; see Appendix C). Wisconsin is not unique in this "
    "respect: in many states, a single county holds the largest share of "
    "the state's Black population (see Appendix C). If mortality conditions for Black "
    "residents of Milwaukee are substantially worse than elsewhere in the "
    "state\u2014as one might expect given the city's concentrated poverty and "
    "extreme segregation\u2014then the statewide Black life expectancy is "
    "overwhelmingly a Milwaukee statistic. The \"Wisconsin gap\" is, "
    "to a considerable extent, the Milwaukee gap. Conversely, Dane County "
    "(Madison) has experienced rapid growth in its Black population and is "
    "often seen as a high-opportunity community, yet casual observation "
    "of aggregate statistics may overstate racial equity there."
)

pdf.body_text(
    "This paper makes three contributions. First, I disaggregate "
    "Wisconsin's Black-White life expectancy gap into three regions\u2014"
    "Milwaukee County, Dane County, and the rest of the state\u2014revealing "
    "striking geographic variation. Second, I show that the statewide "
    "gap is dominated by the combination of very poor Black mortality "
    "conditions in Milwaukee and the fact that about two-thirds of "
    "Wisconsin's Black population lives there, yielding a substantial "
    "composition penalty. Third, I use counterfactual mortality-replacement "
    "exercises to quantify how much of the statewide gap would remain "
    "if Milwaukee's Black mortality matched that of Black residents in "
    "the rest of the state or if Dane County's White mortality matched "
    "that of Whites elsewhere. The analytic approach is validated against "
    "the published results of Roberts et al. (2019); this replication is "
    "reported in the appendix."
)


# ------------------------------------------------------------------
# 2. BACKGROUND
# ------------------------------------------------------------------
pdf.section_heading("2. Background")

pdf.body_text(
    "A growing literature documents within-state and within-city variation "
    "in racial life expectancy gaps. Murray et al. (2006) showed that "
    "life expectancy varied enormously across population subgroups defined "
    "by geography and race, identifying 'Eight Americas' with gaps "
    "exceeding 20 years. Chetty et al. (2016) documented large differences "
    "in life expectancy across US counties, with race and income as key "
    "correlates. Kaufman et al. (2019) showed that Black-White "
    "differences in life expectancy varied substantially across four US "
    "states from 1969 to 2013. Roesch et al. (2023) found that the "
    "Black-White gap differed markedly across three large US cities, "
    "with male gaps on the order of 9 to 11 years. These studies demonstrate "
    "that state or national averages are inadequate for understanding "
    "local health disparities."
)

pdf.body_text(
    "A less-explored dimension of this heterogeneity is the role of "
    "population composition. When a state's minority population is "
    "geographically concentrated in areas with poor health outcomes, the "
    "statewide disparity metric conflates two distinct phenomena: the "
    "underlying severity of local health disadvantage and the share of "
    "the population exposed to it. A counterfactual framework helps "
    "disentangle these. By hypothetically replacing one region's "
    "age-specific mortality rates with those of another while holding "
    "population shares constant, one can estimate how much of the "
    "statewide gap is attributable to conditions in a specific locality."
)

pdf.body_text(
    "This compositional lens is especially relevant for Wisconsin. With "
    "about two-thirds of its Black population in Milwaukee County "
    "(a pattern shared by many states; Appendix C), "
    "any statewide Black health statistic is disproportionately a "
    "Milwaukee statistic. Understanding this is essential for correctly "
    "targeting interventions: statewide programs may dilute resources "
    "across regions where the gap is modest, while the community most "
    "in need\u2014Milwaukee\u2014requires concentrated investment."
)

pdf.body_text(
    "Similarly, the interpretation of large Black-White gaps in "
    "high-amenity communities like Dane County (Madison) requires care. "
    "A large gap can arise from severely disadvantaged Black mortality, "
    "from exceptionally advantaged White mortality, or from both. These "
    "scenarios have different policy implications: the first calls for "
    "investment in Black health infrastructure; the second may simply "
    "reflect a comparison group with unusually favorable conditions."
)


# ------------------------------------------------------------------
# 3. DATA AND METHODS
# ------------------------------------------------------------------
pdf.section_heading("3. Data and Methods")

pdf.subsection_heading("3.1 Data Sources")

pdf.body_text(
    "Mortality data come from individual death records for all deaths in "
    "Wisconsin from 2005 to 2017, including year of death, county of "
    "residence (FIPS code), age, sex, race, and Hispanic origin. I restrict "
    "the analysis to non-Hispanic Black and non-Hispanic White individuals "
    "(classified as non-Hispanic on the death record). The data contain 614,954 deaths "
    "meeting these criteria."
)

pdf.body_text(
    "Population denominators come from the CDC's bridged-race population "
    "estimates for Wisconsin counties, 2005\u20132017, by single year of age "
    "(0\u201389, 90+), sex, and race. Hispanic origin is not separately "
    "identified in the population data (origin = 9 for all records), "
    "so the denominators include Hispanic individuals within each racial "
    "category. This is a minor concern for Black populations in Wisconsin, "
    "where the Hispanic share is small."
)

pdf.body_text(
    "Geographic regions are defined using county FIPS codes: Milwaukee "
    "County (55079), Dane County (55025), and the rest of Wisconsin "
    "(all other counties)."
)

pdf.body_text(
    "Data management and analysis steps followed guidelines outlined in "
    "Sant'Anna (2024)."
)

pdf.subsection_heading("3.2 Life Table Construction")

pdf.body_text(
    "I construct abridged period life tables following Chiang (1968) and "
    "Preston et al. (2001). Deaths and populations are aggregated into "
    "19 age groups: <1, 1\u20134, 5\u20139, ..., 80\u201384, 85+. To stabilize rates "
    "for smaller populations, I pool data over three-year windows centered "
    "on each year from 2006 to 2016 (e.g., the \"2010\" estimate uses data "
    "from 2009\u20132011). Both deaths and population are summed across the "
    "three-year window, so the resulting rates represent average annual "
    "age-specific mortality. These moving windows overlap substantially, "
    "so adjacent estimates should be interpreted as smoothed trends over "
    "time rather than as independent year-by-year values. Infant nax values "
    "use Coale-Demeny formulas "
    "from Preston et al. (2001, Table 3.3); the open-ended interval (85+) "
    "uses nax = 1/M."
)

pdf.subsection_heading("3.3 Counterfactual Framework")

pdf.body_text(
    "To decompose the sources of geographic variation, I conduct three "
    "counterfactual exercises. In each, I replace one group's set of "
    "19 age-specific mortality rates with those of a donor region, hold "
    "the target population's age composition and size constant, and "
    "reconstruct the relevant life table. These are purely mechanical "
    "exercises\u2014they quantify the arithmetic importance of particular "
    "mortality schedules, not causal effects."
)

pdf.body_text(
    "Exercise 1: I replace Milwaukee's Black age-specific mortality rates "
    "with those of the rest of Wisconsin's Black population, then "
    "recompute the statewide Black life table. This answers: how much of "
    "the statewide gap is driven by Milwaukee's elevated Black mortality? "
    "Exercise 2 substitutes Dane County's Black mortality rates for "
    "Milwaukee's, as an alternative benchmark. Exercise 3 asks a different "
    "question about Dane County: I replace Dane County's White mortality "
    "rates with those of the rest of the state, to estimate how much of "
    "Dane's gap reflects its exceptionally healthy White population rather "
    "than its Black mortality disadvantage."
)

pdf.subsection_heading("3.4 Formal Gap Decomposition")

pdf.body_text(
    "To provide a comprehensive accounting of the statewide gap, I also "
    "decompose it into geography-specific contributions. If life "
    "expectancy is approximately a population-weighted average of "
    "sub-regional values, then the statewide Black-White gap can be "
    "written as:"
)

pdf.set_font("Helvetica", "I", 10)
pdf.multi_cell(0, 5, ascii_safe(
    "    Gap_WI ~= Sum_g [ pi(g) x gap(g) ] + W_comp + R"
))
pdf.ln(2)

pdf.body_text(
    "where pi(g) is the share of the statewide Black population living in "
    "geography g, gap(g) is the local Black-White life expectancy gap in "
    "geography g, W_comp is an adjustment because statewide White life "
    "expectancy is weighted by White (rather than Black) population "
    "shares, and R is a small residual term that reflects the "
    "nonlinearity of life expectancy aggregation. Each geography's "
    "contribution pi(g) x gap(g) is the product of a composition weight "
    "(how many Black residents live there) and a place-specific gap (how "
    "large the local disparity is). This decomposition quantifies how much "
    "of the statewide gap is attributable to each region and separates "
    "\"place\" effects from \"composition\" effects."
)

pdf.body_text(
    "To isolate the composition effect, I compare the actual weighted sum "
    "of local gaps (using Black population shares) with the sum that "
    "would obtain if Black people had the same geographic distribution as "
    "White people. The difference measures how much the concentration of "
    "Black residents in high-gap regions inflates the statewide disparity "
    "beyond what geography-specific health conditions alone would produce."
)

pdf.subsection_heading("3.5 Bootstrap Confidence Intervals")

pdf.body_text(
    "To quantify uncertainty in life expectancy and gap estimates, I use "
    "a parametric bootstrap. For each of 500 replicates, I resample "
    "death counts in each age-geography-race-sex cell from a Poisson "
    "distribution with mean equal to the observed death count, hold "
    "population denominators fixed, and recompute all life tables. "
    "Reported 95% confidence intervals are the 2.5th and 97.5th percentiles "
    "of the bootstrap distribution. This approach reflects sampling "
    "uncertainty in death counts; estimates for small populations "
    "(e.g., Dane County Black residents) are less precise. "
    "Confidence intervals are reported for life expectancy levels, "
    "Black-White gaps, and changes in the gap over time. "
    "Decomposition contributions and counterfactual results are reported "
    "as point estimates without confidence intervals, because the "
    "bootstrap would need to jointly resample all geographic cells "
    "and propagate through the full decomposition machinery; this "
    "extension is left for future work."
)

pdf.subsection_heading("3.6 Sensitivity and Uncertainty")

pdf.body_text(
    "The estimates presented below should be interpreted with sampling "
    "uncertainty and population size in mind. Bootstrap confidence "
    "intervals primarily capture variability in death counts given fixed "
    "population denominators; they do not account for potential "
    "systematic error in the numerator or denominator data. Geographic "
    "units with small Black populations, especially Dane County, have "
    "wider intervals and occasional apparent reversals over time that are "
    "consistent with noise. The figures and tables that report 95 percent "
    "intervals are intended to distinguish patterns that are well supported "
    "by the data from those that are more tentative. In particular, claims "
    "about worsening Black mortality in Dane County should be read in light "
    "of the reported uncertainty intervals."
)


# ------------------------------------------------------------------
# 4. RESULTS
# ------------------------------------------------------------------
pdf.section_heading("4. Results")

pdf.subsection_heading("4.1 Geographic Variation in the Black-White Gap")

pdf.body_text(
    "Table 1 presents life expectancy and the Black-White gap for the most "
    "recent period (2015\u20132017) across the four geographic units. The results "
    "reveal substantial heterogeneity masked by the statewide average. "
    "(Statewide trends are validated against Roberts et al. 2019 in "
    "Appendix B.)"
)

_, t2_rows = load_csv(TABLE_DIR / "table2_wide_2016.csv")
pdf.add_table(
    headers=["Geography", "Sex", "White LE", "Black LE", "B-W Gap"],
    rows=[[r[0], r[1], fmt(r[2]), fmt(r[3]), fmt(r[4])] for r in t2_rows],
    col_widths=[35, 25, 30, 30, 30],
    caption="Table 1. Life expectancy at birth (years) by race, sex, and "
            "geography, 2015\u20132017 (3-year pooled)."
)

_gap_rest_m = fmt_gap_ci(2016, "Rest_of_WI", "Male", 3.8)
_gap_mke_m = fmt_gap_ci(2016, "Milwaukee", "Male", 9.2)
_gap_dane_m = fmt_gap_ci(2016, "Dane", "Male", 8.5)
pdf.body_text(
    "For males, the Black-White gap ranges from " + _gap_rest_m + " years in the rest of "
    "Wisconsin to " + _gap_mke_m + " years in Milwaukee County\u2014a nearly 2.5-fold "
    "difference. Dane County's male gap (" + _gap_dane_m + " years) is nearly as large as "
    "Milwaukee's, despite Dane County's substantially higher overall life "
    "expectancy. This reflects a dual pattern: White males in Dane County "
    "enjoy the highest life expectancy of any group (80.2 years), but "
    "Black males in Dane County do not share proportionally in this "
    "advantage (71.7 years). Milwaukee has the lowest Black male life "
    "expectancy of any region (68.3 years), which is 5.7 years below the "
    "rest-of-state average for Black males."
)

_gap_rest_f = fmt_gap_ci(2016, "Rest_of_WI", "Female", 4.3)
_gap_mke_f = fmt_gap_ci(2016, "Milwaukee", "Female", 6.1)
_gap_dane_f = fmt_gap_ci(2016, "Dane", "Female", 5.4)
pdf.body_text(
    "For females, the geographic pattern is less dramatic but still "
    "notable. The gap ranges from " + _gap_rest_f + " years (rest of Wisconsin) to "
    + _gap_mke_f + " years (Milwaukee). Dane County's female gap "
    "(" + _gap_dane_f + " years) is intermediate, but it features relatively high "
    "Black female life expectancy (78.3 years, the highest of any region). A caveat is "
    "warranted: Dane County's Black population is small relative to the "
    "other regions (roughly 50,000 per sex over the 3-year window, or "
    "about 103,000 total person-years, with "
    "approximately 260 male and 158 female Black deaths), which limits "
    "the precision of these estimates."
)

if pdf.get_y() > 130:
    pdf.add_page()

pdf.add_figure(
    FIG_DIR / "fig5_le_by_race_geography_2016.png",
    "Figure 1. Life expectancy at birth by race and geography, males "
    "(left) and females (right), 2015\u20132017 (95% CI; Dane County intervals wider).",
    width=160
)

pdf.subsection_heading("4.2 Trends in the Gap by Geography")

pdf.body_text(
    "Figures 2 and 3 plot the Black-White gap over time for each "
    "geography. The most striking finding is the divergent trajectory of "
    "the male gap across regions. In Milwaukee, the male gap narrowed from "
    "8.6 years (2006) to a low of 7.1 years (2010) before widening "
    "sharply to 9.2 years by 2016. In Dane County, the male gap nearly "
    "doubled from 5.3 years (2006) to 8.5 years (2016). In the rest of "
    "Wisconsin, the gap remained comparatively small but also widened, "
    "from 2.1 to 3.8 years."
)

pdf.add_figure(
    FIG_DIR / "fig3_male_bw_gap_by_geography.png",
    "Figure 2. Black-White life expectancy gap for males by geography, "
    "2006\u20132016 (3-year pooled; 95% CI; Dane County uncertainty emphasized).",
    width=125
)

pdf.add_figure(
    FIG_DIR / "fig4_female_bw_gap_by_geography.png",
    "Figure 3. Black-White life expectancy gap for females by geography, "
    "2006\u20132016 (3-year pooled; 95% CI; Dane County uncertainty emphasized).",
    width=125
)

pdf.body_text(
    "For females, trends were more stable. The statewide female gap "
    "narrowed slightly from 6.2 to 5.7 years. Milwaukee's female gap "
    "remained roughly constant near 6 years. Dane County showed "
    "considerable volatility\u2014likely reflecting the small Black female "
    "population\u2014but ended the period at 5.4 years, similar to where "
    "it began."
)

pdf.subsection_heading("4.3 Decomposing the Change Over Time")

pdf.body_text(
    "Table 2 decomposes the change in the gap between the earliest "
    "(2005\u20132007) and latest (2015\u20132017) periods into changes in White "
    "and Black life expectancy. A widening gap could reflect White gains, "
    "Black losses, or both\u2014and the pattern differs sharply by geography."
)

# Table 2 (change over time): load with CIs if present
t3_headers = ["Geography", "Sex", "Gap (05-07)", "Gap (15-17)",
              "Change", "Delta White LE", "Delta Black LE"]
t3_path = TABLE_DIR / "table3_gap_change_2006_vs_2016.csv"
with open(t3_path) as _f:
    _reader = csv.DictReader(_f)
    t3_rows = list(_reader)
if t3_rows and "gap_change_lo" in t3_rows[0]:
    t3_headers = ["Geography", "Sex", "Gap (05-07)", "Gap (15-17)", "Change (95% CI)",
                  "Delta White LE", "Delta Black LE (95% CI)"]
    t3_display = []
    for r in t3_rows:
        ch = fmt(r.get("Change", ""))
        if r.get("gap_change_lo") not in (None, "", []) and str(r.get("gap_change_lo", "")).strip():
            try:
                ch = ch + " [" + fmt(r["gap_change_lo"], 1) + ", " + fmt(r["gap_change_hi"], 1) + "]"
            except (KeyError, ValueError, TypeError):
                pass
        dbl = fmt(r.get("Black LE Change", ""))
        if r.get("black_le_change_lo") not in (None, "", []) and str(r.get("black_le_change_lo", "")).strip():
            try:
                dbl = dbl + " [" + fmt(r["black_le_change_lo"], 1) + ", " + fmt(r["black_le_change_hi"], 1) + "]"
            except (KeyError, ValueError, TypeError):
                pass
        t3_display.append([r.get("Geography", ""), r.get("Sex", ""),
                          fmt(r.get("Gap (2005-07)", "")), fmt(r.get("Gap (2015-17)", "")),
                          ch, fmt(r.get("White LE Change", "")), dbl])
    t3_table_rows = t3_display
else:
    t3_table_rows = [[r.get("Geography", ""), r.get("Sex", ""),
                      fmt(r.get("Gap (2005-07)", "")), fmt(r.get("Gap (2015-17)", "")),
                      fmt(r.get("Change", "")), fmt(r.get("White LE Change", "")),
                      fmt(r.get("Black LE Change", ""))] for r in t3_rows]
pdf.add_table(
    headers=t3_headers[:7],
    rows=t3_table_rows,
    col_widths=[24, 16, 20, 20, 36, 20, 36] if "95% CI" in str(t3_headers) else [28, 18, 23, 23, 20, 23, 23],
    caption="Table 2. Change in the Black-White life expectancy gap (years) "
            "between 2005\u20132007 and 2015\u20132017, with decomposition into "
            "White and Black LE changes. 95% CI in brackets when available.",
    font_size=8
)

# Dane County uncertainty: qualify the decline claim using change_ci
_dane_qualifier = ""
if change_ci_df is not None:
    _dane = change_ci_df[(change_ci_df["geography"] == "Dane") & (change_ci_df["sex_label"] == "Male")]
    if len(_dane) > 0:
        _r = _dane.iloc[0]
        _lo, _hi = _r.get("black_le_change_lo"), _r.get("black_le_change_hi")
        if pd.notna(_lo) and pd.notna(_hi):
            _dane_qualifier = (
                " The estimated decline in Dane County Black male life expectancy is "
                + fmt(_r["black_le_change"], 1) + " years (95% CI "
                + fmt(_lo, 1) + " to " + fmt(_hi, 1) + "). "
            )
            if _hi < 0:
                _dane_qualifier += "The interval excludes zero, consistent with a statistically significant decline. "
            elif _lo > 0:
                _dane_qualifier += "The interval includes positive values; the point estimate of decline should be interpreted with caution. "
            else:
                _dane_qualifier += "The interval includes zero; precision is limited by the small Black male population in Dane County. "

pdf.body_text(
    "In Dane County, the male gap widened by 3.2 years\u2014the largest "
    "increase of any region-sex combination. The estimates point to "
    "a decline of about 2.4 years in Black male life expectancy (from 74.1 to 71.7 "
    "years), while White male life expectancy increased by 0.9 years." + _dane_qualifier +
    "In Milwaukee, the male gap widened by 0.6 years, with both groups "
    "gaining but White males gaining faster (+1.1 vs. +0.5 years). In "
    "the rest of Wisconsin, Black male life expectancy declined by 1.3 "
    "years, widening the gap by 1.7 years. Among females, the statewide "
    "gap narrowed by 0.5 years, driven by faster improvement among Black "
    "females (+0.7 years) relative to White females (+0.2 years)."
)

# ---- 4.4 Decomposition of the statewide gap ----
pdf.subsection_heading("4.4 Decomposing the Statewide Gap")

pdf.body_text(
    "The formal decomposition reveals that the statewide gap is "
    "overwhelmingly driven by Milwaukee. Table 3 presents the "
    "decomposition for three key periods and both sexes. Each "
    "geography's contribution equals the product of its Black "
    "population share (pi) and its local B-W gap. The contributions "
    "sum, with a small White composition adjustment, to the total "
    "statewide gap."
)

# Load decomposition data and build table for key years
decomp_table_rows = []
import csv as _csv
with open(TABLE_DIR / "table4_gap_decomposition.csv") as _f:
    _reader = _csv.DictReader(_f)
    _all_decomp = list(_reader)

for _r in _all_decomp:
    if int(_r["center_year"]) in (2006, 2010, 2016):
        _gap = float(_r["actual_gap"])
        _mke = float(_r["MKE_contrib"])
        _dane = float(_r["Dane_contrib"])
        _row_wi = float(_r["RoW_contrib"])
        _wcomp = float(_r["white_comp_adj"])
        _resid = float(_r["nonlinearity"])
        decomp_table_rows.append([
            _r["center_year"], _r["sex"],
            fmt(_r["actual_gap"]),
            f"{fmt(_r['MKE_contrib'])} ({100*_mke/_gap:.0f}%)",
            f"{fmt(_r['Dane_contrib'])} ({100*_dane/_gap:.0f}%)",
            f"{fmt(_r['RoW_contrib'])} ({100*_row_wi/_gap:.0f}%)",
            fmt(str(round(_wcomp + _resid, 2))),
        ])

pdf.add_table(
    headers=["Year", "Sex", "Gap", "Milwaukee", "Dane", "Rest of WI", "Adj."],
    rows=decomp_table_rows,
    col_widths=[16, 17, 16, 32, 26, 26, 16],
    caption="Table 3. Decomposition of the statewide B-W gap (years). "
            "Each geography's contribution = pi_g (Black pop. share) x "
            "local B-W gap. Percentages show share of total gap. "
            "Adj. = White composition + aggregation residual.",
    font_size=8
)

_gap_sw_m = fmt_gap_ci(2016, "Statewide", "Male", 7.9)
pdf.body_text(
    "For males in 2016, Milwaukee contributes 5.6 years of the " + _gap_sw_m + "-year "
    "statewide gap -- 70 percent of the total. This dominance reflects "
    "both Milwaukee's large Black male population share (about 60 percent) and its "
    "large local gap (" + _gap_mke_m + " years). Dane County's gap is nearly as large "
    "(" + _gap_dane_m + " years), but because only 8.5 percent of the state's Black males "
    "live there, its contribution is just 0.7 years (9 percent). The rest "
    "of Wisconsin contributes 1.2 years (15 percent), with a moderate gap "
    "(3.8 years) offset by a moderate population share (31 percent). "
    "The White composition adjustment is small (0.4 years combined), "
    "confirming that the decomposition is driven almost entirely by the "
    "interplay of Black population shares and local gaps."
)

pdf.body_text(
    "For females, Milwaukee's contribution is also dominant (4.1 years, "
    "73 percent of the 5.7-year gap in 2016), though the rest of "
    "Wisconsin contributes a larger share (18 percent) than for males, "
    "reflecting the fact that the female gap is more geographically "
    "uniform."
)

pdf.body_text(
    "Figure 4 visualizes this decomposition over time. Each stacked bar "
    "shows how the statewide gap is built from geography-specific "
    "contributions. Milwaukee's red segment dominates in every period, "
    "but its share of the total has fluctuated. For males, the widening "
    "gap after 2012 reflects growing contributions from all three "
    "regions, with both Milwaukee's and the rest of Wisconsin's "
    "segments expanding."
)

if pdf.get_y() > 100:
    pdf.add_page()

pdf.add_figure(
    FIG_DIR / "fig7_gap_decomposition_stacked.png",
    "Figure 4. Decomposition of the statewide Black-White life "
    "expectancy gap into geographic contributions "
    "(pi x local gap) for males (left) and females (right), "
    "2006\u20132016.",
    width=155
)

pdf.add_page()

pdf.body_text(
    "The composition effect -- how much the geographic concentration of "
    "Black residents in high-gap areas inflates the statewide gap -- is "
    "substantial. If Black Wisconsinites had the same geographic "
    "distribution as White Wisconsinites, the weighted sum of local male "
    "gaps would be 4.9 years instead of 7.5 years in 2016: the "
    "composition penalty is 2.6 years. In other words, roughly a third "
    "of what drives the statewide male gap is not the severity of local "
    "disparities per se, but the fact that most Black residents live in "
    "the worst-performing region."
)

pdf.body_text(
    "Figure 5 illustrates the two components of each geography's "
    "contribution: the Black population share (Panel A) and the local "
    "B-W gap (Panel B). Milwaukee's contribution is large because it "
    "ranks highest on both dimensions. Dane County's high local gap "
    "is offset by its small Black population share, keeping its "
    "statewide contribution modest."
)

pdf.add_figure(
    FIG_DIR / "fig8_decomp_components.png",
    "Figure 5. Components of the gap decomposition for males: "
    "(A) Black population shares by geography and "
    "(B) local B-W life expectancy gaps by geography, "
    "2006\u20132016.",
    width=155
)


# ---- 4.5 Counterfactual exercises ----
if pdf.get_y() > 180:
    pdf.add_page()
else:
    pdf.ln(4)
pdf.subsection_heading("4.5 Counterfactual Exercises")

pdf.body_text(
    "The decomposition quantifies each region's contribution to the "
    "statewide gap; the counterfactual exercises below ask what the gap "
    "would be under specific alternative mortality schedules."
)

pdf.body_text(
    "Table 4 presents Exercise 1: what if Black Milwaukeeans had the same "
    "age-specific mortality rates as Black people in the rest of Wisconsin? "
    "In 2016, the statewide male gap would fall "
    "from " + _gap_sw_m + " to 4.2 years -- a reduction of 3.75 years, or nearly half "
    "the observed gap. Black male life expectancy would rise from 70.0 to "
    "73.8 years. For females, the gap would narrow from 5.7 to 4.4 years. "
    "Note that this ~47 percent counterfactual reduction differs from "
    "the 70 percent decomposition share reported in Table 3: the former "
    "measures the fractional reduction in the gap under a specific "
    "mortality-replacement scenario, while the latter measures "
    "Milwaukee's share of the gap in a population-weighted accounting. "
    "Both point to Milwaukee as the dominant driver, but they quantify "
    "different aspects of its role."
)

pdf.add_table(
    headers=["Year", "Sex", "Actual Gap", "CF Gap",
             "Reduction", "Actual Black e0", "CF Black e0"],
    rows=[
        ["2006", "Male", "7.57", "2.19", "5.38", "69.83", "75.21"],
        ["2006", "Female", "6.24", "4.32", "1.91", "75.81", "77.73"],
        ["2010", "Male", "6.69", "3.64", "3.05", "71.38", "74.43"],
        ["2010", "Female", "5.78", "5.16", "0.62", "76.87", "77.49"],
        ["2016", "Male", "7.91", "4.17", "3.75", "70.03", "73.78"],
        ["2016", "Female", "5.72", "4.37", "1.35", "76.53", "77.88"],
    ],
    col_widths=[16, 18, 22, 22, 22, 28, 28],
    caption="Table 4. Counterfactual Exercise 1: statewide B-W gap if "
            "Milwaukee's Black population had Rest-of-WI Black "
            "age-specific mortality.",
    font_size=8.5
)

pdf.body_text(
    "Exercise 2 asks: what if Milwaukee's Black population instead had "
    "Dane County's Black mortality? In 2006, this would have reduced the "
    "male gap by 4.6 years (from 7.6 to 3.0), since Dane County Black "
    "males had relatively favorable life expectancy at that time "
    "(74.1 years). But by 2016, this exercise yields a smaller reduction "
    "of only 2.3 years (from 7.9 to 5.6), because Dane County Black male "
    "mortality had itself deteriorated. This time comparison underscores "
    "that the Black male mortality crisis extends beyond Milwaukee."
)

pdf.body_text(
    "Exercise 3 addresses a different question: why is Dane County's gap "
    "so large despite its reputation as a progressive, high-opportunity "
    "community? Part of the answer is that the comparison group -- "
    "Dane County Whites -- is exceptionally healthy. Table 5 shows "
    "what happens when Dane County White mortality is replaced with "
    "Rest-of-WI White mortality."
)

pdf.add_table(
    headers=["Year", "Sex", "Actual Gap", "CF Gap",
             "Reduction", "Actual White e0", "CF White e0"],
    rows=[
        ["2006", "Male", "5.29", "3.29", "2.00", "79.36", "77.37"],
        ["2006", "Female", "5.05", "3.84", "1.21", "83.27", "82.06"],
        ["2010", "Male", "6.05", "4.32", "1.73", "79.76", "78.04"],
        ["2010", "Female", "6.32", "5.03", "1.30", "83.91", "82.61"],
        ["2016", "Male", "8.50", "6.07", "2.43", "80.21", "77.78"],
        ["2016", "Female", "5.43", "3.83", "1.59", "83.73", "82.13"],
    ],
    col_widths=[16, 18, 22, 22, 22, 28, 28],
    caption="Table 5. Counterfactual Exercise 3: Dane County B-W gap if "
            "Dane Whites had Rest-of-WI White age-specific mortality.",
    font_size=8.5
)

pdf.body_text(
    "In 2016, replacing Dane White mortality with Rest-of-WI rates "
    "reduces the male gap from 8.5 to 6.1 years and the female gap from "
    "5.4 to 3.8 years. Roughly one-quarter to one-third of Dane County's "
    "gap is attributable to the exceptionally favorable White mortality "
    "environment. The remaining gap of 6.1 years for males is still "
    "substantial and suggests disadvantaged Black mortality "
    "in Dane County. Point estimates in Table 2 suggest a 2.4-year decline "
    "in Black male life expectancy, although the wide confidence interval "
    "means this should be interpreted cautiously. Dane County's large gap "
    "thus reflects an unusually healthy White benchmark combined with "
    "suggestive evidence of worsening Black health outcomes."
)


# ------------------------------------------------------------------
# 5. DISCUSSION
# ------------------------------------------------------------------
pdf.section_heading("5. Discussion")

pdf.body_text(
    "This analysis yields three principal findings. First, the statewide "
    "Black-White life expectancy gap in Wisconsin masks a nearly 2.5-fold "
    "range across regions: from " + _gap_rest_m + " years in the rest of the state to "
    + _gap_mke_m + " years in Milwaukee for males. Second, the formal decomposition "
    "reveals that Milwaukee contributes 70 percent of the statewide male "
    "gap -- a dominance driven by the combination of its large Black male "
    "population share (about 60 percent in 2016) and its large local gap (" + _gap_mke_m + " years). "
    "The geographic concentration of Black Wisconsinites in Milwaukee "
    "adds approximately 2.6 years to the statewide male gap compared to "
    "a scenario in which Black and White residents had the same geographic "
    "distribution. Third, the male gap widened in all regions between "
    "2005-2007 and 2015-2017. A cautionary note concerns Dane County, "
    "where the male gap (" + _gap_dane_m + " years) is nearly as large as Milwaukee's. "
    "Counterfactual analysis shows that roughly a quarter to a third of "
    "Dane's gap reflects its exceptionally healthy White population rather "
    "than Black disadvantage per se. Point estimates also suggest "
    "deteriorating Black male mortality in Dane County, but this pattern "
    "is estimated with substantial uncertainty due to the small Black "
    "population and should be interpreted as a signal warranting "
    "further investigation rather than an established trend."
)

pdf.body_text(
    "These findings have important implications for how we interpret and "
    "respond to state-level racial health disparities. The \"Wisconsin "
    "gap\" is not a diffuse, statewide phenomenon amenable to generic "
    "state-level programs. The decomposition shows that 70 percent of "
    "the statewide male gap (" + _gap_sw_m + " years) traces to a single county where "
    "about two-thirds of the state's Black population lives under mortality conditions "
    "that produce a male life expectancy of 68.3 years -- below the "
    "US national average for Black males and 5.7 years below the Black "
    "male average in the rest of the state. "
    "Statewide interventions that spread resources uniformly are poorly "
    "matched to this geographic concentration of disadvantage."
)

pdf.body_text(
    "The Dane County finding deserves particular attention. Dane County "
    "is widely perceived as a progressive, high-opportunity community "
    "with strong public institutions and a robust economy. Yet the "
    "Black-White male life expectancy gap there (" + _gap_dane_m + " years) is nearly as "
    "large as Milwaukee's, and it widened faster. The counterfactual "
    "decomposition reveals that this gap has two sources: the exceptional "
    "longevity of Dane County's White population (which inflates the "
    "reference standard by 2.4 years) and what point estimates suggest is a "
    "decline in Black male life expectancy, though this is imprecisely "
    "estimated given the small population. The latter is the more actionable concern. "
    "Favorable average conditions do not automatically produce equitable "
    "health outcomes. Social determinants driving mortality disparities "
    "may operate through mechanisms\u2014residential segregation within the "
    "county, differential incarceration, concentrated poverty\u2014that are "
    "not captured by county-level aggregates."
)

pdf.body_text(
    "The decline in Black male life expectancy in several regions during "
    "the latter years of the study period is consistent with emerging "
    "national trends linked to the opioid epidemic, increases in "
    "homicide, and rising \"deaths of despair\" (Case & Deaton 2015). Cause-of-death "
    "decomposition (e.g., Arriaga 1984) is needed to identify which "
    "specific causes are driving these reversals and to inform targeted "
    "interventions."
)

pdf.body_text(
    "Several limitations should be noted. The population denominators do "
    "not separately identify Hispanic origin, which may introduce a small "
    "upward bias in population counts for non-Hispanic groups. Reported "
    "95% confidence intervals from a parametric bootstrap (Section 3.5) "
    "reflect sampling uncertainty in death counts; Dane County's Black "
    "population, while growing, remains relatively small, and the 3-year "
    "pooling mitigates but does not eliminate instability in those "
    "estimates. As a result, the apparent decline in Black male life "
    "expectancy in Dane County should be viewed as a warning signal that "
    "warrants continued monitoring and investigation rather than as a "
    "precisely measured effect. The counterfactual exercises are mechanical "
    "decompositions, not causal estimates\u2014they quantify the arithmetic "
    "contribution of regional mortality schedules but do not identify why "
    "those schedules differ. The analysis covers 2005\u20132017 and does not "
    "capture more recent trends, including the COVID-19 pandemic, which "
    "disproportionately affected Black life expectancy nationwide. "
    "Finally, this analysis does not decompose the gap by cause of death, "
    "which would help identify targeted intervention points."
)


# ------------------------------------------------------------------
# 6. CONCLUSION
# ------------------------------------------------------------------
pdf.section_heading("6. Conclusion")

pdf.body_text(
    "Statewide life expectancy statistics, while valuable, can obscure "
    "the geographic concentration of racial health disparities. In "
    "Wisconsin, the Black-White life expectancy gap (" + _gap_sw_m + " years for males) "
    "varies by a factor of nearly 2.5 across regions, and the trajectories are diverging. "
    "A formal decomposition reveals that Milwaukee alone accounts for "
    "70 percent of the statewide male gap, driven by the double burden "
    "of a large Black population share and severe local mortality "
    "disadvantage. Black geographic concentration adds roughly 2.6 years "
    "to the statewide male gap -- a quantifiable composition penalty. "
    "Dane County's gap (" + _gap_dane_m + " years), meanwhile, is inflated by exceptionally high "
    "White life expectancy but also reflects what appears to be a troubling "
    "decline in Black male life expectancy, a finding that warrants "
    "continued monitoring given the small population size. Policy responses must be "
    "geographically targeted: Milwaukee's crisis requires investment in "
    "the structural determinants of Black health in a hyper-segregated "
    "urban environment, while Dane County's growing disparity calls for "
    "investigation of why a seemingly prosperous community is failing "
    "its Black residents."
)


# ------------------------------------------------------------------
# APPENDIX A: GEOGRAPHIC REFERENCE
# ------------------------------------------------------------------
pdf.add_page()
pdf.section_heading("Appendix A: Geographic Reference")

pdf.add_figure(
    FIG_DIR / "fig6_wisconsin_map_bw_gap.png",
    "Figure A1. Wisconsin counties with Milwaukee, Dane, and "
    "rest-of-state regions highlighted. Annotations show male "
    "Black-White life expectancy gap for 2015\u20132017.",
    width=120
)


# ------------------------------------------------------------------
# APPENDIX B: REPLICATION OF ROBERTS ET AL. (2019)
# ------------------------------------------------------------------
pdf.add_page()
pdf.section_heading("Appendix B: Replication of Roberts et al. (2019)")

pdf.body_text(
    "To validate the analytic pipeline, I replicate the statewide life "
    "expectancy estimates of Roberts et al. (2019) for the 2014\u20132016 "
    "period (center year 2015). Table B1 compares my estimates with the "
    "published values. My estimates are within 0.1 to 0.4 years of the "
    "published values across all race-sex groups. The small discrepancies "
    "likely reflect differences in Hispanic-origin filtering and the "
    "exact population denominators used. The Black-White gap in my "
    "estimates is 7.2 years for males and 5.6 years for females, "
    "compared to 7.3 and 5.6 years in Roberts et al."
)

pdf.add_table(
    headers=["Group", "Roberts et al.", "This Paper", "Difference"],
    rows=[
        ["White Males", "77.75", "78.06", "+0.31"],
        ["Black Males", "70.41", "70.84", "+0.43"],
        ["White Females", "82.15", "82.24", "+0.09"],
        ["Black Females", "76.54", "76.67", "+0.13"],
        ["Male B-W Gap", "7.34", "7.22", "-0.12"],
        ["Female B-W Gap", "5.61", "5.57", "-0.04"],
    ],
    col_widths=[45, 35, 35, 35],
    caption="Table B1. Replication check: statewide life expectancy (years) "
            "for 2014\u20132016, compared with Roberts et al. (2019)."
)

pdf.body_text(
    "Figures B1 and B2 show statewide life expectancy trends for males "
    "and females, respectively. Among males, White life expectancy was "
    "essentially flat (77.4 to 78.0 years), while Black male life "
    "expectancy rose from 69.8 to a peak of 71.6 years around 2012 "
    "before declining to 70.0 years by 2016. This reversal widened "
    "the male gap from 6.5 years at its narrowest (2012) to 7.9 years "
    "at the end of the study period. Female trends were more stable, "
    "with the gap fluctuating between 5.6 and 6.2 years."
)

pdf.add_page()

pdf.add_figure(
    FIG_DIR / "fig1_male_le_trends_statewide.png",
    "Figure B1. Life expectancy at birth for non-Hispanic Black and "
    "White males, Wisconsin statewide, 2006\u20132016 (3-year pooled "
    "estimates).",
    width=125
)

pdf.add_figure(
    FIG_DIR / "fig2_female_le_trends_statewide.png",
    "Figure B2. Life expectancy at birth for non-Hispanic Black and "
    "White females, Wisconsin statewide, 2006\u20132016 (3-year pooled "
    "estimates).",
    width=125
)

# ------------------------------------------------------------------
# APPENDIX C: SAMPLE CONTEXT AND COUNTY CONCENTRATION
# ------------------------------------------------------------------
pdf.add_page()
pdf.section_heading("Appendix C: Sample Context and County Concentration")

pdf.subsection_heading("C.1 Sample context by geography, sex, and race")

pdf.body_text(
    "Table C1 reports the number of deaths, pooled 3-year person-years, "
    "and crude death rates by geography, sex, and race for 2015\u20132017 "
    "(the 2016 centered window). These figures provide context for the "
    "precision of life expectancy estimates: cells with fewer deaths and "
    "smaller person-years, especially Black residents in Dane County, "
    "yield wider confidence intervals and more sampling variability."
)

_ctx_path = TABLE_DIR / "table6_sample_context_2016.csv"
if _ctx_path.exists():
    _ctx = pd.read_csv(_ctx_path)
    _ctx_rows = []
    for _, r in _ctx.iterrows():
        _ctx_rows.append([
            ascii_safe(str(r["Geography"])),
            ascii_safe(str(r["Sex"])),
            ascii_safe(str(r["Race"])),
            int(r["Total Deaths (3yr)"]),
            int(r["Total Population (3yr person-years)"]),
            f'{float(r["Crude Death Rate (per 1,000)"]):.3f}',
        ])
    pdf.add_table(
        headers=[
            "Geography", "Sex", "Race",
            "Deaths (3yr)", "Person-years (3yr)",
            "Crude rate\n(per 1,000)"
        ],
        rows=_ctx_rows,
        col_widths=[28, 18, 20, 22, 30, 28],
        caption="Table C1. Sample context for 2015\u20132017 (center year 2016): "
                "deaths, pooled person-years, and crude death rates by "
                "geography, sex, and race.",
        font_size=8
    )
else:
    pdf.body_text("[Table C1: table6_sample_context_2016.csv not found.]")

pdf.subsection_heading("C.2 County concentration of Black population by state")

pdf.body_text(
    "Wisconsin's concentration of its Black population in Milwaukee "
    "County is not unusual. Many states have a single county or equivalent "
    "that holds the largest share of the state's Black population. "
    "Table C2 shows, for each state and the District of Columbia, the "
    "county (or county-equivalent) with the largest share of the state's "
    "Black population and that share. Wisconsin ranks among the states "
    "where this concentration is high: Milwaukee County holds about "
    "two-thirds of the state's Black population. Several states show "
    "even higher concentration (e.g., Nevada 94%, Hawaii 89%, Rhode "
    "Island 87%, Arizona 77%, Illinois 67%). Thus the compositional "
    "challenge for interpreting statewide disparity statistics is "
    "widespread, not unique to Wisconsin."
)

# Load and display county Black proportions
_county_prop_path = TABLE_DIR / "county_black_population_proportions.csv"
if _county_prop_path.exists():
    _cp = pd.read_csv(_county_prop_path)
    _cp_rows = []
    for _, r in _cp.iterrows():
        _cp_rows.append([
            ascii_safe(str(r["State"])),
            ascii_safe(str(r["County_with_largest_share"])),
            str(r["Share_of_state_Black_pop_pct"]) + "%",
        ])
    pdf.add_table(
        headers=["State", "County (largest share)", "Share (%)"],
        rows=_cp_rows,
        col_widths=[38, 60, 22],
        caption="Table C2. County (or county-equivalent) with largest share "
                "of state's Black population and approximate share. "
                "Source: compiled from publicly available demographic "
                "estimates following Sant'Anna (2024) workflow guidance.",
        font_size=8
    )
else:
    pdf.body_text("[Table C2: county_black_population_proportions.csv not found.]")

# ------------------------------------------------------------------
# REFERENCES
# ------------------------------------------------------------------
pdf.add_page()
pdf.section_heading("References")

refs = [
    "Arriaga, E. E. (1984). Measuring and explaining the change in life "
    "expectancies. Demography, 21(1), 83\u201396.",

    "Case, A., & Deaton, A. (2015). Rising morbidity and mortality in "
    "midlife among white non-Hispanic Americans in the 21st century. "
    "Proceedings of the National Academy of Sciences, 112(49), "
    "15078\u201315083.",

    "Chetty, R., Stepner, M., Abraham, S., et al. (2016). The "
    "association between income and life expectancy in the United States, "
    "2001\u20132014. JAMA, 315(16), 1750\u20131766.",

    "Chiang, C. L. (1968). Introduction to Stochastic Processes in "
    "Biostatistics. Wiley.",

    "Harper, S., MacLehose, R. F., & Kaufman, J. S. (2014). Trends in "
    "the Black-White life expectancy gap among US states, 1990\u20132009. "
    "Health Affairs, 33(8), 1375\u20131382.",

    "Kaufman, J. S., Riddell, C. A., & Harper, S. (2019). Black and "
    "White differences in life expectancy in 4 US states, 1969\u20132013. "
    "Public Health Reports, 134(6), 634\u2013642.",

    "Kochanek, K. D., Arias, E., & Anderson, R. N. (2013). How did "
    "cause of death contribute to racial differences in life expectancy "
    "in the United States in 2010? NCHS Data Brief, No. 125.",

    "Murray, C. J. L., Kulkarni, S. C., Michaud, C., et al. (2006). "
    "Eight Americas: investigating mortality disparities across races, "
    "counties, and race-counties in the United States. PLoS Medicine, "
    "3(9), e260.",

    "Preston, S. H., Heuveline, P., & Guillot, M. (2001). Demography: "
    "Measuring and Modeling Population Processes. Blackwell.",

    "Riddell, C. A., Morrison, K. T., Kaufman, J. S., & Harper, S. "
    "(2018). Trends in the contribution of major causes of death to the "
    "Black-White life expectancy gap by US state. Health & Place, 52, "
    "85\u2013100.",

    "Roberts, M. T., Reither, E. N., & Lim, S. (2019). Contributors to "
    "Wisconsin's persistent Black-White gap in life expectancy. BMC "
    "Public Health, 19(1), 891.",

    "Roesch, P. T., Saiyed, N. S., Laflamme, E., De Maio, F. G., & "
    "Benjamins, M. R. (2023). Life expectancy gaps among Black and "
    "White persons and contributing causes of death in 3 large US "
    "cities, 2018\u20132019. JAMA Network Open, 6(3), e233146.",

    "Sant'Anna, P. H. C. (2024). Using Claude Code for academic work. "
    "Workflow guide, accessed March 2026.",
]

for ref in refs:
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 4.5, ascii_safe(ref))
    pdf.ln(2)


# ------------------------------------------------------------------
# Save
# ------------------------------------------------------------------
pdf.output(str(OUT_PDF))
print(f"Paper saved to: {OUT_PDF}")
print(f"Pages: {pdf.page_no()}")
