* NOTE: You need to set the Stata working directory to the path
* where the data file is located.

set more off

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

format perweight  %12.0f
format sampweight %12.3f
format fweight    %12.6f
format supp3wt    %9.0f
format mortwt     %8.0f
format mortwtsa   %8.0f

label var year       `"Survey year"'
label var serial     `"Sequential Serial Number, Household Record"'
label var numprec    `"Number of person records in household"'
label var strata     `"Stratum for variance estimation"'
label var psu        `"Primary sampling unit (PSU) for variance estimation"'
label var nhishid    `"NHIS Unique identifier, household"'
label var hhweight   `"Household weight, final annual"'
label var region     `"Region of residence"'
label var pernum     `"Person number within family/household (from reformatting)"'
label var nhispid    `"NHIS Unique Identifier, person"'
label var hhx        `"Household number (from NHIS)"'
label var fmx        `"Family number (from NHIS)"'
label var px         `"Person number of respondent (from NHIS)."'
label var perweight  `"Final basic annual weight"'
label var sampweight `"Sample Person Weight"'
label var fweight    `"Final annual family weight"'
label var supp3wt    `"Supplemental Person Weight 3"'
label var intervwmo  `"Month of NHIS interview"'
label var intervwyr  `"Year of NHIS interview"'
label var astatflg   `"Sample adult flag"'
label var cstatflg   `"Sample child flag"'
label var screspond  `"Relationship of respondent to sample child"'
label var respond    `"Respondent"'
label var age        `"Age"'
label var sex        `"Sex"'
label var sexorien   `"Sexual orientation"'
label var marstcur   `"Current marital status"'
label var marstat    `"Legal marital status"'
label var marst      `"Current marital status"'
label var marstcohab `"Marital status, including living with partner"'
label var cohabmarst `"Legal marital status of cohabiting person"'
label var cohabevmar `"Cohabiting person ever married"'
label var birthmo    `"Month of birth"'
label var birthyr    `"Year of birth"'
label var relate     `"Relationship to householder"'
label var racenew    `"Self-reported Race (Post-1997 OMB standards)"'
label var racea      `"Main Racial Background (Pre-1997 Revised OMB Standards), self-reported or interv"'
label var hispeth    `"Hispanic ethnicity"'
label var racesr     `"Self-Reported Main Racial Background (Pre-1997 Revised OMB Standards)"'
label var educrec2   `"Educational attainment recode, intervalled"'
label var educrec1   `"Educational attainment recode, nonintervalled"'
label var mortelig   `"Eligibility status for mortality follow-up"'
label var mortstat   `"Final mortality status"'
label var mortdodq   `"Quarter of death"'
label var mortdody   `"Year of death"'
label var mortucodld `"Leading underlying cause of death (ICD-10)"'
label var mortwt     `"Weight adjusted for ineligible respondents in mortality analysis"'
label var mortwtsa   `"Sample adult weight adjusted for ineligible respondents in mortality analysis"'

label define region_lbl 01 `"Northeast"'
label define region_lbl 02 `"North Central/Midwest"', add
label define region_lbl 03 `"South"', add
label define region_lbl 04 `"West"', add
label define region_lbl 08 `"NO DATA IN ROUND"', add
label define region_lbl 09 `"Unknown"', add
label values region region_lbl

label define intervwmo_lbl 01 `"January"'
label define intervwmo_lbl 02 `"February"', add
label define intervwmo_lbl 03 `"March"', add
label define intervwmo_lbl 04 `"April"', add
label define intervwmo_lbl 05 `"May"', add
label define intervwmo_lbl 06 `"June"', add
label define intervwmo_lbl 07 `"July"', add
label define intervwmo_lbl 08 `"August"', add
label define intervwmo_lbl 09 `"September"', add
label define intervwmo_lbl 10 `"October"', add
label define intervwmo_lbl 11 `"November"', add
label define intervwmo_lbl 12 `"December"', add
label define intervwmo_lbl 98 `"Unknown-not ascertained"', add
label values intervwmo intervwmo_lbl

label define astatflg_lbl 0 `"NIU"'
label define astatflg_lbl 1 `"Sample adult, has record"', add
label define astatflg_lbl 2 `"Sample adult, no record"', add
label define astatflg_lbl 3 `"Not selected as sample adult"', add
label define astatflg_lbl 4 `"No one selected as sample adult"', add
label define astatflg_lbl 5 `"Armed forces member"', add
label define astatflg_lbl 6 `"AF member, selected as sample adult"', add
label values astatflg astatflg_lbl

