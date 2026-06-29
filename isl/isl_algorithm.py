import numpy as np
import igraph as ig
import time
from isl.community_state import CommunityState
from isl.graph_engine import GraphEngine
from isl.affected_set import build_affected_set_1hop, build_affected_set_adaptive
from isl.local_moves import run_local_moves
from isl.connectivity import check_and_fix_connectivity
from isl.periodic_recompute import PeriodicRecomputeEngine

class ISLAlgorithm:
    def __init__(self, config: dict, variant: str = 'isl_1hop'):
        self.variant = variant
        self.config = config
        self.params = config.get('params', {})

        # Determine R_max, tau
        self.R_max = self.params.get('R_max', 3)
        self.tau = self.params.get('tau_min', 1e-6)

        # Configure periodic recompute
        if variant == 'isl_no_correction':
            self.K = -1 # Never trigger
        else:
            self.K = self.params.get('K', 50)

        # Configure dwell time
        if variant == 'isl_no_dwell':
            self.params['delta_dwell'] = 0

        self.periodic_recompute = PeriodicRecomputeEngine(K=self.K, nmi_threshold=0.9, seed=42)

        self.graph = None
        self.state = None

    def initialize(self, graph: ig.Graph, initial_sigma: np.ndarray):
        self.graph = graph
        self.state = CommunityState(graph.vcount(), initial_sigma.copy(), graph)
        self.state.recompute_from_scratch(graph)

    def process_batch(
        self,
        edges_add: list,
        edges_del: list,
        batch_idx: int,
        ground_truth: np.ndarray = None
    ) -> dict:
        t_start = time.perf_counter()

        sigma_before = self.state.sigma.copy()
        n = self.graph.vcount()

        # 1. Apply edge updates
        max_v = max(max(u, v) for u, v in edges_add + edges_del) if (edges_add or edges_del) else -1
        if max_v >= self.graph.vcount():
            self.graph.add_vertices(max_v - self.graph.vcount() + 1)
            # update state counters if we added vertices
            # dwell_counter needs to be extended
            if max_v >= len(self.state.dwell_counter):
                self.state.dwell_counter = np.pad(self.state.dwell_counter, (0, max_v - len(self.state.dwell_counter) + 1), constant_values=0)
                self.state.sigma = np.pad(self.state.sigma, (0, max_v - len(self.state.sigma) + 1), constant_values=0) # assign to default 0
        for u, v in edges_add:
            self.graph.add_edges([(u, v)])
            self.state.apply_edge_update(u, v, +1)

        for u, v in edges_del:
            try:
                eid = self.graph.get_eid(u, v)
                self.graph.delete_edges(eid)
                self.state.apply_edge_update(u, v, -1)
            except ig.InternalError:
                pass # Edge didn't exist

        # 2. Construct affected set
        updated_edges = edges_add + edges_del
        if not updated_edges:
            affected = set()
        elif self.variant == 'isl_adaptive':
            affected = build_affected_set_adaptive(self.graph, updated_edges, self.state, self.tau, self.R_max)
        else:
            affected = build_affected_set_1hop(self.graph, updated_edges)

        # 3. Local moves
        local_result = {'nodes_moved': 0, 'passes_completed': 0, 'communities_modified': set(), 'all_orderings_surprise': [], 'best_ordering_surprise': 0.0}
        if affected:
            local_result = run_local_moves(self.graph, self.state, affected, self.params)

        # 4. Connectivity check
        affected_communities = local_result.get('communities_modified', set())
        if affected_communities:
            check_and_fix_connectivity(self.graph, self.state, affected_communities)

        # 5. Periodic recomputation
        self.state.increment_dwell_counters()
        self.periodic_recompute.increment_batch()

        periodic_result = self.periodic_recompute.run_if_triggered(
            self.graph, self.state, batch_idx, ground_truth
        )

        t_end = time.perf_counter()
        time_ms = (t_end - t_start) * 1000

        # 6. Metrics (excluded from timing)

        # Calculate Modularity
        # Modularity requires list of memberships
        # It's an igraph builtin
        try:
            q = self.graph.modularity(self.state.sigma.tolist())
        except Exception:
            q = 0.0

        churn_rate = np.mean(sigma_before != self.state.sigma)

        metrics = {
            'batch_idx': batch_idx,
            'algorithm': self.variant,
            'S': self.state.get_significance(),
            'Q': q,
            'time_ms': time_ms,
            'nodes_moved': local_result['nodes_moved'],
            'affected_set_size': len(affected),
            'affected_set_fraction': len(affected) / n if n > 0 else 0,
            'community_count': len(self.state.comm_size),
            'churn_rate': float(churn_rate),
            'passes_completed': local_result['passes_completed'],
            'ordering_surprise_std': float(np.std(local_result['all_orderings_surprise'])) if local_result['all_orderings_surprise'] else 0.0,
            'periodic_trigger_fired': periodic_result.get('triggered', False),
            'periodic_trigger_adopted': periodic_result.get('adopted_full', False),
            'nmi_vs_full_at_trigger': periodic_result.get('nmi_incremental_vs_full', -1.0)
        }

        return metrics

    def get_current_partition(self) -> np.ndarray:
        return self.state.sigma.copy()

    def get_current_surprise(self) -> float:
        return self.state.get_significance()
