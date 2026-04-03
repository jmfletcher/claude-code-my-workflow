# Project Memory

Corrections and learned facts that persist across sessions.
When a mistake is corrected, append a `[LEARN:category]` entry below.

---

<!-- Append new entries below. Most recent at bottom. -->

## Wisconsin Schools Project (initialized 2026-04-03)

[LEARN:data] Primary data source is Wisconsin DPI Forward Exam downloads (CSV), accessed via WISEdash Public Portal or DPI direct download. School-level, broken down by race/ethnicity, grades 3–8, ELA and Math. Merge key is DPI/NCES school ID. See DATA.md for download instructions.

[LEARN:data] DPI suppresses cells where N < 10 students. Suppressed cells appear as `*` or blank in downloaded files. Decision: treat as NaN, do not impute, log to `output/tables/suppression_log.csv`. Report suppression rate in any summary of coverage.

[LEARN:data] Test type separation is non-negotiable: Forward Exam (grades 3–8), PreACT (9–10), ACT (11). Never mix in a single analysis without explicit cross-test documentation. Initial analysis focuses exclusively on Forward Exam.

[LEARN:data] DPI changed proficiency cut scores in recent years. Time trends that cross a standard-revision year are unreliable. Document the revision year as soon as data is inspected. Default to same-standard years for trend analysis.

[LEARN:analysis] MMSD comparison framework: two priority cross-district comparisons are (1) MMSD minority students vs. same-race students in Milwaukee / other WI districts, and (2) MMSD minority students vs. non-MMSD white students statewide. These address the outlier-SES problem — MMSD white students have very high parental education and income, so raw within-MMSD gaps overstate "typical" racial gaps.

[LEARN:analysis] Within–between decomposition: decompose statewide racial gap at three levels — county, district, school. Both weighted and unweighted versions needed. Components must sum to total gap ± 0.001 pp tolerance.

[LEARN:workflow] Deliverables for this project: Python analysis pipeline + school-level merged dataset + professional Quarto report (PDF) + Quarto RevealJS slide deck (PDF). Manuscript in manuscript/main.qmd, slides in Slides/main.qmd.

[LEARN:data] Forward Exam zip files contain two files: a data CSV and a layout CSV. Data CSV confirmed: 21 columns, 925K rows for 2022-23. Format is LONG: one row per school × grade × subject × GROUP_BY × GROUP_BY_VALUE × TEST_RESULT. Proficiency rate = sum of PERCENT_OF_GROUP for TEST_RESULT in ('Proficient', 'Advanced'). PERCENT_OF_GROUP is 0-100 scale. Suppression symbol is "*" in STUDENT_COUNT, PERCENT_OF_GROUP, GROUP_COUNT.

[LEARN:data] Race labels in DPI Forward Exam (GROUP_BY_VALUE when GROUP_BY=="Race/Ethnicity"): "White", "Black", "Hispanic", "Asian", "Amer Indian", "Pacific Isle", "Two or More", "Unknown", "[Data Suppressed]". Note: "Black" NOT "Black or African American".

[LEARN:data] MMSD district name in DPI data: "Madison Metropolitan". Filter: df[df.DISTRICT_NAME=="Madison Metropolitan"]. District-level rows have blank SCHOOL_CODE; school-level rows have populated SCHOOL_CODE.

[LEARN:data] TEST_GROUP column: use only "Forward" rows. "DLM" = Dynamic Learning Maps (students with severe disabilities tested on alternate assessment) — exclude from proficiency rate calculations.

[LEARN:data] Forward Exam available years: 2015-16, 2016-17, 2017-18, 2018-19, [2019-20 MISSING], 2020-21, 2021-22, 2022-23, 2023-24, 2024-25. Download script: python3 analysis/00_download_data.py --era forward. Files land in Data/raw/forward/.

[LEARN:data] 2023-24 and 2024-25 zips each contain TWO CSVs split by subject (ELA_RDG_WRT and MTH_SCN_SOC). Load script must concatenate both. 2015-16 through 2022-23 each have one CSV.

