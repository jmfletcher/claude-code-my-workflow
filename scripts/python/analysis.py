"""
Wisconsin Black-White Life Expectancy Gap Analysis
Author: Jason Fletcher
Purpose: Replicate Roberts et al. (2019) LE trends, then extend
         to Milwaukee County, Dane County, and Rest-of-WI
Inputs:  Data/mortality/wi59_17.csv
         Data/population/wi.1969_2023.singleages.through89.90plus.txt
         Data/shp/cb_2018_us_county_500k.*
Outputs: Figures/, output/
"""

# 0. Setup --------------------------------------------------------
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import warnings

warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

np.random.seed(20260312)

ROOT = Path(__file__).resolve().parent.parent.parent
FIG_DIR = ROOT / "Figures"
OUT_DIR = ROOT / "output"
for d in [FIG_DIR, OUT_DIR, OUT_DIR / "diagnostics", OUT_DIR / "tables"]:
    d.mkdir(parents=True, exist_ok=True)

# --- Constants ---
MILWAUKEE_FIPS = 55079
DANE_FIPS = 55025

# UW-Madison palette
WHITE_POP = "#4a7fb5"   # Blue for NH-White lines
BLACK_POP = "#d62728"   # Red for NH-Black lines
ACCENT_GRAY = "#525252"
LIGHT_GRAY = "#dadfe1"

# Age group definitions for abridged life table
AGE_CUTS = [0, 1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85]
AGE_LABELS = ["<1", "1-4", "5-9", "10-14", "15-19", "20-24", "25-29",
              "30-34", "35-39", "40-44", "45-49", "50-54", "55-59",
              "60-64", "65-69", "70-74", "75-79", "80-84", "85+"]
AGE_WIDTHS = [1, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, np.inf]

# 3-year windows centered on each year (using data from 2005-2017)
# Earliest center = 2006 (needs 2005), latest center = 2016 (needs 2017)
WINDOWS = {yr: (yr - 1, yr + 1) for yr in range(2006, 2017)}


def set_mortality_theme():
    plt.rcParams.update({
        "figure.figsize": (10, 6),
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.size": 12,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.labelsize": 12,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
        "legend.fontsize": 11,
        "legend.framealpha": 0.9,
        "lines.linewidth": 2,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.bbox": "tight",
    })


set_mortality_theme()


# =================================================================
# PHASE 1: DATA PREPARATION
# =================================================================
print("=" * 60)
print("PHASE 1: DATA PREPARATION")
print("=" * 60)

# --- 1a. Load mortality data ---
print("\n--- Loading mortality data ---")
mort = pd.read_csv(ROOT / "Data" / "mortality" / "wi59_17.csv",
                    low_memory=False)
print(f"Mortality records: {len(mort):,}")
print(f"Year range: {mort['deathyear'].min()} - {mort['deathyear'].max()}")
print(f"\nRace values:\n{mort['race'].value_counts().sort_index()}")
print(f"\nHispanic field - non-null by decade:")
for decade_start in range(1960, 2020, 10):
    mask = (mort["deathyear"] >= decade_start) & (mort["deathyear"] < decade_start + 10)
    n_total = mask.sum()
    n_hisp_present = mort.loc[mask, "hispanic"].notna().sum()
    if n_total > 0:
        print(f"  {decade_start}s: {n_hisp_present:,}/{n_total:,} "
              f"({100*n_hisp_present/n_total:.1f}%)")

print(f"\nHispanic values (when present):\n"
      f"{mort['hispanic'].dropna().value_counts().head(10)}")

# --- 1b. Load population data ---
print("\n--- Loading population data ---")
colspecs = [(0, 4), (4, 6), (6, 11), (13, 14), (14, 15), (15, 16),
            (16, 18), (18, 26)]
colnames = ["year", "state", "fips", "race", "origin", "sex", "age", "pop"]

pop = pd.read_fwf(ROOT / "Data" / "population" /
                   "wi.1969_2023.singleages.through89.90plus.txt",
                   colspecs=colspecs, names=colnames, header=None)

print(f"Population records: {len(pop):,}")
print(f"Year range: {pop['year'].min()} - {pop['year'].max()}")
print(f"\nRace values:\n{pop['race'].value_counts().sort_index()}")
print(f"\nOrigin values:\n{pop['origin'].value_counts().sort_index()}")
print(f"\nSex values:\n{pop['sex'].value_counts().sort_index()}")
print(f"\nAge range: {pop['age'].min()} - {pop['age'].max()}")

# --- 1c. Filter and prepare mortality ---
print("\n--- Filtering mortality data ---")

# Restrict to 2005-2017
mort = mort[(mort["deathyear"] >= 2005) & (mort["deathyear"] <= 2017)].copy()
print(f"After restricting to 2005-2017: {len(mort):,} records")

# Check Hispanic coding for this period
print(f"\nHispanic values (2005-2017):\n"
      f"{mort['hispanic'].value_counts(dropna=False).head(10)}")

# Filter to non-Hispanic: hispanic < 200 when present, or handle missing
# In NCHS coding: 100-199 = Non-Hispanic, 200+ = Hispanic
# Some records have hispanic=0 or NaN in early ICD-10 years
mort["hispanic_num"] = pd.to_numeric(mort["hispanic"], errors="coerce")

hisp_available = mort["hispanic_num"].notna()
print(f"\nHispanic field available: {hisp_available.sum():,}/{len(mort):,}")

# Filter to non-Hispanic (hispanic < 200 in NCHS coding)
non_hispanic_mask = mort["hispanic_num"].notna() & (mort["hispanic_num"] < 200)
mort = mort[non_hispanic_mask].copy()
print(f"\nAfter non-Hispanic filter: {len(mort):,} records")

# Filter to Black (race=2) and White (race=1)
mort = mort[mort["race"].isin([1, 2])].copy()
print(f"After Black/White filter: {len(mort):,} records")
print(f"  White (race=1): {(mort['race']==1).sum():,}")
print(f"  Black (race=2): {(mort['race']==2).sum():,}")

# Create age groups for abridged life table
def assign_age_group(age):
    """Assign single-year age to abridged life table age group."""
    if pd.isna(age) or age < 0:
        return np.nan
    if age < 1:
        return 0
    for i, cut in enumerate(AGE_CUTS[1:], 1):
        if age < cut:
            return i - 1
    return len(AGE_CUTS) - 1  # 85+

mort["age_group"] = mort["age"].apply(assign_age_group)
mort = mort.dropna(subset=["age_group"])
mort["age_group"] = mort["age_group"].astype(int)
print(f"After dropping missing age: {len(mort):,} records")

# Create geography variable
def assign_geography(fips):
    if fips == MILWAUKEE_FIPS:
        return "Milwaukee"
    elif fips == DANE_FIPS:
        return "Dane"
    else:
        return "Rest_of_WI"

mort["geography"] = mort["countyrs"].apply(assign_geography)

# --- 1d. Filter and prepare population ---
print("\n--- Filtering population data ---")

# Restrict to 2005-2017, Black & White
pop = pop[(pop["year"] >= 2005) & (pop["year"] <= 2017) &
          (pop["race"].isin([1, 2]))].copy()
print(f"After 2005-2017 and Black/White filter: {len(pop):,} records")

# Note: origin=9 means all origins (no Hispanic breakdown)
# This is a known limitation -- document it
print(f"\nOrigin values (should all be 9): "
      f"{pop['origin'].unique()}")

# Create age groups
def assign_age_group_pop(age):
    if age < 1:
        return 0
    for i, cut in enumerate(AGE_CUTS[1:], 1):
        if age < cut:
            return i - 1
    return len(AGE_CUTS) - 1  # 85+

pop["age_group"] = pop["age"].apply(assign_age_group_pop)

# Create geography variable
pop["geography"] = pop["fips"].apply(assign_geography)

# Aggregate population by year × race × sex × age_group × geography
pop_agg = (pop.groupby(["year", "race", "sex", "age_group", "geography"])["pop"]
           .sum()
           .reset_index())

# Also create statewide aggregation
pop_state = (pop.groupby(["year", "race", "sex", "age_group"])["pop"]
             .sum()
             .reset_index())
pop_state["geography"] = "Statewide"

pop_all = pd.concat([pop_agg, pop_state], ignore_index=True)
print(f"Population aggregated: {len(pop_all):,} rows")

# --- 1e. Aggregate mortality ---
print("\n--- Aggregating mortality ---")

mort_agg = (mort.groupby(["deathyear", "race", "sex", "age_group", "geography"])
            .size()
            .reset_index(name="deaths"))

# Statewide mortality
mort_state = (mort.groupby(["deathyear", "race", "sex", "age_group"])
              .size()
              .reset_index(name="deaths"))
mort_state["geography"] = "Statewide"

mort_all = pd.concat([mort_agg, mort_state], ignore_index=True)
print(f"Mortality aggregated: {len(mort_all):,} rows")

# --- 1f. Pool 3-year windows ---
print("\n--- Pooling 3-year windows ---")


def pool_three_year(center_year, mort_df, pop_df):
    """Pool mortality and population over a 3-year window.

    Both deaths and population are summed across all 3 years.
    The ratio sum(D)/sum(N) gives the average annual death rate
    because both numerator and denominator span the same 3 years.
    """
    y_start, y_end = center_year - 1, center_year + 1
    years = list(range(y_start, y_end + 1))

    d = (mort_df[mort_df["deathyear"].isin(years)]
         .groupby(["race", "sex", "age_group", "geography"])["deaths"]
         .sum()
         .reset_index())

    p = (pop_df[pop_df["year"].isin(years)]
         .groupby(["race", "sex", "age_group", "geography"])["pop"]
         .sum()
         .reset_index())

    merged = d.merge(p, on=["race", "sex", "age_group", "geography"], how="outer")
    merged["deaths"] = merged["deaths"].fillna(0)
    merged["pop"] = merged["pop"].fillna(0)
    merged["center_year"] = center_year
    return merged


pooled_frames = []
for cy in WINDOWS:
    pooled_frames.append(pool_three_year(cy, mort_all, pop_all))

pooled = pd.concat(pooled_frames, ignore_index=True)
print(f"Pooled dataset: {len(pooled):,} rows")
print(f"Center years: {sorted(pooled['center_year'].unique())}")

