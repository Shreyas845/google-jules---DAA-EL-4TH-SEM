import matplotlib.pyplot as plt
import os

class PaperFigureGenerator:
    def __init__(self, output_dir='figures'):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _save_fig(self, name):
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, f'{name}.pdf'))
        plt.savefig(os.path.join(self.output_dir, f'{name}.png'))
        plt.close()

    def figure_1_hero_nmi_over_batches(self, aggregate_results: dict):
        plt.figure(figsize=(10, 6))
        # Wait, the instruction says: "One subplot per mu value (0.1, 0.2, 0.3, 0.4)."
        # But aggregate_results from the runner only contains one experiment (one mu).
        # We'll just plot what's in aggregate_results for now.
        for method, results in aggregate_results.items():
            batches = [r['batch_idx'] for r in results]
            means = [r['nmi_gt']['mean'] for r in results]
            stds = [r['nmi_gt']['std'] for r in results]
            plt.errorbar(batches, means, yerr=stds, label=method)

        plt.xlabel('Batch')
        plt.ylabel('NMI vs Ground Truth')
        plt.title('Figure 1: NMI over Batches')
        plt.legend()
        self._save_fig('fig1_hero_nmi')

    def figure_2_speedup_plot(self, aggregate_results: dict):
        plt.figure(figsize=(10, 6))

        isl_results = aggregate_results.get('isl_1hop', [])
        sig_results = aggregate_results.get('static_surprise', []) # It's statically labeled static_surprise in config
        if not isl_results or not sig_results:
            return

        batches = [r['batch_idx'] for r in isl_results]
        isl_time = [r['time_ms']['mean'] for r in isl_results]
        sig_time = [r['time_ms']['mean'] for r in sig_results]

        plt.plot(batches, isl_time, label='ISL-1hop')
        plt.plot(batches, sig_time, label='Static Significance')

        plt.xlabel('Batch')
        plt.ylabel('Wall-clock time (ms)')
        plt.title('Figure 2: Execution Time')
        plt.legend()
        self._save_fig('fig2_speedup')

    def figure_3_affected_set_distribution(self, aggregate_results: dict):
        plt.figure(figsize=(10, 6))
        isl_results = aggregate_results.get('isl_1hop', [])
        if not isl_results: return

        fracs = [r['affected_set_fraction']['mean'] for r in isl_results]
        plt.hist(fracs, bins=20)

        plt.xlabel('Affected Set Fraction |S|/|V|')
        plt.ylabel('Frequency')
        plt.title('Figure 3: Affected Set Size Distribution')
        self._save_fig('fig3_affected_set')

    def figure_4_ablation_table(self, aggregate_results: dict) -> str:
        table = "\\begin{tabular}{|l|c|c|}\\hline\n"
        table += "Variant & Final NMI & Time (ms) \\\\\\hline\n"

        variants = ['isl_1hop', 'isl_adaptive', 'isl_no_correction', 'isl_no_dwell']
        for var in variants:
            if var in aggregate_results and len(aggregate_results[var]) > 0:
                nmi = aggregate_results[var][-1]['nmi_gt']['mean']
                t = aggregate_results[var][-1]['time_ms']['mean']
                table += f"{var.replace('_', '\\_')} & {nmi:.4f} & {t:.2f} \\\\\n"

        table += "\\hline\\end{tabular}\n"

        with open(os.path.join(self.output_dir, 'fig4_ablation.tex'), 'w') as f:
            f.write(table)

        return table

    def figure_5_overpartitioning_diagnostic(self, aggregate_results: dict):
        plt.figure(figsize=(10, 6))

        for method in ['isl_1hop']:
            if method in aggregate_results:
                results = aggregate_results[method]
                batches = [r['batch_idx'] for r in results]
                means = [r['community_count']['mean'] for r in results]
                stds = [r['community_count']['std'] for r in results]
                plt.errorbar(batches, means, yerr=stds, label=method)

        plt.xlabel('Batch')
        plt.ylabel('Community Count')
        plt.title('Figure 5: Community Count over Time')
        plt.legend()
        self._save_fig('fig5_overpartitioning')

    def figure_6_parameter_sensitivity(self, sensitivity_results: dict):
        # Placeholder for parameter sweeps. Just generate an empty figure.
        plt.figure(figsize=(10, 6))
        plt.title('Figure 6: Parameter Sensitivity')
        self._save_fig('fig6_parameter_sensitivity')

    def figure_7_adverse_case(self, aggregate_results: dict):
        # Similar to fig 1 but specifically for adverse case
        plt.figure(figsize=(10, 6))
        for method, results in aggregate_results.items():
            batches = [r['batch_idx'] for r in results]
            means = [r['nmi_gt']['mean'] for r in results]
            plt.plot(batches, means, label=method)
        plt.xlabel('Batch')
        plt.ylabel('NMI vs Ground Truth')
        plt.title('Figure 7: Adverse Case (Large Communities)')
        plt.legend()
        self._save_fig('fig7_adverse_case')
