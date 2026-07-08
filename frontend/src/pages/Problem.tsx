import React from 'react';
import { PageHeader, ExplainPanel, PresenterNotes, Badge } from '../components/ui';

const Problem: React.FC = () => (
  <div>
    <PageHeader
      eyebrow="Problem Statement"
      title="Communities change; recomputing them is expensive"
      lead="Real networks are dynamic — friendships form, links break, interactions arrive in
        streams. We want the current community structure at every moment, but re-running a full
        community detection after every change does not scale."
    />

    <h2>What is community detection?</h2>
    <div className="card">
      <p style={{ marginTop: 0 }}>
        Given a graph, partition its nodes into <b>communities</b>: groups that are densely
        connected inside and sparsely connected to the rest. It underpins recommendation,
        fraud rings, biological modules, and social-structure analysis.
      </p>
    </div>

    <h2>Why "dynamic" makes it hard</h2>
    <ExplainPanel
      items={[
        {
          q: 'What changes?',
          a: 'Edges are inserted and deleted over time, arriving in batches. The "true" communities drift as the graph evolves.',
        },
        {
          q: 'Why not recompute?',
          a: 'Static algorithms re-examine the entire graph for every batch. On a large, fast-changing graph this is wasteful — most of the graph did not change.',
        },
        {
          q: 'Why is it important?',
          a: 'Streaming systems need up-to-date structure continuously and cheaply. Cost per update is the bottleneck, not one-off accuracy.',
        },
      ]}
    />

    <h2>The core tension</h2>
    <div className="grid grid-2">
      <div className="card">
        <div className="row between">
          <h3 style={{ margin: 0 }}>Recompute every time</h3>
          <Badge kind="bad">Expensive</Badge>
        </div>
        <p>Accurate, but pays full cost for every small update. Wasteful when little changed.</p>
      </div>
      <div className="card">
        <div className="row between">
          <h3 style={{ margin: 0 }}>Update incrementally</h3>
          <Badge kind="ok">Efficient</Badge>
        </div>
        <p>
          Touch only what the update affects. The challenge: doing this <i>without</i> letting the
          partition drift away from what a full recomputation would find.
        </p>
      </div>
    </div>

    <p className="muted" style={{ marginTop: 20 }}>
      There is also a second, subtler problem — the <b>quality function</b> most methods use is
      itself flawed. That is the subject of the next page.
    </p>

    <PresenterNotes
      points={[
        <>Frame the goal precisely: <b>maintain</b> the partition per-update, not compute it once.</>,
        <>The enemy is <b>cost per update</b>. Static Leiden is accurate but recomputes everything each batch.</>,
        <>Tease the second problem — the objective function's <b>resolution limit</b> — which Motivation covers.</>,
      ]}
    />
  </div>
);

export default Problem;