# Quick cell-size check for Dane County
dane_black = pooled[(pooled["geography"] == "Dane") &
                    (pooled["race"] == 2)]
print(f"\nDane County Black population check (smallest cells):")
print(dane_black.groupby("center_year")["pop"].sum().to_string())

# Save Phase 1 outputs
pooled.to_parquet(OUT_DIR / "pooled_data.parquet", index=False)
print("\nPhase 1 complete. Saved pooled_data.parquet")


# =================================================================
# PHASE 2: LIFE TABLE CONSTRUCTION & REPLICATION
# =================================================================
print("\n" + "=" * 60)
print("PHASE 2: LIFE TABLE CONSTRUCTION")
print("=" * 60)


def build_life_table(deaths, population, sex_code):
    """
    Build an abridged life table following Chiang (1968) / Preston et al. (2001).

    Parameters
    ----------
    deaths : array-like, length 19
        Death counts for each age group.
    population : array-like, length 19
        Person-years (average annual population × years pooled) for each group.
    sex_code : int
        1 = male, 2 = female. Used for infant _na_x values.

    Returns
    -------
    dict with life table columns and e0.
    """
    n_groups = len(AGE_CUTS)
    D = np.array(deaths, dtype=float)
    N = np.array(population, dtype=float)
    n = np.array(AGE_WIDTHS, dtype=float)

    # Handle zero populations: if N=0, rate is undefined -> set to 0
    M = np.where(N > 0, D / N, 0.0)

    # Handle zero deaths in cells: substitute 0.5
    D_adj = np.where((D == 0) & (N > 0), 0.5, D)
    M = np.where(N > 0, D_adj / N, 0.0)

    # Compute _na_x
    a = np.full(n_groups, 2.5)  # default for 5-year groups

    # Infant (<1): Coale-Demeny formulas from Preston et al. Table 3.3
    M0 = M[0]
    if sex_code == 1:  # male
        if M0 >= 0.107:
            a[0] = 0.330
        else:
            a[0] = 0.045 + 2.684 * M0
    else:  # female
        if M0 >= 0.107:
            a[0] = 0.350
        else:
            a[0] = 0.053 + 2.800 * M0

    # Age 1-4
    if sex_code == 1:
        if M0 >= 0.107:
            a[1] = 1.352
        else:
            a[1] = 1.651 - 2.816 * M0
    else:
        if M0 >= 0.107:
            a[1] = 1.361
        else:
            a[1] = 1.522 - 1.518 * M0

    # Open interval 85+
    if M[-1] > 0:
        a[-1] = 1.0 / M[-1]
    else:
        a[-1] = 5.0  # fallback

    # Compute _nq_x
    q = np.zeros(n_groups)
    for i in range(n_groups - 1):
        denom = 1.0 + (n[i] - a[i]) * M[i]
        if denom > 0 and M[i] > 0:
            q[i] = (n[i] * M[i]) / denom
            q[i] = min(q[i], 1.0)
        else:
            q[i] = 0.0
    q[-1] = 1.0  # everyone dies in open interval

    # Build life table
    RADIX = 100_000
    l = np.zeros(n_groups)
    d = np.zeros(n_groups)
    L = np.zeros(n_groups)

    l[0] = RADIX
    for i in range(n_groups):
        d[i] = l[i] * q[i]
        if i < n_groups - 1:
            l[i + 1] = l[i] - d[i]

        if i < n_groups - 1:
            L[i] = n[i] * (l[i] - d[i]) + a[i] * d[i]
        else:
            # Open interval
            if M[i] > 0:
                L[i] = l[i] / M[i]
            else:
                L[i] = l[i] * a[i]

    T = np.zeros(n_groups)
    T[-1] = L[-1]
    for i in range(n_groups - 2, -1, -1):
        T[i] = T[i + 1] + L[i]

    e = T / np.where(l > 0, l, 1)

    return {
        "age_group": list(range(n_groups)),
        "age_label": AGE_LABELS,
        "n": AGE_WIDTHS,
        "D": D.tolist(),
        "N": N.tolist(),
        "M": M.tolist(),
        "a": a.tolist(),
        "q": q.tolist(),
        "l": l.tolist(),
        "d": d.tolist(),
        "L": L.tolist(),
        "T": T.tolist(),
        "e": e.tolist(),
        "e0": e[0],
    }


def compute_le_for_group(df, race, sex, geography):
    """Extract deaths and population for a specific group and build life table."""
    mask = (df["race"] == race) & (df["sex"] == sex) & (df["geography"] == geography)
    sub = df[mask].sort_values("age_group")

    # Ensure all 19 age groups are present
    all_groups = pd.DataFrame({"age_group": range(len(AGE_CUTS))})
    sub = all_groups.merge(sub, on="age_group", how="left")
    sub["deaths"] = sub["deaths"].fillna(0)
    sub["pop"] = sub["pop"].fillna(0)

    deaths = sub["deaths"].values
    population = sub["pop"].values

    lt = build_life_table(deaths, population, sex)
    return lt


# --- Compute life expectancy for all groups across all windows ---
print("\n--- Computing life expectancies ---")

results = []
geographies = ["Statewide", "Milwaukee", "Dane", "Rest_of_WI"]
race_labels = {1: "White", 2: "Black"}
sex_labels = {1: "Male", 2: "Female"}

for cy in sorted(WINDOWS.keys()):
    cy_data = pooled[pooled["center_year"] == cy]
    for geo in geographies:
        for race in [1, 2]:
            for sex in [1, 2]:
                lt = compute_le_for_group(cy_data, race, sex, geo)
                total_deaths = sum(lt["D"])
                total_pop = sum(lt["N"])
                results.append({
                    "center_year": cy,
                    "geography": geo,
                    "race": race,
                    "race_label": race_labels[race],
                    "sex": sex,
                    "sex_label": sex_labels[sex],
                    "e0": lt["e0"],
                    "total_deaths": total_deaths,
                    "total_pop": total_pop,
                })

results_df = pd.DataFrame(results)

# --- Replication check against Roberts et al. (2019) ---
print("\n--- REPLICATION CHECK: Roberts et al. (2019) ---")
print("Target: Statewide Wisconsin, 3-year averages\n")

targets = [
    ("2014-16 (cy=2015)", 2015, "Male", "White", 77.75),
    ("2014-16 (cy=2015)", 2015, "Male", "Black", 70.41),
    ("2014-16 (cy=2015)", 2015, "Female", "White", 82.15),
    ("2014-16 (cy=2015)", 2015, "Female", "Black", 76.54),
]

print(f"{'Period':<22} {'Sex':<8} {'Race':<8} {'Paper':>8} {'Ours':>8} {'Diff':>8}")
print("-" * 62)

for label, cy, sex_l, race_l, paper_val in targets:
    mask = ((results_df["center_year"] == cy) &
            (results_df["geography"] == "Statewide") &
            (results_df["sex_label"] == sex_l) &
            (results_df["race_label"] == race_l))
    our_val = results_df.loc[mask, "e0"].values[0]
    diff = our_val - paper_val
    print(f"{label:<22} {sex_l:<8} {race_l:<8} {paper_val:8.2f} "
          f"{our_val:8.2f} {diff:+8.2f}")

# B-W gaps
print("\n--- B-W Life Expectancy Gaps (Statewide) ---")
print(f"{'Year':<8} {'Sex':<8} {'White LE':>10} {'Black LE':>10} "
      f"{'Gap':>8} {'Roberts Gap':>12}")

roberts_gaps = {
    (2015, "Male"): 7.34, (2015, "Female"): 5.61,
    (2008, "Male"): 6.96, (2008, "Female"): 5.82,
}

for cy in [2006, 2008, 2010, 2012, 2015, 2016]:
    for sex_l in ["Male", "Female"]:
        w_mask = ((results_df["center_year"] == cy) &
                  (results_df["geography"] == "Statewide") &
                  (results_df["sex_label"] == sex_l) &
                  (results_df["race_label"] == "White"))
        b_mask = ((results_df["center_year"] == cy) &
                  (results_df["geography"] == "Statewide") &
                  (results_df["sex_label"] == sex_l) &
                  (results_df["race_label"] == "Black"))
        w_le = results_df.loc[w_mask, "e0"].values[0]
        b_le = results_df.loc[b_mask, "e0"].values[0]
        gap = w_le - b_le
        roberts = roberts_gaps.get((cy, sex_l), None)
        r_str = f"{roberts:.2f}" if roberts else "--"
        print(f"{cy:<8} {sex_l:<8} {w_le:10.2f} {b_le:10.2f} "
              f"{gap:8.2f} {r_str:>12}")


# =================================================================
# PHASE 2B: BOOTSTRAP CONFIDENCE INTERVALS
# =================================================================
N_BOOT = 500
print("\n" + "=" * 60)
print("PHASE 2B: BOOTSTRAP CONFIDENCE INTERVALS")
print("=" * 60)
print(f"Running {N_BOOT} bootstrap replicates (Poisson resample of deaths)...")

boot_e0 = []  # list of dicts: center_year, geography, race, sex, e0
for b in range(N_BOOT):
    for cy in sorted(WINDOWS.keys()):
        cy_data = pooled[pooled["center_year"] == cy]
        for geo in geographies:
            for race in [1, 2]:
                for sex in [1, 2]:
                    sub = cy_data[(cy_data["race"] == race) &
                                 (cy_data["sex"] == sex) &
                                 (cy_data["geography"] == geo)].sort_values("age_group")
                    all_groups = pd.DataFrame({"age_group": range(len(AGE_CUTS))})
                    sub = all_groups.merge(sub, on="age_group", how="left")
                    sub["deaths"] = sub["deaths"].fillna(0)
                    sub["pop"] = sub["pop"].fillna(0)
                    D = sub["deaths"].values
                    N = sub["pop"].values
                    D_boot = np.random.poisson(D)  # resample deaths; N fixed
                    lt = build_life_table(D_boot, N, sex)
                    boot_e0.append({
                        "rep": b, "center_year": cy, "geography": geo,
                        "race": race, "sex": sex, "e0": lt["e0"],
                    })

