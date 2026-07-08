import React, { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { GraphTrace } from '../api';
import {
  PageHeader, Stat, Loading, ErrorState, PresenterNotes, Badge, fmt,
} from '../components/ui';
import GraphCanvas from '../components/GraphCanvas';
import { usePlayback, PlaybackControls } from '../components/Playback';
import { useTrace } from '../components/useTrace';

const frameLabel = (i: number, total: number) =>
  i === 0 ? 'Initial graph' : `Batch ${i} of ${total - 1}`;

/** Per-frame narration for the Explanation panel. */
function narrate(f: GraphTrace['frames'][number]) {
  if (f.stage === 'initial') {
    return {
      what: 'The initial graph with its starting community partition (each color is a community).',
      why: 'ISL begins from an existing partition and maintains it — this is the warm start.',
      take: 'Everything after this frame is an incremental update, not a recomputation.',
    };
  }
  const hops = f.affected_layers?.length ?? 0;
  return {
    what: `This batch inserted ${f.added.length} edge(s). From those seeds ISL grew an affected region of ${f.affected.length} node(s) over ${hops} hop-layer(s) (ringed), and ${f.moved.length} node(s) actually changed community.`,
    why: 'Only nodes near the change can plausibly want to move, so ISL re-optimizes just that region under Significance — the adaptive variant only expands further while the boundary keeps improving.',
    take: `Communities: ${f.metrics.community_count} · Significance: ${fmt(f.metrics.significance, 1)} · Update time: ${fmt(f.metrics.time_ms, 1)} ms.`,
  };
}

const GraphViewer: React.FC = () => {
  const { trace, loading, error, params, setParams, reload } = useTrace({
    n: 60, batches: 8, batch_size: 4, mu: 0.35, seed: 42, variant: 'isl_1hop',
  });
  const [partition, setPartition] = useState<'before' | 'after'>('after');
  const [selected, setSelected] = useState<number | null>(null);

  const numFrames = trace?.frames.length ?? 0;
  const pb = usePlayback(numFrames, 1500);
  const frame = trace?.frames[pb.index];
  const isUpdate = frame?.stage === 'updated';

  return (
    <div>
      <PageHeader
        eyebrow="Graph Viewer"
        title="Watch ISL respond to live updates"
        lead="This is a real ISL run on a small graph, computed on demand by the backend. Step through
          each batch to see the affected region grow from the changed edges, which nodes move, and
          how communities change. Click any node to isolate its community."
      />

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="row between">
          <div className="row" style={{ gap: 16 }}>
            <div>
              <label className="field">Variant</label>
              <select value={params.variant} onChange={(e) => setParams({ variant: e.target.value })} style={{ width: 150 }}>
                <option value="isl_1hop">ISL-1hop</option>
                <option value="isl_adaptive">ISL-adaptive</option>
              </select>
            </div>
            <div>
              <label className="field">Seed</label>
              <select value={params.seed} onChange={(e) => setParams({ seed: Number(e.target.value) })} style={{ width: 110 }}>
                {[42, 123, 456, 789].map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="field">Colour by</label>
              <div className="seg">
                <button className={partition === 'before' ? 'on' : ''} onClick={() => setPartition('before')} disabled={!isUpdate}>Before</button>
                <button className={partition === 'after' ? 'on' : ''} onClick={() => setPartition('after')}>After</button>
              </div>
            </div>
          </div>
          <button className="btn" onClick={reload} disabled={loading}>
            <RefreshCw size={15} /> New run
          </button>
        </div>
      </div>

      {loading && <Loading label="Running ISL on a fresh graph…" />}
      {error && <ErrorState message={error} hint="Start it with: cd backend && uvicorn main:app" />}

      {trace && frame && !loading && (
        <>
          <div className="grid" style={{ gridTemplateColumns: '1.6fr 1fr', gap: 16, alignItems: 'start' }}>
            <div>
              <GraphCanvas
                nodes={trace.nodes} frame={frame} height={480}
                partition={isUpdate ? partition : 'after'}
                selectedCommunity={selected}
                onSelectCommunity={setSelected}
              />
              <div className="card" style={{ marginTop: 12 }}>
                <div className="legend">
                  <span className="item"><span className="dot" style={{ background: 'var(--warn)', opacity: 0.5 }} /> Seed (changed edge)</span>
                  <span className="item"><span className="dot" style={{ border: '2.5px solid var(--accent)', background: 'transparent' }} /> Affected hop-layer</span>
                  <span className="item"><span className="dot" style={{ background: 'var(--text)' }} /> Moved node (thick ring)</span>
                  <span className="item"><span style={{ width: 20, height: 3, background: 'var(--accent)', display: 'inline-block' }} /> Inserted edge</span>
                  <span className="item">Shaded blob = community</span>
                </div>
                {selected !== null && (
                  <div className="row between" style={{ marginTop: 10 }}>
                    <Badge kind="accent">Inspecting community {selected}</Badge>
                    <button className="btn ghost" style={{ padding: '4px 10px', fontSize: '0.82rem' }} onClick={() => setSelected(null)}>Clear</button>
                  </div>
                )}
              </div>
            </div>

            <div>
              <PlaybackControls
                index={pb.index} numFrames={numFrames} playing={pb.playing}
                onPrev={pb.prev} onNext={pb.next} onToggle={pb.toggle} onReset={pb.reset}
                onScrub={pb.goto}
                labels={trace.frames.map((_, i) => frameLabel(i, numFrames))}
              />
              <div className="grid grid-2" style={{ marginTop: 12 }}>
                <Stat label="Significance" value={fmt(frame.metrics.significance, 1)} accent />
                <Stat label="Communities" value={frame.metrics.community_count} />
                <Stat label="Affected" value={frame.metrics.affected_size} sub="nodes this batch" />
                <Stat label="Moved" value={frame.metrics.nodes_moved} sub="changed community" />
              </div>
              {frame.metrics.periodic_fired && (
                <div style={{ marginTop: 12 }}>
                  <Badge kind="accent">Periodic recomputation checked this batch</Badge>
                </div>
              )}
            </div>
          </div>

          <h2>What's happening in this frame?</h2>
          {(() => {
            const n = narrate(frame);
            return (
              <div className="explain">
                <div className="box"><div className="q">What</div><p>{n.what}</p></div>
                <div className="box"><div className="q">Why</div><p>{n.why}</p></div>
                <div className="box"><div className="q">Takeaway</div><p>{n.take}</p></div>
              </div>
            );
          })()}
        </>
      )}

      <PresenterNotes
        points={[
          <>This is a <b>real algorithm run</b>, not an animation — every color, ring and metric comes from ISL.</>,
          <>Toggle <b>Colour by: Before / After</b> on an update frame to see exactly which nodes the batch moved.</>,
          <>Switch the variant to <b>ISL-adaptive</b> and watch the affected region grow an extra dashed hop-layer only where it pays off.</>,
        ]}
      />
    </div>
  );
};

export default GraphViewer;
