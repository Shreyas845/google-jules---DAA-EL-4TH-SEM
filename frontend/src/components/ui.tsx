/** Shared, reusable UI primitives used across all pages. */
import React from 'react';
import { Presentation, Lightbulb } from 'lucide-react';

/** Ten categorical community colors, matching theme.css --c0..--c9. */
export const COMMUNITY_COLORS = [
  '#4f46e5', '#0f9d6b', '#c9820a', '#d1495b', '#2b8ac9',
  '#8b5cf6', '#e07b39', '#12b3a6', '#b0498c', '#6b7280',
];

export const communityColor = (c: number): string =>
  COMMUNITY_COLORS[((c % COMMUNITY_COLORS.length) + COMMUNITY_COLORS.length) % COMMUNITY_COLORS.length];

export const PageHeader: React.FC<{
  eyebrow?: string;
  title: string;
  lead?: React.ReactNode;
}> = ({ eyebrow, title, lead }) => (
  <div className="page-head">
    {eyebrow && <div className="eyebrow">{eyebrow}</div>}
    <h1>{title}</h1>
    {lead && <p className="lead">{lead}</p>}
  </div>
);

export const Stat: React.FC<{
  label: string;
  value: React.ReactNode;
  sub?: React.ReactNode;
  accent?: boolean;
}> = ({ label, value, sub, accent }) => (
  <div className={`stat${accent ? ' accent' : ''}`}>
    <div className="label">{label}</div>
    <div className="value">{value}</div>
    {sub && <div className="sub">{sub}</div>}
  </div>
);

export const Badge: React.FC<{
  kind?: 'ok' | 'warn' | 'bad' | 'neutral' | 'accent';
  children: React.ReactNode;
}> = ({ kind = 'neutral', children }) => (
  <span className={`badge ${kind}`}>{children}</span>
);

/** Presenter notes: concise bullets for a faculty demonstration. */
export const PresenterNotes: React.FC<{ points: React.ReactNode[] }> = ({ points }) => (
  <div className="presenter">
    <div className="head">
      <Presentation size={15} /> Presenter Notes
    </div>
    <ul>
      {points.map((p, i) => (
        <li key={i}>{p}</li>
      ))}
    </ul>
  </div>
);

/** "What / Why / Takeaway" explanation grid for visualizations. */
export const ExplainPanel: React.FC<{
  items: { q: string; a: React.ReactNode }[];
}> = ({ items }) => (
  <div className="explain">
    {items.map((it, i) => (
      <div className="box" key={i}>
        <div className="q">
          <Lightbulb size={13} style={{ verticalAlign: '-2px', marginRight: 4 }} />
          {it.q}
        </div>
        <p>{it.a}</p>
      </div>
    ))}
  </div>
);

export const Loading: React.FC<{ label?: string }> = ({ label = 'Loading…' }) => (
  <div className="state">
    <div className="spinner" />
    <div>{label}</div>
  </div>
);

export const ErrorState: React.FC<{ message: string; hint?: string }> = ({ message, hint }) => (
  <div className="state error">
    <div style={{ fontWeight: 650 }}>{message}</div>
    {hint && <div className="faint" style={{ fontSize: '0.85rem' }}>{hint}</div>}
  </div>
);

export const EmptyState: React.FC<{ message: string; children?: React.ReactNode }> = ({
  message,
  children,
}) => (
  <div className="state">
    <div>{message}</div>
    {children}
  </div>
);

/** Format helpers. */
export const fmt = (v: number | undefined, digits = 3): string =>
  v === undefined || Number.isNaN(v) ? '—' : v.toFixed(digits);

export const fmtInt = (v: number | undefined): string =>
  v === undefined || Number.isNaN(v) ? '—' : Math.round(v).toLocaleString();
