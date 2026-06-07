# FINAL MASTER BLUEPRINT — PART 2

**Status:** Authoritative. Continuation of Part 1.

---

## 11. Final Architecture Specification

### Technology Stack

| Layer | Technology | Rationale |
|:---|:---|:---|
| Graph storage | python-igraph (C backend) | Integrates with leidenalg; 10-100× faster than NetworkX |
| Static Surprise baseline | leidenalg `SurpriseVertexPartition` | Author's own implementation; eliminates custom optimizer |
| Static Modularity baseline | leidenalg `ModularityVertexPartition` | Same library, fair comparison |
| Community state | numpy array (sigma) + Python dicts (per-community stats) | O(1) lookup, O(d_v) update |
| Metrics | scikit-learn (NMI, ARI) + custom (Surprise, churn) | Standard, reproducible |
| Benchmarks | igraph LFR generator or external `networkx` LFR | Validated generators |
| Orchestration | Python scripts with JSON configs | Simple, reproducible |

### Module Boundaries (Final)

```
┌──────────────────────────────────────────────┐
│          EXPERIMENT RUNNER                     │
│  (config loading, orchestration, logging)      │
├──────────┬────────────┬──────────────────────┤
│  GRAPH   │  ISL       │  BASELINE            │
│  ENGINE  │  ENGINE    │  SUITE               │
│          │            │  (static Surprise,    │
│  igraph  │  3-stage   │   static Leiden,      │
│  wrapper │  algorithm │   BFS+Leiden,         │
│          │            │   no-update)          │
├──────────┴─────┬──────┴──────────────────────┤
│  COMMUNITY STATE MANAGER                      │
│  sigma[], comm_size{}, comm_internal{},       │
│  m, p, M, N scalars, dwell_counter[]          │
├────────────────┴─────────────────────────────┤
│  EVALUATION ENGINE                            │
│  NMI, ARI, Surprise, Modularity, churn,       │
│  time, community count, trigger rate           │
├──────────────────────────────────────────────┤
│  BENCHMARK SUITE                              │
│  LFR generator, SBM generator, SNAP loader,   │
│  update stream generator                       │
└──────────────────────────────────────────────┘
```

### Key Interface Contracts

**Graph Engine → ISL Engine:**
- `get_neighbors(v)` → list of neighbor node IDs
- `apply_batch(edges_add, edges_del)` → mutate graph
- `get_subgraph(node_set)` → igraph subgraph for connectivity check

**Community State Manager → ISL Engine:**
- `get_community(v)` → community label
- `move_node(v, c_old, c_new)` → updates sigma, comm_size, comm_internal, p, M immediately
- `get_delta_s(v, c_target)` → computes ΔS using current state
- `get_global_surprise()` → computes S from current m, p, M, N in O(1)

**ISL Engine → Evaluation Engine:**
- After each batch: emit `{S, Q, time_ms, nodes_moved, affected_set_size, community_count, churn_rate}`

---

## 12. Final Evaluation Framework

### Metric Hierarchy (Corrected per Sonnet #2)

**PRIMARY evidence (non-circular):**

| Metric | Computed Against | Purpose |
|:---|:---|:---|
| NMI vs. ground truth | Planted partition (synthetic only) | Absolute quality — the headline number |
| ARI vs. ground truth | Planted partition (synthetic only) | Second quality measure |

**SECONDARY evidence (diagnostic):**

| Metric | Purpose |
|:---|:---|
| Surprise S | Shows ISL maintains its optimization objective |
| Modularity Q | Comparison metric; shows ISL doesn't destroy modularity |
| Community count | Over-partitioning diagnostic |
| NMI vs. full static Surprise recomputation | Quality gap between incremental and static |

**EFFICIENCY evidence:**

| Metric | Purpose |
|:---|:---|
| Wall-clock time per batch | Practical speed |
| Speedup ratio vs. static Surprise | Headline efficiency number |
| Nodes reprocessed per batch | Locality measure |
| Affected set size |S₂| / |V| | Shows locality holds |

**STABILITY evidence:**

| Metric | Purpose |
|:---|:---|
| Community churn rate | Fraction of nodes changing community per batch |
| Node flickering rate (3-batch window) | Instability detection |
| Gap trigger rate | How often full recomputation fires |

### Statistical Requirements

