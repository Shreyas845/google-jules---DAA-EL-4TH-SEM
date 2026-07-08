import React from 'react';
import { PageHeader, PresenterNotes } from '../components/ui';

const LAYERS = [
  { t: 'React Dashboard', d: 'This app — narrative, interactive graph, experiment control, result & validation views.', tech: 'React · TypeScript · Recharts' },
  { t: 'FastAPI Backend', d: 'Thin API layer: serves artifacts, launches experiments as background jobs, generates live ISL traces.', tech: 'FastAPI · Uvicorn' },
  { t: 'Experiment Runner', d: 'Orchestrates multi-seed runs across ISL variants and baselines; aggregates and writes results.', tech: 'isl/experiment_runner.py' },
  { t: 'ISL Library', d: 'The algorithm: community state, affected set, local moves, connectivity, periodic recompute.', tech: 'isl/*.py · igraph · leidenalg' },
  { t: 'Evaluation & Benchmark', d: 'NMI/ARI/Significance/modularity metrics, LFR/SBM graph generation, update streams.', tech: 'isl/evaluation.py · isl/benchmark.py' },
  { t: 'Stored Results & Artifacts', d: 'Aggregated experiment JSON and committed validation results + plots.', tech: 'results/ · validations/' },
];

const Architecture: React.FC = () => (
  <div>
    <PageHeader
      eyebrow="Architecture"
      title="A thin API over a real research library"
      lead="The dashboard never re-implements the science. Every number it shows comes from the same
        ISL library the experiments use — the backend just exposes it over HTTP."
    />

    <h2>Layered flow</h2>
    <div className="card">
      {LAYERS.map((l, i) => (
        <div key={l.t}>
          <div className="row between" style={{ alignItems: 'flex-start', padding: '14px 4px' }}>
            <div style={{ maxWidth: '70%' }}>
              <div style={{ fontWeight: 650 }}>{l.t}</div>
              <div className="muted" style={{ fontSize: '0.9rem' }}>{l.d}</div>
            </div>
            <span className="badge neutral mono" style={{ fontSize: '0.72rem' }}>{l.tech}</span>
          </div>
          {i < LAYERS.length - 1 && (
            <div className="center faint" style={{ fontSize: '1.1rem', lineHeight: 0.6 }}>↓</div>
          )}
        </div>
      ))}
    </div>

    <h2>Request paths</h2>
    <div className="grid grid-2">
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Read-only artifacts</h3>
        <p className="mono" style={{ fontSize: '0.82rem' }}>
          GET /api/validations<br />GET /api/results/&#123;name&#125;<br />GET /api/images/&#123;name&#125;
        </p>
        <p>Serve committed validation JSON/plots and stored experiment aggregates directly.</p>
      </div>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Live computation</h3>
        <p className="mono" style={{ fontSize: '0.82rem' }}>
          POST /api/experiment/run<br />GET /api/experiment/status/&#123;id&#125;<br />GET /api/graph/trace
        </p>
        <p>Launch the real runner as a background job (poll for progress); generate a real step-by-step ISL trace on request.</p>
      </div>
    </div>

    <h2>Design choices</h2>
    <div className="explain">
      <div className="box"><div className="q">Polling, not WebSockets</div><p>Experiment jobs report progress via a simple status endpoint. Fewer moving parts, easy to reason about, sufficient here.</p></div>
      <div className="box"><div className="q">Library untouched</div><p>The backend imports the ISL modules; it does not fork or reimplement them. One source of truth for the science.</p></div>
      <div className="box"><div className="q">Real traces</div><p>The Graph Viewer runs the actual algorithm on a small graph — positions, communities and metrics are all genuine.</p></div>
    </div>

    <PresenterNotes
      points={[
        <>Key message: the dashboard is a <b>window</b> onto the real library, not a separate re-implementation.</>,
        <>Two request classes: <b>read stored artifacts</b> vs. <b>run live computation</b> (jobs + traces).</>,
        <>Polling was a deliberate simplicity choice over WebSockets — call that out as good engineering judgment.</>,
      ]}
    />
  </div>
);

export default Architecture;