[LEARN:data] Race labels are IDENTICAL across all 9 Forward Exam years (confirmed 2026-04-03). All labels: "Amer Indian", "Asian", "Black", "Hispanic", "Pacific Isle", "Two or More", "Unknown", "White", "[Data Suppressed]". ELL Status → EL Status label change in 2020-21 onward (same concept).

[LEARN:data] AGENCY_TYPE values (full strings, not codes): "Public school" = school-level, "School District" = district-level, NaN = statewide, plus charter types. Do NOT use "03"/"04" codes — those are WINSS/old format.

[LEARN:data] Suppression in school panel: ~70-77% of cells suppressed (race group too small at school level). By race: Pacific Islander ~100%, American Indian ~94%, Black ~82%, White ~37%. Suppression = pct_proficient is NaN (no valid Proficient/Advanced rows for that group). n_tested is often non-NaN even for suppressed cells (group exists but performance breakdown is hidden).

[LEARN:analysis] Statewide Black–White ELA proficiency gap (grade 5, school-weighted): ~34-38 pp in primary years (2015-22). MMSD Black ELA grade 5: 7-16% proficient; MMSD White: 54-67%. Gap within MMSD: ~47-55 pp — much larger than statewide because MMSD White students are high-SES outliers.

[LEARN:data] Panel datasets saved to output/data/: panel_school_race.parquet (365K rows, ~1.8 MB), panel_district_race.parquet (171K rows, ~0.9 MB). School panel includes all years 2015-16 to 2024-25; use primary_analysis==True to filter to clean years.

[LEARN:analysis] TWO-ERA ANALYSIS FRAMEWORK: This project runs two separate, non-bridged analyses. (1) WKCE Era (2003-04 to 2013-14): statewide scale score data from Keo SSS TXT files; statewide and district-level mean scale scores and percentile distributions; 5→7 race categories change at 2010-11 boundary. (2) Forward Exam Era (2015-16 to present): school-level proficiency rates; primary window 2015-16 to 2022-23 (same standards, no COVID); new-standards sub-era 2023-24 onward labeled separately. Never trend across eras. 2014-15 (Smarter Balanced) is a permanent gap year.

[LEARN:data] Keo Data reorganized (2026-04-03): Raw WKCE SSS TXT files (64 files, 11 year-directories) copied to Data/raw/wkce_sss/. Excel and Stata compiled files archived to Data/archive/keo_compiled/ (reference only — do not use for analysis). The layout file layout_EXW_IAS_SPS_SSS (1).xls and MMSD Data Documentation.docx are also in Data/archive/keo_compiled/ for codebook reference.

[LEARN:analysis] PEER DISTRICT SUB-ANALYSIS: A curated set of Wisconsin districts with substantial and consistent Black AND Hispanic enrollment (n>=30, 5+ Forward Exam years) is used to compare MMSD minority students to comparable districts. From 82 eligible districts, the designated peer set is: (Tier 1 — major urban) Milwaukee, Racine Unified, Kenosha, Green Bay Area Public, Beloit; (Tier 2 — mid-size) Sun Prairie Area, Appleton Area, Waukesha, Janesville, West Allis-West Milwaukee; (Madison region) Verona Area, Middleton-Cross Plains Area. All peer comparisons should label which tier. Median district-level n_tested for Black students in primary years: Milwaukee ~30k, Racine ~3.8k, Madison ~3.7k, Kenosha ~2.5k, Green Bay ~1.4k, Beloit ~1.2k.

[LEARN:analysis] AGGREGATION STRATEGY (confirmed 2026-04-03): (1) Statewide decomposition → use district × race (district panel); suppression not a concern at this level. (2) MMSD within-district school analysis → use school × race (collapse across grade/subject); suppression drops to ~16% for Black, ~12% for Hispanic in MMSD — feasible. (3) Peer district comparison → use district × race for cross-district gaps; school × race within each peer district for within-district patterns.

## Workflow Patterns

[LEARN:workflow] Requirements specification phase catches ambiguity before planning → reduces rework 30-50%. Use spec-then-plan for complex/ambiguous tasks (>1 hour or >3 files).

