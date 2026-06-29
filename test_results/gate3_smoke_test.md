# Gate 3 Smoke Test Report

LFR Graph Parameters: n=20, mu=0.1, average_degree=3, min_community=5

| Baseline | Communities | Time (ms) |
|----------|-------------|-----------|
| Static Significance | 10 | 1.63 |
| Static Leiden | 6 | 1.08 |
| BFS-Leiden | 2 | 0.70 |
| No Update | 1 | 0.00 |

Confirmation: All 4 baselines ran without error.
