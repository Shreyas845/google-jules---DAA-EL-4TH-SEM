import numpy as np
import igraph as ig
import leidenalg
from sklearn.metrics import normalized_mutual_info_score as nmi
from isl.community_state import CommunityState
from isl.baselines import run_static_significance, partition_to_sigma

class PeriodicRecomputeEngine:
    def __init__(self, K: int = 50, nmi_threshold: float = 0.9, seed: int = 42):
        self.K = K
        self.nmi_threshold = nmi_threshold
        self.seed = seed
        self.batch_counter = 0
        self.trigger_count = 0
        self.trigger_batches = []

    def should_trigger(self) -> bool:
        return self.batch_counter > 0 and self.K > 0 and self.batch_counter % self.K == 0

    def increment_batch(self):
        self.batch_counter += 1

    def run_if_triggered(
        self,
        graph: ig.Graph,
        state: CommunityState,
        current_batch_idx: int,
        ground_truth: np.ndarray = None
    ) -> dict:
        if not self.should_trigger():
            return {
                'triggered': False,
                'nmi_incremental_vs_full': -1.0,
                'S_incremental': state.get_significance(),
                'S_full': -1.0,
                'adopted_full': False,
                'batch_idx': current_batch_idx
            }

        self.trigger_count += 1
        self.trigger_batches.append(current_batch_idx)

        # 1. Run full recompute (from scratch)
        full_sigma, _ = run_static_significance(graph, self.seed + current_batch_idx)

        # 2. Compute NMI
        nmi_val = nmi(state.sigma, full_sigma)

        # 3. Compute S_incremental
        s_inc = state.get_significance()

        # 4. Compute S_full
        part_full = leidenalg.SignificanceVertexPartition(graph, initial_membership=full_sigma.tolist())
        s_full = part_full.quality()

        adopted = False
        if nmi_val < self.nmi_threshold:
            # 5. Adopt full_partition
            state.sigma = full_sigma.copy()
            state.recompute_from_scratch(graph)
            adopted = True

        return {
            'triggered': True,
            'nmi_incremental_vs_full': nmi_val,
            'S_incremental': s_inc,
            'S_full': s_full,
            'adopted_full': adopted,
            'batch_idx': current_batch_idx
        }

    def get_trigger_rate(self) -> float:
        if self.batch_counter == 0:
            return 0.0
        return self.trigger_count / self.batch_counter
