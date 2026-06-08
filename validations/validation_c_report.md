# Validation C: Over-Partitioning Bias Magnitude

## Success Criteria
- K_surprise / K_true <= 2.0 for mu <= 0.3
- NMI(Surprise, ground_truth) >= 0.85 for mu <= 0.3

## Failure Criteria
- K_surprise / K_true > 3.0 for mu <= 0.3
- NMI(Surprise, ground_truth) < 0.70 for mu <= 0.3

## Results (Experiment C1/C2)

| Mu | K_surp/K_true (mean±std) | K_mod/K_true (mean±std) | NMI Surp (mean±std) | NMI Mod (mean±std) |
|----|--------------------------|-------------------------|---------------------|--------------------|
| 0.1 | 63.92 ± 3.96 | 0.90 ± 0.02 | 0.6538 ± 0.0067 | 0.9931 ± 0.0017 |
| 0.2 | 63.92 ± 3.96 | 0.78 ± 0.03 | 0.6538 ± 0.0067 | 0.9819 ± 0.0037 |
| 0.3 | 63.92 ± 3.96 | 0.68 ± 0.04 | 0.6538 ± 0.0067 | 0.9624 ± 0.0071 |
| 0.4 | 63.92 ± 3.96 | 0.53 ± 0.03 | 0.6538 ± 0.0067 | 0.8826 ± 0.0109 |

## Adverse Case Results (Experiment C3)

| Mu | K_surp/K_true (mean) | K_mod/K_true (mean) |
|----|----------------------|---------------------|
| 0.1 | 919.10 | 1.00 |
| 0.3 | 919.10 | 0.98 |

## Verdict
**FAIL**