label define cstatflg_lbl 0 `"NIU"'
label define cstatflg_lbl 1 `"Sample child-has record"', add
label define cstatflg_lbl 2 `"Sample child-no record"', add
label define cstatflg_lbl 3 `"Not selected as sample child"', add
label define cstatflg_lbl 4 `"No one selected as sample child"', add
label define cstatflg_lbl 5 `"Emancipated minor"', add
label values cstatflg cstatflg_lbl

label define screspond_lbl 00 `"NIU"'
label define screspond_lbl 10 `"Parent (biological, adoptive, or step)"', add
label define screspond_lbl 11 `"Mother"', add
label define screspond_lbl 12 `"Father"', add
label define screspond_lbl 20 `"Grandparent"', add
label define screspond_lbl 30 `"Aunt/uncle"', add
label define screspond_lbl 40 `"Brother/sister"', add
label define screspond_lbl 50 `"Other relative"', add
label define screspond_lbl 51 `"Other relative or other non-relative"', add
label define screspond_lbl 60 `"Legal guardian"', add
label define screspond_lbl 70 `"Foster parent"', add
label define screspond_lbl 80 `"Other non-relative"', add
label define screspond_lbl 91 `"Self"', add
label define screspond_lbl 92 `"Spouse"', add
label define screspond_lbl 97 `"Unknown-refused"', add
label define screspond_lbl 98 `"Unknown-not ascertained"', add
label define screspond_lbl 99 `"Unknown-don't know"', add
label values screspond screspond_lbl

label define respond_lbl 00 `"NIU (Under 17)"'
label define respond_lbl 20 `"Self entirely"', add
label define respond_lbl 30 `"Self partly"', add
label define respond_lbl 40 `"Proxy"', add
label define respond_lbl 41 `"Spouse"', add
label define respond_lbl 42 `"Mother"', add
label define respond_lbl 43 `"Father"', add
label define respond_lbl 44 `"Other female family member"', add
label define respond_lbl 45 `"Other male family member"', add
label define respond_lbl 46 `"Other"', add
label define respond_lbl 99 `"Unknown/not reported"', add
label values respond respond_lbl

