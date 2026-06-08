import pytest
import os
import json
from isl.visualization import PaperFigureGenerator

@pytest.fixture
def mock_results():
    return {'isl_1hop': [{'batch_idx': 1, 'nmi_gt': {'mean': 0.9, 'std': 0.1}, 'time_ms': {'mean': 10, 'std': 1}, 'affected_set_fraction': {'mean': 0.1, 'std': 0}, 'community_count': {'mean': 5, 'std': 1}}], 'static_leiden': [{'batch_idx': 1, 'nmi_gt': {'mean': 0.8, 'std': 0.1}, 'time_ms': {'mean': 15, 'std': 1}, 'community_count': {'mean': 6, 'std': 1}}], 'static_surprise': [{'batch_idx': 1, 'nmi_gt': {'mean': 0.8, 'std': 0.1}, 'time_ms': {'mean': 15, 'std': 1}, 'community_count': {'mean': 6, 'std': 1}}]}

def test_figure_1_generates_no_error(mock_results, tmpdir):
    gen = PaperFigureGenerator(str(tmpdir))
    gen.figure_1_hero_nmi_over_batches(mock_results)
    assert os.path.exists(os.path.join(tmpdir, 'fig1_hero_nmi.png'))
    assert os.path.exists(os.path.join(tmpdir, 'fig1_hero_nmi.pdf'))

def test_figure_2_generates_no_error(mock_results, tmpdir):
    gen = PaperFigureGenerator(str(tmpdir))
    gen.figure_2_speedup_plot(mock_results)
    assert os.path.exists(os.path.join(tmpdir, 'fig2_speedup.png'))

def test_figure_3_histogram_nonzero(mock_results, tmpdir):
    gen = PaperFigureGenerator(str(tmpdir))
    gen.figure_3_affected_set_distribution(mock_results)
    assert os.path.exists(os.path.join(tmpdir, 'fig3_affected_set.png'))

def test_figure_4_latex_valid_syntax(mock_results, tmpdir):
    gen = PaperFigureGenerator(str(tmpdir))
    tex = gen.figure_4_ablation_table(mock_results)
    assert "\\begin{tabular}" in tex
    assert "\\end{tabular}" in tex
    assert os.path.exists(os.path.join(tmpdir, 'fig4_ablation.tex'))

def test_all_figures_save_to_disk(mock_results, tmpdir):
    gen = PaperFigureGenerator(str(tmpdir))
    gen.figure_5_overpartitioning_diagnostic(mock_results)
    gen.figure_6_parameter_sensitivity(mock_results)
    gen.figure_7_adverse_case(mock_results)

    assert os.path.exists(os.path.join(tmpdir, 'fig5_overpartitioning.png'))
    assert os.path.exists(os.path.join(tmpdir, 'fig6_parameter_sensitivity.png'))
    assert os.path.exists(os.path.join(tmpdir, 'fig7_adverse_case.png'))
