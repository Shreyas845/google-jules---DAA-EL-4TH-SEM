import numpy as np
import igraph as ig
import leidenalg
from sklearn.metrics import normalized_mutual_info_score as nmi
import networkx as nx
import time
import json
import matplotlib.pyplot as plt

def generate_lfr(n, mu, min_community, max_community, seed):
    G_nx = nx.LFR_benchmark_graph(
        n=n, tau1=3, tau2=1.5, mu=mu, average_degree=15, max_degree=50,
        min_community=min_community, max_community=max_community, seed=seed
    )

    communities = {frozenset(G_nx.nodes[v]['community']) for v in G_nx}

    ground_truth = np.zeros(n, dtype=int)
    for idx, comm in enumerate(communities):
        for node in comm:
            ground_truth[node] = idx

    G_ig = ig.Graph(n, list(G_nx.edges()))
    return G_ig, ground_truth

def get_random_edges(G, num_edges, seed):
    np.random.seed(seed)
    n = G.vcount()
    edges_to_add = []
    while len(edges_to_add) < num_edges:
        u = np.random.randint(0, n)
        v = np.random.randint(0, n)
        if u != v and not G.are_adjacent(u, v) and (u, v) not in edges_to_add and (v, u) not in edges_to_add:
            edges_to_add.append((u, v))
    return edges_to_add

def main():
    print("Starting Validation B...")

    n = 5000
    mu = 0.3
    min_community = 20
    max_community = 200
    seeds = [42, 123, 456, 789, 1011]

    num_batches = 5
    batch_size = 50

    results = {
        'metrics': [],
        'partition_distances': []
    }

    for seed in seeds:
        print(f"Processing seed {seed}...")

        G, ground_truth = generate_lfr(n, mu, min_community, max_community, seed)

        np.random.seed(seed)
        partition_0 = leidenalg.find_partition(G, leidenalg.SurpriseVertexPartition, seed=seed)
        p_t_minus_1 = partition_0.membership
        p_cold_prev = partition_0.membership

        for t in range(num_batches):
            edges = get_random_edges(G, batch_size, seed + t * 100)
            G.add_edges(edges)

            t0 = time.perf_counter()
            p_cold = leidenalg.find_partition(G, leidenalg.SurpriseVertexPartition, seed=seed + t)
            t_cold = time.perf_counter() - t0

            t0 = time.perf_counter()
            p_warm = leidenalg.find_partition(
                G,
                leidenalg.SurpriseVertexPartition,
                initial_membership=p_t_minus_1,
                seed=seed + t
            )
            t_warm = time.perf_counter() - t0

            nmi_cold_gt = nmi(p_cold.membership, ground_truth)
            nmi_warm_gt = nmi(p_warm.membership, ground_truth)
            nmi_warm_cold = nmi(p_warm.membership, p_cold.membership)

            results['metrics'].append({
                'seed': seed,
                'batch': t + 1,
                'nmi_cold_gt': nmi_cold_gt,
                'nmi_warm_gt': nmi_warm_gt,
                'nmi_warm_cold': nmi_warm_cold,
                'time_cold': t_cold,
                'time_warm': t_warm
            })

            dist = nmi(p_cold_prev, p_cold.membership)
            results['partition_distances'].append({
                'seed': seed,
                'batch': t + 1,
                'nmi_dist': dist
            })

            p_t_minus_1 = p_warm.membership
            p_cold_prev = p_cold.membership

    with open('validations/validation_b_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    batches = range(1, num_batches + 1)

    avg_nmi_warm = [np.mean([m['nmi_warm_gt'] for m in results['metrics'] if m['batch'] == b]) for b in batches]
    std_nmi_warm = [np.std([m['nmi_warm_gt'] for m in results['metrics'] if m['batch'] == b]) for b in batches]

    avg_nmi_cold = [np.mean([m['nmi_cold_gt'] for m in results['metrics'] if m['batch'] == b]) for b in batches]
    std_nmi_cold = [np.std([m['nmi_cold_gt'] for m in results['metrics'] if m['batch'] == b]) for b in batches]

    avg_speedup = [np.mean([m['time_cold']/m['time_warm'] for m in results['metrics'] if m['batch'] == b]) for b in batches]
    std_speedup = [np.std([m['time_cold']/m['time_warm'] for m in results['metrics'] if m['batch'] == b]) for b in batches]

    plt.figure(figsize=(10, 6))
    plt.errorbar(batches, avg_nmi_warm, yerr=std_nmi_warm, label='Warm Start', marker='o')
    plt.errorbar(batches, avg_nmi_cold, yerr=std_nmi_cold, label='Cold Start', marker='x')
    plt.xlabel('Batch Number')
    plt.ylabel('NMI vs Ground Truth')
    plt.title('NMI: Warm vs Cold Start')
    plt.legend()
    plt.grid(True)
    plt.savefig('validations/validation_b_nmi_plot.png')

    plt.figure(figsize=(10, 6))
    plt.errorbar(batches, avg_speedup, yerr=std_speedup, marker='o')
    plt.axhline(y=2.0, color='r', linestyle='--', label='2x Speedup Target')
    plt.axhline(y=1.0, color='k', linestyle='-')
    plt.xlabel('Batch Number')
    plt.ylabel('Speedup (Time Cold / Time Warm)')
    plt.title('Speedup from Warm Start')
    plt.legend()
    plt.grid(True)
    plt.savefig('validations/validation_b_speedup_plot.png')

    with open('validations/validation_b_report.md', 'w') as f:
        f.write("# Validation B: Warm-Start Effectiveness\n\n")
        f.write("## Success Criteria\n")
        f.write("- NMI(P_warm) >= 0.95 * NMI(P_cold) across all batches and seeds (mean)\n")
        f.write("- Speedup >= 2x on average across batches\n\n")

        f.write("## Results\n\n")
        f.write("| Batch | NMI Warm (mean ± std) | NMI Cold (mean ± std) | Ratio | Speedup |\n")
        f.write("|-------|-----------------------|-----------------------|-------|---------|\n")

        passed_nmi = True
        overall_speedup_sum = 0

        for b in batches:
            idx = b - 1
            ratio = avg_nmi_warm[idx] / avg_nmi_cold[idx] if avg_nmi_cold[idx] > 0 else 0
            f.write(f"| {b} | {avg_nmi_warm[idx]:.4f} ± {std_nmi_warm[idx]:.4f} | {avg_nmi_cold[idx]:.4f} ± {std_nmi_cold[idx]:.4f} | {ratio:.4f} | {avg_speedup[idx]:.2f}x |\n")

            if ratio < 0.95:
                passed_nmi = False
            overall_speedup_sum += avg_speedup[idx]

        overall_speedup = overall_speedup_sum / num_batches
        passed_speedup = overall_speedup >= 2.0

        f.write(f"\nOverall average speedup: {overall_speedup:.2f}x\n\n")

        f.write("## Verdict\n")
        if passed_nmi and passed_speedup:
            f.write("**PASS**\n")
            print("Validation B: PASS")
        else:
            f.write("**FAIL**\n")
            print("Validation B: FAIL")
            if not passed_nmi:
                print("Failed: NMI ratio < 0.95")
            if not passed_speedup:
                print("Failed: Speedup < 2.0")

if __name__ == "__main__":
    main()
