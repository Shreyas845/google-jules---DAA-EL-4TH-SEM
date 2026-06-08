import numpy as np
import igraph as ig
from sklearn.metrics import normalized_mutual_info_score
from sklearn.metrics import adjusted_rand_score
from scipy.stats import wilcoxon
from isl.community_state import CommunityState

class EvaluationEngine:

    def compute_nmi(self, sigma_pred: np.ndarray, sigma_true: np.ndarray) -> float:
        return normalized_mutual_info_score(sigma_true, sigma_pred)

    def compute_ari(self, sigma_pred: np.ndarray, sigma_true: np.ndarray) -> float:
        return adjusted_rand_score(sigma_true, sigma_pred)

    def compute_surprise(self, state: CommunityState) -> float:
        # Since we switched to Significance, we should return Significance here
        # as requested. Although the method name might still be surprise.
        # But we'll return Significance.
        return state.get_significance()

    def compute_modularity(self, graph: ig.Graph, sigma: np.ndarray) -> float:
        try:
            return graph.modularity(membership=sigma.tolist())
        except Exception:
            return 0.0

    def compute_community_count(self, sigma: np.ndarray) -> int:
        return len(set(sigma))

    def compute_churn_rate(self, sigma_before: np.ndarray, sigma_after: np.ndarray) -> float:
        if len(sigma_before) == 0:
            return 0.0
        return np.mean(sigma_before != sigma_after)

    def compute_flickering_rate(self, sigma_t_minus_2: np.ndarray, sigma_t_minus_1: np.ndarray, sigma_t: np.ndarray) -> float:
        if len(sigma_t) == 0:
            return 0.0
        # A node flickers if it changed at t-1 AND changed back to t-2 at t.
        changed_t_minus_1 = (sigma_t_minus_2 != sigma_t_minus_1)
        changed_back = (sigma_t_minus_1 != sigma_t) & (sigma_t == sigma_t_minus_2)
        flickering = changed_t_minus_1 & changed_back
        return np.mean(flickering)

    def compute_affected_set_fraction(self, affected_set_size: int, n: int) -> float:
        if n == 0:
            return 0.0
        return affected_set_size / n

    def aggregate_across_seeds(self, results_per_seed: list) -> dict:
        """
        Input: list of per-batch result dicts, one list per seed.
        Output: {metric_name: {'mean': float, 'std': float}} per batch.
        Wait, output format is dict of batch results?
        Actually, we can return a list of dicts, one per batch, containing means and stds.
        Or a dict mapping batch_idx to {metric: {mean: x, std: y}}.
        Let's return a list of dicts where each dict is a batch.
        """
        num_seeds = len(results_per_seed)
        if num_seeds == 0:
            return []

        num_batches = len(results_per_seed[0])
        aggregated = []

        for b_idx in range(num_batches):
            batch_aggr = {'batch_idx': b_idx + 1}
            # Extract all keys from the first seed's batch
            keys = results_per_seed[0][b_idx].keys()
            for k in keys:
                if k in ['batch_idx', 'algorithm']:
                    batch_aggr[k] = results_per_seed[0][b_idx][k]
                elif isinstance(results_per_seed[0][b_idx][k], (int, float, bool)):
                    vals = [s[b_idx][k] for s in results_per_seed]
                    batch_aggr[k] = {'mean': float(np.mean(vals)), 'std': float(np.std(vals))}
            aggregated.append(batch_aggr)

        return aggregated

    def run_wilcoxon_test(self, results_method_a: list, results_method_b: list) -> dict:
        if len(results_method_a) < 2:
            return {'statistic': 0.0, 'p_value': 1.0, 'significant': False}

        # Check if arrays are identical
        if np.allclose(results_method_a, results_method_b):
            return {'statistic': 0.0, 'p_value': 1.0, 'significant': False}

        try:
            stat, p_val = wilcoxon(results_method_a, results_method_b, zero_method='zsplit')
            return {
                'statistic': float(stat),
                'p_value': float(p_val),
                'significant': bool(p_val < 0.05)
            }
        except ValueError:
            # E.g. all differences are zero
            return {'statistic': 0.0, 'p_value': 1.0, 'significant': False}
