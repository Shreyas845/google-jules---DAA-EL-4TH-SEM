/** Playback controls + hook for stepping through trace frames. */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { SkipBack, SkipForward, Play, Pause, RotateCcw } from 'lucide-react';

export function usePlayback(numFrames: number, intervalMs = 1400) {
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const clear = () => {
    if (timer.current) { clearInterval(timer.current); timer.current = null; }
  };

  useEffect(() => {
    if (!playing) { clear(); return; }
    timer.current = setInterval(() => {
      setIndex((i) => {
        if (i >= numFrames - 1) { setPlaying(false); return i; }
        return i + 1;
      });
    }, intervalMs);
    return clear;
  }, [playing, numFrames, intervalMs]);

  // Clamp when the trace changes size.
  useEffect(() => { setIndex((i) => Math.min(i, Math.max(0, numFrames - 1))); }, [numFrames]);

  const next = useCallback(() => setIndex((i) => Math.min(numFrames - 1, i + 1)), [numFrames]);
  const prev = useCallback(() => setIndex((i) => Math.max(0, i - 1)), []);
  const reset = useCallback(() => { setPlaying(false); setIndex(0); }, []);
  const toggle = useCallback(() => setPlaying((p) => !p), []);
  const goto = useCallback((i: number) => { setPlaying(false); setIndex(i); }, []);

  return { index, playing, next, prev, reset, toggle, goto, setPlaying };
}

type ControlsProps = {
  index: number;
  numFrames: number;
  playing: boolean;
  onPrev: () => void;
  onNext: () => void;
  onToggle: () => void;
  onReset: () => void;
  onScrub: (i: number) => void;
  labels?: string[];
};

export const PlaybackControls: React.FC<ControlsProps> = ({
  index, numFrames, playing, onPrev, onNext, onToggle, onReset, onScrub, labels,
}) => (
  <div className="card" style={{ padding: 14 }}>
    <div className="row between" style={{ marginBottom: 10 }}>
      <div className="row" style={{ gap: 8 }}>
        <button className="btn icon" onClick={onReset} disabled={index === 0 && !playing} aria-label="Reset"><RotateCcw size={16} /></button>
        <button className="btn icon" onClick={onPrev} disabled={index === 0} aria-label="Previous"><SkipBack size={16} /></button>
        <button className="btn primary" onClick={onToggle} style={{ minWidth: 108 }}>
          {playing ? <><Pause size={16} /> Pause</> : <><Play size={16} /> Autoplay</>}
        </button>
        <button className="btn icon" onClick={onNext} disabled={index >= numFrames - 1} aria-label="Next"><SkipForward size={16} /></button>
      </div>
      <div className="faint mono" style={{ fontSize: '0.82rem' }}>
        Frame {index + 1} / {numFrames}
        {labels && labels[index] ? ` · ${labels[index]}` : ''}
      </div>
    </div>
    <input
      type="range" min={0} max={Math.max(0, numFrames - 1)} value={index}
      onChange={(e) => onScrub(Number(e.target.value))}
      style={{ width: '100%', accentColor: 'var(--accent)' }}
    />
  </div>
);
