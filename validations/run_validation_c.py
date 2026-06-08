import numpy as np
import igraph as ig
import leidenalg
from sklearn.metrics import normalized_mutual_info_score as nmi
import networkx as nx
import json
import matplotlib.pyplot as plt

def generate_lfr(n, mu, min_community, max_community, seed, max_degree=None, tau1=3, tau2=1.5, average_degree=15):
    try:
        kwargs = {
            'n': n,
            'tau1': tau1,
            'tau2': tau2,
            'mu': mu,
            'average_degree': average_degree,
            'min_community': min_community,
            'max_community': max_community,
            'seed': seed,
            'max_iters': 1000
        }
        if max_degree is not None:
            kwargs['max_degree'] = max_degree

        G_nx = nx.LFR_benchmark_graph(**kwargs)

        communities = {frozenset(G_nx.nodes[v]['community']) for v in G_nx}
        ground_truth = np.zeros(n, dtype=int)
        for idx, comm in enumerate(communities):
            for node in comm:
                ground_truth[node] = idx

        G_ig = ig.Graph(n, list(G_nx.edges()))
        return G_ig, ground_truth, len(communities)
    except Exception as e:
        print(f"LFR generation failed: {e}")
        return None, None, None

def run_c1_c2():
    n = 5000
    mus = [0.1, 0.2, 0.3, 0.4]
    min_community = 20
    max_community = 200
    seeds = range(42, 42 + 10)

    results = []

    for mu in mus:
        print(f"Running C1/C2 for mu = {mu}...")
        for seed in seeds:
            # We relax max_degree here as learned from Validation A
            # to ensure LFR generation doesn't fail frequently.
            G, ground_truth, k_true = generate_lfr(
                n, mu, min_community, max_community, seed,
                max_degree=50, average_degree=15
            )

            if G is None:
                continue

            np.random.seed(seed)
            p_significance = leidenalg.find_partition(G, leidenalg.SignificanceVertexPartition, seed=seed)
            k_surprise = len(set(p_significance.membership))
            nmi_significance = nmi(p_significance.membership, ground_truth)

            np.random.seed(seed)
            p_modularity = leidenalg.find_partition(G, leidenalg.ModularityVertexPartition, seed=seed)
            k_modularity = len(set(p_modularity.membership))
            nmi_modularity = nmi(p_modularity.membership, ground_truth)

            results.append({
                'experiment': 'C1_C2',
                'mu': mu,
                'seed': seed,
                'k_true': k_true,
                'k_surprise': k_surprise,
                'k_modularity': k_modularity,
                'nmi_significance': nmi_significance,
                'nmi_modularity': nmi_modularity
            })

    return results

def run_c3():
    n = 10000
    mus = [0.1, 0.3]
    min_community = 500
    max_community = 2000
    seeds = range(42, 42 + 5)

    results = []

    for mu in mus:
        print(f"Running C3 for mu = {mu}...")
        for seed in seeds:
            # For C3, to avoid "Could not create power law sequence",
            # we need parameters that make sense for large communities
            # Or we can use the generic networkx SBM if LFR fails.
            # But the blueprint strictly asks for LFR.
            # Let's try to generate it with more relaxed parameters.
            G, ground_truth, k_true = generate_lfr(
                n, mu, min_community, max_community, seed,
                tau1=3, tau2=2, average_degree=50, max_degree=250
            )

            if G is None:
                print(f"C3 LFR failed for mu={mu}, seed={seed}")
                continue

            np.random.seed(seed)
            p_significance = leidenalg.find_partition(G, leidenalg.SignificanceVertexPartition, seed=seed)
            k_surprise = len(set(p_significance.membership))

            np.random.seed(seed)
            p_modularity = leidenalg.find_partition(G, leidenalg.ModularityVertexPartition, seed=seed)
            k_modularity = len(set(p_modularity.membership))

            results.append({
                'experiment': 'C3',
                'mu': mu,
                'seed': seed,
                'k_true': k_true,
                'k_surprise': k_surprise,
                'k_modularity': k_modularity
            })

    return results

