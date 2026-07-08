import React from 'react';
import { PageHeader, PresenterNotes, Badge } from '../components/ui';

const ITEMS = [
  { t: 'Edge deletions in streams', s: 'scoped', d: 'The stream generator currently emits insertions only. Adding deletion streams would exercise the full update path end-to-end.' },
  { t: 'Real-world datasets (SNAP)', s: 'scoped', d: 'The SNAP loader is simplistic (ignores timestamps). Wiring temporal real-world graphs would broaden the evidence beyond synthetic LFR/SBM.' },
  { t: 'Larger graphs', s: 'known limit', d: 'The Python prototype targets n ≲ 10⁵. Scaling to millions of nodes is an engineering effort (native core, parallelism), deliberately out of scope here.' },
  { t: 'Over-partitioning control', s: 'research', d: 'Significance can over-split at high mixing (see Validation C). A merge post-process or regularizer is a natural extension.' },
  { t: 'Adaptive K', s: 'research', d: 'The periodic-recompute interval K is fixed. Triggering recomputation from an online drift estimate could tighten the accuracy/cost trade-off.' },
];

const badgeKind = (s: string) => (s === 'scoped' ? 'accent' : s === 'research' ? 'warn' : 'neutral');

const Future: React.FC = () => (
  <div>
    <PageHeader
      eyebrow="Future Scope"
      title="Honest next steps"
      lead="What this project deliberately did not do, and where it would go next. Scope was chosen
        for a complete, defensible prototype — not maximum surface area."
    />

    <div className="card">
      {ITEMS.map((it, i) => (
        <div key={it.t}>
          <div className="row between" style={{ alignItems: 'flex-start', padding: '14px 4px' }}>
            <div style={{ maxWidth: '78%' }}>
              <div style={{ fontWeight: 650 }}>{it.t}</div>
              <div className="muted" style={{ fontSize: '0.9rem' }}>{it.d}</div>
            </div>
            <Badge kind={badgeKind(it.s) as any}>{it.s}</Badge>
          </div>
          {i < ITEMS.length - 1 && <div style={{ height: 1, background: 'var(--surface-border)' }} />}
        </div>
      ))}
    </div>

    <h2>What is already done</h2>
    <p className="muted">
      The algorithm, experiment/evaluation/benchmark frameworks, three validations, a test suite,
      and this end-to-end dashboard are complete and runnable. The items above are extensions, not
      gaps in the core contribution.
    </p>

    <PresenterNotes
      points={[
        <>Framing matters: these are <b>deliberate scope boundaries</b>, not unfinished work.</>,
        <>The most defensible next step is <b>edge-deletion streams + real datasets</b> — small, high-value.</>,
        <>Over-partitioning control ties directly back to <b>Validation C</b>, showing research awareness.</>,
      ]}
    />
  </div>
);

export default Future;