boot_df = pd.DataFrame(boot_e0)
# Percentiles for e0 by (center_year, geography, race, sex)
ci = boot_df.groupby(["center_year", "geography", "race", "sex"])["e0"].agg(
    e0_lo=lambda x: np.percentile(x, 2.5),
    e0_hi=lambda x: np.percentile(x, 97.5),
).reset_index()
results_df = results_df.merge(
    ci,
    on=["center_year", "geography", "race", "sex"],
    how="left",
)
# Gap CIs: in each rep, gap = e0_white - e0_black; then percentile
gap_boot = []
for b in range(N_BOOT):
    bdat = boot_df[boot_df["rep"] == b]
    for cy in sorted(WINDOWS.keys()):
        for geo in geographies:
            for sex in [1, 2]:
                w = bdat[(bdat["center_year"] == cy) & (bdat["geography"] == geo) &
                         (bdat["sex"] == sex) & (bdat["race"] == 1)]
                bl = bdat[(bdat["center_year"] == cy) & (bdat["geography"] == geo) &
                          (bdat["sex"] == sex) & (bdat["race"] == 2)]
                if len(w) > 0 and len(bl) > 0:
                    gap_boot.append({
                        "rep": b, "center_year": cy, "geography": geo, "sex": sex,
                        "gap": w["e0"].values[0] - bl["e0"].values[0],
                    })
gap_boot_df = pd.DataFrame(gap_boot)
gap_ci = gap_boot_df.groupby(["center_year", "geography", "sex"])["gap"].agg(
    gap_lo=lambda x: np.percentile(x, 2.5),
    gap_hi=lambda x: np.percentile(x, 97.5),
).reset_index()
gap_ci["sex_label"] = gap_ci["sex"].map({1: "Male", 2: "Female"})

# Change over time (2006 -> 2016): bootstrap distribution of Black LE change and gap change
cy_early, cy_late = 2006, 2016
change_black_le = []
change_gap = []
for b in range(N_BOOT):
    bdat = boot_df[boot_df["rep"] == b]
    gdat = gap_boot_df[gap_boot_df["rep"] == b]
    for geo in geographies:
        for sex in [1, 2]:
            e0_b_early = bdat[(bdat["center_year"] == cy_early) & (bdat["geography"] == geo) &
                              (bdat["race"] == 2) & (bdat["sex"] == sex)]
            e0_b_late = bdat[(bdat["center_year"] == cy_late) & (bdat["geography"] == geo) &
                             (bdat["race"] == 2) & (bdat["sex"] == sex)]
            if len(e0_b_early) > 0 and len(e0_b_late) > 0:
                change_black_le.append({
                    "rep": b, "geography": geo, "sex": sex,
                    "black_le_change": e0_b_late["e0"].values[0] - e0_b_early["e0"].values[0],
                })
            g_early = gdat[(gdat["center_year"] == cy_early) & (gdat["geography"] == geo) &
                          (gdat["sex"] == sex)]
            g_late = gdat[(gdat["center_year"] == cy_late) & (gdat["geography"] == geo) &
                         (gdat["sex"] == sex)]
            if len(g_early) > 0 and len(g_late) > 0:
                change_gap.append({
                    "rep": b, "geography": geo, "sex": sex,
                    "gap_change": g_late["gap"].values[0] - g_early["gap"].values[0],
                })
change_le_df = pd.DataFrame(change_black_le)
change_gap_df = pd.DataFrame(change_gap)
change_le_ci = change_le_df.groupby(["geography", "sex"])["black_le_change"].agg(
    black_le_change_lo=lambda x: np.percentile(x, 2.5),
    black_le_change_hi=lambda x: np.percentile(x, 97.5),
).reset_index()
change_gap_ci = change_gap_df.groupby(["geography", "sex"])["gap_change"].agg(
    gap_change_lo=lambda x: np.percentile(x, 2.5),
    gap_change_hi=lambda x: np.percentile(x, 97.5),
).reset_index()
# Point estimates from results_df
change_pts = []
for geo in geographies:
    for sex in [1, 2]:
        early_mask = ((results_df["center_year"] == cy_early) &
                      (results_df["geography"] == geo) &
                      (results_df["race"] == 2) & (results_df["sex"] == sex))
        late_mask = ((results_df["center_year"] == cy_late) &
                     (results_df["geography"] == geo) &
                     (results_df["race"] == 2) & (results_df["sex"] == sex))
        early_b = results_df.loc[early_mask, "e0"]
        late_b = results_df.loc[late_mask, "e0"]
        w_early = results_df.loc[(results_df["center_year"] == cy_early) & (results_df["geography"] == geo) &
                                 (results_df["sex"] == sex) & (results_df["race"] == 1), "e0"].values
        b_early = results_df.loc[(results_df["center_year"] == cy_early) & (results_df["geography"] == geo) &
                                 (results_df["sex"] == sex) & (results_df["race"] == 2), "e0"].values
        w_late = results_df.loc[(results_df["center_year"] == cy_late) & (results_df["geography"] == geo) &
                                (results_df["sex"] == sex) & (results_df["race"] == 1), "e0"].values
        b_late = results_df.loc[(results_df["center_year"] == cy_late) & (results_df["geography"] == geo) &
                                (results_df["sex"] == sex) & (results_df["race"] == 2), "e0"].values
        pt_le = (late_b.values[0] - early_b.values[0]) if len(late_b) and len(early_b) else np.nan
        pt_gap = ((w_late[0] - b_late[0]) - (w_early[0] - b_early[0])) if all(len(x) > 0 for x in [w_late, b_late, w_early, b_early]) else np.nan
        change_pts.append({
            "geography": geo, "sex": sex,
            "black_le_change": round(pt_le, 3) if not np.isnan(pt_le) else None,
            "gap_change": round(pt_gap, 3) if not np.isnan(pt_gap) else None,
        })
change_pts_df = pd.DataFrame(change_pts)
change_ci = change_pts_df.merge(
    change_le_ci[["geography", "sex", "black_le_change_lo", "black_le_change_hi"]],
    on=["geography", "sex"], how="left"
).merge(
    change_gap_ci[["geography", "sex", "gap_change_lo", "gap_change_hi"]],
    on=["geography", "sex"], how="left"
)
change_ci["sex_label"] = change_ci["sex"].map({1: "Male", 2: "Female"})
change_ci.to_csv(OUT_DIR / "tables" / "change_ci.csv", index=False)

# Dane County uncertainty: how certain are we that Black mortality worsened?
print("\n--- Uncertainty: Change in Black LE and B-W Gap (2006 -> 2016) ---")
for _, r in change_ci.iterrows():
    geo, sex_l = r["geography"], r["sex_label"]
    le_ch = r.get("black_le_change") if pd.notna(r.get("black_le_change")) else 0
    le_lo, le_hi = r.get("black_le_change_lo"), r.get("black_le_change_hi")
    gap_ch = r.get("gap_change") if pd.notna(r.get("gap_change")) else 0
    gap_lo, gap_hi = r.get("gap_change_lo"), r.get("gap_change_hi")
    le_str = f"{le_ch:+.2f}" if pd.notna(le_ch) else "?"
    le_ci_str = f"{le_lo:.2f} to {le_hi:.2f}" if pd.notna(le_lo) and pd.notna(le_hi) else "?"
    gap_str = f"{gap_ch:+.2f}" if pd.notna(gap_ch) else "?"
    gap_ci_str = f"{gap_lo:.2f} to {gap_hi:.2f}" if pd.notna(gap_lo) and pd.notna(gap_hi) else "?"
    le_sig = " (CI excludes 0)" if pd.notna(le_lo) and pd.notna(le_hi) and (le_lo > 0 or le_hi < 0) else ""
    gap_sig = " (CI excludes 0)" if pd.notna(gap_lo) and pd.notna(gap_hi) and (gap_lo > 0 or gap_hi < 0) else ""
    print(f"  {geo} {sex_l}: Black LE change = {le_str} (95% CI {le_ci_str}){le_sig}; "
          f"Gap change = {gap_str} (95% CI {gap_ci_str}){gap_sig}")
dane_male = change_ci[(change_ci["geography"] == "Dane") & (change_ci["sex_label"] == "Male")].iloc[0]
lo, hi = dane_male["black_le_change_lo"], dane_male["black_le_change_hi"]
if pd.isna(lo) or pd.isna(hi):
    print("\n  DANE COUNTY MALE: CIs not available.")
elif hi < 0:
    print("\n  DANE COUNTY MALE: 95% CI for Black LE change lies entirely below 0 -- "
          "decline is statistically significant.")
elif lo > 0:
    print("\n  DANE COUNTY MALE: 95% CI lies entirely above 0 -- "
          "data consistent with no decline or improvement; point estimate of decline is uncertain.")
else:
    print("\n  DANE COUNTY MALE: 95% CI includes 0 -- "
          "decline is not statistically significant; interpret with caution (small Black male population).")

# Save CI summary for paper/tables
results_df.to_parquet(OUT_DIR / "life_expectancy_results.parquet", index=False)
le_ci_wide = results_df[["center_year", "geography", "race_label", "sex_label",
                          "e0", "e0_lo", "e0_hi"]].copy()
le_ci_wide.to_csv(OUT_DIR / "tables" / "le_with_ci.csv", index=False)
gap_ci.to_csv(OUT_DIR / "tables" / "gap_ci.csv", index=False)
print(f"Bootstrap complete. Saved le_with_ci.csv, gap_ci.csv, change_ci.csv.")


# =================================================================
# PHASE 3: GEOGRAPHIC EXTENSION
# =================================================================
print("\n" + "=" * 60)
print("PHASE 3: GEOGRAPHIC EXTENSION")
print("=" * 60)

# Show LE and gaps for all geographies
print("\n--- Life Expectancy by Geography (2016 = 2015-2017) ---")
print(f"{'Geography':<15} {'Sex':<8} {'White LE':>10} {'Black LE':>10} "
      f"{'Gap':>8} {'B Deaths':>10} {'B Pop':>10}")
print("-" * 80)

for geo in geographies:
    for sex_l in ["Male", "Female"]:
        w_mask = ((results_df["center_year"] == 2016) &
                  (results_df["geography"] == geo) &
                  (results_df["sex_label"] == sex_l) &
                  (results_df["race_label"] == "White"))
        b_mask = ((results_df["center_year"] == 2016) &
                  (results_df["geography"] == geo) &
                  (results_df["sex_label"] == sex_l) &
                  (results_df["race_label"] == "Black"))
        w_le = results_df.loc[w_mask, "e0"].values[0]
        b_le = results_df.loc[b_mask, "e0"].values[0]
        gap = w_le - b_le
        b_deaths = results_df.loc[b_mask, "total_deaths"].values[0]
        b_pop = results_df.loc[b_mask, "total_pop"].values[0]
        print(f"{geo:<15} {sex_l:<8} {w_le:10.2f} {b_le:10.2f} "
              f"{gap:8.2f} {b_deaths:10.0f} {b_pop:10.0f}")


