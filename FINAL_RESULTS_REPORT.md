# FINAL RESULTS REPORT

## Section 1: NMI Results Table
| Method | E1 NMI (mean±std) | E2 NMI (mean±std) | E3 NMI (mean±std) | E4 NMI (mean±std) |
|---|---|---|---|---|
| isl_1hop | 0.5886±0.0192 | 0.5351±0.0183 | 0.4513±0.0121 | 0.4266±0.0153 |
| isl_adaptive | 0.6081±0.0113 | 0.5646±0.0143 | 0.4572±0.0085 | 0.4397±0.0154 |
| isl_no_correction | 0.5887±0.0221 | 0.5315±0.0220 | 0.4460±0.0197 | 0.4267±0.0209 |
| isl_no_dwell | 0.5865±0.0197 | 0.5323±0.0194 | 0.4512±0.0141 | 0.4261±0.0148 |
| static_significance | 0.6002±0.0174 | 0.5472±0.0204 | 0.4548±0.0107 | 0.4339±0.0226 |
| static_leiden | 0.8752±0.0369 | 0.5368±0.0552 | 0.2104±0.0304 | 0.1541±0.0308 |
| bfs_leiden | 0.5715±0.0343 | 0.4628±0.0341 | 0.3476±0.0189 | 0.3197±0.0227 |
| no_update | 0.6465±0.0174 | 0.5973±0.0172 | 0.4736±0.0140 | 0.4576±0.0117 |

## Section 2: Speed Table
| Method | Mean Time (ms/batch) |
|---|---|
| isl_1hop | 320.28 |
| isl_adaptive | 890.28 |
| isl_no_correction | 319.54 |
| isl_no_dwell | 325.75 |
| static_significance | 20.67 |
| static_leiden | 17.10 |
| bfs_leiden | 6.62 |
| no_update | 0.00 |

## Section 3: Over-Partitioning
| Mu | ISL-1hop | Ground Truth |
|---|---|---|
| 0.1 | 71.3 | ~6 (n=200, sizes=20-50) |
| 0.2 | 74.5 | ~6 (n=200, sizes=20-50) |
| 0.3 | 78.2 | ~6 (n=200, sizes=20-50) |
| 0.4 | 79.7 | ~6 (n=200, sizes=20-50) |

## Section 4: Key Finding
The ISL-1hop method does not exceed the static Leiden (Modularity) baseline on E1 (mu=0.1); it achieved a mean NMI of 0.5886 compared to static Leiden's 0.8752.
