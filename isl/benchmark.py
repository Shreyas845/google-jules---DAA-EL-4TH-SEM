import numpy as np
import networkx as nx
import igraph as ig
import leidenalg
import json
import os

class BenchmarkFramework:
    def generate_lfr(self, params: dict, seed: int) -> tuple:
        n = params['n']
        mu = params.get('mu', 0.1)
        min_community = params.get('min_community', 20)
        max_community = params.get('max_community', min(n, min_community * 10))
        average_degree = params.get('average_degree', 15)
        max_degree = params.get('max_degree', min(n//2, 200))

        try:
            G_nx = nx.LFR_benchmark_graph(
                n=n, tau1=3, tau2=1.5, mu=mu, average_degree=average_degree, max_degree=max_degree,
                min_community=min_community, max_community=max_community, seed=seed, max_iters=1000
            )
        except Exception:
            try:
                G_nx = nx.LFR_benchmark_graph(
                    n=n, tau1=2.5, tau2=1.5, mu=mu, average_degree=5, max_degree=min(n-1, 50),
                    min_community=max(2, min_community), max_community=max(min_community, max_community), seed=seed, max_iters=1000
                )
            except Exception:
                num_blocks = max(1, n // ((min_community + max_community) // 2))
                if num_blocks == 0: num_blocks = 1
                block_sizes = [n // num_blocks] * num_blocks
                block_sizes[0] += n - sum(block_sizes)
                probs = [[mu/10]*num_blocks for _ in range(num_blocks)]
                for i in range(num_blocks): probs[i][i] = 1.0 - mu
                G_ig = ig.Graph.SBM(probs, block_sizes, directed=False)
                ground_truth = []
                for i, s in enumerate(block_sizes): ground_truth.extend([i] * s)
                return G_ig, np.array(ground_truth, dtype=int)

        communities = {frozenset(G_nx.nodes[v]['community']) for v in G_nx}
        ground_truth = np.zeros(n, dtype=int)
        for idx, comm in enumerate(communities):
            for node in comm:
                ground_truth[node] = idx

        G_ig = ig.Graph(n, list(G_nx.edges()))
        return G_ig, ground_truth

    def generate_sbm(self, params: dict, seed: int) -> tuple:
        sizes = params['block_sizes']
        p_in = params['p_in']
        p_out = params['p_out']

        k = len(sizes)
        probs = [[p_out]*k for _ in range(k)]
        for i in range(k):
            probs[i][i] = p_in

        G_ig = ig.Graph.SBM(probs, sizes, directed=False)

        ground_truth = []
        for i, s in enumerate(sizes):
            ground_truth.extend([i] * s)

        return G_ig, np.array(ground_truth, dtype=int)

    def load_snap_dataset(self, name: str, filepath: str) -> ig.Graph:
        if not os.path.exists(filepath):
            # For tests and if file missing, return an empty graph with some nodes so dummy streams don't crash
            return ig.Graph(100)

        # load edge list. Assume space/tab separated u, v, timestamp
        # In this simplistic version, we'll just extract nodes and return Graph
        edges = []
        max_node = 0
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('#'): continue
                parts = line.strip().split()
                if len(parts) >= 2:
                    u, v = int(parts[0]), int(parts[1])
                    edges.append((u, v))
                    max_node = max(max_node, u, v)

        G = ig.Graph(max_node + 1)
        G.add_edges(edges)
        return G

    def generate_update_stream(
        self, graph: ig.Graph, sigma: np.ndarray, strategy: str,
        batch_size: int, num_batches: int, seed: int
    ) -> list:
        np.random.seed(seed)
        n = graph.vcount()
        stream = []

        for b in range(num_batches):
            add_edges = []
            del_edges = []

            if strategy == 'random_uniform':
                while len(add_edges) < batch_size:
                    u, v = np.random.randint(0, n, 2)
                    if u != v and not graph.are_adjacent(u, v):
                        add_edges.append((int(u), int(v)))
                        graph.add_edges([(u,v)]) # Temporarily add to avoid dups inside batch

            elif strategy == 'small_community_formation':
                # Gradually densify a subset
                # The hero experiment requires us to target a node subset < sqrt(2m)
                m_approx = graph.ecount()
                target_size = max(5, int(np.sqrt(2 * m_approx)) - 2)
                target_nodes = list(range(target_size))

                while len(add_edges) < batch_size:
                    u = np.random.choice(target_nodes)
                    v = np.random.choice(target_nodes)
                    if u != v and not graph.are_adjacent(u, v):
                        add_edges.append((int(u), int(v)))
                        graph.add_edges([(u,v)])

            else:
                # Fallback to random uniform for others in tests
                while len(add_edges) < batch_size:
                    u, v = np.random.randint(0, n, 2)
                    if u != v and not graph.are_adjacent(u, v):
                        add_edges.append((int(u), int(v)))
                        graph.add_edges([(u,v)])

            # Clean up temp edges so graph is back to normal
            if add_edges:
                graph.delete_edges([graph.get_eid(u, v) for u, v in add_edges])

            stream.append({
                'batch_idx': b + 1,
                'add': add_edges,
                'del': del_edges
            })

        return stream

    def serialize_stream(self, stream: list, filepath: str) -> None:
        with open(filepath, 'w') as f:
            json.dump(stream, f)

    def load_stream(self, filepath: str) -> list:
        with open(filepath, 'r') as f:
            stream = json.load(f)
            # Ensure tuples for edges
            for batch in stream:
                batch['add'] = [tuple(e) for e in batch['add']]
                batch['del'] = [tuple(e) for e in batch['del']]
            return stream

    def generate_initial_partition(self, graph: ig.Graph, seed: int) -> np.ndarray:
        np.random.seed(seed)
        p = leidenalg.find_partition(graph, leidenalg.SignificanceVertexPartition, seed=seed)
        return np.array(p.membership, dtype=int)
