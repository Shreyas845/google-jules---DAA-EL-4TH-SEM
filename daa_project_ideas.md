# Advanced DAA Project Ideas — Research-Oriented

> [!IMPORTANT]
> Each project below is designed to be **resume-worthy**, **IEEE-publishable**, and **implementation-heavy**. They are grounded in real research gaps identified from 2024–2025 literature.

---

## Project 1: Adaptive Hybrid Metaheuristic for Dynamic Capacitated Vehicle Routing with Stochastic Demands

### Problem Statement
In last-mile logistics, delivery demands arrive dynamically and stochastically. The Dynamic Capacitated Vehicle Routing Problem with Stochastic Demands (DCVRPSD) requires real-time re-optimization of routes as new orders appear and existing demand quantities are uncertain. This is an NP-hard problem where solution quality degrades rapidly with scale.

### Why Existing Approaches Fail
| Limitation | Detail |
|:---|:---|
| **Static solvers** | Classical VRP solvers (Clarke-Wright, branch-and-cut) assume all demands are known upfront — unusable for dynamic contexts |
| **Pure RL approaches** | Deep RL methods suffer from curse of dimensionality when vehicles exceed ~50; training is brittle |
| **Single metaheuristics** | Standalone GA or ACO get trapped in local optima under time pressure; no convergence guarantees |
| **Latency** | Most methods cannot produce feasible solutions within the 1–5 second window required for real-time logistics |

### Proposed Algorithmic Improvement
A **three-phase adaptive hybrid**:
1. **Phase 1 — Constructive Heuristic**: Modified nearest-neighbor with regret-based insertion for initial feasible solution (O(n² log n))
2. **Phase 2 — Adaptive Large Neighborhood Search (ALNS)**: Destroy-and-repair operators with roulette-wheel selection that adapts operator probabilities based on recent performance
3. **Phase 3 — Intensification via Simulated Annealing**: Adaptive cooling schedule that tightens as computation budget depletes

**Key innovation**: An *operator portfolio* mechanism that switches between exploration (random removal, worst removal) and exploitation (greedy repair, regret-2 repair) based on a sliding-window success metric.

### Algorithms & Data Structures
- ALNS with adaptive operator selection
- Simulated Annealing with reheating
- Priority queues (Fibonacci heaps) for customer insertion
- k-d trees for spatial nearest-neighbor queries
- Rolling-horizon framework for dynamic events

### Expected Research Contribution
- Demonstration that adaptive operator portfolios outperform fixed-operator ALNS by 8–15% on dynamic instances
- Scalability analysis showing sub-second solutions for 200+ customer instances
- Pareto analysis of solution quality vs. computation time

### Feasibility
**High** — Core ALNS is well-documented; student extends with adaptive selection and dynamic event handling. Can start with static CVRP, then add dynamism incrementally.

### Tech Stack
`Python 3.11+` · `NumPy/SciPy` · `OR-Tools (Google)` for baselines · `Matplotlib/Plotly` for visualization · `SimPy` for discrete-event simulation of dynamic arrivals

### Datasets & Simulators
- **Solomon benchmark instances** (VRPTW, 100 customers) — classic baselines
- **Gehring & Homberger** large-scale instances (200–1000 customers)
- **DIMACS VRP Challenge** datasets
- Custom dynamic generator using Poisson arrival process

### Evaluation Metrics
- Total distance / total cost
- Number of vehicles used
- Computation time per re-optimization
- Gap from best-known static solution (%)
- Robustness: variance across stochastic runs

### IEEE/Publication Potential
**High** — Dynamic VRP with adaptive metaheuristics is actively published in *IEEE Access*, *IEEE Transactions on Intelligent Transportation Systems*, and *Computers & Operations Research*.

### Difficulty Level
🟡 **Intermediate–Advanced**

### Future Scope
- Multi-depot variant · Electric vehicle range constraints · Integration with real-time traffic APIs · Multi-objective (cost + emissions)

---

## Project 2: Graph Coloring–Based Dynamic Spectrum Allocation for 5G Heterogeneous Networks

### Problem Statement
In 5G heterogeneous networks (HetNets), macro cells, small cells, and D2D pairs share limited spectrum. Assigning frequency channels to minimize co-channel interference is equivalent to the **graph coloring problem** — which is NP-hard. Static allocation wastes spectrum; the network topology changes as users move.

