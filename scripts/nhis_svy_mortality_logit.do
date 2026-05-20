*! Survey-weighted adult mortality (NHIS Linked Mortality Files, 1986-2018)
*! ----------------------------------------------------------------------------
*! Question: Do roster-based co-resident minor children (count and mean age)
*!           predict adult mortality after age, sex, race/ethnicity, period FE?
*!
*! Design  : svyset psu [pweight=mortwtsa], strata(strata) singleunit(scale)
*! Outcome : died = (mortstat==1) | (mortstat==2)  among mortelig==1
*!
*! Samples (run BOTH; results stored & exported with sample suffix):
*!   1) parent  - parentrole_hh==1, age 18-64  (primary; cleaner attribution)
*!   2) all     - age 18+                       (sensitivity / appendix)
*!
*! Caveats (see also results/README.md):
*!   - RELATE is to the householder, NOT to each adult; the primary sample
*!     restricts to plausible parents to limit attribution noise.
*!   - Co-residence != completed parity; nonresident minor children invisible.
*!   - These are weighted associations, NOT a causal effect of fertility on
*!     mortality; output is intended to calibrate kinship-model assumptions
*!     (see deep-research-report.md).
*!
*! Outputs (relative to project root):
*!   nhis_svy_mort_ready.dta                          analytic frame
*!   results/coef_<model>_<sample>.csv                tidy coefficients
*!   results/jointtests_<sample>.csv                  joint Wald tests
*!   results/qc_nkf_x_raceth5_<sample>.csv            descriptive QC table
*!   results/margins_pr_died_<sample>.csv             adjusted probabilities
*!   results/marginsplot_<sample>.gph                 figure
*! ----------------------------------------------------------------------------

version 17
clear all
set more off
set linesize 120

local proj "`c(pwd)'"
capture mkdir "`proj'/results"

/*-----------------------------------------------------------------------------
   0. Load roster-enhanced file (build it if absent)
-----------------------------------------------------------------------------*/

capture confirm file "`proj'/nhis_with_coresident_minors.dta"
if _rc {
    quietly do "`proj'/scripts/nhis_coresident_minors.do"
}

capture confirm file "`proj'/nhis_with_coresident_minors.dta"
if _rc {
    di as error "ERROR: cannot find nhis_with_coresident_minors.dta. cd to project root and retry."
    exit 603
}

use "`proj'/nhis_with_coresident_minors.dta", clear

/*-----------------------------------------------------------------------------
   1. Mortality outcome
-----------------------------------------------------------------------------*/

gen byte died = .
replace died = 1 if mortelig == 1 & mortstat == 1
replace died = 0 if mortelig == 1 & mortstat == 2
label var died "Deceased by linkage cutoff (NHIS-LMF)"

/*-----------------------------------------------------------------------------
   2. Race / ethnicity (5 cats, ref = NH White; bridges racenew & racea)
-----------------------------------------------------------------------------*/

gen byte hisp_eth = inrange(hispeth, 20, 70)

gen byte race_nhx = .

* Post-1997 OMB single-race buckets first
replace race_nhx = 1 if !hisp_eth & racenew == 100                              // White
replace race_nhx = 2 if !hisp_eth & racenew == 200                              // Black
replace race_nhx = 3 if !hisp_eth & racenew == 400                              // Asian only
replace race_nhx = 4 if !hisp_eth & racenew == 300                              // AIAN only

* Pre-1997 racea cascade
replace race_nhx = 1 if missing(race_nhx) & !hisp_eth & racea == 100
replace race_nhx = 2 if missing(race_nhx) & !hisp_eth & racea == 200
replace race_nhx = 3 if missing(race_nhx) & !hisp_eth                           ///
    & inlist(racea, 400, 410, 411, 412, 413, 414, 415, 416, 417, 419,            ///
                    420, 430, 431, 432, 433, 434)
replace race_nhx = 4 if missing(race_nhx) & !hisp_eth                           ///
    & inlist(racea, 300, 310, 320, 330, 340, 350)
replace race_nhx = 5 if missing(race_nhx) & !hisp_eth                           // other/mult/unclass

gen byte raceth5 = .
replace raceth5 = 1 if hisp_eth
replace raceth5 = 2 if !hisp_eth & race_nhx == 1
replace raceth5 = 3 if !hisp_eth & race_nhx == 2
replace raceth5 = 4 if !hisp_eth & race_nhx == 3
replace raceth5 = 5 if !hisp_eth & inlist(race_nhx, 4, 5)
replace raceth5 = 5 if missing(raceth5)

label define raceth5lbl                                                          ///
    1 "Hispanic"                                                                 ///
    2 "Non-Hisp White"                                                           ///
    3 "Non-Hisp Black"                                                           ///
    4 "Non-Hisp Asian/PI"                                                        ///
    5 "Non-Hisp AIAN/Other/Multiple"
label values raceth5 raceth5lbl
label var raceth5 "Race/ethnicity (5 cats; bridged racenew+racea)"

/*-----------------------------------------------------------------------------
   3. Co-resident minor children (count + mean age)
-----------------------------------------------------------------------------*/

