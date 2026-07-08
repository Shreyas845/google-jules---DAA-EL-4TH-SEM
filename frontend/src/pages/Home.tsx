import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Network, Zap, ShieldCheck } from 'lucide-react';
import { PageHeader, Stat, PresenterNotes } from '../components/ui';

const Home: React.FC = () => (
  <div>
    <PageHeader
      eyebrow="Dynamic Community Detection"
      title="Incremental Significance-Leiden (ISL)"
      lead="A method for keeping community structure up to date on graphs that change over time —
        recomputing only what an update actually affects, while detecting communities that
        modularity-based methods are mathematically blind to."
    />

    <div className="grid grid-3" style={{ marginBottom: 8 }}>
      <div className="card">
        <Zap size={20} color="var(--accent)" />
        <h3 style={{ marginTop: 10 }}>Incremental</h3>
        <p>Each edge update reprocesses only the affected neighborhood — not the whole graph.</p>
      </div>
      <div className="card">
        <ShieldCheck size={20} color="var(--good)" />
        <h3 style={{ marginTop: 10 }}>Resolution-limit free</h3>
        <p>Optimizes <b>Significance</b>, so small-but-real communities remain visible.</p>
      </div>
      <div className="card">
        <Network size={20} color="var(--warn)" />
        <h3 style={{ marginTop: 10 }}>Stable</h3>
        <p>Partitions stay consistent across updates (NMI ≈ 1.0 vs. full recomputation).</p>
      </div>
    </div>

    <h2>The result at a glance</h2>
    <div className="grid grid-4">
      <Stat label="Warm-start NMI" value="≈ 1.0" sub="vs. full recomputation" accent />
      <Stat label="Community recovery" value="0.97+" sub="NMI on LFR (Significance)" />
      <Stat label="Reprocessed" value="Local" sub="affected neighborhood only" />
      <Stat label="Validations" value="3" sub="A · B · C, fully reported" />
    </div>

    <h2>Walk through the research</h2>
    <p>This dashboard is organized as a guided narrative. Follow it top to bottom, or jump in.</p>
    <div className="grid grid-2">
      <Link to="/problem" className="card" style={{ display: 'block' }}>
        <div className="row between">
          <b>1 · The problem</b> <ArrowRight size={16} />
        </div>
        <p>Why dynamic graphs make static community detection expensive.</p>
      </Link>
      <Link to="/graph" className="card" style={{ display: 'block' }}>
        <div className="row between">
          <b>See it work</b> <ArrowRight size={16} />
        </div>
        <p>Watch ISL respond to live edge updates in the interactive Graph Viewer.</p>
      </Link>
      <Link to="/results" className="card" style={{ display: 'block' }}>
        <div className="row between">
          <b>The evidence</b> <ArrowRight size={16} />
        </div>
        <p>Runtime, NMI, Significance and baseline comparisons from real experiment runs.</p>
      </Link>
      <Link to="/demo" className="card" style={{ display: 'block' }}>
        <div className="row between">
          <b>One-click demo</b> <ArrowRight size={16} />
        </div>
        <p>Auto-presented walkthrough of the full incremental update cycle.</p>
      </Link>
    </div>

    <PresenterNotes
      points={[
        <>ISL answers a specific question: <b>can we keep good communities up to date without recomputing from scratch?</b></>,
        <>Two claims to land: it is <b>incremental</b> (fast, local) and <b>resolution-limit free</b> (sees small communities).</>,
        <>Suggested route for a live demo: <b>Problem → ISL Overview → Graph Viewer / Demo → Results → Validation</b>.</>,
      ]}
    />
  </div>
);

export default Home;