### Why Existing Approaches Fail
| Limitation | Detail |
|:---|:---|
| **Fixed frequency reuse** | Wastes 40–60% of spectrum in dense urban deployments |
| **Greedy coloring (DSATUR, Welsh-Powell)** | Produces feasible but highly suboptimal chromatic numbers for dense interference graphs |
| **Centralized optimization** | Requires global interference knowledge; latency makes it impractical for real-time |
| **Pure GNN approaches** | Promising but lack theoretical guarantees on chromatic number bounds |

### Proposed Algorithmic Improvement
A **two-tier distributed algorithm**:
1. **Tier 1 — Weighted Conflict Graph Construction**: Build dynamic interference graph where edge weights = measured SINR degradation. Use spatial hashing for O(n) neighbor detection.
2. **Tier 2 — Hybrid Tabu-Search Graph Coloring**: Each base station runs a local Tabu Search that minimizes its chromatic neighborhood conflicts. A lightweight gossip protocol synchronizes color choices across 2-hop neighborhoods.

**Key innovation**: *Adaptive Tabu tenure* — tenure length adapts based on a "conflict density" metric (ratio of conflicting neighbors to total neighbors), preventing cycling in dense subgraphs while allowing rapid convergence in sparse regions.

### Algorithms & Data Structures
- Graph coloring (DSATUR, greedy, Tabu Search)
- Conflict/interference graph modeling
- Spatial hashing / R-trees for proximity queries
- Gossip-based distributed consensus
- Branch-and-bound (for small instances as exact baseline)

### Expected Research Contribution
- Adaptive Tabu coloring achieves 12–20% fewer colors than DSATUR on dense HetNet graphs
- Distributed algorithm converges in O(Δ·log n) rounds (Δ = max degree)
- Spectrum utilization improvement quantified via SINR and throughput metrics

### Feasibility
**High** — Graph coloring is well-understood; the novelty is in the adaptive Tabu + distributed protocol. Simulation-based (no real hardware needed).

### Tech Stack
`Python` · `NetworkX` for graph modeling · `SimPy` or custom event-driven simulator · `Matplotlib` for interference heatmaps · `NumPy`

### Datasets & Simulators
- **3GPP TR 36.814** HetNet deployment models (standardized cell layouts)
- **COST-231 propagation model** for path loss simulation
- Random geometric graphs (Poisson point process) for scalability testing
- Synthetic interference matrices (varying density)

### Evaluation Metrics
- Chromatic number achieved vs. theoretical lower bound (clique number)
- SINR improvement (dB)
- Spectrum utilization ratio (%)
- Convergence time (rounds / wall-clock)
- Message overhead (distributed protocol)

### IEEE/Publication Potential
**High** — Directly relevant to *IEEE Communications Letters*, *IEEE Transactions on Wireless Communications*.

### Difficulty Level
🔴 **Advanced**

### Future Scope
- Extension to list coloring / fractional coloring · mmWave beamforming integration · Quantum approximate coloring (QAOA) comparison

---

## Project 3: Fair Facility Location for Emergency Healthcare Access Using Approximation Algorithms

### Problem Statement
Placing emergency healthcare facilities (trauma centers, ambulance stations) optimally is a variant of the **k-median / k-center Facility Location Problem** (FLP). The challenge: minimizing *average* distance (efficiency) often leaves rural/underserved populations with catastrophically long response times. We need algorithms that are both efficient *and* equitable.

### Why Existing Approaches Fail
| Limitation | Detail |
|:---|:---|
| **Pure k-median** | Minimizes total/average distance but ignores worst-case; rural populations get 3–5× worse service |
| **Pure k-center** | Minimizes maximum distance but wastes resources in dense areas |
| **ILP solvers** | Exact but scale poorly beyond ~500 demand points; impractical for city-scale |
| **Greedy without fairness** | No principled way to balance efficiency vs. equity |

### Proposed Algorithmic Improvement
A **fairness-aware approximation framework**:
1. **LP Relaxation + Rounding**: Solve the LP relaxation of the k-facility problem with an augmented objective: `minimize α·(average distance) + (1-α)·(Gini coefficient of distances)`. Round fractional solution using dependent rounding.
2. **Local Search with Swap Moves**: Post-process with a local search that evaluates facility swaps using a bi-criteria cost function (efficiency + Atkinson inequality index).
3. **Pareto Frontier Generation**: Run for multiple α values to produce a portfolio of solutions for policymakers.

