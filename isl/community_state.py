import numpy as np
import igraph as ig
import leidenalg

class CommunityState:
    def __init__(self, n: int, initial_partition_labels: np.ndarray, graph: ig.Graph = None):
        """
        Initializes the community state.

        Args:
            n: Number of nodes in the graph
            initial_partition_labels: numpy array where initial_partition_labels[v] = community of node v
            graph: The igraph.Graph object. Needed for exact Significance evaluation via leidenalg.
        """
        self.sigma = np.array(initial_partition_labels, dtype=int)
        self.comm_size = {}
        for c in self.sigma:
            self.comm_size[c] = self.comm_size.get(c, 0) + 1

        self.comm_internal_edges = {c: 0 for c in self.comm_size}

        self.m = 0
        self.p = 0
        self.M = sum(n_c * (n_c - 1) // 2 for n_c in self.comm_size.values())
        self.N = n * (n - 1) // 2

        self.dwell_counter = np.zeros(n, dtype=int)
        self.graph = graph

        # Keep an active partition object for fast evaluation
        if self.graph is not None:
            self.partition_obj = leidenalg.SignificanceVertexPartition(self.graph, initial_membership=self.sigma.tolist())
        else:
            self.partition_obj = None

    def move_node(self, v: int, c_target: int, e_to_old: int, e_to_new: int, n_old_before_move: int, n_new_before_move: int):
        c_old = self.sigma[v]

        if c_old == c_target:
            return

        self.sigma[v] = c_target

        self.comm_size[c_old] -= 1
        self.comm_size[c_target] = self.comm_size.get(c_target, 0) + 1

        self.comm_internal_edges[c_old] -= e_to_old
        self.comm_internal_edges[c_target] = self.comm_internal_edges.get(c_target, 0) + e_to_new

        self.p += (e_to_new - e_to_old)
        self.M += (self.comm_size[c_target] - 1) - self.comm_size[c_old]

        if self.comm_size[c_old] == 0:
            del self.comm_size[c_old]
            del self.comm_internal_edges[c_old]

        self.dwell_counter[v] = 0



    def apply_edge_update(self, u: int, v: int, action: int):
        self.m += action
        if self.sigma[u] == self.sigma[v]:
            self.p += action
            c = self.sigma[u]
            self.comm_internal_edges[c] = self.comm_internal_edges.get(c, 0) + action

        if self.partition_obj is not None:
            # If the graph edges are updated, the graph inside partition_obj doesn't change automatically
            # Actually, igraph modifies it in-place usually, but let's be safe and recreate it.
            # However, apply_edge_update is called batch-wise, so we can defer recreation.
            pass

    def get_significance(self) -> float:
        """
        Calculates the exact significance of the current partition using leidenalg.
        """
        if self.graph is None:
            return 0.0

        # Leidenalg requires labels to be consecutive and < n. Map them.
        unique_labels = list(self.comm_size.keys())
        label_map = {old_label: new_label for new_label, old_label in enumerate(unique_labels)}
        mapped_membership = [label_map[c] for c in self.sigma]

        self.partition_obj = leidenalg.SignificanceVertexPartition(self.graph, initial_membership=mapped_membership)
        return self.partition_obj.quality()

    def get_delta_s(self, v: int, c_target: int, e_to_old: int, e_to_new: int, n_old: int, n_new: int) -> float:
        raise NotImplementedError("Delegated to delta_s module for subgraph significance")

    def increment_dwell_counters(self):
        self.dwell_counter += 1

    def recompute_from_scratch(self, graph: ig.Graph):
        self.graph = graph
        n = graph.vcount()
        self.m = graph.ecount()

        self.comm_size = {}
        for c in self.sigma:
            self.comm_size[c] = self.comm_size.get(c, 0) + 1

        self.comm_internal_edges = {c: 0 for c in self.comm_size}
        self.p = 0

        for e in graph.es:
            u, v = e.source, e.target
            if self.sigma[u] == self.sigma[v]:
                self.p += 1
                self.comm_internal_edges[self.sigma[u]] += 1

        self.M = sum(n_c * (n_c - 1) // 2 for n_c in self.comm_size.values())
        self.N = n * (n - 1) // 2

        self.partition_obj = leidenalg.SignificanceVertexPartition(self.graph, initial_membership=self.sigma.tolist())