- ≥10 random seeds per experiment configuration
- ≥3 random node orderings per batch within each run
- Report mean ± standard deviation for all metrics
- Wilcoxon signed-rank test for pairwise method comparisons (p < 0.05)

---

## 13. Final Benchmark Strategy

### Datasets

**Synthetic (primary evidence — has ground truth):**

| Dataset | Parameters | Purpose |
|:---|:---|:---|
| LFR-small | n=5000, μ∈{0.1,0.2,0.3,0.4}, community sizes 20-200 | **KEY:** Resolution-limit demonstration |
| LFR-medium | n=10000, μ∈{0.1,0.3,0.5}, mixed community sizes | General quality |
| LFR-large-communities | n=10000, community sizes 500-2000 | Adverse case (Surprise may over-partition) |
| SBM-merge-split | n=5000, 2 communities merge/split over time | Event detection |

**Real (secondary evidence — no ground truth):**

| Dataset | Size | Purpose |
|:---|:---|:---|
| SNAP CollegeMsg | ~1.9K nodes, ~59K edges | Small real temporal graph |
| SNAP email-Eu-core | ~1K nodes, ~25K edges | Small with ground-truth departments |
| Enron email | ~36K nodes, ~184K edges | Medium temporal graph |

**Explicitly excluded from direct experiments:** WikiTalk (2.4M nodes), DBLP (1.3M nodes), Reddit — exceed Python prototype's n ≤ 10⁵ ceiling. Paper discusses scalability theoretically.

### Update Stream Generation

| Strategy | Description | Purpose |
|:---|:---|:---|
| Random uniform | Random edge insertions | Baseline stress test |
| Community-localized | Insertions within existing communities | Tests locality exploitation |
| Cross-community bridge | Insertions between communities | Boundary adaptation |
| Small-community formation | Gradually densify a node subset (size < √(2m)) | **HERO EXPERIMENT** |
| Community merge | Two communities grow toward each other | Event handling |
| Community dissolution | Remove edges from one community progressively | Dissolution handling |
| Burst insertion | k = 500 edges in one batch | Degradation behavior |

### Benchmarking Fairness Requirements

1. ALL methods start from the SAME initial partition (static Surprise via leidenalg)
2. ALL methods see the IDENTICAL update stream (serialized to disk)
3. ALL methods use the SAME random seeds
4. Wall-clock timing excludes I/O and metric computation
5. Methods that need full graph access (static baselines) get it; incremental methods work within their affected sets

### Baselines (Final)

| Baseline | What It Is | Role |
|:---|:---|:---|
| Static Surprise (leidenalg) | Full SurpriseVertexPartition per batch | Quality oracle |
| Static Leiden (leidenalg) | Full ModularityVertexPartition per batch | Modularity quality oracle |
| BFS-r + Static Leiden | Fixed 1-hop BFS + local Leiden re-optimization | Incremental modularity proxy |
| No-update | Keep P(0) forever | Lower bound |
| ISL-1hop | ISL with fixed 1-hop expansion | Primary method |
| ISL-adaptive | ISL with adaptive expansion | Ablation variant |
| ISL-no-correction | ISL without periodic full recomputation (K=∞) | Ablation: shows correction value |
| ISL-no-dwell | ISL without dwell time (δ=0) | Ablation: shows flickering mitigation value |

---

## 14. Final Experimentation Framework

### Experiment Lifecycle

```
1. CONFIGURE  → Load JSON config (dataset, algorithm, params, seeds)
2. GENERATE   → Create/load graph + generate/load update stream
3. INITIALIZE → Compute initial partition via static Surprise
4. SERIALIZE  → Save initial partition + stream to disk (reproducibility)
5. EXECUTE    → For each batch:
                  a. Apply edge updates to graph
                  b. Run algorithm → get P(t+1)
                  c. Compute all metrics
                  d. Log to results file
6. AGGREGATE  → Compute mean ± std across seeds
7. COMPARE    → Statistical tests across methods
8. VISUALIZE  → Generate paper figures
```

### Configuration Schema

```json
{
  "experiment_id": "lfr_small_mu03_isl",
  "dataset": {"type": "lfr", "n": 5000, "mu": 0.3, "min_community": 20, "max_community": 200},
  "stream": {"type": "random_uniform", "batch_size": 50, "num_batches": 200},
  "algorithm": "isl_1hop",
  "params": {"K": 50, "delta_dwell": 2, "tau_min": 1e-6, "max_iter": 100, "num_orderings": 3},
  "seeds": [42, 123, 456, 789, 1011, 1213, 1415, 1617, 1819, 2021],
  "baselines": ["static_surprise", "static_leiden", "bfs_leiden", "no_update"],
  "output_dir": "results/lfr_small_mu03/"
}
```

