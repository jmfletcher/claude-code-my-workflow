## R cross-check of Stata survey-weighted mortality logits (NHIS-LMF 1986-2018)
## ----------------------------------------------------------------------------
## Reads nhis_svy_mort_ready.dta produced by scripts/nhis_svy_mortality_logit.do
## and fits the same four logistic models with the survey package, so the two
## stacks can be reconciled. Outputs tidy CSVs under results/r_cross/.
##
## Caveats are inherited from the Stata pipeline (RELATE is to householder;
## co-residence != parity; weighted associations, not causal).

suppressPackageStartupMessages({
  required <- c("haven", "survey", "dplyr", "tibble", "readr", "purrr", "broom")
  for (pkg in required) {
    if (!requireNamespace(pkg, quietly = TRUE)) {
      install.packages(pkg, repos = "https://cloud.r-project.org")
    }
    library(pkg, character.only = TRUE)
  }
})

options(survey.lonely.psu = "adjust")

proj_root <- normalizePath(".")
in_file   <- file.path(proj_root, "nhis_svy_mort_ready.dta")
out_dir   <- file.path(proj_root, "results", "r_cross")
if (!dir.exists(out_dir)) dir.create(out_dir, recursive = TRUE)

if (!file.exists(in_file)) {
  stop("Missing ", in_file,
       ". Run scripts/nhis_svy_mortality_logit.do first to build the analytic frame.")
}

message("Reading ", in_file)
dat <- haven::read_dta(in_file)

## ---- Variable hygiene -------------------------------------------------------

dat <- dat %>%
  mutate(
    died               = as.integer(died),
    sex                = factor(sex, levels = c(1, 2), labels = c("male", "female")),
    raceth5            = factor(raceth5, levels = 1:5,
                                labels = c("Hispanic", "NH White", "NH Black",
                                           "NH Asian/PI", "NH AIAN/Other/Mult")),
    yeardec            = factor(yeardec, levels = 1:4,
                                labels = c("1986-1989", "1990s", "2000s", "2010-2018")),
    nkf                = factor(nkf, levels = 0:3,
                                labels = c("0 minors", "1 minor", "2 minors", "3+ minors")),
    nk_under18         = as.numeric(nk_under18),
    minors_mean_age_ctr = as.numeric(minors_mean_age_ctr),
    age_c              = as.numeric(age_c)
  ) %>%
  ## Reference levels matching Stata (ib2.sex => female; ib2.raceth5 => NH White)
  mutate(
    sex     = relevel(sex,     ref = "female"),
    raceth5 = relevel(raceth5, ref = "NH White")
  )

## ---- Build a survey design per sample ---------------------------------------

build_design <- function(d, sample_var) {
  sub <- d[d[[sample_var]] == 1 & !is.na(d[[sample_var]]), , drop = FALSE]
  if (nrow(sub) == 0) {
    warning("Empty sample for ", sample_var)
    return(NULL)
  }
  survey::svydesign(
    ids     = ~psu,
    strata  = ~strata,
    weights = ~mortwtsa,
    data    = sub,
    nest    = TRUE
  )
}

samples <- c(parent = "subpop_parent", all = "subpop_all")

## Tidy helper
tidy_svyglm <- function(fit, model_name, sample_name) {
  broom::tidy(fit, conf.int = TRUE) %>%
    mutate(
      model     = model_name,
      sample    = sample_name,
      odds_ratio = exp(estimate),
      or_low     = exp(conf.low),
      or_high    = exp(conf.high)
    ) %>%
    select(model, sample, term, estimate, std.error, statistic, p.value,
           conf.low, conf.high, odds_ratio, or_low, or_high)
}

## Joint Wald wrappers
joint_test <- function(fit, terms, label) {
  rt <- tryCatch(
    survey::regTermTest(fit, as.formula(paste("~", paste(terms, collapse = " + "))),
                        method = "Wald"),
    error = function(e) NULL
  )
  if (is.null(rt)) {
    return(tibble(test = label, F = NA_real_, df1 = NA_real_,
                  df2 = NA_real_, pvalue = NA_real_))
  }
  tibble(
    test   = label,
    F      = as.numeric(rt$Ftest),
    df1    = as.numeric(rt$df),
    df2    = as.numeric(rt$ddf),
    pvalue = as.numeric(rt$p)
  )
}