gen double nk_under18 = n_fam_childminor017
replace    nk_under18 = 0 if missing(nk_under18) | nk_under18 < 0
replace    nk_under18 = 8 if nk_under18 > 8 & !missing(nk_under18)
label var  nk_under18 "Co-res minors <=17 (family unit; capped at 8)"

gen byte   has_minor = nk_under18 > 0
gen double minors_mean_age_ctr = 0
replace    minors_mean_age_ctr = hh_mean_child_age if has_minor & !missing(hh_mean_child_age)
label var  minors_mean_age_ctr "Mean age of co-res minors (0 if none)"

recode nk_under18 (0=0)(1=1)(2=2)(3/8=3), gen(nkf)
label define nkf_lab 0 "0 minors" 1 "1 minor" 2 "2 minors" 3 "3+ minors"
label values nkf nkf_lab
label var nkf "Co-res minors (factor, 3+ collapsed)"

/*-----------------------------------------------------------------------------
   4. Adult age, sex, period (decade) fixed effects
-----------------------------------------------------------------------------*/

gen double age_c = age
label var age_c "Age (centered after sample selection)"

gen byte yeardec = .
replace yeardec = 1 if inrange(year, 1986, 1989)
replace yeardec = 2 if inrange(year, 1990, 1999)
replace yeardec = 3 if inrange(year, 2000, 2009)
replace yeardec = 4 if inrange(year, 2010, 2018)
label define yeardec_lab 1 "1986-1989" 2 "1990s" 3 "2000s" 4 "2010-2018"
label values yeardec yeardec_lab
label var yeardec "NHIS interview period (decade bin)"

/*-----------------------------------------------------------------------------
   5. Sample flags: parent-role primary + all-adults sensitivity
-----------------------------------------------------------------------------*/

gen byte common_ok =                                                             ///
       inlist(astatflg, 1, 6)                                                    ///
     & inlist(sex, 1, 2)                                                         ///
     & inlist(died, 0, 1)                                                        ///
     & !missing(strata, psu, mortwtsa)                                           ///
     & mortwtsa > 0                                                              ///
     & !missing(raceth5) & !missing(yeardec)

gen byte subpop_all    = common_ok & adult_agerestr == 1
gen byte subpop_parent = common_ok & parentrole_hh == 1 & inrange(age, 18, 64)

label var subpop_all    "Adults 18+ (sensitivity sample)"
label var subpop_parent "Parent-role adults 18-64 (primary sample)"

quietly count if subpop_all
local n_all = r(N)
quietly count if subpop_parent
local n_parent = r(N)
di as txt "Sample sizes: parent=`n_parent'  all=`n_all'"

/*-----------------------------------------------------------------------------
   6. Survey design
-----------------------------------------------------------------------------*/

capture svyset, clear
svyset psu [pweight=mortwtsa], strata(strata) singleunit(scale)

/*-----------------------------------------------------------------------------
   7. Model loop over the two samples
-----------------------------------------------------------------------------*/