# Show gap trends over time by geography
print("\n--- B-W Gap Trends by Geography ---")
print(f"{'Year':<6} {'Sex':<7} {'Statewide':>10} {'Milwaukee':>10} "
      f"{'Dane':>10} {'Rest_of_WI':>11}")
print("-" * 60)

for cy in [2006, 2008, 2010, 2012, 2015, 2016]:
    for sex_l in ["Male", "Female"]:
        vals = []
        for geo in geographies:
            w = results_df.loc[(results_df["center_year"] == cy) &
                               (results_df["geography"] == geo) &
                               (results_df["sex_label"] == sex_l) &
                               (results_df["race_label"] == "White"), "e0"]
            b = results_df.loc[(results_df["center_year"] == cy) &
                               (results_df["geography"] == geo) &
                               (results_df["sex_label"] == sex_l) &
                               (results_df["race_label"] == "Black"), "e0"]
            if len(w) > 0 and len(b) > 0:
                vals.append(f"{w.values[0] - b.values[0]:10.2f}")
            else:
                vals.append(f"{'--':>10}")
        print(f"{cy:<6} {sex_l:<7} {''.join(vals)}")


# =================================================================
# PHASE 3B: DECOMPOSITION & COUNTERFACTUAL ANALYSIS
# =================================================================
print("\n" + "=" * 60)
print("PHASE 3B: DECOMPOSITION & COUNTERFACTUAL ANALYSIS")
print("=" * 60)


def get_age_rates(pooled_df, cy, race, sex, geography):
    """Extract age-specific death rates (Mx) for a group from pooled data."""
    mask = ((pooled_df["center_year"] == cy) &
            (pooled_df["race"] == race) &
            (pooled_df["sex"] == sex) &
            (pooled_df["geography"] == geography))
    sub = pooled_df[mask].sort_values("age_group")
    all_groups = pd.DataFrame({"age_group": range(len(AGE_CUTS))})
    sub = all_groups.merge(sub, on="age_group", how="left")
    sub["deaths"] = sub["deaths"].fillna(0)
    sub["pop"] = sub["pop"].fillna(0)
    return sub


def counterfactual_statewide_black_e0(pooled_df, cy, sex,
                                       replace_geo, donor_geo):
    """Compute statewide Black e0 if `replace_geo` had `donor_geo` mortality.

    Replaces the age-specific death rates of Black people in `replace_geo`
    with those from `donor_geo`, then reconstructs the statewide Black
    life table from the counterfactual deaths and actual populations.
    """
    geos = ["Milwaukee", "Dane", "Rest_of_WI"]

    total_deaths = np.zeros(len(AGE_CUTS))
    total_pop = np.zeros(len(AGE_CUTS))

    donor = get_age_rates(pooled_df, cy, 2, sex, donor_geo)
    donor_mx = np.where(donor["pop"].values > 0,
                        donor["deaths"].values / donor["pop"].values, 0.0)

    for geo in geos:
        sub = get_age_rates(pooled_df, cy, 2, sex, geo)
        pop_g = sub["pop"].values

        if geo == replace_geo:
            deaths_g = donor_mx * pop_g
        else:
            deaths_g = sub["deaths"].values

        total_deaths += deaths_g
        total_pop += pop_g

    lt = build_life_table(total_deaths, total_pop, sex)
    return lt["e0"]


def counterfactual_geo_white_e0(pooled_df, cy, sex,
                                 target_geo, donor_geo):
    """Compute White e0 in `target_geo` if Whites had `donor_geo` mortality."""
    target = get_age_rates(pooled_df, cy, 1, sex, target_geo)
    donor = get_age_rates(pooled_df, cy, 1, sex, donor_geo)

    donor_mx = np.where(donor["pop"].values > 0,
                        donor["deaths"].values / donor["pop"].values, 0.0)
    cf_deaths = donor_mx * target["pop"].values

    lt = build_life_table(cf_deaths, target["pop"].values, sex)
    return lt["e0"]


# --- Population composition of statewide Black population ---
print("\n--- Black Population Share by Geography ---")
print(f"{'Year':<8} {'Sex':<8} {'Milwaukee':>12} {'Dane':>12} {'Rest_of_WI':>12}")
print("-" * 55)

for cy in [2006, 2010, 2016]:
    for sex in [1, 2]:
        sex_l = sex_labels[sex]
        shares = {}
        total = 0
        for geo in ["Milwaukee", "Dane", "Rest_of_WI"]:
            sub = get_age_rates(pooled, cy, 2, sex, geo)
            geo_pop = sub["pop"].sum()
            shares[geo] = geo_pop
            total += geo_pop
        pcts = {g: 100 * v / total for g, v in shares.items()}
        print(f"{cy:<8} {sex_l:<8} {pcts['Milwaukee']:11.1f}% "
              f"{pcts['Dane']:11.1f}% {pcts['Rest_of_WI']:11.1f}%")


# --- Counterfactual 1: What if Milwaukee Black had Rest-of-WI mortality? ---
print("\n--- Counterfactual 1: Milwaukee Black → Rest-of-WI Black Mortality ---")
print("(What would statewide B-W gap be if Black Milwaukeeans had Rest-of-WI "
      "Black death rates?)\n")

print(f"{'Year':<8} {'Sex':<8} {'Actual Gap':>12} {'CF Gap':>12} "
      f"{'Reduction':>12} {'Actual B e0':>12} {'CF B e0':>12}")
print("-" * 75)

cf1_results = []
for cy in [2006, 2010, 2016]:
    for sex in [1, 2]:
        sex_l = sex_labels[sex]
        actual_w = results_df.loc[(results_df["center_year"] == cy) &
                                  (results_df["geography"] == "Statewide") &
                                  (results_df["sex"] == sex) &
                                  (results_df["race"] == 1), "e0"].values[0]
        actual_b = results_df.loc[(results_df["center_year"] == cy) &
                                  (results_df["geography"] == "Statewide") &
                                  (results_df["sex"] == sex) &
                                  (results_df["race"] == 2), "e0"].values[0]
        actual_gap = actual_w - actual_b

        cf_b = counterfactual_statewide_black_e0(pooled, cy, sex,
                                                   "Milwaukee", "Rest_of_WI")
        cf_gap = actual_w - cf_b
        reduction = actual_gap - cf_gap

        cf1_results.append({
            "center_year": cy, "sex": sex_l,
            "actual_gap": round(actual_gap, 2),
            "cf_gap": round(cf_gap, 2),
            "reduction": round(reduction, 2),
            "actual_b_e0": round(actual_b, 2),
            "cf_b_e0": round(cf_b, 2),
        })
        print(f"{cy:<8} {sex_l:<8} {actual_gap:12.2f} {cf_gap:12.2f} "
              f"{reduction:12.2f} {actual_b:12.2f} {cf_b:12.2f}")


# --- Counterfactual 2: Milwaukee Black → Dane County Black Mortality ---
print("\n--- Counterfactual 2: Milwaukee Black → Dane County Black Mortality ---")
print("(What would statewide B-W gap be if Black Milwaukeeans had Dane County "
      "Black death rates?)\n")

print(f"{'Year':<8} {'Sex':<8} {'Actual Gap':>12} {'CF Gap':>12} "
      f"{'Reduction':>12} {'Actual B e0':>12} {'CF B e0':>12}")
print("-" * 75)

cf2_results = []
for cy in [2006, 2010, 2016]:
    for sex in [1, 2]:
        sex_l = sex_labels[sex]
        actual_w = results_df.loc[(results_df["center_year"] == cy) &
                                  (results_df["geography"] == "Statewide") &
                                  (results_df["sex"] == sex) &
                                  (results_df["race"] == 1), "e0"].values[0]
        actual_b = results_df.loc[(results_df["center_year"] == cy) &
                                  (results_df["geography"] == "Statewide") &
                                  (results_df["sex"] == sex) &
                                  (results_df["race"] == 2), "e0"].values[0]
        actual_gap = actual_w - actual_b

        cf_b = counterfactual_statewide_black_e0(pooled, cy, sex,
                                                   "Milwaukee", "Dane")
        cf_gap = actual_w - cf_b
        reduction = actual_gap - cf_gap

        cf2_results.append({
            "center_year": cy, "sex": sex_l,
            "actual_gap": round(actual_gap, 2),
            "cf_gap": round(cf_gap, 2),
            "reduction": round(reduction, 2),
            "actual_b_e0": round(actual_b, 2),
            "cf_b_e0": round(cf_b, 2),
        })
        print(f"{cy:<8} {sex_l:<8} {actual_gap:12.2f} {cf_gap:12.2f} "
              f"{reduction:12.2f} {actual_b:12.2f} {cf_b:12.2f}")


# --- Counterfactual 3: Dane White → Rest-of-WI White Mortality ---
print("\n--- Counterfactual 3: Dane County White → Rest-of-WI White Mortality ---")
print("(What would Dane County B-W gap be if Dane Whites had Rest-of-WI White "
      "death rates?)\n")

print(f"{'Year':<8} {'Sex':<8} {'Actual Gap':>12} {'CF Gap':>12} "
      f"{'Reduction':>12} {'Actual W e0':>12} {'CF W e0':>12}")
print("-" * 75)

