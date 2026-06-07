# FINAL MASTER BLUEPRINT — PART 1

**Status:** Authoritative. Supersedes all prior documents on any point of conflict.

---

## 1. Executive Summary

This project develops **ISL (Incremental Surprise-Leiden)**, the first algorithm for incrementally maintaining Surprise-optimal community partitions on dynamic graphs. ISL addresses a fundamental limitation of ALL existing incremental community detection methods: their reliance on modularity, which suffers from a proven resolution limit that makes communities smaller than √(2m) invisible.

The project has undergone a genuine intellectual pivot from the original framing (adaptive BFS + local Louvain) to a novel direction with first-mover status. The novelty claim — that no prior work exists on incremental Surprise optimization — is confirmed by literature search and Sonnet Review #2.

**However, the project cannot proceed directly to full implementation.** Sonnet Review #2 identified three critical unvalidated assumptions that could invalidate the paper:

1. The asymptotic Surprise approximation is least accurate for small communities — exactly where ISL claims its advantage
2. The warm-start assumption (P(t) is useful for optimizing Surprise at t+1) is untested and potentially undermined by Surprise's known landscape degeneracy
3. Surprise's over-partitioning bias may compound under incremental optimization

A **mandatory 10-day pre-validation phase** precedes implementation. Go/no-go criteria are defined below.

---

## 2. Final Research Direction

**Title:** *"Beyond Modularity: Resolution-Limit-Free Incremental Community Detection via Surprise Optimization"*

**Primary axis of competition:** Quality (resolution-limit-free detection), NOT speed.

ISL does not compete with HIT-Leiden on wall-clock time. ISL competes on detecting multi-scale community structure that modularity-based methods systematically miss.

**Framing:** The paper's primary evidence is NMI against ground truth on synthetic benchmarks with small communities. The Surprise metric is secondary (diagnostic, not primary evidence — to avoid evaluation circularity).

**HIT-Leiden comparison strategy:** ISL vs. static Leiden (via leidenalg) on quality, serving as a proxy for HIT-Leiden. Since HIT-Leiden ≈ incremental Leiden ≈ static Leiden quality, demonstrating ISL quality > static Leiden quality on small-community graphs is the evidence. No direct HIT-Leiden integration required.

---

## 3. Final Contribution Statement

**Primary contributions (claimed as novel):**

1. **First incremental algorithm for Surprise optimization on dynamic graphs.** No prior work exists.
2. **Incremental ΔS node-move gain formula** derivable from the asymptotic Surprise approximation, computable in O(d_v) time.
3. **Constructive proof that incremental modularity methods fail on emerging small communities** (T4 from Phase 2) — showing a dynamic graph sequence where ISL succeeds and modularity-based methods provably fail.
4. **Empirical characterization of Surprise's behavior under incremental optimization** — first study of degeneracy, over-partitioning, and warm-start effectiveness in the dynamic setting.

**Secondary contributions (supporting):**

5. Surprise sensitivity value bound |ΔS| ≤ O(k · ln(m/k)) under k-edge perturbations (if provable).
6. Quality-triggered correction mechanism for incremental community maintenance.

**What is NOT claimed as novel:**
- Surprise as a metric (Aldecoa & Marín 2011)
- The asymptotic approximation (Traag et al. 2015)
- Local node-move optimization (Blondel et al. 2008)
- Affected-region detection via BFS (standard)

---

## 4. Conflict Resolution Log

### Conflict 1: Community Closure

| Phase 2 | Phase 3 | Sonnet #2 | **Final Decision** |
|:---|:---|:---|:---|
| Include community closure in affected set | Remove closure; use edge-proximity only | Closure removal correct; but notes global landscape shift accumulates over time for non-additive objectives | **REMOVE community closure. Use edge-proximity (1-hop + adaptive). Accept that global landscape drift accumulates; mitigate via periodic full recomputation (gap monitor).** |

**Downstream effect:** Affected set is much smaller; locality is preserved; accumulated drift is a known limitation acknowledged in the paper.

### Conflict 2: Surprise-Gap Monitor

| Phase 2 | Phase 3 | Sonnet #2 | **Final Decision** |
|:---|:---|:---|:---|
| Compare against cached S_full(t₀) with ε threshold | "Relative drift" over moving average (underspecified) | Neither is implementable as written; proposes three alternatives | **Use periodic full recomputation every K batches. K is a parameter (recommended K=50). After recomputation, compare NMI(P_incremental, P_full) and S_incremental vs S_full. If NMI < δ (recommended δ=0.9), adopt P_full as new partition.** |

