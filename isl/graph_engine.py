import igraph as ig
import numpy as np

class GraphEngine:
    def __init__(self, n: int):
        self.graph = ig.Graph(n)

    def apply_batch(self, edges_add: list, edges_del: list) -> list:
        # Since igraph deletes by edge ID, we need to find the IDs of edges to delete
        # before any addition changes the graph structure.

        # 1. Look up edge IDs for deletion
        # igraph get_eid returns the edge ID or throws an error if it doesn't exist
        # But we need to handle non-existent gracefully or error loudly.
        # The blueprint says: "Deleting a non-existent edge raises a clear error"
        eids_to_del = []
        for u, v in edges_del:
            try:
                # get_eid raises ValueError if the edge does not exist
                eid = self.graph.get_eid(u, v)
                eids_to_del.append(eid)
            except ig.InternalError:
                raise ValueError(f"Cannot delete non-existent edge ({u}, {v})")

        # Check for duplicate insertions. igraph does not support multigraphs gracefully in ISL.
        for u, v in edges_add:
            if self.graph.are_adjacent(u, v):
                raise ValueError(f"Cannot add duplicate edge ({u}, {v})")

        self.graph.delete_edges(eids_to_del)
        self.graph.add_edges(edges_add)

        # Return affected node pairs
        return edges_add + edges_del

    def get_neighbors(self, v: int) -> list:
        return self.graph.neighbors(v)

    def get_neighbor_communities(self, v: int, sigma: np.ndarray) -> dict:
        neighbors = self.graph.neighbors(v)
        comm_counts = {}
        for n in neighbors:
            c = sigma[n]
            comm_counts[c] = comm_counts.get(c, 0) + 1
        return comm_counts

    def get_subgraph(self, node_set: list) -> ig.Graph:
        return self.graph.subgraph(node_set)

    def get_degree(self, v: int) -> int:
        return self.graph.degree(v)

    def load_from_edgelist(self, filepath: str):
        # Assumes space-separated edgelist.
        with open(filepath, 'r') as f:
            edges = []
            max_node = 0
            for line in f:
                if not line.strip() or line.startswith('#'):
                    continue
                u, v = map(int, line.strip().split())
                edges.append((u, v))
                max_node = max(max_node, u, v)

            self.graph = ig.Graph(max_node + 1)
            self.graph.add_edges(edges)

    def get_edge_count(self) -> int:
        return self.graph.ecount()

    @property
    def n(self) -> int:
        return self.graph.vcount()

    @property
    def m(self) -> int:
        return self.graph.ecount()
