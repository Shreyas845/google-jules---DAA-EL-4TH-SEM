/**
 * Interactive SVG renderer for ISL execution traces.
 *
 * Renders one frame of a trace and makes the algorithm's behavior legible:
 *   • nodes colored by community, with soft community "territory" hulls behind them;
 *   • the affected region drawn as concentric hop-layers (seed → 1-hop → adaptive expansion),
 *     which is how ISL's adaptive radius actually grows;
 *   • inserted/deleted edges of the batch highlighted;
 *   • moved nodes emphasized, and before→after community changes animated by fill transition;
 *   • click a node to isolate its community; zoom / pan / hover throughout.
 *
 * Node positions come from the backend layout and are fixed across frames, so the graph never
 * jumps — only communities, highlights and the affected region change. A `substage` prop lets
 * Demo Mode walk a single batch through its phases without any extra data.
 */
import React, { useMemo, useRef, useState } from 'react';
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import { TraceNode, TraceFrame } from '../api';
import { communityColor } from './ui';

/** The phases Demo Mode steps a single batch through. */
export type Substage = 'update' | 'affected' | 'optimize' | 'settle';

type Props = {
  nodes: TraceNode[];
  frame: TraceFrame;
  height?: number;
  showAffected?: boolean;
  showUpdates?: boolean;
  showHulls?: boolean;
  /** Which partition to color by. Defaults to the post-batch ("after") assignment. */
  partition?: 'before' | 'after';
  /** When set, drives a staged single-batch reveal (overrides showAffected/partition). */
  substage?: Substage;
  /** Controlled community isolation. If omitted, the canvas manages its own selection. */
  selectedCommunity?: number | null;
  onSelectCommunity?: (c: number | null) => void;
};

const VB = 1000; // internal viewBox coordinate space

// -------------------------------------------------------------------------------------
// Geometry helpers — convex hull + a smooth closed path for community territories.
// -------------------------------------------------------------------------------------
type Pt = { x: number; y: number };

function convexHull(pts: Pt[]): Pt[] {
  if (pts.length < 3) return pts.slice();
  const p = [...pts].sort((a, b) => a.x - b.x || a.y - b.y);
  const cross = (o: Pt, a: Pt, b: Pt) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  const lower: Pt[] = [];
  for (const q of p) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], q) <= 0) lower.pop();
    lower.push(q);
  }
  const upper: Pt[] = [];
  for (let i = p.length - 1; i >= 0; i--) {
    const q = p[i];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], q) <= 0) upper.pop();
    upper.push(q);
  }
  lower.pop();
  upper.pop();
  return lower.concat(upper);
}

/** Push hull vertices outward from the centroid so the territory wraps around its nodes. */
function pad(hull: Pt[], amount: number): Pt[] {
  const cx = hull.reduce((s, p) => s + p.x, 0) / hull.length;
  const cy = hull.reduce((s, p) => s + p.y, 0) / hull.length;
  return hull.map((p) => {
    const dx = p.x - cx;
    const dy = p.y - cy;
    const len = Math.hypot(dx, dy) || 1;
    return { x: p.x + (dx / len) * amount, y: p.y + (dy / len) * amount };
  });
}

/** A smooth closed path through the midpoints of a polygon (vertices act as control points). */
function smoothClosedPath(pts: Pt[]): string {
  const n = pts.length;
  const mid = (a: Pt, b: Pt) => ({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 });
  let m = mid(pts[n - 1], pts[0]);
  let d = `M ${m.x.toFixed(1)} ${m.y.toFixed(1)}`;
  for (let i = 0; i < n; i++) {
    const next = mid(pts[i], pts[(i + 1) % n]);
    d += ` Q ${pts[i].x.toFixed(1)} ${pts[i].y.toFixed(1)} ${next.x.toFixed(1)} ${next.y.toFixed(1)}`;
  }
  return d + ' Z';
}