## ---- Loop over samples ------------------------------------------------------

all_coefs <- list()
all_jts   <- list()

for (sn in names(samples)) {
  flag <- samples[[sn]]
  message("\n=== Sample: ", sn, " (flag=", flag, ") ===")

  des <- build_design(dat, flag)
  if (is.null(des)) next

  ## M_full
  f_full <- survey::svyglm(
    died ~ sex + age_c + I(age_c^2) + raceth5 + yeardec +
           nk_under18 + minors_mean_age_ctr,
    design = des, family = quasibinomial()
  )

  ## M_counts
  f_counts <- survey::svyglm(
    died ~ sex + age_c + I(age_c^2) + raceth5 + yeardec + nk_under18,
    design = des, family = quasibinomial()
  )

  ## M_fact
  f_fact <- survey::svyglm(
    died ~ sex + age_c + I(age_c^2) + raceth5 + yeardec +
           nkf + minors_mean_age_ctr,
    design = des, family = quasibinomial()
  )

  ## M_int
  f_int <- survey::svyglm(
    died ~ sex + age_c + I(age_c^2) + raceth5 + yeardec +
           nk_under18 * minors_mean_age_ctr,
    design = des, family = quasibinomial()
  )

  all_coefs[[paste0("mfull_",  sn)]] <- tidy_svyglm(f_full,   "mfull",   sn)
  all_coefs[[paste0("mcounts_", sn)]] <- tidy_svyglm(f_counts, "mcounts", sn)
  all_coefs[[paste0("mfact_",  sn)]] <- tidy_svyglm(f_fact,   "mfact",   sn)
  all_coefs[[paste0("mint_",   sn)]] <- tidy_svyglm(f_int,    "mint",    sn)

  jts <- bind_rows(
    joint_test(f_full,   c("nk_under18", "minors_mean_age_ctr"),
               "mfull_joint_nk_meanage"),
    joint_test(f_full,   "nk_under18",            "mfull_nk_only"),
    joint_test(f_full,   "minors_mean_age_ctr",   "mfull_meanage_only"),
    joint_test(f_counts, "nk_under18",            "mcounts_nk"),
    joint_test(f_fact,   "nkf",                   "mfact_joint_nkf"),
    joint_test(f_fact,   "minors_mean_age_ctr",   "mfact_meanage"),
    joint_test(f_int,    "nk_under18:minors_mean_age_ctr",
               "mint_interaction"),
    joint_test(f_int,    c("nk_under18", "minors_mean_age_ctr",
                            "nk_under18:minors_mean_age_ctr"),
               "mint_joint_all_kid_terms")
  ) %>% mutate(sample = sn)

  all_jts[[sn]] <- jts
}

## ---- Write outputs ----------------------------------------------------------

if (length(all_coefs) > 0) {
  coef_df <- bind_rows(all_coefs)
  for (sn in unique(coef_df$sample)) {
    for (mn in unique(coef_df$model[coef_df$sample == sn])) {
      sub <- coef_df %>% filter(sample == sn, model == mn)
      readr::write_csv(sub, file.path(out_dir,
                                      sprintf("coef_%s_%s.csv", mn, sn)))
    }
  }
  readr::write_csv(coef_df, file.path(out_dir, "coef_all_models.csv"))
}

if (length(all_jts) > 0) {
  jt_df <- bind_rows(all_jts)
  for (sn in unique(jt_df$sample)) {
    readr::write_csv(jt_df %>% filter(sample == sn),
                     file.path(out_dir, sprintf("jointtests_%s.csv", sn)))
  }
  readr::write_csv(jt_df, file.path(out_dir, "jointtests_all.csv"))
}

message("\nR cross-check outputs written under: ", out_dir)
