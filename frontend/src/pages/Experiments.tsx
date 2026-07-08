import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Play, Loader2 } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import {
  getConfigs, runExperiment, getJobStatus, ExperimentConfigSummary, JobStatus,
} from '../api';
import {
  PageHeader, Loading, ErrorState, PresenterNotes, Badge, Stat, fmt, COMMUNITY_COLORS,
} from '../components/ui';

/** Read a metric mean whether the aggregate stores {mean,std} or a bare number. */
const metricMean = (rec: any, key: string): number | undefined => {
  const v = rec?.[key];
  if (v && typeof v === 'object' && 'mean' in v) return v.mean;
  if (typeof v === 'number') return v;
  return undefined;
};

const Experiments: React.FC = () => {
  const [configs, setConfigs] = useState<ExperimentConfigSummary[] | null>(null);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [selected, setSelected] = useState<string>('smoke_test.json');
  const [job, setJob] = useState<JobStatus | null>(null);
  const [running, setRunning] = useState(false);
  const poll = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    getConfigs().then(setConfigs).catch(() =>
      setLoadErr('Could not reach the backend. Start it with: cd backend && uvicorn main:app'));
    return () => { if (poll.current) clearInterval(poll.current); };
  }, []);

  const cfg = configs?.find((c) => c.name === selected);
  const heavy = (cfg?.n ?? 0) >= 1000;

  const start = async () => {
    setRunning(true); setJob(null);
    try {
      const { job_id } = await runExperiment(selected);
      poll.current = setInterval(async () => {
        const s = await getJobStatus(job_id);
        setJob(s);
        if (s.status === 'completed' || s.status === 'failed') {
          if (poll.current) clearInterval(poll.current);
          setRunning(false);
        }
      }, 1000);
    } catch {
      setRunning(false);
      setJob(null);
      setLoadErr('Failed to launch the experiment.');
    }
  };

  if (loadErr && !configs) return (
    <div>
      <PageHeader eyebrow="Experiments" title="Run the ISL pipeline" />
      <ErrorState message={loadErr} />
    </div>
  );
  if (!configs) return <div><PageHeader eyebrow="Experiments" title="Run the ISL pipeline" /><Loading /></div>;

  // Summarize final-batch results if completed.
  let summary: { method: string; nmi?: number; time?: number; s?: number }[] = [];
  let methods: string[] = [];
  const timeSeries: Record<string, number | string>[] = [];
  if (job?.status === 'completed' && job.results) {
    const agg = job.results.aggregate;
    methods = Object.keys(agg);
    summary = methods.map((method) => {
      const batches = agg[method];
      const last = batches[batches.length - 1] as any;
      return {
        method,
        nmi: last?.nmi_gt?.mean,
        time: last?.time_ms?.mean,
        s: last?.S?.mean,
      };
    });
    // Per-batch update-time series, so a live run is visual, not just a table.
    const maxB = Math.max(0, ...methods.map((m) => agg[m].length));
    for (let i = 0; i < maxB; i++) {
      const row: Record<string, number | string> = { batch: i + 1 };
      methods.forEach((m) => {
        const v = metricMean(agg[m][i], 'time_ms');
        if (v !== undefined) row[m] = Number(v.toFixed(3));
      });
      timeSeries.push(row);
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Experiments"
        title="Run the real ISL pipeline"
        lead="Launch the actual experiment runner on a chosen configuration. It runs ISL variants and
          baselines across seeds, then aggregates the metrics — the same code path used to produce
          the stored results."
      />

      <div className="grid" style={{ gridTemplateColumns: '1fr 1fr', gap: 16, alignItems: 'start' }}>
        <div className="card">
          <label className="field">Configuration</label>
          <select value={selected} onChange={(e) => setSelected(e.target.value)}>
            {configs.map((c) => (
              <option key={c.name} value={c.name}>
                {c.experiment_id} — n={c.n}, {c.num_batches} batches × {c.seeds} seed(s)
              </option>
            ))}
          </select>

          {cfg && (
            <div className="grid grid-2" style={{ marginTop: 14 }}>
              <Stat label="Dataset" value={cfg.dataset_type.toUpperCase()} sub={`n = ${cfg.n}, μ = ${cfg.mu}`} />
              <Stat label="Workload" value={`${cfg.num_batches} × ${cfg.seeds}`} sub="batches × seeds" />
            </div>
          )}

          <div style={{ marginTop: 14 }}>
            {heavy && (
              <div style={{ marginBottom: 10 }}>
                <Badge kind="warn">Large config — this can take several minutes</Badge>
              </div>
            )}
            <button className="btn primary" onClick={start} disabled={running}>
              {running ? <><Loader2 size={15} className="spin-i" /> Running…</> : <><Play size={15} /> Run experiment</>}
            </button>
          </div>

          <p className="faint" style={{ fontSize: '0.82rem', marginTop: 12 }}>
            Tip: <b>smoke_test</b> completes in seconds and is ideal for a live demo. Larger configs
            reproduce the full study.
          </p>
        </div>

        <div className="card">
          <h3 style={{ marginTop: 0 }}>Job status</h3>
          {!job && !running && <p className="muted">No run yet. Choose a config and press Run.</p>}
          {(running || job) && (
            <>
              <div className="row between" style={{ marginBottom: 8 }}>
                <Badge kind={
                  job?.status === 'completed' ? 'ok' :
                  job?.status === 'failed' ? 'bad' : 'accent'
                }>
                  {job?.status ?? 'starting'}
                </Badge>
                <span className="faint mono" style={{ fontSize: '0.8rem' }}>
                  {job?.message ?? 'Launching…'}
                </span>
              </div>
              <div style={{ height: 8, background: 'var(--bg-sunken)', borderRadius: 999, overflow: 'hidden' }}>
                <div style={{
                  width: `${job?.progress ?? 5}%`, height: '100%',
                  background: job?.status === 'failed' ? 'var(--bad)' : 'var(--accent)',
                  transition: 'width 0.4s ease',
                }} />
              </div>
              {job?.status === 'failed' && (
                <p className="mono" style={{ color: 'var(--bad)', fontSize: '0.82rem', marginTop: 10 }}>{job.error}</p>
              )}
              {job?.status === 'completed' && (
                <p className="muted" style={{ fontSize: '0.85rem', marginTop: 10 }}>
                  Aggregates written to <span className="mono">{job.results?.output_dir}</span>.
                </p>
              )}
            </>
          )}
        </div>
      </div>

      {summary.length > 0 && (
        <>
          <h2>Final-batch results (this run)</h2>
          <div className="table-scroll">
            <table className="data">
              <thead><tr><th>Method</th><th>NMI vs. ground truth</th><th>Update time (ms)</th><th>Significance</th></tr></thead>
              <tbody>
                {summary.map((r) => (
                  <tr key={r.method}>
                    <td>{r.method.startsWith('isl') ? <b>{r.method}</b> : r.method}</td>
                    <td>{fmt(r.nmi)}</td>
                    <td>{fmt(r.time, 2)}</td>
                    <td>{fmt(r.s, 1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {timeSeries.length > 1 && (
            <div className="card" style={{ marginTop: 12 }}>
              <div className="row between" style={{ marginBottom: 8 }}>
                <h3 style={{ margin: 0 }}>Update time per batch (ms)</h3>
                <div className="legend">
                  {methods.map((m, i) => (
                    <span key={m} className="item">
                      <span className="dot" style={{ background: COMMUNITY_COLORS[i % COMMUNITY_COLORS.length] }} /> {m}
                    </span>
                  ))}
                </div>
              </div>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={timeSeries} margin={{ top: 6, right: 12, bottom: 6, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--surface-border)" />
                  <XAxis dataKey="batch" stroke="var(--text-faint)" fontSize={12} />
                  <YAxis stroke="var(--text-faint)" fontSize={12} width={56} />
                  <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--surface-border)', borderRadius: 8, color: 'var(--text)' }} />
                  {methods.map((m, i) => (
                    <Line key={m} type="monotone" dataKey={m} stroke={COMMUNITY_COLORS[i % COMMUNITY_COLORS.length]}
                      strokeWidth={m.startsWith('isl') ? 2.6 : 1.6} dot={false} isAnimationActive={false} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          <p className="muted" style={{ fontSize: '0.9rem' }}>
            Explore this and other runs in detail on the <Link to="/results">Results</Link> page.
          </p>
        </>
      )}

      <PresenterNotes
        points={[
          <>This runs the <b>real runner</b> — the same code that produced the committed study results.</>,
          <>Use <b>smoke_test</b> live (seconds). The 5000-node config reproduces the full run but takes minutes.</>,
          <>Progress is polled from a background job — note the honest <b>queued → running → completed</b> states.</>,
        ]}
      />
    </div>
  );
};

export default Experiments;
