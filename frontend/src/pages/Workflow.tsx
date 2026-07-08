import React from 'react';
import { Link } from 'react-router-dom';
import { PageHeader, PresenterNotes } from '../components/ui';

const STAGES = [
  { n: '01', t: 'Apply edge updates', d: 'Insert/delete the batch edges; update the incremental Significance counters immediately.' },
  { n: '02', t: 'Build affected set', d: 'Endpoints of changed edges, expanded by 1 hop (or adaptively up to R_max hops).' },
  { n: '03', t: 'Local moves', d: 'Re-optimize communities inside the affected set under Significance, best of several orderings.' },
  { n: '04', t: 'Connectivity repair', d: 'Split any community that became internally disconnected.' },
  { n: '05', t: 'Periodic recompute', d: 'Every K batches, compare against a full recomputation and adopt it if drift is too large.' },
  { n: '06', t: 'Record metrics', d: 'Significance, community count, nodes moved, affected size, time — outside the timed region.' },
];

const Workflow: React.FC = () => (
  <div>
    <PageHeader
      eyebrow="Algorithm Workflow"
      title="One batch, six stages"
      lead="Every batch of updates flows through the same pipeline. This is exactly what the Graph
        Viewer animates and what the experiment runner times."
    />

    <div className="card">
      <div className="pipeline" style={{ flexDirection: 'column', gap: 0 }}>
        {STAGES.map((s, i) => (
          <React.Fragment key={s.n}>
            <div className="row" style={{ alignItems: 'flex-start', gap: 16, padding: '12px 4px' }}>
              <div style={{
                minWidth: 40, height: 40, borderRadius: 10, display: 'grid', placeItems: 'center',
                background: 'var(--accent-soft)', color: 'var(--accent)', fontWeight: 800,
              }}>{s.n}</div>
              <div>
                <div style={{ fontWeight: 650 }}>{s.t}</div>
                <div className="muted" style={{ fontSize: '0.9rem' }}>{s.d}</div>
              </div>
            </div>
            {i < STAGES.length - 1 && <div style={{ height: 1, background: 'var(--surface-border)', marginLeft: 56 }} />}
          </React.Fragment>
        ))}
      </div>
    </div>

    <h2>Two variants</h2>
    <div className="grid grid-2">
      <div className="card">
        <h3 style={{ marginTop: 0 }}>ISL-1hop</h3>
        <p>Affected set = changed endpoints + their immediate neighbors. Simple, fast, predictable region size.</p>
      </div>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>ISL-adaptive</h3>
        <p>Expands the boundary further (up to <span className="mono">R_max</span> hops) only while boundary nodes still show meaningful Significance gain — spends effort where it pays off.</p>
      </div>
    </div>

    <h2>Key parameters</h2>
    <div className="table-scroll">
      <table className="data">
        <thead><tr><th>Parameter</th><th>Meaning</th><th>Default</th></tr></thead>
        <tbody>
          <tr><td className="mono">K</td><td>Batches between full recomputation checks</td><td>50</td></tr>
          <tr><td className="mono">delta_dwell</td><td>Stability throttle before a node may move again</td><td>2</td></tr>
          <tr><td className="mono">num_orderings</td><td>Random move orderings per batch (keep best)</td><td>3</td></tr>
          <tr><td className="mono">R_max</td><td>Max hops for adaptive affected-set expansion</td><td>3</td></tr>
          <tr><td className="mono">tau_min</td><td>Minimum Significance gain to accept a move</td><td>1e-6</td></tr>
        </tbody>
      </table>
    </div>

    <p style={{ marginTop: 20 }}>
      Now <Link to="/graph">watch these six stages play out</Link> on a real graph.
    </p>

    <PresenterNotes
      points={[
        <>Stages <b>02–03</b> are the speed story; stages <b>04–05</b> are the correctness story.</>,
        <>Metrics (stage 06) are measured <b>outside</b> the timed region, so timings reflect the algorithm only.</>,
        <>Adaptive vs. 1-hop is an <b>effort-allocation</b> choice — expand only where Significance still improves.</>,
      ]}
    />
  </div>
);

export default Workflow;