### Required Paper Figures

1. **Hero figure:** NMI vs. batch number on LFR-small with small communities. ISL maintains high NMI; static Leiden (modularity) degrades for small communities.
2. **Speedup plot:** Wall-clock time per batch for ISL vs. static Surprise. Shows practical efficiency gain.
3. **Affected set distribution:** Histogram of |S|/|V|. Shows locality holds.
4. **Ablation table:** NMI and time for ISL-1hop, ISL-adaptive, ISL-no-correction, ISL-no-dwell. Shows each component's contribution.
5. **Over-partitioning diagnostic:** Community count over time for ISL vs. ground truth. Honest reporting.
6. **Parameter sensitivity:** NMI vs. K (correction frequency) and NMI vs. δ (dwell time).
7. **Adverse case:** Results on LFR-large-communities where Surprise may over-partition.

---

## 15. Implementation Readiness Assessment

### Fully Specified (Low Risk)

| Component | Specification Status |
|:---|:---|
| ΔS gain formula | Mathematically complete; O(d_v) verified |
| Community State Manager | Data structures, operations, update timing all specified |
| Edge update counter maintenance | O(1) per edge, O(k) per batch |
| Static baselines via leidenalg | One-line call; fully specified |
| Evaluation metrics | Standard library calls (NMI, ARI) + simple formulas |
| Experiment config schema | JSON format defined |
| LFR benchmark generation | igraph or networkx; standard |
| Periodic full recomputation (K-batch trigger) | Fully specified |

### Requires Care (Medium Risk)

| Component | Risk | Mitigation |
|:---|:---|:---|
| Local move phase ordering | Order-dependent results for non-additive objective | Run ≥3 orderings; report variance |
| Connectivity check within S | Requires subgraph extraction + igraph clusters() | Profile; may be slow for large affected sets |
| Dwell-time bookkeeping | Per-node counter; simple but must be correct | Unit test: verify skipped nodes have counter < δ |
| Community cleanup (empty communities) | Dict key deletion when last node leaves | Unit test: verify no phantom communities |

### High Risk

| Component | Risk | Mitigation |
|:---|:---|:---|
| **ΔS formula correctness** | A bug here invalidates ALL results | Exhaustive unit tests comparing against brute-force S recomputation. Test cases: small communities (<10), large communities (>1000), singleton moves, moves to new communities, negative-gain moves (verify rejection). |
| **Counter consistency** | Accumulated floating-point or logic errors in m, p, M, N | Periodic recomputation check: every 10 batches, recompute m, p, M, N from scratch and assert equality |
| **Resolution-limit demo graph** | Must be convincing, not contrived | Human-designed; must show genuinely strong small communities that modularity misses |
| **Baseline fairness** | Any deviation invalidates comparison | Assertion check: all baselines start from identical partition (compare sigma arrays) |

---

## 16. Research Validity Assessment

### Classification: **Strong Academic Project, Conditionally Conference-Grade**

**Justification:**

The project has genuine first-mover novelty (incremental Surprise optimization), a sound mathematical primitive (ΔS formula), and a clear differentiation axis (resolution-limit-free quality). These elements satisfy the requirements for a strong academic contribution.

However, the project is **conditional** on three pre-validation outcomes (approximation accuracy, warm-start, over-partitioning). If all three pass, the project is publishable at CIKM/WSDM with solid empirical results. If the T4 constructive proof is included and the Surprise sensitivity bound is proven, the project reaches the lower end of KDD/WWW consideration.

| Dimension | Assessment |
|:---|:---|
| **Novelty** | HIGH — first-mover status confirmed; no prior work on incremental Surprise |
| **Rigor** | MODERATE — sound math primitive; optimization guarantees limited to convergence (local optimum, not global); honest about limitations |
| **Reproducibility** | HIGH — fully specified configs, serialized streams, fixed seeds, open-source libraries |
| **Scalability** | LIMITED — Python prototype caps at n ≤ 10⁵; honest about this |
| **Publication potential** | CIKM/WSDM: 60-65% if pre-validations pass and experiments are strong. KDD/WWW: 30-35% requires stronger theory. |