**Key innovation**: Formal approximation ratio analysis for the fairness-augmented objective, proving the algorithm achieves O(1)-approximation for the bi-criteria problem.

### Algorithms & Data Structures
- k-median and k-center formulations
- LP relaxation and randomized rounding
- Local search with swap neighborhoods
- Voronoi diagrams for assignment
- Gini coefficient / Atkinson index computation
- Branch-and-bound (exact baseline for small instances)

### Expected Research Contribution
- First student-accessible framework combining formal approximation guarantees with fairness metrics for FLP
- Empirical demonstration of 25–34% Gini reduction with ≤5% cost increase
- Pareto frontier visualization for decision-maker trade-off analysis

### Feasibility
**High** — LP solvers (PuLP, scipy.optimize) handle the relaxation; local search is straightforward. Real-world data is openly available.

### Tech Stack
`Python` · `PuLP` / `scipy.optimize.linprog` for LP · `Gurobi` (free academic license) for ILP baseline · `GeoPandas` + `Folium` for geographic visualization · `Matplotlib`

### Datasets & Simulators
- **OpenStreetMap** (OSM) road network data for any city
- **US Census / India Census** population density data
- **WHO Global Health Observatory** facility location data
- **NYC Open Data** — ambulance response time datasets

### Evaluation Metrics
- Average response time (minutes)
- Maximum response time (worst-case)
- Gini coefficient of response times
- Approximation ratio (achieved vs. LP lower bound)
- Runtime scalability (demand points: 100 → 10,000)

### IEEE/Publication Potential
**Very High** — Fairness in optimization is a hot topic. Suitable for *IEEE Transactions on Services Computing*, *AAAI*, *IJCAI*.

### Difficulty Level
🟡 **Intermediate–Advanced**

### Future Scope
- Dynamic FLP (facilities can relocate over time) · Multi-period demand modeling · Robust FLP under demand uncertainty · Integration with real ambulance dispatch data

---

## Project 4: Distributed Minimum Spanning Tree for Self-Healing Smart Grid Reconfiguration

### Problem Statement
When a fault occurs in a power distribution network (tree topology), the grid must rapidly reconfigure to restore power to unfaulted sections. This is equivalent to finding a new **minimum spanning tree** in the residual graph, subject to voltage, capacity, and radiality constraints. Centralized approaches are too slow and create single points of failure.

### Why Existing Approaches Fail
| Limitation | Detail |
|:---|:---|
| **Centralized MST (Kruskal/Prim)** | Requires global graph knowledge; single point of failure; communication latency |
| **Manual switching** | Takes 30–120 minutes; unacceptable for critical loads |
| **Simple distributed MST (GHS algorithm)** | Doesn't account for electrical constraints (voltage drop, line capacity, power flow) |
| **RL-based approaches** | Training requires extensive simulation; poor generalization to unseen topologies |

### Proposed Algorithmic Improvement
An **electrically-constrained distributed MST** algorithm:
1. **Modified GHS (Gallager-Humblet-Spira)**: Extend the classic distributed MST algorithm with edge weights that combine: `w(e) = β₁·resistance + β₂·hazard_exposure + β₃·(1/remaining_capacity)`
2. **Constraint Verification Layer**: After each MST merge step, agents verify voltage drop (DistFlow equations) and line capacity. Infeasible edges are pruned and alternatives explored.
3. **Priority-Aware Restoration**: Critical loads (hospitals, water pumps) get priority via a modified edge-weight bias during MST construction.

**Key innovation**: First integration of DistFlow power-flow constraints into a distributed MST protocol, with proven message complexity O(|E| + n·log n).

### Algorithms & Data Structures
- Distributed MST (GHS algorithm)
- Kruskal's / Prim's (centralized baselines)
- DistFlow equations for power flow
- Union-Find for component tracking
- Priority queues for edge selection
- Multi-agent message passing

### Expected Research Contribution
- Distributed MST that respects electrical constraints with provable message complexity
- 60–70% faster restoration compared to centralized SCADA-based reconfiguration
- Demonstration on IEEE test feeders (13-bus, 37-bus, 123-bus)