**Rationale:** The periodic approach is simple, fully specified, and avoids the "stale cache" and "undefined drift" problems. K=50 means full recomputation every 50 batches — affordable and interpretable.

**Downstream effect:** Jules can implement this without ambiguity. The ablation study varies K ∈ {20, 50, 100, ∞} to characterize the quality-efficiency tradeoff.

### Conflict 3: Multi-Level Aggregation

| Phase 2 | Phase 3 | Sonnet #2 | **Final Decision** |
|:---|:---|:---|:---|
| Leiden refinement included | Aggregation dropped; single-level only | Dropping aggregation converts ISL to Louvain-equivalent quality; connectivity check is detection, not prevention | **Drop aggregation for incremental case. Retain connectivity check. Acknowledge in paper that ISL's local optimization is Louvain-style (not Leiden-style) within the affected set. Full recomputation (triggered every K batches) uses leidenalg with full Leiden quality.** |

**Rationale:** Multi-level aggregation for Surprise is an unsolved problem (Surprise is not community-additive). Attempting it introduces more risk than it solves. The periodic full recomputation via leidenalg provides Leiden-quality partitions every K batches.

**Naming:** ISL remains "Incremental Surprise-Leiden" because: (a) the static baseline and periodic recomputation use Leiden, (b) the incremental local moves are Louvain-style but scoped to affected set, (c) the overall system combines incremental Louvain-style moves with periodic Leiden corrections.

### Conflict 4: Adaptive Expansion

| Phase 2 | Phase 3 | Sonnet #2 | **Final Decision** |
|:---|:---|:---|:---|
| Adaptive expansion based on ΔS gain at boundary | Start with fixed 1-hop; add adaptive as ablation later | Acceptable deferral | **Implement two variants: ISL-1hop (fixed 1-hop expansion) and ISL-adaptive (expand when boundary ΔS > τ). ISL-1hop is the primary method; ISL-adaptive is an ablation variant.** |

### Conflict 5: Counter Update Timing

| Phase 2 | Phase 3 | Sonnet #2 | **Final Decision** |
|:---|:---|:---|:---|
| Not explicitly specified | Not explicitly specified | CRITICAL: counters must update IMMEDIATELY after each accepted node move, before next gain computation | **Counters (sigma, comm_size, comm_internal_edges, p, M) update IMMEDIATELY after each accepted move. The ΔS computation for the next candidate node uses the post-move state. This is a correctness requirement.** |

### Additional Resolutions from Sonnet #2

| Issue | Decision |
|:---|:---|
| **Approximation accuracy for small communities** | Mandatory pre-validation (Pre-Sprint A). Go/no-go gate. |
| **Warm-start validity** | Mandatory pre-validation (Pre-Sprint A). Go/no-go gate. |
| **Over-partitioning bias** | Mandatory pre-validation (Pre-Sprint A). If severe, add community-count regularization or switch to Significance. |
| **Node ordering dependence** | Acknowledged in paper. Run ≥3 random orderings per batch; report mean ± std. |
| **Edge deletion semantics for real datasets** | SNAP datasets used in insertion-only mode. Explicitly stated in paper. |
| **DynaMo baseline** | Replace with "Fixed-Radius BFS + Static Leiden" as the incremental modularity proxy. Fully specifiable, no DynaMo ambiguity. |
| **Community cleanup (empty communities)** | When last node leaves community A, delete A from comm_size and comm_internal_edges dicts. |
| **Dataset scale** | Python prototype targets n ≤ 10⁵. Paper is honest about this. Larger datasets use static comparison only. |
| **T4 constructive proof** | Required contribution. Straightforward construction using resolution-limit theorem. |

---

## 5. Final Algorithm Specification

### Objective Function

**Asymptotic Surprise:** S(P) = m · D_KL(q ∥ ⟨q⟩)

where q = p/m, ⟨q⟩ = M/N, D_KL(x∥y) = x·ln(x/y) + (1−x)·ln((1−x)/(1−y))

### ΔS Node-Move Gain (v moves from A to B)

```
Δp = e_B(v) − e_A(v)           # change in intra-community edges
ΔM = n_B − (n_A − 1)           # change in possible intra-community edges
q' = (p + Δp) / m
⟨q'⟩ = (M + ΔM) / N
ΔS = m · [D_KL(q'∥⟨q'⟩) − D_KL(q∥⟨q⟩)]
```

Complexity: O(d_v) per evaluation. Counters update IMMEDIATELY after each accepted move.

