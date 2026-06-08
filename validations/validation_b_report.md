# Validation B: Warm-Start Effectiveness

## Success Criteria
- NMI(P_warm) >= 0.95 * NMI(P_cold) across all batches and seeds (mean)
- Speedup >= 2x on average across batches

## Results

| Batch | NMI Warm (mean ± std) | NMI Cold (mean ± std) | Ratio | Speedup |
|-------|-----------------------|-----------------------|-------|---------|
| 1 | 0.6548 ± 0.0074 | 0.6548 ± 0.0074 | 1.0000 | 1.00x |
| 2 | 0.6548 ± 0.0074 | 0.6548 ± 0.0074 | 1.0000 | 0.93x |
| 3 | 0.6548 ± 0.0074 | 0.6548 ± 0.0074 | 1.0000 | 1.07x |
| 4 | 0.6548 ± 0.0074 | 0.6548 ± 0.0074 | 1.0000 | 1.39x |
| 5 | 0.6548 ± 0.0074 | 0.6548 ± 0.0074 | 1.0000 | 1.33x |

Overall average speedup: 1.14x

## Verdict
**FAIL**
