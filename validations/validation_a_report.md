# Validation A: Asymptotic Approximation Accuracy

## Success Criteria
- Relative error < 5% for communities >= 50 nodes
- Relative error < 2% for communities >= 100 nodes
- Ordering consistency >= 95% for all community sizes >= 50

## Failure Criteria
- Relative error >= 10% for communities >= 100 nodes
- Ordering consistency < 90% for communities >= 100 nodes
- Numerical instability (NaN, Inf) in exact Surprise for any test case

## Results

| Community Size | Mean Rel Err | Max Rel Err | Ordering Consistency |
|----------------|--------------|-------------|----------------------|
| 20 | 6.7750% | 6.8024% | 99.0000% |
| 50 | 4.0226% | 4.0439% | 100.0000% |
| 100 | 2.3412% | 2.3763% | 100.0000% |
| 200 | 1.4026% | 1.4257% | 100.0000% |
| 500 | 0.7654% | 0.7779% | 100.0000% |

## Verdict
**FAIL**
