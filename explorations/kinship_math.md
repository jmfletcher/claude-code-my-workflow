# Kinship Matrix Math (Caswell & Song 2021) - Python Port Notation

This is the math we will port to Python in `pykin/`. It is the time-varying
two-sex matrix kinship model of **Caswell and Song (2021)** as implemented in
DemoKin's `kin_time_variant_2sex.R`. We focus on the recurrences we actually
need for orphanhood: living parents (`m`), dead parents (tracked alongside),
and the offspring block (`d`) when we later need to derive expected children
of decedents for the calibration step.

## Indexing

- \(a \in \{0, 1, \ldots, \omega\}\): single-year age, with `ages = ω + 1`.
- \(s \in \{f, m\}\): sex.
- \(t\): calendar year.

## Per-year input matrices

Constructed from age-by-year rate tables `pf[a, t]`, `pm[a, t]` (survival
probabilities) and `ff[a, t]`, `fm[a, t]` (age-specific fertility rates).

### Survival (transition) matrix

For sex \(s\),

\[
U^s_t = \begin{pmatrix}
0 & 0 & \cdots & 0 \\
p^s_{0,t} & 0 & \cdots & 0 \\
0 & p^s_{1,t} & \cdots & 0 \\
\vdots & & \ddots & \vdots \\
0 & 0 & \cdots & p^s_{\omega,t}
\end{pmatrix}_{(\omega+1) \times (\omega+1)}
\]

with the last entry on the diagonal preserving the open-ended age class
(`U[ages, ages] = p[ages, t]`).

### Mortality (incoming-dead) matrix

\[
M^s_t = \mathrm{diag}(1 - p^s_{a,t})
\]

### Combined block matrix

Living and dead, female and male, stacked:

\[
U_t = \begin{pmatrix}
\mathrm{bdiag}(U^f_t, U^m_t) & 0 \\
\mathrm{bdiag}(M^f_t, M^m_t) & 0
\end{pmatrix}
\quad \text{shape } 4(\omega+1) \times 4(\omega+1)
\]

The top-left block ages living kin forward. The bottom-left block records
**newly-dead-this-year** in each age and sex slot. The right two block-columns
are zero because dead kin do not propagate forward.

### Fertility matrix (offspring assignment)

Reproducer-by-recipient. The first row gets the age-specific fertility rates;
all other rows are zero. With \(\beta\) = female share at birth:

\[
F^{2s}_t =
\begin{pmatrix}
\beta F^f_t & \beta F^m_t \\
(1-\beta) F^f_t & (1-\beta) F^m_t
\end{pmatrix}_{2(\omega+1) \times 2(\omega+1)}
\]

