# Data

## `input/` — Source Data (Read-Only)

WISH (Wisconsin Interactive Statistics on Health) PDF tables. **Do not modify these files.**

| File | Content |
|------|---------|
| Dane County Births by race and year.pdf | Births by race and year (Dane County) |
| Dane County Infant Mortality Count By Race.pdf | Infant deaths by race and year (Dane County) |
| Milwaukee birth counts by race.pdf | Births by race and year (Milwaukee County) |
| Milwaukee county infant death counts by race.pdf | Infant deaths by race and year (Milwaukee County) |
| State birth counts by race.pdf | Births by race and year (Wisconsin statewide) |
| State infant death counts by race.pdf | Infant deaths by race and year (Wisconsin statewide) |
| WISH — Infant Mortality Module Query Results.pdf | Dane infant deaths by year (WISH module query) |

## `processed/` — Generated CSVs

Produced by Attempt 1's Python scripts (copied here as starting data). Can be regenerated from the input PDFs if needed.

| File | Columns | Content |
|------|---------|---------|
| dane_county_infant_deaths_by_year.csv | year, county, infant_deaths | Total Dane infant deaths by year (1999–2023) |
| dane_infant_mortality_by_race.csv | year, race, births, deaths, rate_per_1000, rate_lo, rate_hi | Dane rates by race with 95% Poisson CIs |
| state_infant_mortality_by_race.csv | (same) | Statewide rates by race |
| milwaukee_infant_mortality_by_race.csv | (same) | Milwaukee rates by race |
| rest_of_wisconsin_infant_mortality_by_race.csv | (same) | Rest of WI = State − Milwaukee − Dane |

### Suppression Handling

WISH suppresses counts of 1–4 with "X". Black counts are imputed as **Total − White** when suppressed. This is documented in the report and in the Python scripts.