### Feasibility
**Medium-High** — Requires understanding of both graph algorithms and basic power systems. IEEE test feeders provide standardized test cases.

### Tech Stack
`Python` · `pandapower` for power flow simulation · `NetworkX` for graph operations · `SimPy` for distributed simulation · `Matplotlib` for network visualization

### Datasets & Simulators
- **IEEE 13-bus, 37-bus, 123-bus test feeders** (standard benchmarks)
- **pandapower** built-in test networks
- **MATPOWER** case files (convertible to Python)
- Custom fault scenario generator

### Evaluation Metrics
- Restoration time (seconds/rounds)
- Load restored (% of total / % of critical)
- Voltage deviation from nominal (%)
- Message complexity (total messages exchanged)
- Comparison: distributed vs. centralized MST vs. manual

### IEEE/Publication Potential
**Very High** — Smart grid resilience is a priority area for *IEEE Transactions on Power Systems* and *IEEE Transactions on Smart Grid*.

### Difficulty Level
🔴 **Advanced**

### Future Scope
- Integration with renewable DERs · Cyber-attack resilience · Real-time hardware-in-the-loop testing · Extension to mesh topologies

---

## Project 5: Multi-Objective Evacuation Routing with Equity-Aware Graph Optimization

### Problem Statement
During urban disasters (floods, earthquakes, industrial accidents), evacuating a population through a road network requires solving a **multi-commodity flow problem** on a time-expanded graph. The challenge: maximizing evacuation throughput while ensuring no neighborhood is disproportionately delayed (equity), all under dynamically changing road conditions.

### Why Existing Approaches Fail
| Limitation | Detail |
|:---|:---|
| **Shortest-path routing** | Creates bottlenecks; ignores road capacity; cascading congestion |
| **Static max-flow** | Doesn't model time; can't handle contraflow or phased evacuation |
| **Time-expanded networks** | Correct but graph size explodes: O(n·T) nodes for T time steps |
| **Efficiency-only optimization** | Poor neighborhoods with fewer exits get systematically deprioritized |

### Proposed Algorithmic Improvement
1. **Compressed Time-Expanded Graph**: Reduce graph size by merging time steps with similar flow patterns using a clustering-based compression (reduce O(n·T) to O(n·√T))
2. **Multi-Objective LP + ε-Constraint**: Solve for two objectives: (a) minimize total evacuation time, (b) minimize max neighborhood clearance time (equity). Use augmented ε-constraint to generate Pareto frontier.
3. **Adaptive Contraflow**: Greedy heuristic that iteratively reverses road directions on bottleneck edges, re-solving the flow problem after each reversal.

**Key innovation**: Graph compression technique that makes time-expanded network tractable for cities with 5,000+ road segments, combined with formal equity modeling.

### Algorithms & Data Structures
- Max-flow / min-cost flow (Ford-Fulkerson, successive shortest paths)
- Time-expanded network construction
- Multi-objective LP (ε-constraint method)
- Graph compression via temporal clustering
- Contraflow heuristic (greedy edge reversal)
- Dijkstra / A* for shortest paths

### Expected Research Contribution
- Graph compression reduces problem size by 60–75% with ≤3% optimality loss
- Equity-aware routing reduces worst-case neighborhood clearance time by 30–40%
- Scalable to real city road networks (10,000+ edges)

### Feasibility
**Medium-High** — Max-flow and LP are well-understood; the novelty is in compression + equity. Real road network data is freely available.

### Tech Stack
`Python` · `NetworkX` · `PuLP` / `Gurobi` for LP/ILP · `OSMnx` for real road network extraction · `Folium` for map visualization · `Matplotlib`

### Datasets & Simulators
- **OpenStreetMap** via `OSMnx` — any city's road network
- **Sioux Falls network** (classic transportation benchmark)
- **FEMA flood zone maps** for hazard overlays
- Custom demand generators based on census population data

### Evaluation Metrics
- Total evacuation time (all evacuees cleared)
- Max neighborhood clearance time
- Equity index (Gini of clearance times)
- Network utilization (% of road capacity used)
- Compression ratio and optimality gap

### IEEE/Publication Potential
**Very High** — Equity in evacuation is a timely topic. Suitable for *IEEE Transactions on Intelligent Transportation Systems*, *Transportation Research Part B*.

