"""
14_load_states.py — Harmonize state DOE school-level by-race test results.

Reads raw files downloaded by 13_download_states.py (Data/raw/states/) and maps
each state to a common long schema:

  state, year, district_id, district_name, school_id, school_name,
  race (White/Black/Hispanic), subject (ELA/Math), grade_band,
  n_tested (NaN where the state does not publish counts),
  pct_proficient (0-100), proficiency_label

Conventions
-----------
- `year` = spring of the school year (2024 = 2023-24).
- Masked/suppressed cells -> NaN (never imputed). Bounded values (">95", "<5")
  are clipped to the bound and counted in the QC report.
- Each state's own proficiency standard is recorded in `proficiency_label`;
  levels are NOT comparable across states.

Outputs:
  output/data/panel_school_race_multistate.parquet
  output/tables/multistate_qc.txt

Run from repo root:
  python3 analysis/14_load_states.py
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "Data" / "raw" / "states"
OUT_DATA = ROOT / "output" / "data"
OUT_TABLES = ROOT / "output" / "tables"
OUT_DATA.mkdir(parents=True, exist_ok=True)
OUT_TABLES.mkdir(parents=True, exist_ok=True)

SCHEMA = [
    "state", "year", "district_id", "district_name", "school_id", "school_name",
    "race", "subject", "grade_band", "n_tested", "pct_proficient", "proficiency_label",
]

QC_LINES: list[str] = []


def qc(msg: str) -> None:
    print(msg)
    QC_LINES.append(msg)


def _clip_bounded(s: pd.Series) -> pd.Series:
    """Convert '>95'/'<5'-style strings to their bound; other non-numerics -> NaN."""
    s = s.astype(str).str.strip().str.replace("%", "", regex=False)
    bounded = s.str.match(r"^[<>]=?\s*\d+(\.\d+)?$")
    s = s.where(~bounded, s.str.replace(r"[<>=\s]", "", regex=True))
    return pd.to_numeric(s, errors="coerce")


# ================================================================ CA
CA_GROUPS = {"74": "Black", "78": "Hispanic", "80": "White"}


def load_ca() -> pd.DataFrame:
    """CAASPP SB research files. Proficiency = 'Standard Met and Above' (Levels 3-4)."""
    frames = []
    base_cols = ["County Code", "District Code", "School Code", "Test Type",
                 "Test ID", "Student Group ID", "Grade",
                 "Percentage Standard Met and Above"]
    # research-file schema changed between 2023 and 2024
    n_col_candidates = ["Total Students Tested with Scores", "Students with Scores"]
    for y in [2023, 2024, 2025]:
        zpath = RAW / "ca" / f"sb_ca{y}_all_csv_v1.zip"
        epath = RAW / "ca" / f"sb_ca{y}entities_csv.zip"
        if not zpath.exists():
            qc(f"  [CA] missing {zpath.name}; skipping year {y}")
            continue
        with zipfile.ZipFile(epath) as z:
            ename = [n for n in z.namelist() if n.endswith(".txt")][0]
            ent = pd.read_csv(io.BytesIO(z.read(ename)), sep="^", dtype=str,
                              encoding="latin-1")
        ent["County Code"] = ent["County Code"].str.zfill(2)
        ent["District Code"] = ent["District Code"].str.zfill(5)
        ent["School Code"] = ent["School Code"].str.zfill(7)
        schools = ent[ent["School Code"] != "0000000"].set_index(
            ["County Code", "District Code", "School Code"])["School Name"]
        districts = (ent[(ent["School Code"] == "0000000") & (ent["District Code"] != "00000")]
                     .set_index(["County Code", "District Code"])["District Name"])

        chunks = []
        with zipfile.ZipFile(zpath) as z:
            fname = [n for n in z.namelist() if n.endswith(".txt")][0]
            with z.open(fname) as f:
                header = pd.read_csv(f, sep="^", nrows=0, encoding="latin-1").columns
            n_col = next(c for c in n_col_candidates if c in header)
            usecols = base_cols + [n_col]
            with z.open(fname) as f:
                for ch in pd.read_csv(f, sep="^", usecols=usecols, dtype=str,
                                      encoding="latin-1", chunksize=1_000_000):
                    ch = ch[
                        (ch["Test Type"] == "B")
                        & ch["Test ID"].isin(["1", "2"])
                        & ch["Student Group ID"].isin(CA_GROUPS)
                        & ch["Grade"].isin(["3", "4", "5", "6", "7", "8"])
                        & (ch["School Code"] != "0000000")
                    ]
                    if len(ch):
                        chunks.append(ch)
        df = pd.concat(chunks, ignore_index=True)
        df["County Code"] = df["County Code"].str.zfill(2)
        df["District Code"] = df["District Code"].str.zfill(5)
        df["School Code"] = df["School Code"].str.zfill(7)
        key_s = pd.MultiIndex.from_frame(df[["County Code", "District Code", "School Code"]])
        key_d = pd.MultiIndex.from_frame(df[["County Code", "District Code"]])
        out = pd.DataFrame({
            "state": "CA",
            "year": int(y),
            "district_id": df["County Code"] + df["District Code"],
            "district_name": districts.reindex(key_d).to_numpy(),
            "school_id": df["County Code"] + df["District Code"] + df["School Code"],
            "school_name": schools.reindex(key_s).to_numpy(),
            "race": df["Student Group ID"].map(CA_GROUPS),
            "subject": df["Test ID"].map({"1": "ELA", "2": "Math"}),
            "grade_band": df["Grade"].str.zfill(2),
            "n_tested": pd.to_numeric(df[n_col], errors="coerce"),
            "pct_proficient": _clip_bounded(df["Percentage Standard Met and Above"]),
            "proficiency_label": "SB Standard Met and Above",
        })
        frames.append(out)
    return pd.concat(frames, ignore_index=True)


# ================================================================ TX
TX_GROUPS = {"DB": "Black", "DH": "Hispanic", "DW": "White"}
TX_FILES = {2024: ("tapr2024_campus_staar1.csv", "24"),
            2023: ("tapr2023_campus_staar1.csv", "23")}


def load_tx() -> pd.DataFrame:
    """TEA TAPR campus STAAR. Proficiency = 'Meets Grade Level or Above' (num/den)."""
    # campus/district names only ship in the 2024+ vintage; build a lookup
    names = pd.read_csv(RAW / "tx" / "tapr2024_campus_staar1.csv", dtype=str,
                        usecols=["CAMPUS", "CAMPNAME", "DISTRICT", "DISTNAME"])
    camp_names = names.drop_duplicates("CAMPUS").set_index("CAMPUS")
    frames = []
    for year, (fname, yy) in TX_FILES.items():
        path = RAW / "tx" / fname
        df = pd.read_csv(path, dtype=str)
        for col in ["CAMPNAME", "DISTNAME"]:
            if col not in df.columns:
                df[col] = df["CAMPUS"].map(camp_names[col])
        recs = []
        for grp, race in TX_GROUPS.items():
            for gg in ["03", "04", "05", "06", "07", "08"]:
                for subj_code, subj in [("RE", "ELA"), ("MA", "Math")]:
                    den_c = f"C{grp}{gg}A{subj_code}10{yy}D"
                    num_c = f"C{grp}{gg}A{subj_code}12{yy}N"
                    if den_c not in df.columns or num_c not in df.columns:
                        continue
                    den = pd.to_numeric(df[den_c], errors="coerce")
                    num = pd.to_numeric(df[num_c], errors="coerce")
                    # TEA masks with negative codes
                    den = den.where(den >= 0)
                    num = num.where(num >= 0)
                    pct = 100.0 * num / den.where(den > 0)
                    recs.append(pd.DataFrame({
                        "district_id": df["DISTRICT"].str.strip("'"),
                        "district_name": df["DISTNAME"],
                        "school_id": df["CAMPUS"].str.strip("'"),
                        "school_name": df["CAMPNAME"],
                        "race": race, "subject": subj, "grade_band": gg,
                        "n_tested": den, "pct_proficient": pct,
                    }))
        out = pd.concat(recs, ignore_index=True)
        out.insert(0, "state", "TX")
        out.insert(1, "year", year)
        out["proficiency_label"] = "STAAR Meets Grade Level or Above"
        frames.append(out)
    return pd.concat(frames, ignore_index=True)[SCHEMA]


# ================================================================ IL
IL_RACE_COLS = {
    "White": "IAR {subj} Proficiency Rate - White",
    "Black": "IAR {subj} Proficiency Rate - Black or African American",
    "Hispanic": "IAR {subj} Proficiency Rate - Hispanic or Latino",
}


def load_il() -> pd.DataFrame:
    """ISBE Report Card, IAR sheet. School-level pooled (grades 3-8) proficiency by race.
    ISBE does not publish per-race tested counts in this file -> n_tested = NaN.
    The 2023 file lacks the pooled by-race proficiency-rate columns, so IL covers
    2024 + 2025 only."""
    frames = []
    for y in [2024, 2025]:
        path = RAW / "il" / f"rc{y}.xlsx"
        if not path.exists():
            qc(f"  [IL] missing {path.name}; skipping")
            continue
        df = pd.read_excel(path, sheet_name="IAR", dtype=str)
        # 2023/2024 use a 'Type' column; 2025 renamed it 'Level' (+ dashed RCDTS)
        type_col = "Type" if "Type" in df.columns else "Level"
        df = df[df[type_col].astype(str).str.strip().str.lower() == "school"]
        df["RCDTS"] = df["RCDTS"].str.replace("-", "", regex=False)
        for subj_lab, subj in [("ELA", "ELA"), ("Math", "Math")]:
            for race, tpl in IL_RACE_COLS.items():
                col = tpl.format(subj=subj_lab)
                if col not in df.columns:
                    continue
                frames.append(pd.DataFrame({
                    "state": "IL", "year": int(y),
                    "district_id": df["RCDTS"].str[:11],
                    "district_name": df["District"],
                    "school_id": df["RCDTS"],
                    "school_name": df["School Name"],
                    "race": race, "subject": subj, "grade_band": "3-8 pooled",
                    "n_tested": np.nan,
                    "pct_proficient": _clip_bounded(df[col]),
                    "proficiency_label": "IAR Proficient (Levels 4-5)",
                }))
    return pd.concat(frames, ignore_index=True)


# ================================================================ NY
NY_RACES = {"White": "White", "Black or African American": "Black",
            "Hispanic or Latino": "Hispanic"}


def load_ny() -> pd.DataFrame:
    """NYSED report card DB exports, per-grade rows ELA3-ELA8 / MATH3-MATH8
    (the 3_8 combined rows only exist for All Students). Proficiency = Levels 3-4.
    SRC2024 carries 2023+2024; SRC2025 carries 2024+2025."""
    frames = []
    for src_year in [2024, 2025]:
        for subj, tag in [("ELA", "ela"), ("Math", "math")]:
            path = RAW / "ny" / f"annual_em_{tag}_{src_year}.csv"
            df = pd.read_csv(path, dtype=str, usecols=[
                "ENTITY_CD", "ENTITY_NAME", "YEAR", "ASSESSMENT_NAME",
                "SUBGROUP_NAME", "NUM_TESTED", "PER_PROF"])
            grade_re = "ELA([3-8])$" if subj == "ELA" else "MATH([3-8])$"
            grade = df["ASSESSMENT_NAME"].str.upper().str.extract(grade_re)[0]
            df = df[grade.notna() & df["SUBGROUP_NAME"].isin(NY_RACES)]
            grade = grade[df.index]
            cd = df["ENTITY_CD"].str.zfill(12)
            is_school = (~cd.str.endswith("0000") & ~cd.str.startswith("00000000")
                         & (cd != "111111111111"))  # statewide 'All Public Schools' row
            dist_names = (df.loc[cd.str.endswith("0000"), ["ENTITY_CD", "ENTITY_NAME"]]
                          .drop_duplicates("ENTITY_CD")
                          .set_index("ENTITY_CD")["ENTITY_NAME"])
            sub = df[is_school].copy()
            sub_cd = sub["ENTITY_CD"].str.zfill(12)
            dist_cd = sub_cd.str[:8] + "0000"
            frames.append(pd.DataFrame({
                "state": "NY",
                "year": pd.to_numeric(sub["YEAR"]),
                "district_id": dist_cd,
                "district_name": dist_names.reindex(dist_cd).to_numpy(),
                "school_id": sub_cd,
                "school_name": sub["ENTITY_NAME"],
                "race": sub["SUBGROUP_NAME"].map(NY_RACES),
                "subject": subj, "grade_band": "0" + grade[is_school],
                "n_tested": pd.to_numeric(sub["NUM_TESTED"], errors="coerce"),
                "pct_proficient": _clip_bounded(sub["PER_PROF"]),
                "proficiency_label": "NYS Levels 3-4 (Proficient)",
            }))
    out = pd.concat(frames, ignore_index=True)
    # overlapping year 2024 appears in both SRC files; keep the later vintage
    out = out.drop_duplicates(
        subset=["year", "school_id", "race", "subject", "grade_band"], keep="last")
    return out


# ================================================================ OH
OH_RACES = {"WHITE, NON-HISPANIC": "White", "BLACK, NON-HISPANIC": "Black",
            "HISPANIC": "Hispanic"}
# year span in column names is present through 2023-24 and dropped in 2024-25
OH_COL_RE = re.compile(
    r"^(\d)[a-z]{2} Grade (English Language Arts|Math)(?: \d{4}-\d{4})? Percent Proficient or above$"
)


def load_oh() -> pd.DataFrame:
    """Ohio building-level results by race. Per-grade percent proficient only
    (no tested counts published) -> n_tested = NaN."""
    frames = []
    for y, fname in [(2023, "building_ethnic_2223.xlsx"),
                     (2024, "building_ethnic_2324.xlsx"),
                     (2025, "building_ethnic_2425.xlsx")]:
        path = RAW / "oh" / fname
        df = pd.read_excel(path, sheet_name="RACE", dtype=str)
        df = df[df["Student Group"].isin(OH_RACES)]
        for col in df.columns:
            m = OH_COL_RE.match(str(col))
            if not m or m.group(1) not in "345678":
                continue
            subj = "ELA" if m.group(2).startswith("English") else "Math"
            frames.append(pd.DataFrame({
                "state": "OH", "year": int(y),
                "district_id": df["District IRN"],
                "district_name": df["District Name"],
                "school_id": df["Building IRN"],
                "school_name": df["Building Name"],
                "race": df["Student Group"].map(OH_RACES),
                "subject": subj, "grade_band": f"0{m.group(1)}",
                "n_tested": np.nan,
                "pct_proficient": _clip_bounded(df[col]),
                "proficiency_label": "Ohio Proficient or above",
            }))
    return pd.concat(frames, ignore_index=True)


# ================================================================ GA
GA_RACES = {"White": "White", "Black or African American": "Black",
            "Hispanic": "Hispanic"}


def load_ga() -> pd.DataFrame:
    """GA Milestones EOG (grades 3-8, pooled 'ALL GRADES' rows).
    Proficiency = Proficient + Distinguished Learner."""
    frames = []
    for y in [2023, 2024, 2025]:
        path = RAW / "ga" / f"eog_{y}.csv"
        df = pd.read_csv(path, dtype=str)
        df.columns = [c.lstrip("#") for c in df.columns]
        mask = (df["SUBGROUP_NAME"].isin(GA_RACES)
                & df["TEST_CMPNT_TYP_NM"].isin(["English Language Arts", "Mathematics"]))
        # 2023 file is EOG-only without the ACDMC_LVL column; later files carry it
        if "ACDMC_LVL" in df.columns:
            mask &= df["ACDMC_LVL"] == "ALL GRADES"
        df = df[mask].copy()
        # keep school rows only (state rows: district code 'ALL'; district rows: instn 'ALL')
        df = df[(df["INSTN_NUMBER"].str.upper() != "ALL")
                & (df["SCHOOL_DISTRCT_CD"].str.upper() != "ALL")]
        pct = _clip_bounded(df["PROFICIENT_PCT"]) + _clip_bounded(df["DISTINGUISHED_PCT"])
        frames.append(pd.DataFrame({
            "state": "GA", "year": int(y),
            "district_id": df["SCHOOL_DISTRCT_CD"],
            "district_name": df["SCHOOL_DSTRCT_NM"],
            "school_id": df["SCHOOL_DISTRCT_CD"] + "-" + df["INSTN_NUMBER"],
            "school_name": df["INSTN_NAME"],
            "race": df["SUBGROUP_NAME"].map(GA_RACES),
            "subject": df["TEST_CMPNT_TYP_NM"].map(
                {"English Language Arts": "ELA", "Mathematics": "Math"}),
            "grade_band": "3-8 pooled",
            "n_tested": pd.to_numeric(df["NUM_TESTED_CNT"], errors="coerce"),
            "pct_proficient": pct,
            "proficiency_label": "Milestones Proficient + Distinguished",
        }))
    return pd.concat(frames, ignore_index=True)


# ================================================================ NC
NC_RACES = {"WHTE": "White", "BLCK": "Black", "HISP": "Hispanic"}


def load_nc() -> pd.DataFrame:
    """NC accountability disaggregated EOG data. Proficiency = Grade Level
    Proficient (Level 3+). District names not in file; district_id = LEA code."""
    frames = []
    for y, span in [(2023, "2022-23"), (2024, "2023-24"), (2025, "2024-25")]:
        path = RAW / "nc" / f"y{y}" / f"Disag_{span}_Data.txt"
        df = pd.read_csv(path, sep="\t", dtype=str)
        df = df[
            df["subject"].isin(["RD", "MA"])
            & df["grade"].isin(["03", "04", "05", "06", "07", "08"])
            & df["subgroup"].isin(NC_RACES)
            & (df["type"] == "ALL")
            # drop state (NC-SEA), SBE region (NC-SBx) and LEA aggregate rows
            & ~df["school_code"].str.contains("LEA|SEA|SB", na=False)
        ].copy()
        frames.append(pd.DataFrame({
            "state": "NC", "year": int(y),
            "district_id": df["school_code"].str[:3],
            "district_name": df["school_code"].str[:3],
            "school_id": df["school_code"],
            "school_name": df["name"],
            "race": df["subgroup"].map(NC_RACES),
            "subject": df["subject"].map({"RD": "ELA", "MA": "Math"}),
            "grade_band": df["grade"],
            "n_tested": pd.to_numeric(df["num_tested"], errors="coerce"),
            "pct_proficient": _clip_bounded(df["pct_glp"]),
            "proficiency_label": "NC Grade Level Proficient (Level 3+)",
        }))
    return pd.concat(frames, ignore_index=True)


# ================================================================ NJ
NJ_RACES = {"White": "White", "African American": "Black", "Hispanic": "Hispanic"}


def load_nj() -> pd.DataFrame:
    """NJSLA per-grade files. Proficiency = Levels 4-5 (Met + Exceeded)."""
    frames = []
    for yy, year in [("2223", 2023), ("2324", 2024), ("2425", 2025)]:
        for subj_tag, subj in [("ela", "ELA"), ("mat", "Math")]:
            for g in ["03", "04", "05", "06", "07", "08"]:
                path = RAW / "nj" / f"{subj_tag}{g}_{yy}.xlsx"
                if not path.exists():
                    qc(f"  [NJ] missing {path.name}; skipping")
                    continue
                df = pd.read_excel(path, skiprows=2, dtype=str)
                df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]
                df = df[
                    (df["Subgroup"] == "Race/Ethnicity")
                    & df["Subgroup Type"].isin(NJ_RACES)
                    & df["School Code"].notna()
                    & (df["School Code"].astype(str).str.strip() != "")
                ].copy()
                l4 = _clip_bounded(df["L4 Percent"])
                l5 = _clip_bounded(df["L5 Percent"])
                frames.append(pd.DataFrame({
                    "state": "NJ", "year": year,
                    "district_id": df["County Code"] + "-" + df["District Code"],
                    "district_name": df["District Name"],
                    "school_id": (df["County Code"] + "-" + df["District Code"]
                                  + "-" + df["School Code"]),
                    "school_name": df["School Name"],
                    "race": df["Subgroup Type"].map(NJ_RACES),
                    "subject": subj, "grade_band": g,
                    "n_tested": pd.to_numeric(df["Valid Scores"], errors="coerce"),
                    "pct_proficient": (l4 + l5),
                    "proficiency_label": "NJSLA Met + Exceeded (Levels 4-5)",
                }))
    return pd.concat(frames, ignore_index=True)


# ================================================================ QC + main
def qc_state(df: pd.DataFrame, st: str) -> None:
    sub = df[df["state"] == st]
    ela = sub[sub["subject"] == "ELA"]
    qc(f"\n[{st}] rows={len(sub):,}  years={sorted(sub['year'].unique())}")
    qc(f"  schools={sub['school_id'].nunique():,}  "
       f"ELA rows={len(ela):,}  "
       f"pct missing/suppressed={ela['pct_proficient'].isna().mean():.1%}")
    for race in ["White", "Black", "Hispanic"]:
        r = ela[ela["race"] == race]
        v = r.dropna(subset=["pct_proficient"])
        if v["n_tested"].notna().any():
            w = v.dropna(subset=["n_tested"])
            agg = np.average(w["pct_proficient"], weights=w["n_tested"]) if len(w) else np.nan
            n_str = f"n-weighted state mean={agg:.1f}%  (total n={w['n_tested'].sum():,.0f})"
        else:
            n_str = f"unweighted school mean={v['pct_proficient'].mean():.1f}%  (no N published)"
        qc(f"    {race:9s} non-missing={len(v):,}  {n_str}")


def main() -> None:
    print("=" * 65)
    print("14_load_states.py — harmonize state school-by-race files")
    print("=" * 65)

    loaders = {"CA": load_ca, "TX": load_tx, "IL": load_il, "NY": load_ny,
               "OH": load_oh, "GA": load_ga, "NC": load_nc, "NJ": load_nj}
    frames = []
    for st, fn in loaders.items():
        print(f"\nLoading {st} ...")
        try:
            df = fn()
            frames.append(df[SCHEMA])
        except Exception as e:
            qc(f"  [{st}] FAILED: {e}")
            raise

    panel = pd.concat(frames, ignore_index=True)
    panel["year"] = panel["year"].astype(int)

    for st in loaders:
        qc_state(panel, st)

    out_path = OUT_DATA / "panel_school_race_multistate.parquet"
    panel.to_parquet(out_path, index=False)
    qc(f"\nSaved {out_path.relative_to(ROOT)}  ({len(panel):,} rows)")

    qc_path = OUT_TABLES / "multistate_qc.txt"
    qc_path.write_text("\n".join(QC_LINES) + "\n")
    print(f"QC report -> {qc_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