### Algorithm Flow (Final, Unified)

**On receiving batch Δ(t):**

1. **Apply edge updates to graph.** Update m, p counters (O(k)).
2. **Construct affected set S.** S₀ = update endpoints → S₁ = S₀ ∪ N(S₀). For ISL-adaptive: expand boundary if max boundary ΔS > τ, up to R_max hops.
3. **Local Surprise optimization within S.**
   - For each pass (up to max_iter passes):
     - Visit nodes in S in random order
     - For each node v with dwell_counter ≥ δ: evaluate ΔS(v → C) for each neighboring community C ≠ σ(v)
     - If max ΔS > τ_min: move v to best community; update ALL counters immediately; reset v's dwell_counter
   - Stop when no improving move found or max_iter reached
4. **Connectivity check.** For each community modified in step 3: extract subgraph, check connectedness. If disconnected: split into components, re-run local moves on fragments.
5. **Periodic full recomputation (every K batches).** Run leidenalg SurpriseVertexPartition on full graph. Compare NMI(P_incremental, P_full). If NMI < δ: adopt P_full. Log trigger event.
6. **Record metrics.** S, Q, time, |S|, nodes moved, community count, churn rate.

### Parameters

| Parameter | Meaning | Recommended | Tunable? |
|:---|:---|:---|:---|
| K | Batches between full recomputation | 50 | Yes (ablation: 20, 50, 100, ∞) |
| δ (dwell) | Min batches before node re-evaluation | 2 | Yes (ablation: 0, 1, 2, 5) |
| τ_min | Min ΔS gain to accept a move | 1e-6 | Yes |
| max_iter | Max local-move passes per batch | 100 | Fixed |
| R_max | Max expansion radius (ISL-adaptive) | 3 | Fixed |

---

## 6. Pre-Implementation Validation Plan

### MANDATORY. 10 calendar days. Three experiments.

---

### Validation 1: Asymptotic Approximation Accuracy

**What:** Compare exact Surprise (hypergeometric formula) vs. asymptotic Surprise (KL divergence) across varying community sizes.

**Why:** ISL's primary claim (finding small communities) relies on the approximation being accurate for small communities. Sonnet #2 identified this as the most dangerous risk.

**Procedure:**
1. Generate LFR graphs: n=5000, average degree=15, community sizes in {20, 50, 100, 200, 500}
2. For each graph: compute ground-truth partition's exact Surprise and asymptotic Surprise
3. Also compute 10 random partitions' exact and asymptotic Surprise
4. Plot: relative error = |S_exact − S_asymptotic| / S_exact vs. minimum community size

**Acceptable result:** Relative error < 5% for communities ≥ 50 nodes. Relative error < 2% for communities ≥ 100 nodes.

**If validation fails:** Options: (a) use exact Surprise for ΔS computation (slower but correct); (b) reframe claims to apply only to communities ≥ 100 nodes; (c) switch to Significance metric (Traag et al. 2015) which may have better small-community approximation.

---

### Validation 2: Warm-Start Effectiveness

**What:** Test whether P(t) is a useful starting point for Surprise optimization at t+1.

**Why:** If the warm-start provides no benefit, ISL's efficiency claim collapses — local moves from P(t) won't reach a good partition at t+1.

**Procedure:**
1. Generate LFR graph (n=5000, μ=0.3)
2. Compute initial P(0) via static Surprise (leidenalg)
3. Apply 5 batches of k=50 random edge insertions
4. For each batch t: compute P_warm(t) = ISL local moves starting from P(t−1) AND P_cold(t) = full static Surprise from scratch
5. Measure: NMI(P_warm, ground_truth) vs. NMI(P_cold, ground_truth) and wall-clock time

**Acceptable result:** NMI(P_warm) ≥ 0.95 · NMI(P_cold) with at least 2× speedup.

**If validation fails:** The warm-start is not useful for Surprise. Options: (a) use more aggressive local optimization (more passes, larger affected set); (b) combine warm-start with random perturbation (shake); (c) this is a fundamental limitation — acknowledge and proceed with more frequent full recomputation.

---

### Validation 3: Over-Partitioning Bias Magnitude

**What:** Measure how many communities Surprise produces vs. ground truth on LFR benchmarks.

**Why:** If Surprise produces 3× more communities than ground truth, the "better community detection" claim collapses.

**Procedure:**
1. Generate LFR graphs: n=5000, μ ∈ {0.1, 0.2, 0.3, 0.4}, known community count
2. Run leidenalg SurpriseVertexPartition → count communities found
3. Run leidenalg ModularityVertexPartition → count communities found
4. Compare both against ground truth community count

