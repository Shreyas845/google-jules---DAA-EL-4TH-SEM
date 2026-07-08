import React, { useEffect, useMemo } from 'react';
import { Play, RotateCcw } from 'lucide-react';
import { GraphTrace } from '../api';
import { PageHeader, Loading, ErrorState, Stat, Badge, fmt } from '../components/ui';
import GraphCanvas, { Substage } from '../components/GraphCanvas';
import { usePlayback, PlaybackControls } from '../components/Playback';
import { useTrace } from '../components/useTrace';

/** The four phases each batch is walked through, in order. */
const PHASES: { key: Substage; label: string }[] = [
  { key: 'update', label: 'Edge update' },
  { key: 'affected', label: 'Affected region' },
  { key: 'optimize', label: 'Local optimization' },
  { key: 'settle', label: 'Repair & commit' },
];

type Step = { fi: number; sub?: Substage };

/** Explanation shown for the current step. */
function explain(step: Step, frame: GraphTrace['frames'][number], batchNo: number) {
  if (step.sub === undefined) {
    return {
      title: 'Starting partition',
      body: 'ISL begins from an existing community partition — the “warm start”. From here it only ever updates this partition incrementally; it never recomputes it from scratch.',
    };
  }
  const hops = frame.affected_layers?.length ?? 0;
  switch (step.sub) {
    case 'update':
      return {
        title: `Batch ${batchNo} · edges arrive`,
        body: `${frame.added.length} new edge(s) are inserted (highlighted). The counters behind Significance are updated immediately, but the partition is still the previous one — nothing has moved yet.`,
      };
    case 'affected':
      return {
        title: `Batch ${batchNo} · affected region`,
        body: `From the changed endpoints (seeds), ISL grows an affected region outward — 1 hop, then further only while the boundary keeps improving. ${frame.affected.length} node(s) across ${hops} hop-layer(s) are now in scope; the rest of the graph is left untouched.`,
      };
    case 'optimize':
      return {
        title: `Batch ${batchNo} · local optimization`,
        body: `Inside the affected region only, ISL moves nodes to the community that most improves Significance (best of several orderings). ${frame.moved.length} node(s) actually change community — watch them pulse and recolor.`,
      };
    case 'settle':
    default:
      return {
        title: `Batch ${batchNo} · repair & commit`,
        body: `Any community left internally disconnected is split so every community stays connected. Every K batches ISL also checks itself against a full recomputation to bound drift. The updated partition is committed.${frame.metrics.periodic_fired ? ' A periodic check fired this batch.' : ''}`,
      };
  }
}