`F^*_t` (used only for siblings/grandparents through the focal's mother) is

\[
F^{*}_t =
\begin{pmatrix}
\beta F^f_t \\
(1-\beta) F^f_t
\end{pmatrix}_{2(\omega+1) \times (\omega+1)}
\]

## Kin recurrences (the part we need)

Each kin type is a column vector of length \(4(\omega+1)\) indexed
\([\text{live-f}, \text{live-m}, \text{dead-f}, \text{dead-m}]\) of size
\(\omega+1\) each.

Focal "self-distribution" \(\phi_x\) tracks where focal is at age \(x\):

\[
\phi_{x+1} = G_t \phi_x \quad \text{with} \quad \phi_0[\text{sex\_focal}, 0] = 1
\]

where \(G_t\) shifts ages by +1.

The parents block \(m_x(t)\), which is everything we need for orphanhood:

\[
m_{x+1}(t+1) = U_t \, m_x(t)
\]

with initial condition at \(x = 0\) given by

\[
m_0(t) = \pi_t = \begin{pmatrix} \pi^f_t \\ \pi^m_t \\ 0 \\ 0 \end{pmatrix}
\]

the age distribution of mothers and fathers when focal is born in year \(t\).
DemoKin computes \(\pi_t\) either from observed `pif`, `pim` directly or
from the stable-population approximation
\(\pi^s_t = w^s_t \odot f^s_t / \sum (w^s_t \odot f^s_t)\) where \(w_t\) is
the leading eigenvector of \(\mathrm{bdiag}(U^f_t, U^m_t) + F^*_t\).

For the offspring block \(d_x(t)\), we additionally have a birth term:

\[
d_{x+1}(t+1) = U_t \, d_x(t) + F^{2s}_t \, \phi_x
\]

(initial condition \(d_0 = 0\) - focal has no children at birth).

## Orphanhood quantity

For a focal child observed at age \(x \in \{0, \ldots, 17\}\) in year \(t\),
the dead-kin block of \(m_x(t)\) records the **cumulative number of dead
parents experienced**. DemoKin reassigns this to the focal's age experienced:

```
m[(agess+1):(2*agess), 1:(ages-1)] <- m[(agess+1):(2*agess), 2:ages]
```

(in the post-processing in `kin_time_variant_2sex`). After that shift:

- Sum of `m[(agess+1):(2*agess), x]` = expected number of dead parents
  a focal child has by age \(x\) in year \(t\).
- Cell entries are split by parent's age-at-death and sex.

To convert to a population count of orphans we multiply by population of
focal age \(x\) in year \(t\):

\[
\text{Orphans (incidence)}_{x,t} = N_{x,t}^{\text{children}} \cdot
\sum_{a, s} m_x[\text{dead}, a, s](t) \mathbf{1}\{\text{at least one parent dead}\}
\]

Two practical points:
1. The DemoKin output for `m` counts mothers and fathers separately. For
   "at least one parent has died" we use \(1 - (1 - p^f_{\text{dead}})(1 - p^m_{\text{dead}})\),
   where \(p^s_{\text{dead}}\) is the probability that the parent of sex \(s\)
   has died by the focal child's age \(x\) in year \(t\).
2. The Villaveces "caregiver death" extension layers on grandparent (`gm`)
   probabilities. We start with the parental quantity and can layer caregiver
   later.

## NHIS calibration plug-in

The standard model assumes that the fertility schedule in \(F^s_t\) applies
uniformly to all adults in the cell. The NHIS regression results give us, for
each cell \(c = (\text{age band}, \text{sex}, \text{raceth5}, \text{decade})\):

\[
\kappa_c = \frac{\mathbb{E}[nk_{<18}\mid \text{died},\, c]}
                {\mathbb{E}[nk_{<18}\mid \text{alive},\, c]}
\]

Interpretation: among adults who eventually die during follow-up, observed
co-resident-children stock is \(\kappa_c\) times the survivors' stock. We
apply this to the **expected children of a decedent** in the orphanhood
sum. Two implementation paths:

1. **Death-weighted post-multiplication (simplest):**
   When summing deaths \(D_{x,s,t}\) times expected children
   \(C_{x,s,t}\) implied by the matrix-kinship offspring counts, replace
   \(C_{x,s,t}\) with \(\kappa_{c(x,s,t)} \cdot C_{x,s,t}\).

2. **Fertility schedule replacement:** Construct \(F^s_t\) directly from
   \(\kappa_c\)-adjusted fertility rates; re-run the matrix recurrence.
   Cleaner inside the matrix framework, but requires a per-decade run.

Path 1 is faster to implement and identifies the same delta. We start there
and add path 2 as a sensitivity if the headline shift is large.

## References to read

- Caswell, H. (2019). The formal demography of kinship: A matrix formulation.
  *Demographic Research* 41(24).
- Caswell, H. and Song, X. (2021). The formal demography of kinship III:
  Kinship dynamics with time-varying demographic rates. *Demographic Research*
  45(16).
- Caswell, H. (2022). The formal demography of kinship IV: Two-sex models and
  their approximations. *Demographic Research* 47(13).
- Alburez-Gutierrez et al. (2024). *Science Advances*, replication on OSF
  9PS85, uses `DemoKin::kin_time_variant_2sex`.
- Williams et al. (2023). DemoKin R package, v1.0.3.
- Villaveces et al. (2025). *Nature Medicine*. Replication:
  `MLGlobalHealth/orphanhood-caregiver-death-in-US-from-all-causes-of-mortality`.

