/**
 * Shared loader for ISL execution traces.
 *
 * Both the Graph Viewer (interactive exploration) and Demo Mode (guided simulation) need the
 * same thing: fetch a real trace for a set of parameters, expose loading/error state, and allow
 * re-running with new parameters. This hook is that single source so the two pages don't
 * duplicate the fetch/error plumbing.
 */
import { useCallback, useEffect, useState } from 'react';
import { getGraphTrace, GraphTrace, TraceParams } from '../api';

export type UseTrace = {
  trace: GraphTrace | null;
  loading: boolean;
  error: string | null;
  params: TraceParams;
  setParams: (p: Partial<TraceParams>) => void;
  reload: () => void;
};

const ERROR_MSG = 'Could not reach the backend. Start it with: cd backend && uvicorn main:app';

export function useTrace(initial: TraceParams): UseTrace {
  const [params, setParamsState] = useState<TraceParams>(initial);
  const [trace, setTrace] = useState<GraphTrace | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setTrace(await getGraphTrace(params));
    } catch {
      setError(ERROR_MSG);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, nonce]);

  useEffect(() => {
    load();
  }, [load]);

  const setParams = useCallback(
    (p: Partial<TraceParams>) => setParamsState((prev) => ({ ...prev, ...p })),
    []
  );
  const reload = useCallback(() => setNonce((n) => n + 1), []);

  return { trace, loading, error, params, setParams, reload };
}
