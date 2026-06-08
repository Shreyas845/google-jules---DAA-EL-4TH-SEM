import math
import numpy as np
import scipy.special
import matplotlib.pyplot as plt
import networkx as nx
from networkx.generators.community import LFR_benchmark_graph
import json
import traceback

def compute_exact_surprise(n, m, p, M):
    """
    S_exact(P) = − ln[ C(M, p) · C(N−M, m−p) / C(N, m) ]
    Uses log-space to avoid overflow.
    """
    N = n * (n - 1) // 2
    if p > M or m - p > N - M or m > N or p < 0 or M < 0 or N < 0 or m < 0:
        return float('nan') # Invalid input

    try:
        # log C(n, k) = log Gamma(n+1) - log Gamma(k+1) - log Gamma(n-k+1)
        def log_comb(n, k):
            return scipy.special.gammaln(n + 1) - scipy.special.gammaln(k + 1) - scipy.special.gammaln(n - k + 1)

        log_num = log_comb(M, p) + log_comb(N - M, m - p)
        log_den = log_comb(N, m)
        return -(log_num - log_den)
    except Exception as e:
        return float('nan')


def kl_divergence(x, y):
    """
    D_KL(x || y) = x*ln(x/y) + (1-x)*ln((1-x)/(1-y))
    """
    if x == 0 and y == 0:
        return 0.0
    if x == 1 and y == 1:
        return 0.0
    if x == 0:
        return (1 - x) * math.log((1 - x) / (1 - y))
    if x == 1:
        return x * math.log(x / y)
    if y == 0 or y == 1:
        return float('inf') # KL divergence goes to infinity

    return x * math.log(x / y) + (1 - x) * math.log((1 - x) / (1 - y))


def compute_asymptotic_surprise(n, m, p, M):
    """
    S_asymptotic(P) = m · D_KL(p/m || M/N)
    """
    N = n * (n - 1) // 2
    if m == 0 or N == 0:
        return 0.0

    q = p / m
    q_hat = M / N

    # Check boundaries
    if q < 0 or q > 1 or q_hat < 0 or q_hat > 1:
        return float('nan')

    return m * kl_divergence(q, q_hat)