label define sex_lbl 1 `"Male"'
label define sex_lbl 2 `"Female"', add
label define sex_lbl 7 `"Unknown-refused"', add
label define sex_lbl 8 `"Unknown-not ascertained"', add
label define sex_lbl 9 `"Unknown-don't know"', add
label values sex sex_lbl

label define sexorien_lbl 0 `"NIU"'
label define sexorien_lbl 1 `"Lesbian or gay"', add
label define sexorien_lbl 2 `"Straight, that is, not lesbian or gay"', add
label define sexorien_lbl 3 `"Bisexual"', add
label define sexorien_lbl 4 `"Something else"', add
label define sexorien_lbl 5 `"I don't know the answer"', add
label define sexorien_lbl 7 `"Unknown-refused"', add
label define sexorien_lbl 8 `"Unknown-not ascertained"', add
label values sexorien sexorien_lbl

label define marstcur_lbl 0 `"NIU"'
label define marstcur_lbl 1 `"Married, spouse present"', add
label define marstcur_lbl 2 `"Married, spouse absent"', add
label define marstcur_lbl 3 `"Married, spouse in household unknown"', add
label define marstcur_lbl 4 `"Separated"', add
label define marstcur_lbl 5 `"Divorced"', add
label define marstcur_lbl 6 `"Widowed"', add
label define marstcur_lbl 7 `"Living with partner"', add
label define marstcur_lbl 8 `"Never married"', add
label define marstcur_lbl 9 `"Unknown marital status"', add
label values marstcur marstcur_lbl

label define marstat_lbl 00 `"NIU"'
label define marstat_lbl 10 `"Married"', add
label define marstat_lbl 11 `"Married - Spouse present"', add
label define marstat_lbl 12 `"Married - Spouse not in household"', add
label define marstat_lbl 13 `"Married - Spouse in household unknown"', add
label define marstat_lbl 20 `"Widowed"', add
label define marstat_lbl 30 `"Divorced"', add
label define marstat_lbl 40 `"Separated"', add
label define marstat_lbl 50 `"Never married"', add
label define marstat_lbl 99 `"Unknown marital status"', add
label values marstat marstat_lbl

label define marst_lbl 00 `"NIU"'
label define marst_lbl 10 `"Married"', add
label define marst_lbl 11 `"Married - Spouse present"', add
label define marst_lbl 12 `"Married - Spouse not in household"', add
label define marst_lbl 13 `"Married - Spouse in household unknown"', add
label define marst_lbl 20 `"Widowed"', add
label define marst_lbl 30 `"Divorced"', add
label define marst_lbl 40 `"Separated"', add
label define marst_lbl 50 `"Never married"', add
label define marst_lbl 99 `"Unknown marital status"', add
label values marst marst_lbl

label define marstcohab_lbl 0 `"NIU"'
label define marstcohab_lbl 1 `"Married, spouse present"', add
label define marstcohab_lbl 2 `"Married, spouse absent"', add
label define marstcohab_lbl 3 `"Married, spouse in household unknown"', add
label define marstcohab_lbl 4 `"Separated"', add
label define marstcohab_lbl 5 `"Divorced"', add
label define marstcohab_lbl 6 `"Widowed"', add
label define marstcohab_lbl 7 `"Living with partner"', add
label define marstcohab_lbl 8 `"Never married"', add
label define marstcohab_lbl 9 `"Unknown marital status"', add
label values marstcohab marstcohab_lbl

label define cohabmarst_lbl 0 `"NIU"'
label define cohabmarst_lbl 1 `"Married"', add
label define cohabmarst_lbl 2 `"Widowed"', add
label define cohabmarst_lbl 3 `"Divorced"', add
label define cohabmarst_lbl 4 `"Separated"', add
label define cohabmarst_lbl 7 `"Unknown-refused"', add
label define cohabmarst_lbl 8 `"Unknown-not ascertained"', add
label define cohabmarst_lbl 9 `"Unknown-don't know"', add
label values cohabmarst cohabmarst_lbl

label define cohabevmar_lbl 0 `"NIU"'
label define cohabevmar_lbl 1 `"Not married"', add
label define cohabevmar_lbl 2 `"Married"', add
label define cohabevmar_lbl 7 `"Unknown-refused"', add
label define cohabevmar_lbl 8 `"Unknown-not ascertained"', add
label define cohabevmar_lbl 9 `"Unknown-don't know"', add
label values cohabevmar cohabevmar_lbl

label define birthmo_lbl 00 `"NIU"'
label define birthmo_lbl 01 `"January"', add
label define birthmo_lbl 02 `"February"', add
label define birthmo_lbl 03 `"March"', add
label define birthmo_lbl 04 `"April"', add
label define birthmo_lbl 05 `"May"', add
label define birthmo_lbl 06 `"June"', add
label define birthmo_lbl 07 `"July"', add
label define birthmo_lbl 08 `"August"', add
label define birthmo_lbl 09 `"September"', add
label define birthmo_lbl 10 `"October"', add
label define birthmo_lbl 11 `"November"', add
label define birthmo_lbl 12 `"December"', add
label define birthmo_lbl 97 `"Unknown-refused"', add
label define birthmo_lbl 98 `"Unknown-not ascertained"', add
label define birthmo_lbl 99 `"Unknown-don't know"', add
label values birthmo birthmo_lbl

label define relate_lbl 10 `"Householder"'
label define relate_lbl 20 `"Spouse"', add
label define relate_lbl 21 `"Spouse, other spouse at home and NOT in Armed forces"', add
label define relate_lbl 22 `"Spouse, other spouse at home and in Armed Forces"', add
label define relate_lbl 30 `"Unmarried partner"', add
label define relate_lbl 40 `"Child"', add
label define relate_lbl 41 `"Child (bio/adopt/in-law/step/foster) of householder"', add
label define relate_lbl 43 `"Child of partner"', add
label define relate_lbl 44 `"Child of ineligible householder"', add
label define relate_lbl 50 `"Other relative 1  (not wife, child)"', add
label define relate_lbl 60 `"Grandchild"', add
label define relate_lbl 70 `"Other relative 2 (not grandkid, child, spouse, parent)"', add
label define relate_lbl 71 `"Parent (bio/adopt/in-law/step/foster) of householder"', add
label define relate_lbl 72 `"Brother/sister (bio/adopt/in-law/step/foster)"', add
label define relate_lbl 73 `"Grandparent (Grandma/Grandpa)"', add
label define relate_lbl 74 `"Aunt/uncle"', add
label define relate_lbl 75 `"Niece/nephew"', add
label define relate_lbl 76 `"Other relative 3 (no named category)"', add
label define relate_lbl 80 `"Nonrelative"', add
label define relate_lbl 81 `"Housemate/roommate"', add
label define relate_lbl 82 `"Roomer/boarder"', add
label define relate_lbl 83 `"Legal guardian"', add
label define relate_lbl 84 `"Ward"', add
label define relate_lbl 85 `"Other nonrelative"', add
label define relate_lbl 90 `"Unknown"', add
label define relate_lbl 96 `"Unknown - Don't know or refused"', add
label define relate_lbl 97 `"Unknown-Refused"', add
label define relate_lbl 98 `"Unknown - Not ascertained"', add
label define relate_lbl 99 `"Unknown-Don't know"', add
label values relate relate_lbl

