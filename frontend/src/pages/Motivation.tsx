import React from 'react';
import { PageHeader, ExplainPanel, PresenterNotes, Badge } from '../components/ui';

const Motivation: React.FC = () => (
  <div>
    <PageHeader
      eyebrow="Motivation"
      title="Why static Leiden is expensive — and why modularity is blind"
      lead="Two independent problems motivate ISL: the cost of recomputation, and a mathematical
        flaw in the objective that nearly every incremental method inherits."
    />

    <h2>Problem 1 — Recomputation cost</h2>
    <div className="card">
      <p style={{ marginTop: 0 }}>
        Leiden is a strong, widely-used community detection algorithm. But it is <b>static</b>:
        given an updated graph, it re-optimizes from the whole graph. In a streaming setting with
        many small batches, you pay that full cost again and again — even though a single edge
        insertion typically only perturbs a small neighborhood.
      </p>
      <div className="legend" style={{ marginTop: 12 }}>
        <span className="item"><span className="dot" style={{ background: 'var(--bad)' }} /> Static Leiden: full-graph work per batch</span>
        <span className="item"><span className="dot" style={{ background: 'var(--good)' }} /> ISL: work proportional to the affected region</span>
      </div>
    </div>

    <h2>Problem 2 — The resolution limit</h2>
    <div className="card">
      <p style={{ marginTop: 0 }}>
        Most community methods optimize <b>modularity</b>. Modularity has a proven flaw
        (Fortunato &amp; Barthélemy, 2007): the <b>resolution limit</b>. Communities smaller than
        roughly <span className="mono">√(2m)</span> nodes (where <span className="mono">m</span> is
        the edge count) become invisible — they get merged into larger blobs no matter how strong
        their internal structure is.
      </p>
      <div className="row" style={{ marginTop: 8, gap: 10 }}>
        <Badge kind="bad">Modularity → merges small communities</Badge>
        <Badge kind="ok">Significance → keeps them separate</Badge>
      </div>
    </div>

    <ExplainPanel
      items={[
        {
          q: 'What is Significance?',
          a: 'An alternative quality function (from the Leiden family) that scores a partition by how statistically surprising its internal density is — without a size-based blind spot.',
        },
        {
          q: 'Why does it matter here?',
          a: 'If the objective cannot see small communities, no incremental method built on it can either. Switching the objective fixes the blindness at the source.',
        },
        {
          q: 'What is the trade-off?',
          a: 'Significance can over-partition at high mixing (many tiny communities). Validation C examines exactly this — honestly.',
        },
      ]}
    />

    <h2>ISL's two-part answer</h2>
    <div className="pipeline">
      <div className="step">
        <div className="n">01</div>
        <div className="t">Go incremental</div>
        <div className="d">Reprocess only the affected neighborhood per batch.</div>
      </div>
      <div className="arrow">+</div>
      <div className="step">
        <div className="n">02</div>
        <div className="t">Switch the objective</div>
        <div className="d">Optimize Significance, not modularity — no resolution limit.</div>
      </div>
      <div className="arrow">=</div>
      <div className="step" style={{ borderColor: 'var(--accent)' }}>
        <div className="n" style={{ color: 'var(--good)' }}>ISL</div>
        <div className="t">Fast + multi-scale</div>
        <div className="d">Cheap updates that still see small communities.</div>
      </div>
    </div>

    <PresenterNotes
      points={[
        <>Two problems, two fixes: <b>incremental</b> solves cost; <b>Significance</b> solves blindness.</>,
        <>The resolution limit is a <b>proven</b> property of modularity — √(2m) is the key threshold to name.</>,
        <>Be honest: Significance's failure mode is <b>over-partitioning</b>; we test it directly in Validation C.</>,
      ]}
    />
  </div>
);

export default Motivation;