def get_graph_stats(G, partition):
    """
    Given graph G and a partition (list of sets of nodes),
    returns n, m, p, M
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()

    p = 0
    M = 0
    for comm in partition:
        n_c = len(comm)
        M += n_c * (n_c - 1) // 2

        subgraph = G.subgraph(comm)
        p += subgraph.number_of_edges()

    return n, m, p, M


def main():
    community_sizes = [20, 50, 100, 200, 500]
    seeds = [42, 123, 456, 789, 1011]

    n_nodes = 5000
    average_degree = 15

    results = {
        'A1': {}, # Ground truth
        'A2': {}, # Random
        'A3': {}  # Ordering consistency
    }

    # Store errors for plotting
    mean_errors_a1 = []
    max_errors_a1 = []
    ordering_consistencies = []

    print("Starting Validation A...")

    for size in community_sizes:
        print(f"Processing community size {size}...")
        results['A1'][size] = []
        results['A2'][size] = []
        results['A3'][size] = []

        size_errors_a1 = []
        consistent_count = 0
        total_pairs = 0

        for seed in seeds:
            # 1. Generate LFR graph
            try:
                # networkx LFR generator uses tau1 for degree distribution, tau2 for community sizes.
                # typical values: tau1=3, tau2=1.5
                G = LFR_benchmark_graph(
                    n=n_nodes,
                    tau1=3,
                    tau2=1.5,
                    mu=0.1, # Not strictly defined in A1, but needed for generator
                    average_degree=min(15, size // 2), max_degree=min(50, int(size * 0.9)),
                    min_community=size,
                    max_community=size, # Fixed size for this test
                    seed=seed
                )

                # Extract ground truth partition
                ground_truth = {frozenset(G.nodes[v]['community']) for v in G}

                # --- Experiment A1 ---
                n, m, p, M = get_graph_stats(G, ground_truth)

                s_exact = compute_exact_surprise(n, m, p, M)
                s_asymp = compute_asymptotic_surprise(n, m, p, M)

                if math.isnan(s_exact) or math.isnan(s_asymp) or s_exact == 0:
                    rel_error = float('nan')
                else:
                    rel_error = abs(s_exact - s_asymp) / abs(s_exact)

                results['A1'][size].append({
                    'seed': seed,
                    's_exact': s_exact,
                    's_asymp': s_asymp,
                    'rel_error': rel_error
                })

                if not math.isnan(rel_error):
                    size_errors_a1.append(rel_error)

                # --- Experiment A2 ---
                k = len(ground_truth)
                nodes = list(G.nodes())

                for i in range(10):
                    # random assignment to k communities
                    np.random.seed(seed + i)
                    assignments = np.random.randint(0, k, size=n_nodes)
                    random_partition = [set() for _ in range(k)]
                    for idx, c in enumerate(assignments):
                        random_partition[c].add(nodes[idx])

                    n, m, p, M = get_graph_stats(G, random_partition)

                    s_exact_rand = compute_exact_surprise(n, m, p, M)
                    s_asymp_rand = compute_asymptotic_surprise(n, m, p, M)

                    if math.isnan(s_exact_rand) or math.isnan(s_asymp_rand) or s_exact_rand == 0:
                        rel_error_rand = float('nan')
                    else:
                        rel_error_rand = abs(s_exact_rand - s_asymp_rand) / abs(s_exact_rand)

                    results['A2'][size].append({
                        'seed': seed,
                        'i': i,
                        's_exact': s_exact_rand,
                        's_asymp': s_asymp_rand,
                        'rel_error': rel_error_rand
                    })

                # --- Experiment A3 ---
                for i in range(20):
                    np.random.seed(seed + i * 100)
                    a1 = np.random.randint(0, k, size=n_nodes)
                    a2 = np.random.randint(0, k, size=n_nodes)

                    p1 = [set() for _ in range(k)]
                    p2 = [set() for _ in range(k)]

                    for idx, c in enumerate(a1): p1[c].add(nodes[idx])
                    for idx, c in enumerate(a2): p2[c].add(nodes[idx])

                    n, m, p_1, M_1 = get_graph_stats(G, p1)
                    s_exact_1 = compute_exact_surprise(n, m, p_1, M_1)
                    s_asymp_1 = compute_asymptotic_surprise(n, m, p_1, M_1)

                    n, m, p_2, M_2 = get_graph_stats(G, p2)
                    s_exact_2 = compute_exact_surprise(n, m, p_2, M_2)
                    s_asymp_2 = compute_asymptotic_surprise(n, m, p_2, M_2)

                    if not math.isnan(s_exact_1) and not math.isnan(s_exact_2) and not math.isnan(s_asymp_1) and not math.isnan(s_asymp_2):
                        exact_order = s_exact_1 > s_exact_2
                        asymp_order = s_asymp_1 > s_asymp_2
                        consistent = (exact_order == asymp_order)

                        consistent_count += int(consistent)
                        total_pairs += 1

            except nx.NetworkXError as e:
                print(f"LFR generation failed for size {size}, seed {seed}: {e}")

        # Calculate summary metrics for this size
        mean_err = np.mean(size_errors_a1) if size_errors_a1 else float('nan')
        max_err = np.max(size_errors_a1) if size_errors_a1 else float('nan')
        consistency_rate = consistent_count / total_pairs if total_pairs > 0 else float('nan')

        mean_errors_a1.append(mean_err)
        max_errors_a1.append(max_err)
        ordering_consistencies.append(consistency_rate)

        results['summary'] = results.get('summary', {})
        results['summary'][size] = {
            'mean_rel_error_a1': mean_err,
            'max_rel_error_a1': max_err,
            'ordering_consistency': consistency_rate
        }

    # Save JSON results
    with open('validations/validation_a_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(community_sizes, [e * 100 for e in mean_errors_a1], 'b-o', label='Mean Relative Error (%)')
    plt.plot(community_sizes, [e * 100 for e in max_errors_a1], 'r-s', label='Max Relative Error (%)')
    plt.axhline(y=5, color='gray', linestyle='--', label='5% Threshold')
    plt.axhline(y=2, color='gray', linestyle=':', label='2% Threshold')

    plt.xlabel('Minimum Community Size')
    plt.ylabel('Relative Error (%)')
    plt.title('Asymptotic Approximation Error vs Community Size')
    plt.legend()
    plt.grid(True)
    plt.savefig('validations/validation_a_plot.png')

    # Generate Report
    with open('validations/validation_a_report.md', 'w') as f:
        f.write("# Validation A: Asymptotic Approximation Accuracy\n\n")

        f.write("## Success Criteria\n")
        f.write("- Relative error < 5% for communities >= 50 nodes\n")
        f.write("- Relative error < 2% for communities >= 100 nodes\n")
        f.write("- Ordering consistency >= 95% for all community sizes >= 50\n\n")

        f.write("## Failure Criteria\n")
        f.write("- Relative error >= 10% for communities >= 100 nodes\n")
        f.write("- Ordering consistency < 90% for communities >= 100 nodes\n")
        f.write("- Numerical instability (NaN, Inf) in exact Surprise for any test case\n\n")

        f.write("## Results\n\n")
        f.write("| Community Size | Mean Rel Err | Max Rel Err | Ordering Consistency |\n")
        f.write("|----------------|--------------|-------------|----------------------|\n")

        passed_all = True

        for size in community_sizes:
            mean_err = results['summary'][size]['mean_rel_error_a1']
            max_err = results['summary'][size]['max_rel_error_a1']
            consistency = results['summary'][size]['ordering_consistency']

            f.write(f"| {size} | {mean_err:.4%} | {max_err:.4%} | {consistency:.4%} |\n")

            # Check criteria
            if size >= 50:
                if mean_err >= 0.05: passed_all = False
                if consistency < 0.95: passed_all = False
            if size >= 100:
                if mean_err >= 0.02: passed_all = False
                if mean_err >= 0.10:
                    print("FAILURE: Relative error >= 10% for communities >= 100 nodes")
                    passed_all = False
                if consistency < 0.90:
                    print("FAILURE: Ordering consistency < 90% for communities >= 100 nodes")
                    passed_all = False

        f.write("\n## Verdict\n")
        if passed_all:
            f.write("**PASS**\n")
            print("Validation A: PASS")
        else:
            f.write("**FAIL**\n")
            print("Validation A: FAIL")

if __name__ == "__main__":
    main()