label define racenew_lbl 100 `"White only"'
label define racenew_lbl 200 `"Black/African American only"', add
label define racenew_lbl 300 `"American Indian/Alaska Native only"', add
label define racenew_lbl 400 `"Asian only"', add
label define racenew_lbl 500 `"Other Race and Multiple Race"', add
label define racenew_lbl 510 `"Other Race and Multiple Race (2019-forward: Excluding American Indian/Alaska Native)"', add
label define racenew_lbl 520 `"Other Race"', add
label define racenew_lbl 530 `"Race Group Not Releasable"', add
label define racenew_lbl 540 `"Multiple Race"', add
label define racenew_lbl 541 `"Multiple Race (1999-2018: Including American Indian/Alaska Native)"', add
label define racenew_lbl 542 `"American Indian/Alaska Native and Any Other Race"', add
label define racenew_lbl 997 `"Unknown-Refused"', add
label define racenew_lbl 998 `"Unknown-Not ascertained"', add
label define racenew_lbl 999 `"Unknown-Don't Know"', add
label values racenew racenew_lbl

label define racea_lbl 100 `"White"'
label define racea_lbl 200 `"Black/African-American"', add
label define racea_lbl 300 `"Aleut, Alaskan Native, or American Indian"', add
label define racea_lbl 310 `"Alaskan Native or American Indian"', add
label define racea_lbl 320 `"Alaskan Native/Eskimo"', add
label define racea_lbl 330 `"Aleut"', add
label define racea_lbl 340 `"American Indian"', add
label define racea_lbl 350 `"American Indian or Alaskan Native and any other group"', add
label define racea_lbl 400 `"Asian or Pacific Islander"', add
label define racea_lbl 410 `"Asian"', add
label define racea_lbl 411 `"Chinese"', add
label define racea_lbl 412 `"Filipino"', add
label define racea_lbl 413 `"Korean"', add
label define racea_lbl 414 `"Vietnamese"', add
label define racea_lbl 415 `"Japanese"', add
label define racea_lbl 416 `"Asian Indian"', add
label define racea_lbl 420 `"Pacific Islander"', add
label define racea_lbl 421 `"Hawaiian"', add
label define racea_lbl 422 `"Samoan"', add
label define racea_lbl 423 `"Guamanian"', add
label define racea_lbl 430 `"Other Asian or Pacific Islander"', add
label define racea_lbl 431 `"Other Asian or Pacific Islander (1992-1995)"', add
label define racea_lbl 432 `"Other Asian or Pacific Islander (1996)"', add
label define racea_lbl 433 `"Other Asian or Pacific Islander (1997-1998)"', add
label define racea_lbl 434 `"Other Asian (1999 forward)"', add
label define racea_lbl 500 `"Other Race"', add
label define racea_lbl 510 `"Other Race (1963-1977)"', add
label define racea_lbl 520 `"Other Race (1978)"', add
label define racea_lbl 530 `"Other Race (1979-1991)"', add
label define racea_lbl 540 `"Other Race (1992-1995)"', add
label define racea_lbl 550 `"Other Race (1996)"', add
label define racea_lbl 560 `"Other Race (1997-1998)"', add
label define racea_lbl 570 `"Other Race (1999-2002)"', add
label define racea_lbl 580 `"Primary Race not releasable"', add
label define racea_lbl 600 `"Multiple Race, No Primary Race Selected"', add
label define racea_lbl 610 `"Multiple Race, including Asian, excluding Black and White"', add
label define racea_lbl 611 `"Multiple Race, including Asian and Black, excluding White"', add
label define racea_lbl 612 `"Multiple Race, including Asian and White, excluding Black"', add
label define racea_lbl 613 `"Multiple Race, including Black, excluding Asian and White"', add
label define racea_lbl 614 `"Multiple Race, including Black and White, excluding Asian"', add
label define racea_lbl 615 `"Multiple Race, including White, excluding Asian and Black"', add
label define racea_lbl 616 `"Multiple Race, including Asian, White, and Black"', add
label define racea_lbl 617 `"Multiple Race, excluding Asian, White, and Black"', add
label define racea_lbl 900 `"Unknown"', add
label define racea_lbl 970 `"Unknown-refused"', add
label define racea_lbl 980 `"Unknown-not ascertained"', add
label define racea_lbl 990 `"Unknown (1997 forward: Don't know)"', add
label values racea racea_lbl

label define hispeth_lbl 10 `"Not Hispanic/Spanish origin"'
label define hispeth_lbl 20 `"Mexican"', add
label define hispeth_lbl 21 `"Mexican-Mexicano"', add
label define hispeth_lbl 22 `"Mexicano"', add
label define hispeth_lbl 23 `"Mexican-American"', add
label define hispeth_lbl 24 `"Chicano"', add
label define hispeth_lbl 30 `"Puerto Rican"', add
label define hispeth_lbl 40 `"Cuban/Cuban American"', add
label define hispeth_lbl 50 `"Dominican (Republic)"', add
label define hispeth_lbl 60 `"Other Hispanic"', add
label define hispeth_lbl 61 `"Central or South American"', add
label define hispeth_lbl 62 `"Other Latin American, type not specified"', add
label define hispeth_lbl 63 `"Other Spanish"', add
label define hispeth_lbl 64 `"Hispanic/Latino/Spanish, non-specific type"', add
label define hispeth_lbl 65 `"Hispanic/Latino/Spanish, type refused"', add
label define hispeth_lbl 66 `"Hispanic/Latino/Spanish, type not ascertained"', add
label define hispeth_lbl 67 `"Hispanic/Spanish, type don't know"', add
label define hispeth_lbl 70 `"Multiple Hispanic"', add
label define hispeth_lbl 90 `"Unknown"', add
label define hispeth_lbl 91 `"Unknown if Hispanic/Spanish origin"', add
label define hispeth_lbl 92 `"Two origins, unknown which is the main"', add
label define hispeth_lbl 93 `"Origin unknown, refused or not reported"', add
label define hispeth_lbl 99 `"NIU"', add
label values hispeth hispeth_lbl