const GraphCanvas: React.FC<Props> = ({
  nodes, frame, height = 460,
  showAffected = true, showUpdates = true, showHulls = true,
  partition = 'after', substage, selectedCommunity, onSelectCommunity,
}) => {
  const [zoom, setZoom] = useState(1);
  const [panPos, setPan] = useState({ x: 0, y: 0 });
  const [hover, setHover] = useState<{ id: number; x: number; y: number } | null>(null);
  const [innerSel, setInnerSel] = useState<number | null>(null);
  const drag = useRef<{ x: number; y: number; px: number; py: number; moved: boolean } | null>(null);

  const sel = selectedCommunity !== undefined ? selectedCommunity : innerSel;
  const setSel = onSelectCommunity ?? setInnerSel;

  const padVB = 60;
  const px = (x: number) => padVB + x * (VB - 2 * padVB);
  const py = (y: number) => padVB + y * (VB - 2 * padVB);

  // Resolve what to show. Demo-Mode substages override the plain props.
  const view = useMemo(() => {
    if (frame.stage === 'initial') {
      return { part: 'after' as const, affected: false, moves: false, edgesHot: false, ringsFade: false };
    }
    switch (substage) {
      case 'update':   return { part: 'before' as const, affected: false, moves: false, edgesHot: true, ringsFade: false };
      case 'affected': return { part: 'before' as const, affected: true, moves: false, edgesHot: true, ringsFade: false };
      case 'optimize': return { part: 'after' as const, affected: true, moves: true, edgesHot: true, ringsFade: false };
      case 'settle':   return { part: 'after' as const, affected: showAffected, moves: true, edgesHot: false, ringsFade: true };
      default:         return { part: partition, affected: showAffected, moves: true, edgesHot: showUpdates, ringsFade: false };
    }
  }, [frame.stage, substage, partition, showAffected, showUpdates]);

  const communities = useMemo(() => {
    if (view.part === 'before' && frame.communities_before) return frame.communities_before;
    return frame.communities;
  }, [view.part, frame.communities, frame.communities_before]);

  const movedSet = useMemo(() => new Set(frame.moved), [frame.moved]);
  const addedSet = useMemo(() => new Set(frame.added.map((e) => `${e[0]}-${e[1]}`)), [frame.added]);

  // node id -> which hop-layer of the affected region it belongs to (0 = seed).
  const layerOf = useMemo(() => {
    const m = new Map<number, number>();
    (frame.affected_layers ?? []).forEach((layer, i) => layer.forEach((id) => { if (!m.has(id)) m.set(id, i); }));
    return m;
  }, [frame.affected_layers]);
  const maxLayer = Math.max(0, (frame.affected_layers?.length ?? 1) - 1);

  const nodeById = useMemo(() => {
    const m = new Map<number, TraceNode>();
    nodes.forEach((n) => m.set(n.id, n));
    return m;
  }, [nodes]);

  // Convex-hull territory per community (only communities with ≥1 visible node).
  const hulls = useMemo(() => {
    if (!showHulls) return [];
    const byComm = new Map<number, Pt[]>();
    nodes.forEach((n) => {
      const c = communities[n.id] ?? 0;
      const arr = byComm.get(c) ?? [];
      arr.push({ x: px(n.x), y: py(n.y) });
      byComm.set(c, arr);
    });
    const out: { c: number; d: string; single?: Pt }[] = [];
    byComm.forEach((pts, c) => {
      if (pts.length >= 3) {
        out.push({ c, d: smoothClosedPath(pad(convexHull(pts), 30)) });
      } else if (pts.length === 2) {
        out.push({ c, d: smoothClosedPath(pad([...pts, { x: (pts[0].x + pts[1].x) / 2, y: (pts[0].y + pts[1].y) / 2 + 1 }], 30)) });
      } else {
        out.push({ c, d: '', single: pts[0] });
      }
    });
    return out;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, communities, showHulls]);

  const dimmed = (c: number) => sel !== null && c !== sel;

  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setZoom((z) => Math.min(4, Math.max(0.5, z - e.deltaY * 0.0012)));
  };
  const onDown = (e: React.MouseEvent) => {
    drag.current = { x: e.clientX, y: e.clientY, px: panPos.x, py: panPos.y, moved: false };
  };
  const onMove = (e: React.MouseEvent) => {
    if (!drag.current) return;
    const dx = e.clientX - drag.current.x;
    const dy = e.clientY - drag.current.y;
    if (Math.abs(dx) + Math.abs(dy) > 3) drag.current.moved = true;
    setPan({ x: drag.current.px + dx, y: drag.current.py + dy });
  };
  const onUp = () => { drag.current = null; };
  const reset = () => { setZoom(1); setPan({ x: 0, y: 0 }); };

  // Click background (not a node) clears the community selection.
  const onBgClick = () => { if (!drag.current?.moved) setSel(null); };

  return (
    <div style={{ position: 'relative' }}>
      <div style={{ position: 'absolute', top: 10, right: 10, zIndex: 3, display: 'flex', gap: 6 }}>
        <button className="btn icon ghost" onClick={() => setZoom((z) => Math.min(4, z + 0.3))} aria-label="Zoom in"><ZoomIn size={15} /></button>
        <button className="btn icon ghost" onClick={() => setZoom((z) => Math.max(0.5, z - 0.3))} aria-label="Zoom out"><ZoomOut size={15} /></button>
        <button className="btn icon ghost" onClick={reset} aria-label="Reset view"><Maximize2 size={15} /></button>
      </div>

      <svg
        viewBox={`0 0 ${VB} ${VB}`}
        style={{
          width: '100%', height, background: 'var(--bg-sunken)',
          borderRadius: 'var(--radius)', border: '1px solid var(--surface-border)',
          cursor: drag.current ? 'grabbing' : 'grab', touchAction: 'none',
        }}
        onWheel={onWheel}
        onMouseDown={onDown}
        onMouseMove={onMove}
        onMouseUp={onUp}
        onMouseLeave={onUp}
        onClick={onBgClick}
      >
        <g transform={`translate(${panPos.x} ${panPos.y}) scale(${zoom})`}>
          {/* community territories */}
          {hulls.map((h) => (
            h.single ? (
              <circle key={`h${h.c}`} cx={h.single.x} cy={h.single.y} r={26}
                fill={communityColor(h.c)} fillOpacity={dimmed(h.c) ? 0.03 : 0.10}
                stroke={communityColor(h.c)} strokeOpacity={dimmed(h.c) ? 0.08 : 0.30}
                style={{ transition: 'fill-opacity 0.4s ease, stroke-opacity 0.4s ease' }} />
            ) : (
              <path key={`h${h.c}`} d={h.d}
                fill={communityColor(h.c)} fillOpacity={dimmed(h.c) ? 0.03 : 0.10}
                stroke={communityColor(h.c)} strokeOpacity={dimmed(h.c) ? 0.08 : 0.30}
                strokeWidth={2} strokeLinejoin="round"
                style={{ transition: 'fill-opacity 0.4s ease, stroke-opacity 0.4s ease' }} />
            )
          ))}

          {/* edges */}
          {frame.edges.map(([u, v], i) => {
            const a = nodeById.get(u);
            const b = nodeById.get(v);
            if (!a || !b) return null;
            const isAdded = view.edgesHot && (addedSet.has(`${u}-${v}`) || addedSet.has(`${v}-${u}`));
            const faded = sel !== null && communities[u] !== sel && communities[v] !== sel;
            return (
              <line key={i}
                x1={px(a.x)} y1={py(a.y)} x2={px(b.x)} y2={py(b.y)}
                stroke={isAdded ? 'var(--accent)' : 'var(--surface-border)'}
                strokeWidth={isAdded ? 4 : 1.2}
                strokeOpacity={faded ? 0.12 : isAdded ? 0.95 : 0.5} />
            );
          })}

          {/* deleted edges (dashed) */}
          {view.edgesHot && frame.deleted.map(([u, v], i) => {
            const a = nodeById.get(u);
            const b = nodeById.get(v);
            if (!a || !b) return null;
            return (
              <line key={`d${i}`}
                x1={px(a.x)} y1={py(a.y)} x2={px(b.x)} y2={py(b.y)}
                stroke="var(--bad)" strokeWidth={3} strokeDasharray="6 6" strokeOpacity={0.9} />
            );
          })}

          {/* affected region — concentric hop-layers (adaptive radius) */}
          {view.affected && nodes.map((n) => {
            const layer = layerOf.get(n.id);
            if (layer === undefined) return null;
            if (sel !== null && communities[n.id] !== sel) return null;
            const isSeed = layer === 0;
            const r = (movedSet.has(n.id) ? 13 : 9) + 7 + layer * 3;
            return (
              <circle key={`a${n.id}`} cx={px(n.x)} cy={py(n.y)} r={r}
                className="isl-ring"
                fill={isSeed ? 'var(--warn)' : 'none'} fillOpacity={isSeed ? 0.14 : 0}
                stroke={isSeed ? 'var(--warn)' : 'var(--accent)'}
                strokeWidth={isSeed ? 3 : 2}
                strokeOpacity={Math.max(0.3, 0.9 - layer * 0.22)}
                strokeDasharray={layer >= 2 ? '4 4' : undefined}
                style={{ animationDelay: `${layer * 0.18}s`, transition: 'stroke-opacity 0.4s ease' }} />
            );
          })}

          {/* nodes */}
          {nodes.map((n) => {
            const c = communities[n.id] ?? 0;
            const isMoved = view.moves && movedSet.has(n.id);
            const r = isMoved ? 13 : 9;
            const isDim = dimmed(c);
            return (
              <g key={n.id}
                 style={{ cursor: 'pointer', opacity: isDim ? 0.25 : 1, transition: 'opacity 0.3s ease' }}
                 onClick={(e) => { e.stopPropagation(); if (!drag.current?.moved) setSel(sel === c ? null : c); }}
                 onMouseEnter={() => setHover({ id: n.id, x: px(n.x), y: py(n.y) })}
                 onMouseLeave={() => setHover(null)}>
                {isMoved && (
                  <circle cx={px(n.x)} cy={py(n.y)} r={r + 4} className="isl-pulse"
                    fill="none" stroke="var(--text)" strokeWidth={2} strokeOpacity={0.5} />
                )}
                <circle
                  cx={px(n.x)} cy={py(n.y)} r={r}
                  fill={communityColor(c)}
                  stroke={isMoved ? 'var(--text)' : '#ffffff'}
                  strokeWidth={isMoved ? 3 : 1.5}
                  strokeOpacity={isMoved ? 0.9 : 0.7}
                  style={{ transition: 'fill 0.5s ease, r 0.25s ease' }} />
              </g>
            );
          })}
        </g>

        {hover && (
          <g transform={`translate(${panPos.x} ${panPos.y}) scale(${zoom})`} pointerEvents="none">
            <rect x={hover.x + 12} y={hover.y - 44} width={190} height={62} rx={6}
              fill="var(--bg-elevated)" stroke="var(--surface-border)" />
            <text x={hover.x + 22} y={hover.y - 24} fontSize={17} fill="var(--text)" fontWeight={600}>
              Node {hover.id}
            </text>
            <text x={hover.x + 22} y={hover.y - 4} fontSize={15} fill="var(--text-muted)">
              Community {communities[hover.id]}
              {movedSet.has(hover.id) ? ' · moved' : ''}
            </text>
            {layerOf.has(hover.id) && (
              <text x={hover.x + 22} y={hover.y + 14} fontSize={13} fill="var(--accent)">
                {layerOf.get(hover.id) === 0 ? 'seed (changed edge)' : `affected · hop ${layerOf.get(hover.id)}`}
              </text>
            )}
          </g>
        )}
      </svg>

      {maxLayer >= 1 && view.affected && (
        <div className="faint" style={{ fontSize: '0.75rem', marginTop: 6, textAlign: 'right' }}>
          Affected radius: {maxLayer + 1} hop-layer{maxLayer ? 's' : ''} · seed → 1-hop{maxLayer >= 2 ? ' → adaptive expansion' : ''}
        </div>
      )}
    </div>
  );
};

export default GraphCanvas;