**Acceptable result:** Surprise community count within 2× of ground truth for μ ≤ 0.3. Over-partitioning ratio should be characterized but not necessarily eliminated.

**If validation fails (severe over-partitioning):** Options: (a) add community-count regularization term; (b) switch to Significance (less over-partitioning); (c) add post-processing community merging step; (d) report as a known limitation and focus claims on NMI rather than community count.

---

### Go/No-Go Decision

| Validation | Pass → | Fail → |
|:---|:---|:---|
| Approximation accuracy | Proceed to Sprint 1 | Switch to exact Surprise or reframe claims |
| Warm-start effectiveness | Proceed with current design | Increase K (more frequent full recomputation) or add perturbation |
| Over-partitioning bias | Proceed; report bias as known property | Add regularization or switch to Significance |

**All three must pass for the project to proceed as currently designed.** Partial failures trigger design modifications, not project cancellation.

---

## 7–10. Summary Tables

### FINAL DECISIONS MADE

| # | Decision | Rationale |
|:---|:---|:---|
| 1 | Objective function: Asymptotic Surprise | First-mover advantage; resolution-limit-free |
| 2 | No community closure in affected set | Unnecessary for non-additive objective; harmful to locality |
| 3 | No multi-level aggregation in incremental case | Not feasible for non-additive Surprise; periodic full Leiden recomputation provides quality correction |
| 4 | Gap monitor: periodic full recomputation every K=50 batches | Simple, fully specified, avoids stale-cache and undefined-drift problems |
| 5 | Counter update timing: IMMEDIATE after each node move | Correctness requirement (Sonnet #2 Fix 5) |
| 6 | HIT-Leiden comparison: proxy via static Leiden quality | Avoids Rust integration; cleaner argument by transitivity |
| 7 | DynaMo baseline replaced with Fixed-Radius BFS + Static Leiden | Fully specifiable; no ambiguous "simplified DynaMo" |
| 8 | SNAP datasets: insertion-only mode | Deletion semantics undefined for SNAP; explicit in paper |
| 9 | Scope: Python prototype targets n ≤ 10⁵ | Honest about Python ceiling; larger graphs via static comparison only |
| 10 | T4 constructive proof: REQUIRED contribution | Achievable; strengthens theoretical depth significantly |
| 11 | Node ordering: ≥3 random orderings per batch, report variance | Addresses Sonnet #2's non-additivity concern |
| 12 | Primary evidence: NMI vs. ground truth, NOT Surprise value | Avoids evaluation circularity |

### ASSUMPTIONS ACCEPTED

1. ISL is the first incremental Surprise optimization algorithm ✅
2. ΔS is O(d_v) per node-move evaluation ✅
3. leidenalg SurpriseVertexPartition provides static baseline ✅
4. Surprise is resolution-limit-free (Aldecoa & Marín 2011) ✅
5. igraph is the correct graph backend ✅
6. The Surprise sensitivity value bound is likely provable ✅
7. Edge-proximity affected set (1-hop) is sufficient for most updates ✅

### ASSUMPTIONS REJECTED

1. ~~Community closure is needed~~ → REJECTED (Phase 3 correct)
2. ~~Multi-level aggregation transfers to Surprise~~ → REJECTED (Surprise not community-additive)
3. ~~Surprise-gap monitor via "relative drift"~~ → REJECTED (underspecified; replaced with periodic K-batch recomputation)
4. ~~Python scales to SNAP-sized datasets~~ → REJECTED (cap at n ≤ 10⁵)
5. ~~ISL competes with HIT-Leiden on speed~~ → REJECTED (compete on quality only)
6. ~~DynaMo re-implementation is a viable baseline~~ → REJECTED (replaced with Fixed-Radius BFS + Static Leiden)

### ASSUMPTIONS DEFERRED FOR VALIDATION

1. **Asymptotic approximation accuracy for small communities** → Pre-Sprint A, Validation 1
2. **Warm-start effectiveness for Surprise landscape** → Pre-Sprint A, Validation 2
3. **Over-partitioning bias magnitude and compounding** → Pre-Sprint A, Validation 3
4. **Surprise sensitivity bound provability** → Attempt during Sprint 2; not a blocker
5. **Single-level optimization quality vs. multi-level** → Empirical comparison during Sprint 3 (compare ISL-result vs. leidenalg full Leiden on affected subgraph)

---

**END OF PART 1**

**Awaiting approval before generating Part 2.**