label define racesr_lbl 100 `"White"'
label define racesr_lbl 200 `"Black/African American"', add
label define racesr_lbl 300 `"Aleut, Alaskan Native, or American Indian"', add
label define racesr_lbl 310 `"Alaskan Native or American Indian"', add
label define racesr_lbl 320 `"Alaskan Native"', add
label define racesr_lbl 330 `"Aleut"', add
label define racesr_lbl 340 `"American Indian"', add
label define racesr_lbl 400 `"Asian or Pacific Islander"', add
label define racesr_lbl 410 `"Asian"', add
label define racesr_lbl 411 `"Chinese"', add
label define racesr_lbl 412 `"Filipino"', add
label define racesr_lbl 413 `"Korean"', add
label define racesr_lbl 414 `"Vietnamese"', add
label define racesr_lbl 415 `"Japanese"', add
label define racesr_lbl 416 `"Asian Indian"', add
label define racesr_lbl 417 `"Other Asian (1999-2005)"', add
label define racesr_lbl 420 `"Pacific Islander"', add
label define racesr_lbl 421 `"Hawaiian"', add
label define racesr_lbl 422 `"Samoan"', add
label define racesr_lbl 423 `"Guamanian"', add
label define racesr_lbl 430 `"Other Asian or Pacific Islander"', add
label define racesr_lbl 431 `"Other Asian or Pacific Islander (1992-1995)"', add
label define racesr_lbl 432 `"Other Asian or Pacific Islander (1996)"', add
label define racesr_lbl 433 `"Other Asian or Pacific Islander (1997-1998)"', add
label define racesr_lbl 500 `"Other race"', add
label define racesr_lbl 510 `"Other race (1978)"', add
label define racesr_lbl 520 `"Other race (1979-1991)"', add
label define racesr_lbl 530 `"Other race (1992-1995)"', add
label define racesr_lbl 540 `"Other race (1996)"', add
label define racesr_lbl 550 `"Other race (1997-1998)"', add
label define racesr_lbl 560 `"Other race (1999-2002)"', add
label define racesr_lbl 570 `"Primary race not releasable"', add
label define racesr_lbl 600 `"Multiple race, no primary race selected"', add
label define racesr_lbl 900 `"Unknown"', add
label define racesr_lbl 970 `"Unknown-refused"', add
label define racesr_lbl 980 `"Unknown-not ascertained"', add
label define racesr_lbl 990 `"Unknown-don't know"', add
label values racesr racesr_lbl

label define educrec2_lbl 00 `"NIU"'
label define educrec2_lbl 10 `"Never attended/kindergarten only"', add
label define educrec2_lbl 20 `"Grade 1, 2, 3, or 4"', add
label define educrec2_lbl 30 `"Grade 5, 6, 7, or 8"', add
label define educrec2_lbl 31 `"Grade 5, 6, or 7"', add
label define educrec2_lbl 32 `"Grade 8"', add
label define educrec2_lbl 40 `"Grade 9, 10, 11, or 12"', add
label define educrec2_lbl 41 `"Grade 9, 10, or 11"', add
label define educrec2_lbl 42 `"Grade 12"', add
label define educrec2_lbl 50 `"1 to 4 years of college"', add
label define educrec2_lbl 51 `"1 to 3 years of college"', add
label define educrec2_lbl 52 `"1 to 2 years of college"', add
label define educrec2_lbl 53 `"3 to 4 years of college"', add
label define educrec2_lbl 54 `"4 years college/Bachelor's degree"', add
label define educrec2_lbl 60 `"5+ years of college"', add
label define educrec2_lbl 96 `"Unknown-not reported"', add
label define educrec2_lbl 97 `"Unknown-refused"', add
label define educrec2_lbl 98 `"Unknown-not ascertained"', add
label define educrec2_lbl 99 `"Unknown (1996 forward - Don't know)"', add
label values educrec2 educrec2_lbl

