# Gate 4 ISL Smoke Test Report

Graph: LFR, n=100, mu=0.3, seed=42
Batches run: 10 (batch_size=10 random insertions)
Initial partition: leidenalg SignificanceVertexPartition

| Batch | S | Community Count | Nodes Moved | Affected Set | Time (ms) |
|-------|---|-----------------|-------------|--------------|-----------|
| 1 | 210.9567 | 42 | 0 | 64 | 1.18 |
| 2 | 207.4653 | 42 | 0 | 61 | 1.11 |
| 3 | 189.7027 | 41 | 12 | 65 | 405.82 |
| 4 | 192.3177 | 40 | 17 | 71 | 314.85 |
| 5 | 183.6469 | 39 | 15 | 62 | 308.85 |
| 6 | 184.2081 | 36 | 17 | 66 | 348.18 |
| 7 | 190.5264 | 37 | 20 | 69 | 480.68 |
| 8 | 198.7504 | 35 | 19 | 80 | 480.15 |
| 9 | 187.7278 | 36 | 13 | 80 | 536.56 |
| 10 | 185.0925 | 33 | 22 | 65 | 437.32 |

ISL NMI on 100-node LFR graph = 0.5180