cf3_results = []
for cy in [2006, 2010, 2016]:
    for sex in [1, 2]:
        sex_l = sex_labels[sex]
        actual_w = results_df.loc[(results_df["center_year"] == cy) &
                                  (results_df["geography"] == "Dane") &
                                  (results_df["sex"] == sex) &
                                  (results_df["race"] == 1), "e0"].values[0]
        actual_b = results_df.loc[(results_df["center_year"] == cy) &
                                  (results_df["geography"] == "Dane") &
                                  (results_df["sex"] == sex) &
                                  (results_df["race"] == 2), "e0"].values[0]
        actual_gap = actual_w - actual_b

        cf_w = counterfactual_geo_white_e0(pooled, cy, sex, "Dane", "Rest_of_WI")
        cf_gap = cf_w - actual_b
        reduction = actual_gap - cf_gap

        cf3_results.append({
            "center_year": cy, "sex": sex_l,
            "actual_gap": round(actual_gap, 2),
            "cf_gap": round(cf_gap, 2),
            "reduction": round(reduction, 2),
            "actual_w_e0": round(actual_w, 2),
            "cf_w_e0": round(cf_w, 2),
        })
        print(f"{cy:<8} {sex_l:<8} {actual_gap:12.2f} {cf_gap:12.2f} "
              f"{reduction:12.2f} {actual_w:12.2f} {cf_w:12.2f}")


# Save counterfactual results
cf1_df = pd.DataFrame(cf1_results)
cf2_df = pd.DataFrame(cf2_results)
cf3_df = pd.DataFrame(cf3_results)
cf1_df.to_csv(OUT_DIR / "tables" / "cf1_milwaukee_to_restofwi.csv", index=False)
cf2_df.to_csv(OUT_DIR / "tables" / "cf2_milwaukee_to_dane.csv", index=False)
cf3_df.to_csv(OUT_DIR / "tables" / "cf3_dane_white_to_restofwi.csv", index=False)
print("\nSaved counterfactual tables to output/tables/")


# =================================================================
# PHASE 3C: STATEWIDE GAP DECOMPOSITION
# =================================================================
print("\n" + "=" * 60)
print("PHASE 3C: STATEWIDE GAP DECOMPOSITION")
print("=" * 60)
print("Framework: Gap_SW = Sum(pi_g * gap_g) + White_comp + residual")
print("  pi_g  = Black pop share in geography g")
print("  gap_g = local B-W LE gap in geography g")
print("  White_comp = adjustment for differential White distribution")

sub_geos = ["Milwaukee", "Dane", "Rest_of_WI"]
decomp_rows = []

for cy in sorted(WINDOWS.keys()):
    for sex in [1, 2]:
        sex_l = sex_labels[sex]

        e0_w_sw = results_df.loc[
            (results_df["center_year"] == cy) &
            (results_df["geography"] == "Statewide") &
            (results_df["sex"] == sex) &
            (results_df["race"] == 1), "e0"].values[0]
        e0_b_sw = results_df.loc[
            (results_df["center_year"] == cy) &
            (results_df["geography"] == "Statewide") &
            (results_df["sex"] == sex) &
            (results_df["race"] == 2), "e0"].values[0]
        actual_gap = e0_w_sw - e0_b_sw

        black_pops = {}
        white_pops = {}
        for geo in sub_geos:
            b_sub = get_age_rates(pooled, cy, 2, sex, geo)
            black_pops[geo] = b_sub["pop"].sum()
            w_sub = get_age_rates(pooled, cy, 1, sex, geo)
            white_pops[geo] = w_sub["pop"].sum()

        total_black = sum(black_pops.values())
        total_white = sum(white_pops.values())
        pi = {g: black_pops[g] / total_black for g in sub_geos}
        omega = {g: white_pops[g] / total_white for g in sub_geos}

        local_e0_w = {}
        local_e0_b = {}
        local_gaps = {}
        for geo in sub_geos:
            e0_w_g = results_df.loc[
                (results_df["center_year"] == cy) &
                (results_df["geography"] == geo) &
                (results_df["sex"] == sex) &
                (results_df["race"] == 1), "e0"].values[0]
            e0_b_g = results_df.loc[
                (results_df["center_year"] == cy) &
                (results_df["geography"] == geo) &
                (results_df["sex"] == sex) &
                (results_df["race"] == 2), "e0"].values[0]
            local_e0_w[geo] = e0_w_g
            local_e0_b[geo] = e0_b_g
            local_gaps[geo] = e0_w_g - e0_b_g

        contribs = {g: pi[g] * local_gaps[g] for g in sub_geos}
        place_total = sum(contribs.values())

        # White composition: actual statewide White e0 minus
        # what you'd get weighting local White e0 by Black shares
        e0_w_bweighted = sum(pi[g] * local_e0_w[g] for g in sub_geos)
        white_comp_adj = e0_w_sw - e0_w_bweighted

        # Aggregation nonlinearity (e0 isn't exactly a weighted avg)
        e0_b_approx = sum(pi[g] * local_e0_b[g] for g in sub_geos)
        nonlinearity = e0_b_approx - e0_b_sw

        # Counterfactual: gap if Black pop distributed like White pop
        place_if_same_dist = sum(omega[g] * local_gaps[g] for g in sub_geos)
        composition_effect = place_total - place_if_same_dist

        decomp_rows.append({
            "center_year": cy, "sex": sex_l,
            "actual_gap": round(actual_gap, 3),
            "MKE_pi": round(pi["Milwaukee"], 4),
            "Dane_pi": round(pi["Dane"], 4),
            "RoW_pi": round(pi["Rest_of_WI"], 4),
            "MKE_omega": round(omega["Milwaukee"], 4),
            "Dane_omega": round(omega["Dane"], 4),
            "RoW_omega": round(omega["Rest_of_WI"], 4),
            "MKE_local_gap": round(local_gaps["Milwaukee"], 3),
            "Dane_local_gap": round(local_gaps["Dane"], 3),
            "RoW_local_gap": round(local_gaps["Rest_of_WI"], 3),
            "MKE_contrib": round(contribs["Milwaukee"], 3),
            "Dane_contrib": round(contribs["Dane"], 3),
            "RoW_contrib": round(contribs["Rest_of_WI"], 3),
            "place_total": round(place_total, 3),
            "white_comp_adj": round(white_comp_adj, 3),
            "nonlinearity": round(nonlinearity, 3),
            "decomp_total": round(place_total + white_comp_adj + nonlinearity, 3),
            "place_if_same_dist": round(place_if_same_dist, 3),
            "composition_effect": round(composition_effect, 3),
        })

decomp_df = pd.DataFrame(decomp_rows)
# Add 95% CI for local gaps to decomposition table
gap_ci_for_decomp = gap_ci.copy()
gap_ci_for_decomp["sex_label"] = gap_ci_for_decomp["sex"].map({1: "Male", 2: "Female"})
gap_wide = gap_ci_for_decomp.pivot_table(
    index=["center_year", "sex_label"], columns="geography",
    values=["gap_lo", "gap_hi"], aggfunc="first"
)
gap_wide.columns = [f"{geo}_{c}" for c, geo in gap_wide.columns]
gap_wide = gap_wide.reset_index()
decomp_df = decomp_df.merge(gap_wide, left_on=["center_year", "sex"],
                            right_on=["center_year", "sex_label"], how="left").drop(
    columns=["sex_label"], errors="ignore")
decomp_df.to_csv(OUT_DIR / "tables" / "table4_gap_decomposition.csv", index=False)

print("\n--- Statewide B-W Gap Decomposition ---")
print(f"{'Year':<6} {'Sex':<7} {'Gap':>6} {'MKE':>6} {'Dane':>6} {'RoW':>6} "
      f"{'W.Comp':>7} {'Resid':>6} {'Total':>6}")
print("-" * 58)
for _, r in decomp_df.iterrows():
    print(f"{int(r['center_year']):<6} {r['sex']:<7} "
          f"{r['actual_gap']:6.2f} {r['MKE_contrib']:6.2f} "
          f"{r['Dane_contrib']:6.2f} {r['RoW_contrib']:6.2f} "
          f"{r['white_comp_adj']:7.2f} {r['nonlinearity']:6.2f} "
          f"{r['decomp_total']:6.2f}")

print("\n--- Composition Effect Summary ---")
print("(How much does Black geographic concentration add to the gap?)")
print(f"{'Year':<6} {'Sex':<7} {'Weighted':>10} {'If same':>10} {'Comp. eff':>10}")
print("-" * 48)
for _, r in decomp_df[decomp_df["center_year"].isin([2006, 2010, 2016])].iterrows():
    print(f"{int(r['center_year']):<6} {r['sex']:<7} "
          f"{r['place_total']:10.2f} {r['place_if_same_dist']:10.2f} "
          f"{r['composition_effect']:10.2f}")

# --- Figure 7: Stacked decomposition of statewide gap ---
fig, axes = plt.subplots(1, 2, figsize=(14, 7), sharey=True)

decomp_bar_colors = {"Milwaukee": "#c5050c", "Dane": "#0479a8",
                     "Rest of WI": "#7b6888", "White comp.": "#f0ab00"}

for idx, (panel_title, sex_str) in enumerate([("Males", "Male"),
                                               ("Females", "Female")]):
    ax = axes[idx]
    sdf = decomp_df[decomp_df["sex"] == sex_str].sort_values("center_year")
    yrs = sdf["center_year"].values.astype(float)

    mke_c = sdf["MKE_contrib"].values
    dane_c = sdf["Dane_contrib"].values
    row_c = sdf["RoW_contrib"].values
    wcomp = sdf["white_comp_adj"].values
    actual = sdf["actual_gap"].values

    bw = 0.6
    bottom = np.zeros(len(yrs))

    ax.bar(yrs, mke_c, bw, color=decomp_bar_colors["Milwaukee"],
           label="Milwaukee", bottom=bottom)
    bottom += mke_c

    ax.bar(yrs, dane_c, bw, color=decomp_bar_colors["Dane"],
           label="Dane County", bottom=bottom)
    bottom += dane_c

    ax.bar(yrs, row_c, bw, color=decomp_bar_colors["Rest of WI"],
           label="Rest of WI", bottom=bottom)
    bottom += row_c

    ax.bar(yrs, wcomp, bw, color=decomp_bar_colors["White comp."],
           label="White composition", bottom=bottom, alpha=0.7)

    ax.plot(yrs, actual, "ko-", markersize=5, linewidth=1.5,
            label="Actual statewide gap", zorder=5)

    # Annotate final bar with contribution values
    last = -1
    ann_y = 0
    for val, lbl in [(mke_c[last], "MKE"), (dane_c[last], "Dane"),
                     (row_c[last], "RoW")]:
        mid = ann_y + val / 2
        if val > 0.4:
            ax.text(yrs[last], mid, f"{val:.1f}", ha="center", va="center",
                    fontsize=8, fontweight="bold", color="white")
        ann_y += val

    ax.set_xlabel("Year (center of 3-year window)")
    if idx == 0:
        ax.set_ylabel("Contribution to statewide B-W gap (years)")
    ax.set_title(panel_title, fontsize=13)
    ax.legend(fontsize=8.5, loc="upper left")
    ax.set_xlim(2005, 2017)
    ax.axhline(y=0, color="gray", linewidth=0.5)

