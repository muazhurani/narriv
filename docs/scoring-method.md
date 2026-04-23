# Scoring Method

The ranker starts from Tribe output `P[T, V]`, where `T` is timesteps and `V` is vertices. It computes:

- `global_mean`, `global_peak`, `global_std`
- temporal energy `E[t] = mean(abs(P[t, :]))`
- `early_mean`, `mid_mean`, `late_mean`
- `sustainability`, `spikiness`, `dropoff`, `variance_over_time`

Sentence diagnostics map sentence character spans onto timeline bins, then aggregate `E[t]` over each sentence window.

Composite scores are currently:

- `brainscore = 0.30*hook + 0.25*sustained + 0.20*clarity + 0.15*end + 0.10*novelty`
- `final_score = 0.45*brainscore + 0.20*platform_fit + 0.15*readability + 0.10*novelty + 0.10*constraint_compliance`

These formulas are Narriv product logic. They should not be described as direct TribeV2 claims.