* helper to write a tidy coefficient CSV from r(table)
capture program drop _export_coef
program define _export_coef
    syntax , model(string) sample(string) outdir(string)
    matrix b = r(table)
    local cols : colnames b
    local nc   : word count `cols'

    tempname fh
    file open `fh' using "`outdir'/coef_`model'_`sample'.csv", write replace
    file write `fh' "term,b,se,z,pvalue,ll,ul" _n
    forvalues j = 1/`nc' {
        local term : word `j' of `cols'
        local b_val   = b[1,`j']
        local se_val  = b[2,`j']
        local z_val   = b[3,`j']
        local p_val   = b[4,`j']
        local ll_val  = b[5,`j']
        local ul_val  = b[6,`j']
        file write `fh' `"`term'"' "," "`b_val'" "," "`se_val'" "," "`z_val'" ","   ///
                        "`p_val'" "," "`ll_val'" "," "`ul_val'" _n
    }
    file close `fh'
end

* tidy joint-test row appender
capture program drop _append_jt
program define _append_jt
    syntax , file(string) label(string)
    local F   = r(F)
    local df1 = r(df)
    local df2 = r(df_r)
    local p   = r(p)
    file write `file' `"`label'"' "," "`F'" "," "`df1'" "," "`df2'" "," "`p'" _n
end

foreach sample in parent all {

    di _n(2) "{hline 78}"
    di as txt "Running sample: `sample'"
    di "{hline 78}"

    local flag subpop_`sample'

    /* Center age within sample so age_c interpretable */
    quietly summarize age if `flag', meanonly
    quietly replace age_c = age - r(mean) if `flag'

    tempname jt
    file open `jt' using "`proj'/results/jointtests_`sample'.csv", write replace
    file write `jt' "test,F,df1,df2,pvalue" _n

    /* ---- M_full: count + mean age ---- */
    svy linearized, subpop(`flag'): logistic died                                ///
        ib2.sex c.age_c c.age_c#c.age_c ib2.raceth5 i.yeardec                     ///
        c.nk_under18 c.minors_mean_age_ctr
    estimates store mfull_`sample'
    _export_coef, model("mfull") sample("`sample'") outdir("`proj'/results")

    test nk_under18 minors_mean_age_ctr
    _append_jt, file(`jt') label("mfull_joint_nk_meanage")

    test nk_under18
    _append_jt, file(`jt') label("mfull_nk_only")

    test minors_mean_age_ctr
    _append_jt, file(`jt') label("mfull_meanage_only")

    /* ---- M_counts: count only ---- */
    svy linearized, subpop(`flag'): logistic died                                ///
        ib2.sex c.age_c c.age_c#c.age_c ib2.raceth5 i.yeardec                     ///
        c.nk_under18
    estimates store mcounts_`sample'
    _export_coef, model("mcounts") sample("`sample'") outdir("`proj'/results")

    test nk_under18
    _append_jt, file(`jt') label("mcounts_nk")

    /* ---- M_fact: factor count ---- */
    svy linearized, subpop(`flag'): logistic died                                ///
        ib2.sex c.age_c c.age_c#c.age_c ib2.raceth5 i.yeardec                     ///
        ib0.nkf c.minors_mean_age_ctr
    estimates store mfact_`sample'
    _export_coef, model("mfact") sample("`sample'") outdir("`proj'/results")

    testparm i.nkf
    _append_jt, file(`jt') label("mfact_joint_nkf")

    test minors_mean_age_ctr
    _append_jt, file(`jt') label("mfact_meanage")

    /* ---- M_int: count x mean age interaction ---- */
    svy linearized, subpop(`flag'): logistic died                                ///
        ib2.sex c.age_c c.age_c#c.age_c ib2.raceth5 i.yeardec                     ///
        c.nk_under18##c.minors_mean_age_ctr
    estimates store mint_`sample'
    _export_coef, model("mint") sample("`sample'") outdir("`proj'/results")

    test c.nk_under18#c.minors_mean_age_ctr
    _append_jt, file(`jt') label("mint_interaction")

    test nk_under18 minors_mean_age_ctr c.nk_under18#c.minors_mean_age_ctr
    _append_jt, file(`jt') label("mint_joint_all_kid_terms")

    file close `jt'

    /* ---- Adjusted Pr(died) by nk_under18 from M_full ---- */
    quietly estimates restore mfull_`sample'
    capture noisily margins, at(nk_under18=(0(1)4)) subpop(`flag') predict(pr) post
    if !_rc {
        matrix M = r(b)
        matrix V = r(V)
        tempname fhm
        file open `fhm' using "`proj'/results/margins_pr_died_`sample'.csv", write replace
        file write `fhm' "nk_under18,pr,se" _n
        local kvals 0 1 2 3 4
        local i = 0
        foreach kv of local kvals {
            local ++i
            local b_i = M[1,`i']
            local v_i = V[`i',`i']
            local se_i = sqrt(`v_i')
            file write `fhm' "`kv',`b_i',`se_i'" _n
        }
        file close `fhm'

        quietly estimates restore mfull_`sample'
        capture noisily margins, at(nk_under18=(0(1)4)) subpop(`flag') predict(pr)
        if !_rc {
            capture marginsplot, name(marg_`sample', replace)                    ///
                title("Adjusted Pr(died) by # co-res minors - `sample' sample")  ///
                ytitle("Adjusted Pr(died)") xtitle("# co-res minors (capped)")
            capture graph save  "`proj'/results/marginsplot_`sample'.gph", replace
            capture graph export "`proj'/results/marginsplot_`sample'.png", replace
        }
    }
}

/*-----------------------------------------------------------------------------
   8. QC: weighted/unweighted death rates by nkf x raceth5
-----------------------------------------------------------------------------*/

foreach sample in parent all {

    local flag subpop_`sample'

    preserve
        keep if `flag'
        tempfile qctmp
        gen double n_uw = 1
        gen double w    = mortwtsa
        gen double died_uw = died
        gen double died_w  = died * mortwtsa

        collapse (sum) n_uw n_w=w died_uw died_w, by(nkf raceth5)

        gen double rate_uw  = died_uw / n_uw
        gen double rate_wtd = died_w  / n_w

        label values nkf nkf_lab
        label values raceth5 raceth5lbl

        export delimited using "`proj'/results/qc_nkf_x_raceth5_`sample'.csv", replace
    restore
}

/*-----------------------------------------------------------------------------
   9. Save analytic frame for downstream use
-----------------------------------------------------------------------------*/

compress
save "`proj'/nhis_svy_mort_ready.dta", replace

/*-----------------------------------------------------------------------------
   10. Summary print
-----------------------------------------------------------------------------*/

di _n(2) "{hline 78}"
di as txt "Stored estimates:"
estimates dir
di _n "Outputs written under: `proj'/results/"
di "  coef_<model>_<sample>.csv         tidy coefficient tables"
di "  jointtests_<sample>.csv           joint Wald tests"
di "  margins_pr_died_<sample>.csv      adjusted Pr(died) by nk"
di "  marginsplot_<sample>.{gph,png}    figure"
di "  qc_nkf_x_raceth5_<sample>.csv     descriptive death-rate QC"
di "{hline 78}"