### Difficulty Level
🟡 **Intermediate–Advanced**

### Future Scope
- Real-time re-routing with dynamic edge failures · Pedestrian + vehicular mixed evacuation · Shelter capacity constraints · Agent-based behavioral modeling

---

## Project 6: Energy-Aware DAG Scheduling on Heterogeneous Edge-Cloud Systems

### Problem Statement
Workflow applications (video analytics, scientific computing) are modeled as **Directed Acyclic Graphs (DAGs)** where nodes are tasks and edges are data dependencies. Scheduling these DAGs across heterogeneous processors (edge devices, cloud VMs with varying speeds and energy costs) to minimize makespan *and* energy consumption is NP-hard.

### Why Existing Approaches Fail
| Limitation | Detail |
|:---|:---|
| **HEFT (classic heuristic)** | Optimizes makespan only; ignores energy; assumes homogeneous communication |
| **CPOP** | Focuses on critical path; suboptimal for wide, parallel DAGs |
| **ILP formulations** | Exact but timeout on DAGs with >50 tasks on >10 processors |
| **DRL schedulers** | Require expensive retraining when system configuration changes |

### Proposed Algorithmic Improvement
A **bi-objective list-scheduling heuristic** with three innovations:
1. **Composite Priority Metric**: Replace HEFT's upward rank with: `priority(t) = γ·upward_rank(t) + (1-γ)·energy_rank(t)`, where energy_rank accounts for DVFS-adjusted energy on each processor.
2. **Processor Selection with Pareto Filtering**: For each task, compute (makespan_contribution, energy_contribution) on each eligible processor. Use Pareto filtering to eliminate dominated choices, then select using a weighted Tchebycheff scalarization.
3. **Post-Scheduling DVFS Optimization**: After initial schedule, identify tasks with slack (finish_time < successor_start). Reduce their processor frequency using DVFS to save energy without increasing makespan.

**Key innovation**: DVFS-aware slack reclamation as a polynomial-time post-processing step, provably non-degrading for makespan.

### Algorithms & Data Structures
- DAG topological sorting
- HEFT / CPOP (baselines)
- List scheduling with composite priorities
- Pareto dominance filtering
- DVFS energy modeling
- Critical path analysis

### Expected Research Contribution
- 20–35% energy reduction vs. HEFT with ≤5% makespan increase
- Polynomial time complexity: O(n²·p) for n tasks, p processors
- Scalability to DAGs with 500+ tasks on 20+ heterogeneous processors

### Feasibility
**High** — HEFT implementation is straightforward; extensions are well-scoped. Standard DAG benchmarks are available.

### Tech Stack
`Python` · `NumPy` · `Matplotlib` for Gantt charts · `NetworkX` for DAG manipulation · Custom simulator for heterogeneous processors

### Datasets & Simulators
- **Standard Task Graphs (STG)** — Tobita & Kasahara benchmark DAGs
- **Pegasus Workflow Generator** — scientific workflow DAGs (Montage, LIGO, CyberShake)
- **Random DAG generators** (Erdős-Rényi, layer-by-layer) with tunable parallelism
- **ARM big.LITTLE** energy/frequency profiles for processor modeling

### Evaluation Metrics
- Makespan (total completion time)
- Total energy consumption (Joules)
- Energy-Delay Product (EDP)
- Schedule Length Ratio (SLR = makespan / critical_path_length)
- Speedup vs. sequential execution
- Scalability: runtime vs. DAG size

### IEEE/Publication Potential
**High** — Suitable for *IEEE Transactions on Parallel and Distributed Systems*, *Journal of Parallel and Distributed Computing*.

### Difficulty Level
🟡 **Intermediate**

### Future Scope
- Fault-tolerant scheduling (task replication) · Dynamic DAGs with runtime task spawning · Multi-cloud cost optimization · Deadline-constrained scheduling

---

## Project 7: Carbon-Aware Multi-Objective Knapsack Optimization for Sustainable Supply Chain Selection

### Problem Statement
A manufacturer must select suppliers, transportation modes, and production quantities to maximize profit while minimizing carbon footprint and waste — subject to budget, capacity, and demand constraints. This is a **multi-dimensional, multi-objective knapsack problem** (NP-hard), complicated by conflicting objectives and real-world constraints.

