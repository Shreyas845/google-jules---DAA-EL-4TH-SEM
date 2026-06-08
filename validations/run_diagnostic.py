import igraph as ig
import leidenalg
import networkx as nx

def print_stats(name, membership):
    from collections import Counter
    counts = list(Counter(membership).values())
    counts.sort(reverse=True)

    total = len(counts)
    largest = counts[0] if total > 0 else 0
    smallest = counts[-1] if total > 0 else 0
    top20 = counts[:20]

    print(f"--- Statistics for {name} ---")
    print(f"Total number of communities: {total}")
    print(f"Size of largest community: {largest}")
    print(f"Size of smallest community: {smallest}")
    print(f"First 20 community sizes (sorted descending): {top20}")
    print()

with open('validations/validation_c_diagnostic.txt', 'w') as f:
    import sys
    sys.stdout = f

    print("=== Validation C Diagnostic Report ===\n")

    # Test 1: Simple two-community SBM (Petersen as proxy per user script)
    try:
        G1 = ig.Graph.Famous("Petersen")
        p1 = leidenalg.find_partition(G1, leidenalg.SurpriseVertexPartition)
        print(f"Petersen graph: {len(set(p1.membership))} communities (expected: 1-3)")
        print_stats("Petersen graph", p1.membership)
    except Exception as e:
        print(f"Test 1 failed: {e}\n")

    # Test 2: Clear two-community graph
    try:
        G2 = ig.Graph()
        G2.add_vertices(20)
        edges = [(i,j) for i in range(10) for j in range(i+1,10)] + \
                [(i,j) for i in range(10,20) for j in range(i+1,20)] + \
                [(0,10)]
        G2.add_edges(edges)
        p2 = leidenalg.find_partition(G2, leidenalg.SurpriseVertexPartition)
        print(f"Two-clique graph: {len(set(p2.membership))} communities (expected: 2)")
        print_stats("Two-clique graph", p2.membership)
    except Exception as e:
        print(f"Test 2 failed: {e}\n")

    # Test 3: Small LFR via networkx, check edge count
    try:
        G3_nx = nx.LFR_benchmark_graph(n=100, tau1=3, tau2=1.5, mu=0.1,
                                        average_degree=5, max_degree=15,
                                        min_community=10, max_community=30, seed=42)
        print(f"Small LFR: {G3_nx.number_of_nodes()} nodes, {G3_nx.number_of_edges()} edges")
        G3_ig = ig.Graph(100, list(G3_nx.edges()))
        p3 = leidenalg.find_partition(G3_ig, leidenalg.SurpriseVertexPartition)
        print(f"Small LFR Surprise: {len(set(p3.membership))} communities")
        print_stats("Small LFR Surprise", p3.membership)
    except Exception as e:
        print(f"Test 3 failed: {e}\n")