fig.suptitle("Decomposition of the Statewide Black-White Life Expectancy Gap\n"
             "Contribution = Black pop. share (\u03c0) \u00d7 local B-W gap",
             fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(FIG_DIR / "fig7_gap_decomposition_stacked.pdf")
fig.savefig(FIG_DIR / "fig7_gap_decomposition_stacked.png")
plt.close()
print("Saved Figure 7: Gap decomposition stacked bar chart")

# --- Figure 8: Decomposition components (shares and local gaps) with 95% CI on Panel B ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

_geo_clr = {"Milwaukee": "#c5050c", "Dane": "#0479a8", "Rest_of_WI": "#7b6888"}
male_decomp = decomp_df[decomp_df["sex"] == "Male"].sort_values("center_year")
gap_ci_male_f8 = gap_ci[gap_ci["sex"] == 1]

ax = axes[0]
for geo, prefix in [("Milwaukee", "MKE"), ("Dane", "Dane"),
                     ("Rest_of_WI", "RoW")]:
    ax.plot(male_decomp["center_year"],
            male_decomp[f"{prefix}_pi"] * 100,
            color=_geo_clr[geo], marker="o", markersize=4,
            label=geo.replace("_", " "))
ax.set_xlabel("Year (center of 3-year window)")
ax.set_ylabel("Share of statewide Black population (%)")
ax.set_title("A. Black Population Shares (Males)")
ax.legend(fontsize=10)
ax.set_xlim(2005, 2017)
ax.set_ylim(0, 75)

ax = axes[1]
for geo, prefix in [("Milwaukee", "MKE"), ("Dane", "Dane"),
                     ("Rest_of_WI", "RoW")]:
    yrs = male_decomp["center_year"].values
    gaps = male_decomp[f"{prefix}_local_gap"].values
    lo_arr, hi_arr = [], []
    for cy in yrs:
        g = gap_ci_male_f8[(gap_ci_male_f8["center_year"] == cy) & (gap_ci_male_f8["geography"] == geo)]
        if len(g) > 0:
            lo_arr.append(g["gap_lo"].values[0])
            hi_arr.append(g["gap_hi"].values[0])
        else:
            idx = list(yrs).index(cy)
            lo_arr.append(gaps[idx])
            hi_arr.append(gaps[idx])
    lo_arr = np.array(lo_arr)
    hi_arr = np.array(hi_arr)
    ax.fill_between(yrs, lo_arr, hi_arr, color=_geo_clr[geo], alpha=0.2)
    ax.plot(yrs, gaps, color=_geo_clr[geo], marker="o", markersize=4,
            label=geo.replace("_", " "), linewidth=2 if geo == "Dane" else 1.5)
ax.set_xlabel("Year (center of 3-year window)")
ax.set_ylabel("Local B-W life expectancy gap (years)")
ax.set_title("B. Local B-W Gaps (Males; 95% CI shaded; Dane wider)")
ax.legend(fontsize=10)
ax.set_xlim(2005, 2017)

fig.suptitle("Components of the Gap Decomposition:\n"
             "Statewide Gap \u2248 \u03a3 (Population Share \u00d7 Local Gap)",
             fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(FIG_DIR / "fig8_decomp_components.pdf")
fig.savefig(FIG_DIR / "fig8_decomp_components.png")
plt.close()
print("Saved Figure 8: Decomposition components (shares and local gaps)")

print(f"\nDecomposition saved to {OUT_DIR / 'tables' / 'table4_gap_decomposition.csv'}")


# =================================================================
# PHASE 4: PUBLICATION-READY FIGURES
# =================================================================
print("\n" + "=" * 60)
print("PHASE 4: FIGURES")
print("=" * 60)

# --- Figure 1: Male LE trends (replicating Roberts Fig 1) ---
fig, ax = plt.subplots(figsize=(10, 6))
years = sorted(WINDOWS.keys())

for race, color, label in [(1, WHITE_POP, "NH-White"),
                            (2, BLACK_POP, "NH-Black")]:
    mask = ((results_df["geography"] == "Statewide") &
            (results_df["sex"] == 1) &
            (results_df["race"] == race))
    sub = results_df[mask].sort_values("center_year")
    ax.plot(sub["center_year"], sub["e0"], color=color,
            marker="o", markersize=4, label=f"{label} Males, Wisconsin")

ax.set_xlabel("Year (center of 3-year window)")
ax.set_ylabel("Life expectancy at birth (years)")
ax.set_title("Life Expectancy for Non-Hispanic Black and White Males\n"
             "Wisconsin, 2006–2016")
ax.legend(loc="lower right")
ax.set_xlim(2005, 2017)
ax.yaxis.set_major_locator(mticker.MultipleLocator(2))
fig.savefig(FIG_DIR / "fig1_male_le_trends_statewide.pdf")
fig.savefig(FIG_DIR / "fig1_male_le_trends_statewide.png")
plt.close()
print("Saved Figure 1: Male LE trends (statewide)")

# --- Figure 2: Female LE trends (replicating Roberts Fig 2) ---
fig, ax = plt.subplots(figsize=(10, 6))

for race, color, label in [(1, WHITE_POP, "NH-White"),
                            (2, BLACK_POP, "NH-Black")]:
    mask = ((results_df["geography"] == "Statewide") &
            (results_df["sex"] == 2) &
            (results_df["race"] == race))
    sub = results_df[mask].sort_values("center_year")
    ax.plot(sub["center_year"], sub["e0"], color=color,
            marker="o", markersize=4, label=f"{label} Females, Wisconsin")

ax.set_xlabel("Year (center of 3-year window)")
ax.set_ylabel("Life expectancy at birth (years)")
ax.set_title("Life Expectancy for Non-Hispanic Black and White Females\n"
             "Wisconsin, 2006–2016")
ax.legend(loc="lower right")
ax.set_xlim(2005, 2017)
ax.yaxis.set_major_locator(mticker.MultipleLocator(2))
fig.savefig(FIG_DIR / "fig2_female_le_trends_statewide.pdf")
fig.savefig(FIG_DIR / "fig2_female_le_trends_statewide.png")
plt.close()
print("Saved Figure 2: Female LE trends (statewide)")

# --- Figure 3: B-W Gap by geography (males) with 95% CI ---
fig, ax = plt.subplots(figsize=(10, 6))

geo_colors = {"Statewide": "#282728", "Milwaukee": "#c5050c",
              "Dane": "#0479a8", "Rest_of_WI": "#7b6888"}
geo_styles = {"Statewide": "-", "Milwaukee": "--",
              "Dane": "-.", "Rest_of_WI": ":"}
gap_ci_male = gap_ci[gap_ci["sex"] == 1]

for geo in geographies:
    gaps, err_lo, err_hi = [], [], []
    for cy in years:
        w = results_df.loc[(results_df["center_year"] == cy) &
                           (results_df["geography"] == geo) &
                           (results_df["sex"] == 1) &
                           (results_df["race"] == 1), "e0"]
        b = results_df.loc[(results_df["center_year"] == cy) &
                           (results_df["geography"] == geo) &
                           (results_df["sex"] == 1) &
                           (results_df["race"] == 2), "e0"]
        g = gap_ci_male[(gap_ci_male["center_year"] == cy) & (gap_ci_male["geography"] == geo)]
        if len(w) > 0 and len(b) > 0:
            gap_val = w.values[0] - b.values[0]
            gaps.append(gap_val)
            if len(g) > 0:
                err_lo.append(gap_val - g["gap_lo"].values[0])
                err_hi.append(g["gap_hi"].values[0] - gap_val)
            else:
                err_lo.append(0)
                err_hi.append(0)
        else:
            gaps.append(np.nan)
            err_lo.append(0)
            err_hi.append(0)
    gaps = np.array(gaps)
    err_lo = np.array(err_lo)
    err_hi = np.array(err_hi)
    capsize = 4 if geo == "Dane" else 2
    lw = 2.5 if geo == "Dane" else 1.5
    ax.errorbar(years, gaps, yerr=[err_lo, err_hi], color=geo_colors[geo],
                linestyle=geo_styles[geo], marker="o", markersize=4, capsize=capsize,
                capthick=lw, elinewidth=lw, label=geo.replace("_", " "))

ax.set_xlabel("Year (center of 3-year window)")
ax.set_ylabel("Black-White life expectancy gap (years)")
ax.set_title("Black-White Life Expectancy Gap for Males\n"
             "by Geography, 2006–2016 (95% CI; Dane County uncertainty emphasized)")
ax.legend(loc="best")
ax.set_xlim(2005, 2017)
ax.axhline(y=0, color="gray", linewidth=0.5)
fig.savefig(FIG_DIR / "fig3_male_bw_gap_by_geography.pdf")
fig.savefig(FIG_DIR / "fig3_male_bw_gap_by_geography.png")
plt.close()
print("Saved Figure 3: Male B-W gap by geography (with 95% CI)")

# --- Figure 4: B-W Gap by geography (females) with 95% CI ---
fig, ax = plt.subplots(figsize=(10, 6))

gap_ci_female = gap_ci[gap_ci["sex"] == 2]
for geo in geographies:
    gaps, err_lo, err_hi = [], [], []
    for cy in years:
        w = results_df.loc[(results_df["center_year"] == cy) &
                           (results_df["geography"] == geo) &
                           (results_df["sex"] == 2) &
                           (results_df["race"] == 1), "e0"]
        b = results_df.loc[(results_df["center_year"] == cy) &
                           (results_df["geography"] == geo) &
                           (results_df["sex"] == 2) &
                           (results_df["race"] == 2), "e0"]
        g = gap_ci_female[(gap_ci_female["center_year"] == cy) & (gap_ci_female["geography"] == geo)]
        if len(w) > 0 and len(b) > 0:
            gap_val = w.values[0] - b.values[0]
            gaps.append(gap_val)
            if len(g) > 0:
                err_lo.append(gap_val - g["gap_lo"].values[0])
                err_hi.append(g["gap_hi"].values[0] - gap_val)
            else:
                err_lo.append(0)
                err_hi.append(0)
        else:
            gaps.append(np.nan)
            err_lo.append(0)
            err_hi.append(0)
    gaps = np.array(gaps)
    err_lo = np.array(err_lo)
    err_hi = np.array(err_hi)
    capsize = 4 if geo == "Dane" else 2
    lw = 2.5 if geo == "Dane" else 1.5
    ax.errorbar(years, gaps, yerr=[err_lo, err_hi], color=geo_colors[geo],
                linestyle=geo_styles[geo], marker="o", markersize=4, capsize=capsize,
                capthick=lw, elinewidth=lw, label=geo.replace("_", " "))

ax.set_xlabel("Year (center of 3-year window)")
ax.set_ylabel("Black-White life expectancy gap (years)")
ax.set_title("Black-White Life Expectancy Gap for Females\n"
             "by Geography, 2006–2016 (95% CI; Dane County uncertainty emphasized)")
ax.legend(loc="best")
ax.set_xlim(2005, 2017)
ax.axhline(y=0, color="gray", linewidth=0.5)
fig.savefig(FIG_DIR / "fig4_female_bw_gap_by_geography.pdf")
fig.savefig(FIG_DIR / "fig4_female_bw_gap_by_geography.png")
plt.close()
print("Saved Figure 4: Female B-W gap by geography (with 95% CI)")

# --- Figure 5: LE by race × geography (2016) with 95% CI ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

for idx, (sex, sex_l) in enumerate([(1, "Males"), (2, "Females")]):
    ax = axes[idx]
    sub = results_df[(results_df["center_year"] == 2016) &
                     (results_df["sex"] == sex)]

    x = np.arange(len(geographies))
    width = 0.35

    white_vals, black_vals = [], []
    white_lo, white_hi, black_lo, black_hi = [], [], [], []
    for g in geographies:
        w = sub[(sub["geography"] == g) & (sub["race"] == 1)]
        b = sub[(sub["geography"] == g) & (sub["race"] == 2)]
        white_vals.append(w["e0"].values[0] if len(w) > 0 else 0)
        black_vals.append(b["e0"].values[0] if len(b) > 0 else 0)
        if len(w) > 0 and "e0_lo" in w.columns:
            white_lo.append(w["e0_lo"].values[0])
            white_hi.append(w["e0_hi"].values[0])
        else:
            white_lo.append(white_vals[-1])
            white_hi.append(white_vals[-1])
        if len(b) > 0 and "e0_lo" in b.columns:
            black_lo.append(b["e0_lo"].values[0])
            black_hi.append(b["e0_hi"].values[0])
        else:
            black_lo.append(black_vals[-1])
            black_hi.append(black_vals[-1])

    err_w = [np.array(white_vals) - np.array(white_lo), np.array(white_hi) - np.array(white_vals)]
    err_b = [np.array(black_vals) - np.array(black_lo), np.array(black_hi) - np.array(black_vals)]
    bars1 = ax.bar(x - width/2, white_vals, width, label="NH-White",
                   color=WHITE_POP, edgecolor="white", yerr=err_w, capsize=2)
    bars2 = ax.bar(x + width/2, black_vals, width, label="NH-Black",
                   color=BLACK_POP, edgecolor="white", yerr=err_b, capsize=2)

    ax.set_ylabel("Life expectancy at birth (years)" if idx == 0 else "")
    ax.set_title(f"{sex_l}, 2015–2017 (95% CI; Dane County intervals wider)")
    ax.set_xticks(x)
    ax.set_xticklabels([g.replace("_", " ") for g in geographies],
                       rotation=15, ha="right")
    ax.legend()
    ax.set_ylim(55, 90)

    for i, (w, b) in enumerate(zip(white_vals, black_vals)):
        if w > 0 and b > 0:
            gap = w - b
            ax.annotate(f"Gap: {gap:.1f}",
                        xy=(i, min(w, b) - 1.5),
                        ha="center", fontsize=9, fontweight="bold",
                        color=ACCENT_GRAY)

fig.suptitle("Life Expectancy by Race and Geography, 2015–2017 (95% CI)",
             fontsize=15, fontweight="bold")
fig.tight_layout()
fig.savefig(FIG_DIR / "fig5_le_by_race_geography_2016.pdf")
fig.savefig(FIG_DIR / "fig5_le_by_race_geography_2016.png")
plt.close()
print("Saved Figure 5: LE by race and geography (bar chart with 95% CI)")


# =================================================================
# PHASE 5: GEOGRAPHIC MAP
# =================================================================
print("\n" + "=" * 60)
print("PHASE 5: GEOGRAPHIC MAP")
print("=" * 60)

import geopandas as gpd
from matplotlib.patches import Patch
from matplotlib.colors import Normalize
from matplotlib import cm

shp_path = ROOT / "Data" / "shp" / "cb_2018_us_county_500k.shp"
counties = gpd.read_file(shp_path)

wi = counties[counties["STATEFP"] == "55"].copy()
wi["GEOID"] = wi["GEOID"].astype(int)
print(f"Wisconsin counties loaded: {len(wi)}")

# Compute county-level male B-W gap for 2016 where possible
# (only meaningful for counties with sufficient Black population)
cy_data = pooled[pooled["center_year"] == 2016]

county_gaps = {}
for fips in wi["GEOID"].unique():
    geo_label = assign_geography(fips)
    if geo_label in ("Milwaukee", "Dane"):
        mask_w = ((results_df["center_year"] == 2016) &
                  (results_df["geography"] == geo_label) &
                  (results_df["sex"] == 1) & (results_df["race"] == 1))
        mask_b = ((results_df["center_year"] == 2016) &
                  (results_df["geography"] == geo_label) &
                  (results_df["sex"] == 1) & (results_df["race"] == 2))
        if mask_w.sum() > 0 and mask_b.sum() > 0:
            w_le = results_df.loc[mask_w, "e0"].values[0]
            b_le = results_df.loc[mask_b, "e0"].values[0]
            county_gaps[fips] = w_le - b_le

wi["region"] = wi["GEOID"].apply(
    lambda x: "Milwaukee" if x == MILWAUKEE_FIPS
    else ("Dane" if x == DANE_FIPS else "Rest of WI"))

region_colors = {"Milwaukee": "#c5050c", "Dane": "#0479a8",
                 "Rest of WI": "#dadfe1"}
wi["fill_color"] = wi["region"].map(region_colors)

# --- Figure 6: Wisconsin map with highlighted regions ---
fig, ax = plt.subplots(1, 1, figsize=(8, 10))

for region, color in region_colors.items():
    subset = wi[wi["region"] == region]
    subset.plot(ax=ax, color=color, edgecolor="white", linewidth=0.5)

# Annotate Milwaukee and Dane with gap values
milwaukee_centroid = wi[wi["GEOID"] == MILWAUKEE_FIPS].geometry.centroid.iloc[0]
dane_centroid = wi[wi["GEOID"] == DANE_FIPS].geometry.centroid.iloc[0]

rest_mask = ((results_df["center_year"] == 2016) &
             (results_df["geography"] == "Rest_of_WI") &
             (results_df["sex"] == 1))
rest_w = results_df.loc[rest_mask & (results_df["race"] == 1), "e0"].values[0]
rest_b = results_df.loc[rest_mask & (results_df["race"] == 2), "e0"].values[0]
rest_gap = rest_w - rest_b

gap_milw = county_gaps.get(MILWAUKEE_FIPS, 0)
gap_dane = county_gaps.get(DANE_FIPS, 0)

ax.annotate(f"Milwaukee\nB-W Gap: {gap_milw:.1f} yr",
            xy=(milwaukee_centroid.x, milwaukee_centroid.y),
            xytext=(milwaukee_centroid.x + 0.6, milwaukee_centroid.y - 0.4),
            fontsize=10, fontweight="bold", color="#c5050c",
            arrowprops=dict(arrowstyle="->", color="#c5050c", lw=1.5),
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor="#c5050c", alpha=0.9))

ax.annotate(f"Dane (Madison)\nB-W Gap: {gap_dane:.1f} yr",
            xy=(dane_centroid.x, dane_centroid.y),
            xytext=(dane_centroid.x - 1.5, dane_centroid.y + 0.5),
            fontsize=10, fontweight="bold", color="#0479a8",
            arrowprops=dict(arrowstyle="->", color="#0479a8", lw=1.5),
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor="#0479a8", alpha=0.9))