### Why Existing Approaches Fail
| Limitation | Detail |
|:---|:---|
| **Single-objective knapsack** | Optimizes profit only; ignores environmental impact |
| **Weighted-sum scalarization** | Cannot find solutions on non-convex Pareto regions |
| **NSGA-II (standard)** | Good for 2 objectives but diversity degrades with 3+ objectives; slow convergence on large instances |
| **Exact methods (B&B)** | Infeasible for >100 items with multiple knapsack dimensions |

### Proposed Algorithmic Improvement
1. **Three-Objective Formulation**: Minimize cost, minimize carbon emissions (Scope 1+2+3), minimize waste — subject to capacity, demand, and quality constraints.
2. **Hybrid MOEA/D + Local Search**: Decomposition-based MOEA (MOEA/D) with adaptive weight vectors for uniform Pareto coverage. Augment with a problem-specific local search: swap and 2-opt moves on the supplier selection.
3. **Carbon-Budget ε-Constraint**: Generate "carbon budget" scenarios (e.g., reduce emissions by 20%, 40%, 60%) and solve each as a constrained single-objective problem to produce actionable decision points.

**Key innovation**: Adaptive reference-point generation for MOEA/D that concentrates search effort in the "knee region" of the Pareto front — the area of maximum marginal trade-off.

### Algorithms & Data Structures
- Multi-dimensional knapsack formulation
- MOEA/D with Tchebycheff scalarization
- NSGA-II and NSGA-III (baselines)
- ε-constraint method
- Dynamic programming (for small instances as exact baseline)
- Greedy heuristics (density-ratio based)

### Expected Research Contribution
- Adaptive reference-point MOEA/D achieves 15–25% better hypervolume than standard NSGA-II on 3-objective supply chain instances
- Actionable Pareto frontiers for real supply chain decision-making
- Formal analysis of trade-off between carbon reduction and cost increase

### Feasibility
**High** — MOEA frameworks (pymoo, DEAP) handle infrastructure; student focuses on problem formulation and adaptive mechanisms.

### Tech Stack
`Python` · `pymoo` (multi-objective optimization framework) · `DEAP` · `Pandas` for data handling · `Plotly` for 3D Pareto visualization · `PuLP` for ε-constraint baseline

### Datasets & Simulators
- **Ecoinvent** / **OpenLCA** — lifecycle emission factors for materials and transport
- **World Bank logistics data** — transportation costs by mode
- **Synthetic supply chain generators** — parameterized by number of suppliers, products, transport modes
- **GHG Protocol** emission factors for Scope 1/2/3

### Evaluation Metrics
- Hypervolume indicator (Pareto front quality)
- Inverted Generational Distance (IGD)
- Spacing metric (solution diversity)
- Carbon intensity (kg CO₂ per unit profit)
- Computation time vs. problem size
- Comparison: MOEA/D vs. NSGA-II vs. NSGA-III vs. exact

### IEEE/Publication Potential
**High** — Green supply chain optimization is trending. Suitable for *IEEE Transactions on Engineering Management*, *Journal of Cleaner Production*.

### Difficulty Level
🟡 **Intermediate**

### Future Scope
- Stochastic demands and disruptions · Multi-period planning · Circular economy (recycling loops) · Carbon credit trading integration

---

## Project 8: Scalable Incremental Community Detection in Evolving Social Networks via Adaptive Graph Partitioning

### Problem Statement
Social networks evolve continuously — users join, leave, form/break connections. Detecting community structure in such **dynamic graphs** requires algorithms that update communities incrementally rather than recomputing from scratch (which is O(n²) or worse per snapshot). The challenge: maintaining detection quality while achieving sub-linear update time.

### Why Existing Approaches Fail
| Limitation | Detail |
|:---|:---|
| **Static Louvain/Leiden** | Must rerun on entire graph after each batch of changes; O(n·log²n) per snapshot |
| **Label Propagation** | Fast but unstable; communities "flicker" between snapshots |
| **Streaming algorithms** | Process one edge at a time; miss global community structure |
| **GNN-based methods** | Require retraining or expensive forward passes; poor on unseen graph topologies |

