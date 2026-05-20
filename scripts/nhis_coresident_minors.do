*! Co-resident minor children from NHIS rectangular roster → household/family aggregates
*! Intended use: calibrate "children exposed if this adult dies" proxies vs demographic schedules.
*
* Prerequisites:
*   1. Working directory must be the folder that contains nhis_00002.dat
*   2. Raw person file already loaded OR run load block below once.
*
* Limitations:
*   - RELATE is to the householder, not to each adult; minors are attributed at HH/family level.
*   - Grandchildren / other relatives excluded from counts (see CHILD_REL_CODES).
*   - Pre-1997: FMX unavailable in extract codebook → use household-level counts only.
*
* ----------------------------------------------------------------------------

version 17

/*-----------------------------------------------------------------------------
   Load microdata when not already in memory (same infix spec as root nhis_00002.do)
-----------------------------------------------------------------------------*/

capture confirm variable serial
if (_rc != 0) {
	clear
	quietly infix                  ///
	  int     year        1-4      ///
	  long    serial      5-10     ///
	  int     numprec     11-13    ///
	  int     strata      14-17    ///
	  int     psu         18-20    ///
	  str     nhishid     21-34    ///
	  long    hhweight    35-40    ///
	  byte    region      41-42    ///
	  byte    pernum      43-44    ///
	  str     nhispid     45-60    ///
	  str     hhx         61-67    ///
	  str     fmx         68-69    ///
	  str     px          70-71    ///
	  double  perweight   72-83    ///
	  double  sampweight  84-95    ///
	  double  fweight     96-107   ///
	  double  supp3wt     108-116  ///
	  byte    intervwmo   117-118  ///
	  int     intervwyr   119-122  ///
	  byte    astatflg    123-123  ///
	  byte    cstatflg    124-124  ///
	  byte    screspond   125-126  ///
	  byte    respond     127-128  ///
	  int     age         129-131  ///
	  byte    sex         132-132  ///
	  byte    sexorien    133-133  ///
	  byte    marstcur    134-134  ///
	  byte    marstat     135-136  ///
	  byte    marst       137-138  ///
	  byte    marstcohab  139-139  ///
	  byte    cohabmarst  140-140  ///
	  byte    cohabevmar  141-141  ///
	  byte    birthmo     142-143  ///
	  int     birthyr     144-147  ///
	  byte    relate      148-149  ///
	  int     racenew     150-152  ///
	  int     racea       153-155  ///
	  byte    hispeth     156-157  ///
	  int     racesr      158-160  ///
	  byte    educrec2    161-162  ///
	  byte    educrec1    163-164  ///
	  byte    mortelig    165-165  ///
	  byte    mortstat    166-166  ///
	  byte    mortdodq    167-167  ///
	  int     mortdody    168-171  ///
	  byte    mortucodld  172-173  ///
	  double  mortwt      174-181  ///
	  double  mortwtsa    182-189  ///
	  using `"nhis_00002.dat"'

	replace sampweight = sampweight / 1000
	replace fweight    = fweight    / 1000000

	format mortwt mortwtsa %12.0f
}

/*-----------------------------------------------------------------------------
   Roster-based minor children counts
-----------------------------------------------------------------------------*/

* NHIS RELATE codes: child / child of HH or partner only (omit grandchild=60 etc.)
gen byte hh_childminor = inrange(age, 0, 17)                                   ///
                       & age < .                                                  ///
                       & inlist(relate, 40, 41, 43, 44)

label define hh_childminor_lbl 0 "Not minor child-rel-to-HH roster line"      ///
                                     1 "Minor, RELATE suggests HH/partner kid"
label values hh_childminor hh_childminor_lbl

* Family number for 1997+ (missing / invalid → fall back below)
bysort year serial: egen n_hh_childminor017 = total(hh_childminor)

gen double fmxn = real(trim(itrim(fmx)))
replace fmxn = . if year < 1997

gen byte _fam_ok = !missing(fmxn) & year >= 1997
bys year serial fmxn: egen n_fam_childminor017 = total(hh_childminor) if _fam_ok
replace n_fam_childminor017 = n_hh_childminor017 if missing(n_fam_childminor017)
drop _fam_ok

* Age span among flagged minor children only
gen double _age_if_minor = age if hh_childminor
bys year serial: egen hh_min_child_age = min(_age_if_minor)
bys year serial: egen hh_max_child_age = max(_age_if_minor)
bys year serial: egen hh_mean_child_age = mean(_age_if_minor)
drop _age_if_minor

label var fmxn "NHIS family number (parsed; use 1997+ only)"

label var n_hh_childminor017 "Co-res minors (RELATE kid codes 40/41/43/44, age≤17)"
label var n_fam_childminor017 "Minor kids in same family unit (approx 1997+; else HH)"
label var hh_min_child_age "Min age among minors in hh_childminor"
label var hh_max_child_age "Max age among minors in hh_childminor"
label var hh_mean_child_age "Mean age among minors (. if none in hh_childminor set)"

* Adults for person-level estimation (topcode sentinel ages handled by survey)
gen byte adult_agerestr = age >= 18 & age != . & !(age >= 997)
label var adult_agerestr "Age 18+ with numeric age"

* Optional: flag likely parent role (householder or spouse / unmarried partner)
gen byte parentrole_hh = inlist(relate, 10, 20, 21, 22, 30)
label var parentrole_hh "Householder spouse partner (coarse)"

compress
save "`c(pwd)'/nhis_with_coresident_minors.dta", replace

di as text `"Saved: "`c(pwd)'/nhis_with_coresident_minors.dta" — merge keys: YEAR SERIAL PERNUM NHISPID"'


noi di ""
noi di "Next steps (examples; weight & design vary by substantive question):"
noi di "  * Tabulate co-res minors by mortality-eligible sample adults:"
noi di `". tab n_hh_childminor017 mortstat if mortelig==1 & adult_agerestr==1"'

