# Validation B: Warm-Start Effectiveness

## Success Criteria
- NMI(P_warm) >= 0.95 * NMI(P_cold) across all batches and seeds (mean)
- Speedup >= 2x on average across batches

## Results

| Batch | NMI Warm (mean ± std) | NMI Cold (mean ± std) | Ratio | Speedup |
|-------|-----------------------|-----------------------|-------|---------|
| 1 | 0.6548 ± 0.0074 | 0.6548 ± 0.0074 | 1.0000 | 1.00x |
| 2 | 0.6548 ± 0.0074 | 0.6548 ± 0.0074 | 1.0000 | 0.95x |
| 3 | 0.6548 ± 0.0074 | 0.6548 ± 0.0074 | 1.0000 | 1.06x |
| 4 | 0.6548 ± 0.0074 | 0.6548 ± 0.0074 | 1.0000 | 1.40x |
| 5 | 0.6548 ± 0.0074 | 0.6548 ± 0.0074 | 1.0000 | 1.34x |

Overall average speedup: 1.15x

## Verdict
**FAIL**