# Statewide annotation
state_mask = ((results_df["center_year"] == 2016) &
              (results_df["geography"] == "Statewide") &
              (results_df["sex"] == 1))
state_w = results_df.loc[state_mask & (results_df["race"] == 1), "e0"].values[0]
state_b = results_df.loc[state_mask & (results_df["race"] == 2), "e0"].values[0]
state_gap = state_w - state_b

legend_elements = [
    Patch(facecolor="#c5050c", edgecolor="white", label=f"Milwaukee (Gap: {gap_milw:.1f} yr)"),
    Patch(facecolor="#0479a8", edgecolor="white", label=f"Dane County (Gap: {gap_dane:.1f} yr)"),
    Patch(facecolor="#dadfe1", edgecolor="white", label=f"Rest of WI (Gap: {rest_gap:.1f} yr)"),
]
ax.legend(handles=legend_elements, loc="lower left", fontsize=10,
          title=f"Male B-W LE Gap, 2015–2017\nStatewide: {state_gap:.1f} yr",
          title_fontsize=11)

ax.set_title("Black-White Life Expectancy Gap\nby Region, Males, 2015–2017",
             fontsize=14, fontweight="bold")
ax.axis("off")
fig.tight_layout()
fig.savefig(FIG_DIR / "fig6_wisconsin_map_bw_gap.pdf")
fig.savefig(FIG_DIR / "fig6_wisconsin_map_bw_gap.png")
plt.close()
print("Saved Figure 6: Wisconsin map with B-W gap annotations")


# =================================================================
# PHASE 6: PUBLICATION-READY TABLES
# =================================================================
print("\n" + "=" * 60)
print("PHASE 6: PUBLICATION-READY TABLES")
print("=" * 60)

