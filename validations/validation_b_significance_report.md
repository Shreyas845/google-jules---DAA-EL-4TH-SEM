# Validation B: Warm-Start Effectiveness

## Success Criteria
- NMI(P_warm) >= 0.95 * NMI(P_cold) across all batches and seeds (mean)
- Speedup >= 2x on average across batches

## Results

| Batch | NMI Warm (mean ± std) | NMI Cold (mean ± std) | Ratio | Speedup |
|-------|-----------------------|-----------------------|-------|---------|
| 1 | 0.9745 ± 0.0058 | 0.9742 ± 0.0057 | 1.0003 | 1.75x |
| 2 | 0.9745 ± 0.0059 | 0.9752 ± 0.0051 | 0.9993 | 1.79x |
| 3 | 0.9743 ± 0.0060 | 0.9731 ± 0.0055 | 1.0013 | 1.72x |
| 4 | 0.9744 ± 0.0059 | 0.9740 ± 0.0061 | 1.0003 | 1.76x |
| 5 | 0.9742 ± 0.0058 | 0.9730 ± 0.0055 | 1.0012 | 1.72x |

Overall average speedup: 1.75x

## Verdict
**FAIL**