label define educrec1_lbl 00 `"NIU"'
label define educrec1_lbl 01 `"Never attended/kindergarten only"', add
label define educrec1_lbl 02 `"Grade 1"', add
label define educrec1_lbl 03 `"Grade 2"', add
label define educrec1_lbl 04 `"Grade 3"', add
label define educrec1_lbl 05 `"Grade 4"', add
label define educrec1_lbl 06 `"Grade 5"', add
label define educrec1_lbl 07 `"Grade 6"', add
label define educrec1_lbl 08 `"Grade 7"', add
label define educrec1_lbl 09 `"Grade 8"', add
label define educrec1_lbl 10 `"Grade 9"', add
label define educrec1_lbl 11 `"Grade 10"', add
label define educrec1_lbl 12 `"Grade 11"', add
label define educrec1_lbl 13 `"Grade 12"', add
label define educrec1_lbl 14 `"1 to 3 years of college"', add
label define educrec1_lbl 15 `"4 years college/Bachelor's degree"', add
label define educrec1_lbl 16 `"5+ years of college"', add
label define educrec1_lbl 96 `"Unknown--all causes"', add
label define educrec1_lbl 97 `"Unknown--refused"', add
label define educrec1_lbl 98 `"Unknown--not ascertained"', add
label define educrec1_lbl 99 `"Unknown--not known"', add
label values educrec1 educrec1_lbl

label define mortelig_lbl 1 `"Eligible"'
label define mortelig_lbl 2 `"Under age 18"', add
label define mortelig_lbl 3 `"Ineligible"', add
label define mortelig_lbl 9 `"NIU"', add
label values mortelig mortelig_lbl

label define mortstat_lbl 1 `"Assumed deceased"'
label define mortstat_lbl 2 `"Assumed alive"', add
label define mortstat_lbl 9 `"NIU"', add
label values mortstat mortstat_lbl

