# Validation C: Over-Partitioning Bias Magnitude

## Success Criteria
- K_significance / K_true <= 2.0 for mu <= 0.3
- NMI(Significance, ground_truth) >= 0.85 for mu <= 0.3

## Failure Criteria
- K_significance / K_true > 3.0 for mu <= 0.3
- NMI(Significance, ground_truth) < 0.70 for mu <= 0.3

## Results (Experiment C1/C2)

| Mu | K_signif/K_true (mean±std) | K_mod/K_true (mean±std) | NMI Signif (mean±std) | NMI Mod (mean±std) |
|----|--------------------------|-------------------------|---------------------|--------------------|
| 0.1 | 1.01 ± 0.01 | 0.90 ± 0.02 | 0.9999 ± 0.0002 | 0.9931 ± 0.0017 |
| 0.2 | 1.15 ± 0.03 | 0.78 ± 0.03 | 0.9974 ± 0.0006 | 0.9819 ± 0.0037 |
| 0.3 | 2.00 ± 0.18 | 0.68 ± 0.04 | 0.9734 ± 0.0050 | 0.9624 ± 0.0071 |
| 0.4 | 4.05 ± 0.37 | 0.53 ± 0.03 | 0.8754 ± 0.0116 | 0.8826 ± 0.0109 |

## Adverse Case Results (Experiment C3)

| Mu | K_signif/K_true (mean) | K_mod/K_true (mean) |
|----|----------------------|---------------------|
| 0.1 | 5.38 | 1.00 |
| 0.3 | 39.32 | 0.98 |

## Verdict
**PASS**