[LEARN:workflow] Spec-then-plan protocol: AskUserQuestion (3-5 questions) → create `quality_reports/specs/YYYY-MM-DD_description.md` with MUST/SHOULD/MAY requirements → declare clarity status (CLEAR/ASSUMED/BLOCKED) → get approval → then draft plan.

[LEARN:workflow] Context survival before compression: (1) Update MEMORY.md with [LEARN] entries, (2) Ensure session log current (last 10 min), (3) Active plan saved to disk, (4) Open questions documented. The pre-compact hook displays checklist.

[LEARN:workflow] Plans, specs, and session logs must live on disk (not just in conversation) to survive compression and session boundaries. Quality reports only at merge time.

## Documentation Standards

[LEARN:documentation] When adding new features, update BOTH README and guide immediately to prevent documentation drift. Stale docs break user trust.

[LEARN:documentation] Always document new templates in README's "What's Included" section with purpose description. Template inventory must be complete and accurate.

[LEARN:documentation] Guide must be generic (framework-oriented) not prescriptive. Provide templates with examples for multiple workflows (LaTeX, R, Python, Jupyter), let users customize. No "thou shalt" rules.

[LEARN:documentation] Date fields in frontmatter and README must reflect latest significant changes. Users check dates to assess currency.

## Design Philosophy

[LEARN:design] Framework-oriented > Prescriptive rules. Constitutional governance works as a TEMPLATE with examples users customize to their domain. Same for requirements specs.

[LEARN:design] Quality standard for guide additions: useful + pedagogically strong + drives usage + leaves great impression + improves upon starting fresh + no redundancy + not slow. All 7 criteria must hold.

[LEARN:design] Generic means working for any academic workflow: pure LaTeX (no Quarto), pure R (no LaTeX), Python/Jupyter, any domain (not just econometrics). Test recommendations across use cases.

## File Organization

[LEARN:files] Specifications go in `quality_reports/specs/YYYY-MM-DD_description.md`, not scattered in root or other directories. Maintains structure.

[LEARN:files] Templates belong in `templates/` directory with descriptive names. Currently have: session-log.md, quality-report.md, exploration-readme.md, archive-readme.md, requirements-spec.md, constitutional-governance.md.

## Constitutional Governance

[LEARN:governance] Constitutional articles distinguish immutable principles (non-negotiable for quality/reproducibility) from flexible user preferences. Keep to 3-7 articles max.

[LEARN:governance] Example articles: Primary Artifact (which file is authoritative), Plan-First Threshold (when to plan), Quality Gate (minimum score), Verification Standard (what must pass), File Organization (where files live).

[LEARN:governance] Amendment process: Ask user if deviating from article is "amending Article X (permanent)" or "overriding for this task (one-time exception)". Preserves institutional memory.

## Skill Creation

[LEARN:skills] Effective skill descriptions use trigger phrases users actually say: "check citations", "format results", "validate protocol" → Claude knows when to load skill.

[LEARN:skills] Skills need 3 sections minimum: Instructions (step-by-step), Examples (concrete scenarios), Troubleshooting (common errors) → users can debug independently.

[LEARN:skills] Domain-specific examples beat generic ones: citation checker (psychology), protocol validator (biology), regression formatter (economics) → shows adaptability.

## Memory System

[LEARN:memory] Two-tier memory solves template vs working project tension: MEMORY.md (generic patterns, committed), personal-memory.md (machine-specific, gitignored) → cross-machine sync + local privacy.

[LEARN:memory] Post-merge hooks prompt reflection, don't auto-append → user maintains control while building habit.

## Meta-Governance

[LEARN:meta] Repository dual nature requires explicit governance: what's generic (commit) vs specific (gitignore) → prevents template pollution.

[LEARN:meta] Dogfooding principles must be enforced: plan-first, spec-then-plan, quality gates, session logs → we follow our own guide.

[LEARN:meta] Template development work (building infrastructure, docs) doesn't create session logs in quality_reports/ → those are for user work (slides, analysis), not meta-work. Keeps template clean for users who fork.