label define mortdodq_lbl 1 `"January-March"'
label define mortdodq_lbl 2 `"April-June"', add
label define mortdodq_lbl 3 `"July-September"', add
label define mortdodq_lbl 4 `"October-December"', add
label define mortdodq_lbl 9 `"NIU"', add
label values mortdodq mortdodq_lbl

label define mortdody_lbl 1986 `"1986"'
label define mortdody_lbl 1987 `"1987"', add
label define mortdody_lbl 1988 `"1988"', add
label define mortdody_lbl 1989 `"1989"', add
label define mortdody_lbl 1990 `"1990"', add
label define mortdody_lbl 1991 `"1991"', add
label define mortdody_lbl 1992 `"1992"', add
label define mortdody_lbl 1993 `"1993"', add
label define mortdody_lbl 1994 `"1994"', add
label define mortdody_lbl 1995 `"1995"', add
label define mortdody_lbl 1996 `"1996"', add
label define mortdody_lbl 1997 `"1997"', add
label define mortdody_lbl 1998 `"1998"', add
label define mortdody_lbl 1999 `"1999"', add
label define mortdody_lbl 2000 `"2000"', add
label define mortdody_lbl 2001 `"2001"', add
label define mortdody_lbl 2002 `"2002"', add
label define mortdody_lbl 2003 `"2003"', add
label define mortdody_lbl 2004 `"2004"', add
label define mortdody_lbl 2005 `"2005"', add
label define mortdody_lbl 2006 `"2006"', add
label define mortdody_lbl 2007 `"2007"', add
label define mortdody_lbl 2008 `"2008"', add
label define mortdody_lbl 2009 `"2009"', add
label define mortdody_lbl 2010 `"2010"', add
label define mortdody_lbl 2011 `"2011"', add
label define mortdody_lbl 2012 `"2012"', add
label define mortdody_lbl 2013 `"2013"', add
label define mortdody_lbl 2014 `"2014"', add
label define mortdody_lbl 2015 `"2015"', add
label define mortdody_lbl 2016 `"2016"', add
label define mortdody_lbl 2017 `"2017"', add
label define mortdody_lbl 2018 `"2018"', add
label define mortdody_lbl 2019 `"2019"', add
label define mortdody_lbl 9999 `"NIU"', add
label values mortdody mortdody_lbl

label define mortucodld_lbl 01 `"Diseases of heart"'
label define mortucodld_lbl 02 `"Malignant neoplasms"', add
label define mortucodld_lbl 03 `"Chronic lower respiratory diseases"', add
label define mortucodld_lbl 04 `"Accidents (unintentional injuries)"', add
label define mortucodld_lbl 05 `"Cerebrovascular diseases"', add
label define mortucodld_lbl 06 `"Alzheimer's disease"', add
label define mortucodld_lbl 07 `"Diabetes mellitus"', add
label define mortucodld_lbl 08 `"Influenza and pneumonia"', add
label define mortucodld_lbl 09 `"Nephritis, nephrotic syndrome and nephrosis"', add
label define mortucodld_lbl 10 `"All other causes (residual)"', add
label define mortucodld_lbl 96 `"NIU"', add
label values mortucodld mortucodld_lbl