# --- Table 1: Full gap trends across all years and geographies (with 95% CI) ---
gap_rows = []
for cy in sorted(WINDOWS.keys()):
    for sex in [1, 2]:
        sex_l = sex_labels[sex]
        row = {"Year": cy, "Sex": sex_l}
        for geo in geographies:
            w = results_df.loc[(results_df["center_year"] == cy) &
                               (results_df["geography"] == geo) &
                               (results_df["sex"] == sex) &
                               (results_df["race"] == 1), ["e0", "e0_lo", "e0_hi"]]
            b = results_df.loc[(results_df["center_year"] == cy) &
                               (results_df["geography"] == geo) &
                               (results_df["sex"] == sex) &
                               (results_df["race"] == 2), ["e0", "e0_lo", "e0_hi"]]
            g = gap_ci[(gap_ci["center_year"] == cy) & (gap_ci["geography"] == geo) &
                       (gap_ci["sex"] == sex)]
            if len(w) > 0 and len(b) > 0:
                row[f"{geo}_White"] = round(w["e0"].values[0], 2)
                row[f"{geo}_Black"] = round(b["e0"].values[0], 2)
                row[f"{geo}_Gap"] = round(w["e0"].values[0] - b["e0"].values[0], 2)
                if "e0_lo" in w.columns:
                    row[f"{geo}_White_lo"] = round(w["e0_lo"].values[0], 2)
                    row[f"{geo}_White_hi"] = round(w["e0_hi"].values[0], 2)
                    row[f"{geo}_Black_lo"] = round(b["e0_lo"].values[0], 2)
                    row[f"{geo}_Black_hi"] = round(b["e0_hi"].values[0], 2)
                if len(g) > 0:
                    row[f"{geo}_Gap_lo"] = round(g["gap_lo"].values[0], 2)
                    row[f"{geo}_Gap_hi"] = round(g["gap_hi"].values[0], 2)
        gap_rows.append(row)

table1 = pd.DataFrame(gap_rows)
table1.to_csv(OUT_DIR / "tables" / "table1_le_trends_all_geographies.csv",
              index=False)
print("Saved Table 1: LE and B-W gaps across all years and geographies (with 95% CI)")
print(f"  Dimensions: {table1.shape[0]} rows × {table1.shape[1]} columns")

# --- Table 2: Detailed summary for latest period (2016 = 2015-2017) with 95% CI ---
detail_rows = []
for geo in geographies:
    for sex in [1, 2]:
        for race in [1, 2]:
            mask = ((results_df["center_year"] == 2016) &
                    (results_df["geography"] == geo) &
                    (results_df["sex"] == sex) &
                    (results_df["race"] == race))
            if mask.sum() > 0:
                r = results_df[mask].iloc[0]
                detail_rows.append({
                    "Geography": geo.replace("_", " "),
                    "Sex": sex_labels[sex],
                    "Race": race_labels[race],
                    "Life Expectancy": round(r["e0"], 2),
                    "LE_lo": round(r["e0_lo"], 2) if "e0_lo" in r and pd.notna(r["e0_lo"]) else None,
                    "LE_hi": round(r["e0_hi"], 2) if "e0_hi" in r and pd.notna(r["e0_hi"]) else None,
                    "Total Deaths (3yr)": int(r["total_deaths"]),
                    "Total Population (3yr)": int(r["total_pop"]),
                })

table2 = pd.DataFrame(detail_rows)

# Wide format with CIs: White, White_lo, White_hi, Black, Black_lo, Black_hi, B-W Gap, Gap_lo, Gap_hi
r2016 = results_df[results_df["center_year"] == 2016]
g2016 = gap_ci[gap_ci["center_year"] == 2016]
wide_rows = []
for geo in geographies:
    for sex in [1, 2]:
        sex_l = sex_labels[sex]
        w = r2016[(r2016["geography"] == geo) & (r2016["sex"] == sex) & (r2016["race"] == 1)].iloc[0]
        b = r2016[(r2016["geography"] == geo) & (r2016["sex"] == sex) & (r2016["race"] == 2)].iloc[0]
        g = g2016[(g2016["geography"] == geo) & (g2016["sex"] == sex)]
        row = {
            "Geography": geo.replace("_", " "),
            "Sex": sex_l,
            "White": round(w["e0"], 2),
            "Black": round(b["e0"], 2),
            "B-W Gap": round(w["e0"] - b["e0"], 2),
        }
        if "e0_lo" in w:
            row["White_lo"] = round(w["e0_lo"], 2)
            row["White_hi"] = round(w["e0_hi"], 2)
            row["Black_lo"] = round(b["e0_lo"], 2)
            row["Black_hi"] = round(b["e0_hi"], 2)
        if len(g) > 0:
            row["Gap_lo"] = round(g["gap_lo"].values[0], 2)
            row["Gap_hi"] = round(g["gap_hi"].values[0], 2)
        wide_rows.append(row)
table2_wide = pd.DataFrame(wide_rows).sort_values(["Geography", "Sex"])

table2.to_csv(OUT_DIR / "tables" / "table2_detail_2016.csv", index=False)
table2_wide.to_csv(OUT_DIR / "tables" / "table2_wide_2016.csv", index=False)
table2_wide.to_csv(OUT_DIR / "tables" / "le_summary_2016.csv", index=False)

print("\nTable 2: Detailed life expectancy, 2015-2017 (with 95% CI)")
print(table2_wide.to_string(index=False, float_format="%.2f"))

# --- Table 3: Change in gap over time (earliest vs latest) ---
change_rows = []
for geo in geographies:
    for sex in [1, 2]:
        sex_l = sex_labels[sex]
        for cy_label, cy in [("2006", 2006), ("2016", 2016)]:
            w = results_df.loc[(results_df["center_year"] == cy) &
                               (results_df["geography"] == geo) &
                               (results_df["sex"] == sex) &
                               (results_df["race"] == 1), "e0"]
            b = results_df.loc[(results_df["center_year"] == cy) &
                               (results_df["geography"] == geo) &
                               (results_df["sex"] == sex) &
                               (results_df["race"] == 2), "e0"]
            if len(w) > 0 and len(b) > 0:
                change_rows.append({
                    "Geography": geo.replace("_", " "),
                    "Sex": sex_l,
                    "Period": f"{cy-1}-{cy+1}",
                    "White LE": round(w.values[0], 2),
                    "Black LE": round(b.values[0], 2),
                    "B-W Gap": round(w.values[0] - b.values[0], 2),
                })

table3 = pd.DataFrame(change_rows)
table3_wide = table3.pivot_table(
    index=["Geography", "Sex"],
    columns="Period",
    values=["White LE", "Black LE", "B-W Gap"]
)

# Compute change
t3_summary = []
for geo in geographies:
    for sex_l in ["Male", "Female"]:
        early = table3[(table3["Geography"] == geo.replace("_", " ")) &
                       (table3["Sex"] == sex_l) &
                       (table3["Period"] == "2005-2007")]
        late = table3[(table3["Geography"] == geo.replace("_", " ")) &
                      (table3["Sex"] == sex_l) &
                      (table3["Period"] == "2015-2017")]
        if len(early) > 0 and len(late) > 0:
            e = early.iloc[0]
            l = late.iloc[0]
            t3_summary.append({
                "Geography": geo.replace("_", " "),
                "Sex": sex_l,
                "Gap (2005-07)": e["B-W Gap"],
                "Gap (2015-17)": l["B-W Gap"],
                "Change": round(l["B-W Gap"] - e["B-W Gap"], 2),
                "White LE Change": round(l["White LE"] - e["White LE"], 2),
                "Black LE Change": round(l["Black LE"] - e["Black LE"], 2),
            })

table3_final = pd.DataFrame(t3_summary)
# Merge 95% CIs for change in Black LE and change in gap
change_for_merge = change_ci[["geography", "sex_label", "black_le_change_lo", "black_le_change_hi",
                               "gap_change_lo", "gap_change_hi"]].copy()
change_for_merge["Geography"] = change_for_merge["geography"].str.replace("_", " ")
table3_final = table3_final.merge(
    change_for_merge[["Geography", "sex_label", "black_le_change_lo", "black_le_change_hi",
                      "gap_change_lo", "gap_change_hi"]],
    left_on=["Geography", "Sex"], right_on=["Geography", "sex_label"], how="left"
).drop(columns=["sex_label"], errors="ignore")
for c in ["black_le_change_lo", "black_le_change_hi", "gap_change_lo", "gap_change_hi"]:
    if c in table3_final.columns:
        table3_final[c] = table3_final[c].round(2)
table3_final.to_csv(OUT_DIR / "tables" / "table3_gap_change_2006_vs_2016.csv",
                     index=False)

print("\nTable 3: Change in B-W gap, 2005-07 vs 2015-17 (with 95% CI for change)")
print(table3_final.to_string(index=False, float_format="%.2f"))

print(f"\nAll tables saved to {OUT_DIR / 'tables'}/")

# --- Sample context table: deaths, pooled population, crude rates (2016 = 2015-2017) ---
context_rows = []
r2016 = results_df[results_df["center_year"] == 2016]
for geo in geographies:
    for sex in [1, 2]:
        sex_l = sex_labels[sex]
        for race in [1, 2]:
            race_l = race_labels[race]
            mask = ((r2016["geography"] == geo) &
                    (r2016["sex"] == sex) &
                    (r2016["race"] == race))
            if mask.sum() > 0:
                r = r2016[mask].iloc[0]
                deaths = r["total_deaths"]
                pop = r["total_pop"]
                rate = deaths / pop * 1000 if pop > 0 else np.nan
                context_rows.append({
                    "Geography": geo.replace("_", " "),
                    "Sex": sex_l,
                    "Race": race_l,
                    "Total Deaths (3yr)": int(deaths),
                    "Total Population (3yr person-years)": int(pop),
                    "Crude Death Rate (per 1,000)": round(rate, 3) if not np.isnan(rate) else None,
                })

context_df = pd.DataFrame(context_rows).sort_values(["Geography", "Sex", "Race"])
context_df.to_csv(OUT_DIR / "tables" / "table6_sample_context_2016.csv", index=False)

print("\nSample context, 2015-2017 (3-year pooled):")
print(context_df.to_string(index=False, float_format="%.3f"))
print(f"\nSaved sample context to {OUT_DIR / 'tables' / 'table6_sample_context_2016.csv'}")


print("\n" + "=" * 60)
print("ALL PHASES COMPLETE")
print("=" * 60)