### Proposed Algorithmic Improvement
1. **Affected-Region Detection**: When edges are inserted/deleted, identify the "affected region" — the set of nodes whose community assignment might change. Use a BFS-bounded expansion from modified edges (radius proportional to log of community size).
2. **Local Modularity Re-optimization**: Within the affected region only, run a modified Louvain pass that re-assigns nodes to maximize modularity. Unaffected regions are frozen.
3. **Periodic Global Correction**: Every K batches, run a lightweight global pass to correct accumulated drift.

**Key innovation**: *Adaptive radius* — the BFS expansion radius adapts based on the *boundary density* of the affected community (dense boundaries → small radius; sparse boundaries → larger radius). This prevents both under-exploration (missing genuine changes) and over-exploration (wasted computation).

### Algorithms & Data Structures
- Modularity maximization (Louvain / Leiden)
- BFS with adaptive radius
- Dynamic graph data structures (adjacency lists with O(1) edge insertion/deletion)
- Union-Find for community tracking
- Hash-based edge existence queries
- Batch processing framework

### Expected Research Contribution
- 5–20× speedup over static recomputation with ≤2% modularity degradation
- Formal analysis: amortized update time O(Δk · log n) where Δk = number of affected nodes
- Demonstration on million-node real social network snapshots

### Feasibility
**Medium-High** — Louvain is well-documented; the incremental extension requires careful engineering but is conceptually accessible.

### Tech Stack
`Python` / `C++` (for performance-critical inner loop) · `NetworkX` or `igraph` · `SNAP` dataset tools · `Matplotlib` / `Gephi` for community visualization · `NumPy`

### Datasets & Simulators
- **SNAP datasets**: Temporal edges for Facebook, Reddit, Wikipedia, Bitcoin
- **Enron email network** (temporal)
- **DBLP co-authorship** (yearly snapshots)
- **LFR Benchmark** — synthetic networks with known ground-truth communities and tunable dynamics
- **Stochastic Block Model** generator for controlled experiments

### Evaluation Metrics
- Normalized Mutual Information (NMI) vs. ground truth
- Modularity score
- Update time per batch (ms)
- Speedup over static recomputation
- Community stability (Jaccard similarity between consecutive snapshots)
- Scalability: nodes from 10K → 1M

### IEEE/Publication Potential
**Very High** — Dynamic community detection is a recognized open problem. Suitable for *IEEE Transactions on Knowledge and Data Engineering*, *KDD*, *WWW*.

### Difficulty Level
🔴 **Advanced**

### Future Scope
- Overlapping community detection · Multiplex/multilayer networks · Anomaly detection via community disruption · Privacy-preserving federated community detection

---

## Comparative Summary

| # | Project | Core DAA Technique | Domain | Difficulty | IEEE Potential |
|:--|:--------|:-------------------|:-------|:-----------|:---------------|
| 1 | Adaptive ALNS for Dynamic VRP | Metaheuristic, ALNS, SA | Logistics | Intermediate–Advanced | High |
| 2 | Graph Coloring for 5G Spectrum | Graph Coloring, Tabu Search | Telecom | Advanced | High |
| 3 | Fair Facility Location | Approximation, LP Rounding | Healthcare | Intermediate–Advanced | Very High |
| 4 | Distributed MST for Smart Grid | Distributed MST, GHS | Energy | Advanced | Very High |
| 5 | Equity-Aware Evacuation Routing | Max-Flow, LP, Graph Compression | Disaster Mgmt | Intermediate–Advanced | Very High |
| 6 | Energy-Aware DAG Scheduling | List Scheduling, DVFS, DAG | Cloud/Edge | Intermediate | High |
| 7 | Carbon-Aware Knapsack | Multi-Obj Knapsack, MOEA/D | Sustainability | Intermediate | High |
| 8 | Incremental Community Detection | Modularity, Graph Partitioning | Social Networks | Advanced | Very High |

---

## Recommended Starting Points

> [!TIP]
> **If you want maximum DAA depth**: Projects 3, 4, or 5 (approximation algorithms, distributed algorithms, network flow)
> 
> **If you want industry relevance**: Projects 1, 6, or 7 (logistics, cloud, sustainability)
> 
> **If you want highest publication potential**: Projects 3, 5, or 8 (fairness + algorithms is trending)
> 
> **If you want graph algorithm focus**: Projects 2, 4, or 8 (coloring, MST, partitioning)