### What Would Elevate to Journal-Grade

1. Prove the Surprise sensitivity bound formally (not just claim plausibility)
2. Extend to weighted/directed graphs
3. Cython/C++ implementation enabling experiments on n > 10⁵ graphs
4. Formal analysis of over-partitioning dynamics under incremental optimization

---

## 17. Risk Register

| # | Risk | Severity | Likelihood | Mitigation | Owner |
|:---|:---|:---|:---|:---|:---|
| R1 | Approximation inaccurate for small communities | Critical | Medium | Pre-Sprint A Validation 1 | Pre-validation |
| R2 | Warm-start not useful for Surprise landscape | Major | Medium | Pre-Sprint A Validation 2 | Pre-validation |
| R3 | Over-partitioning compounds incrementally | Major | Medium-High | Pre-Sprint A Validation 3; add regularization if needed | Pre-validation + Sprint 2 |
| R4 | ΔS formula implementation bug | Critical | Low | Exhaustive unit tests vs. brute-force | Sprint 1 |
| R5 | Counter drift over many batches | Major | Low | Periodic full recomputation (every K batches) + assertion checks | Sprint 1 |
| R6 | "ISL = Leiden + different objective" reviewer objection | High | High | T4 constructive proof; empirical demonstration of non-trivial adaptation; honest novelty scoping | Sprint 3 paper |
| R7 | Python performance insufficient for target graph sizes | Major | Medium | Profile early; Cython inner loop if needed; honest scope in paper | Sprint 2 |
| R8 | Surprise degeneracy causes flickering | Moderate | Medium | Dwell time δ; τ_min threshold; report variance across orderings | Sprint 2 |
| R9 | Static Leiden achieves same NMI as ISL on small communities | High | Low-Medium | If this happens, ISL's contribution is efficiency only. Reframe. | Sprint 3 |

---

## 18. Jules Preparation Notes

### What Jules Needs to Know

1. **The project uses igraph + leidenalg.** All graph operations go through igraph. Static Surprise optimization uses `leidenalg.find_partition(G, leidenalg.SurpriseVertexPartition)`.
2. **Counters update IMMEDIATELY after each accepted node move.** This is a correctness requirement. Do not batch counter updates.
3. **The ΔS gain formula is the core primitive.** It must be exhaustively unit-tested before anything else works.
4. **Experiments require ≥10 seeds and ≥3 node orderings per batch.** This is non-negotiable.
5. **All baselines start from the same initial partition and see the same update stream.** Serialize both to disk.

### What Jules Must NOT Decide Independently

1. **Resolution-limit demonstration graph parameters.** Human must design and approve.
2. **Whether to use exact or asymptotic Surprise.** Determined by Pre-Sprint A results.
3. **Whether to add community-count regularization.** Determined by Pre-Sprint A results.
4. **Paper figure design and framing.** Human decision.
5. **Baseline fairness validation.** Human must verify before comparative experiments.

### Implementation Order

| Order | Module | Why First |
|:---|:---|:---|
| 1 | Community State Manager | All other modules depend on it; must be correct |
| 2 | ΔS gain formula + unit tests | Core primitive; everything depends on correctness |
| 3 | Graph Engine wrapper | Batch update interface over igraph |
| 4 | Static baselines (leidenalg calls) | Needed for validation and comparison |
| 5 | ISL Stage 1 (affected set) | Straightforward BFS |
| 6 | ISL Stage 2 (local moves) | Core algorithm |
| 7 | ISL Stage 3 (periodic recomputation) | Simple K-batch counter |
| 8 | Evaluation Engine | Metrics computation |
| 9 | Experiment Runner | Orchestration |
| 10 | Benchmark Suite | Dataset generation + stream creation |

### What Must Be Tested Early

1. **ΔS formula correctness** (Sprint 1, before anything else)
2. **Counter consistency** (Sprint 1, immediately after Community State Manager)
3. **Baseline agreement** (Sprint 1, ISL on initial graph = leidenalg result)
4. **Warm-start benefit** (Pre-Sprint A, before full implementation)

---

## 19. Open Questions

