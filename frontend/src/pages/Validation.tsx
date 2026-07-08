import React, { useEffect, useState } from 'react';
import { getValidations, imageUrl, ValidationSet } from '../api';
import {
  PageHeader, Loading, ErrorState, PresenterNotes, Badge, Stat, fmt,
} from '../components/ui';

type Status = 'pass' | 'fail' | 'mixed';

const StatusBadge: React.FC<{ status: Status }> = ({ status }) => (
  <Badge kind={status === 'pass' ? 'ok' : status === 'fail' ? 'bad' : 'warn'}>
    {status === 'pass' ? 'PASS' : status === 'fail' ? 'FAIL → redirected' : 'MIXED'}
  </Badge>
);

const Section: React.FC<{
  id: string; title: string; status: Status;
  purpose: string; method: string; result: React.ReactNode; interpretation: string;
  images: string[]; stats?: React.ReactNode;
}> = ({ id, title, status, purpose, method, result, interpretation, images, stats }) => (
  <div className="card" style={{ marginBottom: 20 }}>
    <div className="row between" style={{ marginBottom: 4 }}>
      <h2 style={{ margin: 0 }}><span className="faint mono" style={{ fontSize: '0.9rem' }}>{id}</span> &nbsp;{title}</h2>
      <StatusBadge status={status} />
    </div>
    <div className="explain" style={{ marginTop: 14 }}>
      <div className="box"><div className="q">Purpose</div><p>{purpose}</p></div>
      <div className="box"><div className="q">Method</div><p>{method}</p></div>
      <div className="box"><div className="q">Result</div><p>{result}</p></div>
      <div className="box"><div className="q">Interpretation</div><p>{interpretation}</p></div>
    </div>
    {stats && <div className="grid grid-4" style={{ marginTop: 14 }}>{stats}</div>}
    <div className="grid" style={{ gridTemplateColumns: images.length > 1 ? '1fr 1fr' : '1fr', gap: 12, marginTop: 14 }}>
      {images.map((img) => (
        <img key={img} src={imageUrl(img)} alt={img}
          style={{ width: '100%', borderRadius: 'var(--radius-sm)', border: '1px solid var(--surface-border)', background: '#fff' }}
          onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
      ))}
    </div>
  </div>
);

const Validation: React.FC = () => {
  const [data, setData] = useState<ValidationSet | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getValidations().then(setData).catch(() =>
      setError('Could not reach the backend. Start it with: cd backend && uvicorn main:app'));
  }, []);

  if (error) return <div><PageHeader eyebrow="Validation" title="Validation studies" /><ErrorState message={error} /></div>;
  if (!data) return <div><PageHeader eyebrow="Validation" title="Validation studies" /><Loading /></div>;

  // Derive a few honest summary numbers from the committed JSON (Validation B & C).
  let bStats: React.ReactNode = null;
  const B: any = data.B;
  if (B?.metrics?.length) {
    const rows = B.metrics as any[];
    const avg = (k: string) => rows.reduce((s, r) => s + (r[k] ?? 0), 0) / rows.length;
    const speedup = avg('time_cold') / (avg('time_warm') || 1);
    bStats = (
      <>
        <Stat label="Warm↔Cold NMI" value={fmt(avg('nmi_warm_cold'), 3)} sub="partition agreement" accent />
        <Stat label="Warm-start speedup" value={`${fmt(speedup, 2)}×`} sub="cold / warm time" />
        <Stat label="Warm NMI vs GT" value={fmt(avg('nmi_warm_gt'), 3)} />
        <Stat label="Samples" value={rows.length} sub="seed × batch" />
      </>
    );
  }

  let cStats: React.ReactNode = null;
  const C: any = data.C;
  if (Array.isArray(C) && C.length) {
    const lowMu = C.filter((r: any) => r.mu <= 0.2 && r.experiment === 'C1_C2');
    const avgNmiSig = lowMu.length ? lowMu.reduce((s: number, r: any) => s + (r.nmi_significance ?? 0), 0) / lowMu.length : undefined;
    const avgNmiMod = lowMu.length ? lowMu.reduce((s: number, r: any) => s + (r.nmi_modularity ?? 0), 0) / lowMu.length : undefined;
    cStats = (
      <>
        <Stat label="Significance NMI" value={fmt(avgNmiSig, 3)} sub="μ ≤ 0.2, vs ground truth" accent />
        <Stat label="Modularity NMI" value={fmt(avgNmiMod, 3)} sub="μ ≤ 0.2, vs ground truth" />
        <Stat label="Records" value={C.length} sub="μ × seed × experiment" />
        <Stat label="k comparison" value="k_true vs k" sub="over-partition check" />
      </>
    );
  }

  return (
    <div>
      <PageHeader
        eyebrow="Validation"
        title="Validation studies — including what failed"
        lead="Three targeted studies stress-test ISL's assumptions. We report each one's purpose,
          method and outcome honestly — including the validation that failed and redirected the
          project from Surprise to Significance."
      />

      <Section
        id="A"
        title="Approximation accuracy"
        status="fail"
        purpose="Check whether an asymptotic approximation of the objective is accurate enough to drive incremental moves."
        method="Compare the exact objective against its asymptotic approximation across community sizes and seeds; measure relative error."
        result={<>The approximation's relative error was too high to trust for local decisions under the original <b>Surprise</b> objective.</>}
        interpretation="This failure was productive: it motivated moving to the exact Significance objective, which the rest of the project adopts. Reporting it demonstrates the method's evolution."
        images={['validation_a_plot.png']}
      />

      <Section
        id="B"
        title="Warm-start effectiveness"
        status="pass"
        purpose="Does starting from the previous partition (warm start) reach the same answer as recomputing cold — faster?"
        method="For each batch, run a cold recomputation and a warm-started incremental update; compare partitions (NMI) and wall-clock time across seeds."
        result={<>Warm and cold partitions agree almost perfectly (NMI ≈ 0.99), and warm starts are consistently faster.</>}
        interpretation="The warm-start premise holds: the incremental partition tracks the cold-recomputation answer while doing less work. Stability is the standout — the partition barely wavers."
        images={['validation_b_significance_nmi_plot.png', 'validation_b_significance_speedup_plot.png']}
        stats={bStats}
      />

      <Section
        id="C"
        title="Over-partitioning bias"
        status="mixed"
        purpose="Significance can over-split. Does it still recover the true structure, and how does its community count compare to modularity's?"
        method="On planted-partition graphs across mixing levels μ, compare recovered community count (k) and NMI for Significance vs. modularity against the known ground truth."
        result={<>At low mixing Significance recovers the true structure with very high NMI; at high μ it over-partitions (k far above k_true), an acknowledged trade-off.</>}
        interpretation="Significance sees small communities modularity misses (the core benefit) but tends to over-split as mixing rises. This is a known, bounded limitation — not a silent failure — and is the seed for the 'over-partitioning control' future work."
        images={['validation_c_significance_community_count_plot.png', 'validation_c_significance_nmi_plot.png']}
        stats={cStats}
      />

      <PresenterNotes
        points={[
          <><b>A failed on purpose</b> — its failure is why the project uses Significance. Lead with this; it shows maturity.</>,
          <><b>B is the strongest result</b> — warm-start NMI ≈ 0.99 means incremental ≈ full recomputation.</>,
          <><b>C is honest</b> — Significance over-partitions at high μ; we neither hide it nor overclaim.</>,
        ]}
      />
    </div>
  );
};

export default Validation;