def main():
    print("Starting Validation C...")

    results = []
    results.extend(run_c1_c2())
    results.extend(run_c3())

    with open('validations/validation_c_significance_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    c1c2_results = [r for r in results if r['experiment'] == 'C1_C2']
    mus = sorted(list(set([r['mu'] for r in c1c2_results])))

    significance_ratios_mean = []
    significance_ratios_std = []
    modularity_ratios_mean = []
    modularity_ratios_std = []

    significance_nmi_mean = []
    significance_nmi_std = []
    modularity_nmi_mean = []
    modularity_nmi_std = []

    true_counts = []

    for mu in mus:
        rs = [r for r in c1c2_results if r['mu'] == mu]
        if not rs:
            continue

        s_ratios = [r['k_surprise']/r['k_true'] for r in rs]
        m_ratios = [r['k_modularity']/r['k_true'] for r in rs]

        s_nmis = [r['nmi_significance'] for r in rs]
        m_nmis = [r['nmi_modularity'] for r in rs]

        significance_ratios_mean.append(np.mean(s_ratios))
        significance_ratios_std.append(np.std(s_ratios))

        modularity_ratios_mean.append(np.mean(m_ratios))
        modularity_ratios_std.append(np.std(m_ratios))

        significance_nmi_mean.append(np.mean(s_nmis))
        significance_nmi_std.append(np.std(s_nmis))

        modularity_nmi_mean.append(np.mean(m_nmis))
        modularity_nmi_std.append(np.std(m_nmis))

        true_counts.append(np.mean([r['k_true'] for r in rs]))

    plt.figure(figsize=(10, 6))

    k_s_mean = [r * t for r, t in zip(significance_ratios_mean, true_counts)]
    k_m_mean = [r * t for r, t in zip(modularity_ratios_mean, true_counts)]

    plt.plot(mus, true_counts, 'k--', label='Ground Truth')
    plt.plot(mus, k_s_mean, 'b-o', label='Significance')
    plt.plot(mus, k_m_mean, 'r-x', label='Modularity')

    plt.xlabel('Mixing Parameter (mu)')
    plt.ylabel('Community Count')
    plt.title('Community Count vs Mu')
    plt.legend()
    plt.grid(True)
    plt.savefig('validations/validation_c_significance_community_count_plot.png')

    plt.figure(figsize=(10, 6))
    plt.errorbar(mus, significance_nmi_mean, yerr=significance_nmi_std, label='Significance', marker='o')
    plt.errorbar(mus, modularity_nmi_mean, yerr=modularity_nmi_std, label='Modularity', marker='x')

    plt.xlabel('Mixing Parameter (mu)')
    plt.ylabel('NMI vs Ground Truth')
    plt.title('NMI vs Mu')
    plt.legend()
    plt.grid(True)
    plt.savefig('validations/validation_c_significance_nmi_plot.png')

    with open('validations/validation_c_significance_report.md', 'w') as f:
        f.write("# Validation C: Over-Partitioning Bias Magnitude\n\n")

        f.write("## Success Criteria\n")
        f.write("- K_significance / K_true <= 2.0 for mu <= 0.3\n")
        f.write("- NMI(Significance, ground_truth) >= 0.85 for mu <= 0.3\n\n")

        f.write("## Failure Criteria\n")
        f.write("- K_significance / K_true > 3.0 for mu <= 0.3\n")
        f.write("- NMI(Significance, ground_truth) < 0.70 for mu <= 0.3\n\n")

        f.write("## Results (Experiment C1/C2)\n\n")
        f.write("| Mu | K_signif/K_true (mean±std) | K_mod/K_true (mean±std) | NMI Signif (mean±std) | NMI Mod (mean±std) |\n")
        f.write("|----|--------------------------|-------------------------|---------------------|--------------------|\n")

        passed = True
        failed = False

        for i, mu in enumerate(mus):
            f.write(f"| {mu:.1f} | {significance_ratios_mean[i]:.2f} ± {significance_ratios_std[i]:.2f} | ")
            f.write(f"{modularity_ratios_mean[i]:.2f} ± {modularity_ratios_std[i]:.2f} | ")
            f.write(f"{significance_nmi_mean[i]:.4f} ± {significance_nmi_std[i]:.4f} | ")
            f.write(f"{modularity_nmi_mean[i]:.4f} ± {modularity_nmi_std[i]:.4f} |\n")

            if mu <= 0.3:
                if significance_ratios_mean[i] > 2.0: passed = False
                if significance_nmi_mean[i] < 0.85: passed = False

                if significance_ratios_mean[i] > 3.0: failed = True
                if significance_nmi_mean[i] < 0.70: failed = True

        f.write("\n## Adverse Case Results (Experiment C3)\n\n")
        c3_results = [r for r in results if r['experiment'] == 'C3']
        if not c3_results:
            f.write("C3 experiments failed to generate LFR graphs.\n")
        else:
            c3_mus = sorted(list(set([r['mu'] for r in c3_results])))
            f.write("| Mu | K_signif/K_true (mean) | K_mod/K_true (mean) |\n")
            f.write("|----|----------------------|---------------------|\n")
            for mu in c3_mus:
                rs = [r for r in c3_results if r['mu'] == mu]
                s_ratio = np.mean([r['k_surprise']/r['k_true'] for r in rs])
                m_ratio = np.mean([r['k_modularity']/r['k_true'] for r in rs])
                f.write(f"| {mu:.1f} | {s_ratio:.2f} | {m_ratio:.2f} |\n")

        f.write("\n## Verdict\n")
        if failed:
            f.write("**FAIL**\n")
            print("Validation C: FAIL")
        elif passed:
            f.write("**PASS**\n")
            print("Validation C: PASS")
        else:
            f.write("**WARNING (Did not meet success criteria, but did not hit failure criteria)**\n")
            print("Validation C: WARNING")

if __name__ == "__main__":
    main()
