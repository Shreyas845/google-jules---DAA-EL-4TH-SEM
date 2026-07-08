import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell,
} from 'recharts';
import {
  getResultNames, getResult, StoredResult, AggregateBatch, MetricStat,
} from '../api';
import {
  PageHeader, Loading, ErrorState, EmptyState, PresenterNotes, Badge, Stat, fmt, COMMUNITY_COLORS,
} from '../components/ui';

const METRICS: { key: string; label: string }[] = [
  { key: 'nmi_gt', label: 'NMI vs. ground truth' },
  { key: 'time_ms', label: 'Update time (ms)' },
  { key: 'S', label: 'Significance' },
  { key: 'Q', label: 'Modularity' },
  { key: 'community_count', label: 'Community count' },
  { key: 'affected_set_size', label: 'Affected set size' },
  { key: 'nodes_moved', label: 'Nodes moved' },
  { key: 'churn_rate', label: 'Churn rate' },
];

const isStat = (v: unknown): v is MetricStat =>
  typeof v === 'object' && v !== null && 'mean' in (v as any);

const mean = (b: AggregateBatch, key: string): number | undefined => {
  const v = b[key];
  if (isStat(v)) return v.mean;
  if (typeof v === 'number') return v;
  return undefined;
};

const Results: React.FC = () => {
  const [names, setNames] = useState<string[] | null>(null);
  const [current, setCurrent] = useState<StoredResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [metric, setMetric] = useState('time_ms');
  const [hidden, setHidden] = useState<Set<string>>(new Set());

  useEffect(() => {
    getResultNames()
      .then((ns) => {
        setNames(ns);
        if (ns.length) getResult(ns[0]).then(setCurrent).catch(() => setError('Failed to load result set.'));
      })
      .catch(() => setError('Could not reach the backend. Start it with: cd backend && uvicorn main:app'));
  }, []);

  const methods = useMemo(() => (current ? Object.keys(current.aggregate) : []), [current]);
  const availableMetrics = useMemo(() => {
    if (!current) return METRICS;
    const first = methods.map((m) => current.aggregate[m][0]).find(Boolean);
    if (!first) return METRICS;
    return METRICS.filter((mt) => mt.key in first);
  }, [current, methods]);

  // Build per-batch chart data across methods for the selected metric.
  const lineData = useMemo(() => {
    if (!current) return [];
    const maxBatches = Math.max(0, ...methods.map((m) => current.aggregate[m].length));
    const rows: Record<string, number | string>[] = [];
    for (let i = 0; i < maxBatches; i++) {
      const row: Record<string, number | string> = { batch: i + 1 };
      methods.forEach((m) => {
        const b = current.aggregate[m][i];
        if (b) {
          const v = mean(b, metric);
          if (v !== undefined) row[m] = Number(v.toFixed(4));
        }
      });
      rows.push(row);
    }
    return rows;
  }, [current, methods, metric]);

  // Final-batch comparison bar (mean of selected metric at last batch).
  const barData = useMemo(() => {
    if (!current) return [];
    return methods.map((m) => {
      const batches = current.aggregate[m];
      const last = batches[batches.length - 1];
      return { method: m, value: last ? Number((mean(last, metric) ?? 0).toFixed(4)) : 0 };
    });
  }, [current, methods, metric]);

  const toggle = (m: string) =>
    setHidden((h) => { const n = new Set(h); n.has(m) ? n.delete(m) : n.add(m); return n; });

  if (error) return <div><PageHeader eyebrow="Results" title="Experiment results" /><ErrorState message={error} /></div>;
  if (!names) return <div><PageHeader eyebrow="Results" title="Experiment results" /><Loading /></div>;
  if (names.length === 0) return (
    <div>
      <PageHeader eyebrow="Results" title="Experiment results" />
      <EmptyState message="No stored result sets yet.">
        <Link to="/experiments" className="btn primary">Run an experiment</Link>
      </EmptyState>
    </div>
  );

  return (
    <div>
      <PageHeader
        eyebrow="Results"
        title="Experiment results"
        lead="Every series here comes from a real experiment run — ISL variants against Static Leiden,
          Static Significance, BFS-Leiden and no-update baselines, aggregated across seeds."
      />

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="row between">
          <div className="row" style={{ gap: 16 }}>
            <div>
              <label className="field">Result set</label>
              <select
                value={current?.name ?? ''}
                onChange={(e) => getResult(e.target.value).then(setCurrent)}
                style={{ width: 200 }}
              >
                {names.map((n) => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
            <div>
              <label className="field">Metric</label>
              <select value={metric} onChange={(e) => setMetric(e.target.value)} style={{ width: 220 }}>
                {availableMetrics.map((m) => <option key={m.key} value={m.key}>{m.label}</option>)}
              </select>
            </div>
          </div>
          {current?.precomputed && <Badge kind="neutral">precomputed</Badge>}
        </div>
      </div>

      {current && (
        <>
          {/* Headline stats: ISL vs Static Leiden at final batch */}
          <div className="grid grid-4">
            {(() => {
              const cards: React.ReactNode[] = [];
              const push = (m: string, label: string, key: string, digits = 3, unit = '') => {
                const b = current.aggregate[m];
                if (!b?.length) return;
                const v = mean(b[b.length - 1], key);
                cards.push(<Stat key={`${m}-${key}`} label={label} value={v === undefined ? '—' : `${fmt(v, digits)}${unit}`} sub={m} accent={m === 'isl_1hop'} />);
              };
              push('isl_1hop', 'ISL-1hop NMI', 'nmi_gt');
              push('static_leiden', 'Static Leiden NMI', 'nmi_gt');
              push('isl_1hop', 'ISL update time', 'time_ms', 2, ' ms');
              push('static_leiden', 'Leiden update time', 'time_ms', 2, ' ms');

              // Derived headline: the core efficiency claim, stated outright.
              const islB = current.aggregate['isl_1hop'];
              const leiB = current.aggregate['static_leiden'];
              const islT = islB?.length ? mean(islB[islB.length - 1], 'time_ms') : undefined;
              const leiT = leiB?.length ? mean(leiB[leiB.length - 1], 'time_ms') : undefined;
              if (islT && leiT && islT > 0) {
                cards.unshift(
                  <Stat key="speedup" label="ISL speedup" value={`${fmt(leiT / islT, 1)}×`}
                    sub="vs. Static Leiden / batch" accent />
                );
              }
              return cards;
            })()}
          </div>

          <h2>{availableMetrics.find((m) => m.key === metric)?.label} across batches</h2>
          <div className="card">
            <div className="legend" style={{ marginBottom: 10 }}>
              {methods.map((m, i) => (
                <span key={m} className="item" style={{ cursor: 'pointer', opacity: hidden.has(m) ? 0.4 : 1 }} onClick={() => toggle(m)}>
                  <span className="dot" style={{ background: COMMUNITY_COLORS[i % COMMUNITY_COLORS.length] }} /> {m}
                </span>
              ))}
            </div>
            <ResponsiveContainer width="100%" height={340}>
              <LineChart data={lineData} margin={{ top: 6, right: 12, bottom: 6, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--surface-border)" />
                <XAxis dataKey="batch" stroke="var(--text-faint)" fontSize={12}
                  label={{ value: 'Batch', position: 'insideBottom', offset: -2, fontSize: 12, fill: 'var(--text-faint)' }} />
                <YAxis stroke="var(--text-faint)" fontSize={12} width={56} />
                <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--surface-border)', borderRadius: 8, color: 'var(--text)' }} />
                {methods.map((m, i) => (
                  !hidden.has(m) && (
                    <Line key={m} type="monotone" dataKey={m} stroke={COMMUNITY_COLORS[i % COMMUNITY_COLORS.length]}
                      strokeWidth={m.startsWith('isl') ? 2.6 : 1.6} dot={false} isAnimationActive={false} />
                  )
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          <h2>Final-batch comparison</h2>
          <div className="card">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={barData} margin={{ top: 6, right: 12, bottom: 6, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--surface-border)" />
                <XAxis dataKey="method" stroke="var(--text-faint)" fontSize={11} angle={-15} textAnchor="end" height={60} />
                <YAxis stroke="var(--text-faint)" fontSize={12} width={56} />
                <Tooltip contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--surface-border)', borderRadius: 8, color: 'var(--text)' }} />
                <Bar dataKey="value" radius={[5, 5, 0, 0]}>
                  {barData.map((d, i) => (
                    <Cell key={i} fill={d.method.startsWith('isl') ? 'var(--accent)' : COMMUNITY_COLORS[i % COMMUNITY_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {current.metadata?.total_runtime_s !== undefined && (
            <p className="faint" style={{ fontSize: '0.85rem' }}>
              Full run wall-clock: {fmt(current.metadata.total_runtime_s, 1)} s.
            </p>
          )}
        </>
      )}

      <PresenterNotes
        points={[
          <>Switch <b>Metric</b> to tell different parts of the story: <b>NMI</b> (quality), <b>time_ms</b> (cost), <b>community_count</b> (multi-scale).</>,
          <>ISL lines are drawn <b>thicker</b> — contrast them against Static Leiden and the other baselines.</>,
          <>Click legend entries to isolate methods. All values are <b>means across seeds</b> from real runs.</>,
        ]}
      />
    </div>
  );
};

export default Results;