const DemoMode: React.FC = () => {
  const { trace, loading, error } = useTrace({
    n: 55, batches: 7, batch_size: 4, mu: 0.35, seed: 42, variant: 'isl_adaptive',
  });

  // Expand the trace into fine-grained steps: the initial frame, then four phases per batch.
  const steps = useMemo<Step[]>(() => {
    if (!trace) return [];
    const out: Step[] = [{ fi: 0 }];
    trace.frames.forEach((_, i) => {
      if (i === 0) return;
      PHASES.forEach((p) => out.push({ fi: i, sub: p.key }));
    });
    return out;
  }, [trace]);

  const pb = usePlayback(steps.length, 1700);

  // Autoplay once loaded.
  useEffect(() => {
    if (trace && !loading) pb.setPlaying(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trace, loading]);

  const step = steps[pb.index];
  const frame = trace && step ? trace.frames[step.fi] : undefined;
  const batchNo = frame && step?.sub !== undefined ? frame.batch_idx : 0;

  const first = trace?.frames[0];
  const last = trace?.frames[trace.frames.length - 1];

  return (
    <div>
      <PageHeader
        eyebrow="Demo Mode"
        title="The ISL update cycle, step by step"
        lead="A hands-off, guided simulation. It walks each batch of edge updates through the four
          phases ISL really performs — edges arrive, the affected region grows, nodes re-optimize,
          the partition is repaired and committed — then moves to the next batch."
      />

      {loading && <Loading label="Preparing the demonstration…" />}
      {error && <ErrorState message={error} hint="Start it with: cd backend && uvicorn main:app" />}

      {trace && frame && step && !loading && (
        <>
          {/* Phase stepper — honest: shows the current batch's four phases */}
          <div className="row between" style={{ marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
            <div className="row" style={{ gap: 6, flexWrap: 'wrap' }}>
              {PHASES.map((p) => (
                <span key={p.key} className={`badge ${step.sub === p.key ? 'accent' : 'neutral'}`} style={{ fontSize: '0.74rem' }}>
                  {p.label}
                </span>
              ))}
            </div>
            <span className="faint mono" style={{ fontSize: '0.8rem' }}>
              {step.sub === undefined ? 'Warm start' : `Batch ${batchNo} / ${trace.frames.length - 1}`}
            </span>
          </div>

          <div className="grid" style={{ gridTemplateColumns: '1.7fr 1fr', gap: 16, alignItems: 'start' }}>
            <div>
              <GraphCanvas nodes={trace.nodes} frame={frame} substage={step.sub} height={500} />
            </div>
            <div>
              <div className="card" style={{ borderLeft: '3px solid var(--accent)' }}>
                {(() => {
                  const e = explain(step, frame, batchNo);
                  return (
                    <>
                      <div className="eyebrow" style={{ color: 'var(--accent)', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                        Step {pb.index + 1} / {steps.length}
                      </div>
                      <h3 style={{ margin: '6px 0 8px' }}>{e.title}</h3>
                      <p style={{ margin: 0 }}>{e.body}</p>
                    </>
                  );
                })()}
              </div>

              <div className="grid grid-2" style={{ marginTop: 12 }}>
                <Stat label="Significance" value={fmt(frame.metrics.significance, 1)} accent />
                <Stat label="Communities" value={frame.metrics.community_count} />
                <Stat label="Affected" value={frame.metrics.affected_size} />
                <Stat label="Moved" value={frame.metrics.nodes_moved} />
              </div>

              {frame.metrics.periodic_fired && step.sub === 'settle' && (
                <div style={{ marginTop: 12 }}>
                  <Badge kind="accent">Periodic recomputation checked this batch</Badge>
                </div>
              )}

              <div className="row" style={{ marginTop: 12, gap: 8 }}>
                {pb.index >= steps.length - 1 ? (
                  <button className="btn primary" onClick={pb.reset}><RotateCcw size={15} /> Replay</button>
                ) : (
                  <button className="btn primary" onClick={pb.toggle}>
                    <Play size={15} /> {pb.playing ? 'Pause' : 'Resume'}
                  </button>
                )}
              </div>
            </div>
          </div>

          <div style={{ marginTop: 16 }}>
            <PlaybackControls
              index={pb.index} numFrames={steps.length} playing={pb.playing}
              onPrev={pb.prev} onNext={pb.next} onToggle={pb.toggle} onReset={pb.reset}
              onScrub={pb.goto}
            />
          </div>

          {/* Final metric comparison — initial vs final */}
          {first && last && (
            <>
              <h2>Metric comparison — start vs. end</h2>
              <div className="table-scroll">
                <table className="data">
                  <thead><tr><th>Metric</th><th>Initial</th><th>Final</th></tr></thead>
                  <tbody>
                    <tr><td>Significance</td><td>{fmt(first.metrics.significance, 1)}</td><td>{fmt(last.metrics.significance, 1)}</td></tr>
                    <tr><td>Community count</td><td>{first.metrics.community_count}</td><td>{last.metrics.community_count}</td></tr>
                    <tr><td>Edges</td><td>{first.edges.length}</td><td>{last.edges.length}</td></tr>
                  </tbody>
                </table>
              </div>
              <p className="muted" style={{ fontSize: '0.9rem' }}>
                The partition was maintained across every batch incrementally — the final communities
                were never computed from scratch.
              </p>
            </>
          )}
        </>
      )}
    </div>
  );
};

export default DemoMode;