| # | Question | Impact | When to Resolve |
|:---|:---|:---|:---|
| 1 | Approximation accuracy for communities of size 20-100? | Critical — determines if hero experiment is valid | Pre-Sprint A |
| 2 | Does warm-start help for Surprise on typical update distributions? | Critical — determines if efficiency claim holds | Pre-Sprint A |
| 3 | How severe is over-partitioning compounding under incremental optimization? | Major — determines if quality claims hold on real data | Pre-Sprint A |
| 4 | Is the T1 Surprise sensitivity bound straightforward to prove? | Moderate — strengthens theoretical contribution | Sprint 2 |
| 5 | What is the right value of K for periodic recomputation? | Moderate — determines efficiency-quality tradeoff | Sprint 3 (parameter sweep) |
| 6 | Does single-level optimization (no aggregation) produce acceptable quality? | Moderate — if not, need to develop Surprise-compatible aggregation | Sprint 3 (compare vs. leidenalg on affected subgraphs) |

---

## 20. Final Recommendations

1. **Execute Pre-Sprint A immediately.** 10 days. Three validation experiments. Go/no-go decision before any implementation.

2. **Start Sprint 1 with the Community State Manager and ΔS unit tests.** These are zero-risk, fully specified, and foundation for everything else.

3. **Do NOT attempt the hero experiment until Pre-Sprint A confirms approximation accuracy.** Building 8 weeks of code on an unvalidated mathematical assumption is the project's greatest risk.

4. **Include the T4 constructive proof in the paper.** It's achievable, strengthens the theoretical contribution, and pre-empts the "ISL = Leiden + different objective" reviewer objection.

5. **Be honest about limitations.** The paper should explicitly discuss: (a) over-partitioning bias, (b) order-dependence of local optimization, (c) n ≤ 10⁵ scope, (d) insertion-only mode for real datasets.

6. **Frame the paper around quality, not speed.** Every figure, table, and sentence in the abstract should reinforce: "ISL finds communities that modularity-based methods miss." Speed is secondary evidence.

---

## Summary Tables

### REMAINING RISKS

| Risk | Status |
|:---|:---|
| Approximation accuracy for small communities | **UNRESOLVED — Pre-Sprint A** |
| Warm-start effectiveness | **UNRESOLVED — Pre-Sprint A** |
| Over-partitioning compounding | **UNRESOLVED — Pre-Sprint A** |
| "ISL = Leiden + different objective" objection | MITIGATED by T4 proof + empirical demonstration |
| Python performance ceiling | MITIGATED by honest scoping (n ≤ 10⁵) |
| Counter correctness drift | MITIGATED by periodic recomputation + assertions |

### WHAT JULES MUST PRESERVE

1. Asymptotic Surprise as objective function (do not switch to modularity)
2. IMMEDIATE counter updates after each node move
3. ≥10 seeds, ≥3 orderings per experiment
4. All baselines share identical initial partition and update stream
5. Periodic full recomputation every K batches via leidenalg
6. ΔS unit tests comparing against brute-force S recomputation
7. NMI vs. ground truth as PRIMARY metric (not Surprise value)
8. Community count tracking in every experiment
9. JSON experiment configs with git commit hash

### WHAT JULES MAY OPTIMIZE

1. Internal iteration order within local-move phase (random vs. degree-ordered)
2. Exact logging format (JSON vs. CSV vs. SQLite)
3. Plot styling and figure generation tools
4. Directory structure details
5. LFR parameter ranges (within specified bounds)
6. Memory layout of Community State Manager internals
7. Parallelization of multi-seed experiment execution
8. Connectivity check implementation details (igraph API choices)

### CONFIDENCE LEVEL

| Aspect | Confidence |
|:---|:---|
| ISL is implementable (conditional on pre-validation) | **75%** |
| Pre-Sprint A validations will pass | **65%** |
| ISL detects small communities better than modularity methods | **70%** (conditional on approximation accuracy) |
| ISL provides practical speedup over static Surprise | **50%** (warm-start unvalidated) |
| ISL is publishable at CIKM/WSDM | **60%** (conditional on solid experiments) |
| ISL is publishable at KDD/WWW | **30-35%** (needs stronger theory) |
| Architecture is sound and implementable | **85%** |
| Pre-validation phase is achievable in 10 days | **90%** |

---

**END OF FINAL MASTER BLUEPRINT**

**This document is the authoritative project specification. All prior documents (Research Blueprint V1, Algorithm Specification V1, Architecture Specification V1) are superseded on any point of conflict.**
