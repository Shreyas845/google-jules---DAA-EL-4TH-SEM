import React from 'react';
import { Link } from 'react-router-dom';
import { PageHeader, PresenterNotes, ExplainPanel, Stat } from '../components/ui';

const ISLOverview: React.FC = () => (
  <div>
    <PageHeader
      eyebrow="ISL Overview"
      title="How ISL keeps communities current"
      lead="ISL maintains a running community partition. For each batch of edge updates it localizes
        the work, re-optimizes just that region under Significance, repairs any damage, and
        occasionally checks itself against a full recomputation."
    />

    <h2>The idea in one sentence</h2>
    <div className="card">
      <p style={{ marginTop: 0, fontSize: '1.05rem', color: 'var(--text)' }}>
        Treat the current partition as a <b>warm start</b>: when edges change, only the nodes near
        the change can plausibly want to move — so only re-examine those, and only occasionally
        verify nothing has quietly drifted.
      </p>
    </div>

    <h2>Four mechanisms</h2>
    <div className="grid grid-2">
      <div className="card">
        <h3 style={{ marginTop: 0 }}>1 · Affected-set localization</h3>
        <p>From the endpoints of changed edges, expand outward (1-hop, or adaptively) to the set of nodes that might re-evaluate their community. Everything else is left untouched.</p>
      </div>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>2 · Local moves under Significance</h3>
        <p>Within the affected set, greedily move nodes to the community that most improves Significance, using multiple random orderings and keeping the best result.</p>
      </div>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>3 · Connectivity repair</h3>
        <p>Local moves can leave a community internally disconnected. ISL detects and splits such communities so every community stays a connected subgraph.</p>
      </div>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>4 · Periodic recomputation</h3>
        <p>Every K batches, ISL recomputes a full partition and compares. If the incremental partition drifted too far, it adopts the fresh one — bounding accumulated error.</p>
      </div>
    </div>

    <ExplainPanel
      items={[
        { q: 'What keeps it fast?', a: 'Work scales with the affected region, not the graph. Untouched regions cost nothing.' },
        { q: 'What keeps it correct?', a: 'Connectivity repair + periodic recomputation stop small local decisions from compounding into drift.' },
        { q: 'What keeps it multi-scale?', a: 'Every move is scored by Significance, so small communities are never dissolved by design.' },
      ]}
    />

    <h2>What it maintains</h2>
    <div className="grid grid-4">
      <Stat label="σ (sigma)" value="Partition" sub="community of each node" />
      <Stat label="Counters" value="m, p, M, N" sub="incremental Significance state" />
      <Stat label="Dwell" value="per-node" sub="stability throttling" />
      <Stat label="Variant" value="1-hop / adaptive" sub="affected-set strategy" />
    </div>

    <p style={{ marginTop: 20 }}>
      Next: <Link to="/workflow">the exact per-batch workflow</Link>, then{' '}
      <Link to="/graph">watch it run</Link>.
    </p>

    <PresenterNotes
      points={[
        <>Lead with the <b>warm-start</b> intuition — the partition from last batch is almost right.</>,
        <>Name the four mechanisms; mechanisms 3 &amp; 4 are the <b>correctness safety net</b>.</>,
        <>Emphasize: Significance is applied at the level of <b>every single move</b>, not just at the end.</>,
      ]}
    />
  </div>
);

export default ISLOverview;
