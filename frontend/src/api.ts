/**
 * Centralized, typed API client for the ISL Dashboard backend.
 * Every backend call lives here so base URL, paths, and response shapes are in one place.
 */
import axios from 'axios';

export const API_URL =
  process.env.REACT_APP_API_URL ?? 'http://127.0.0.1:8000/api';

// ---------------------------------------------------------------------------
// Validations
// ---------------------------------------------------------------------------
export type ValidationSet = {
  A: unknown | null;
  B: unknown | null;
  C: unknown | null;
};

export async function getValidations(): Promise<ValidationSet> {
  const { data } = await axios.get<ValidationSet>(`${API_URL}/validations`);
  return data;
}

export function imageUrl(name: string): string {
  return `${API_URL}/images/${name}`;
}

// ---------------------------------------------------------------------------
// Configs & stored results
// ---------------------------------------------------------------------------
export type ExperimentConfigSummary = {
  name: string;
  experiment_id: string;
  dataset_type: string;
  n: number | null;
  mu: number | null;
  num_batches: number | null;
  seeds: number;
  baselines: string[];
};

export async function getConfigs(): Promise<ExperimentConfigSummary[]> {
  const { data } = await axios.get<{ configs: ExperimentConfigSummary[] }>(
    `${API_URL}/configs`
  );
  return data.configs;
}

/** One batch's aggregated value: mean + std across seeds. */
export type MetricStat = { mean: number; std: number };

/** A per-batch aggregated record for a method. */
export type AggregateBatch = {
  batch_idx: number;
  algorithm?: string;
  [metric: string]: number | string | MetricStat | undefined;
};

export type AggregateResults = Record<string, AggregateBatch[]>;

export type StoredResult = {
  name: string;
  aggregate: AggregateResults;
  metadata: { total_runtime_s?: number; config?: unknown } | null;
  precomputed: boolean;
};

export async function getResultNames(): Promise<string[]> {
  const { data } = await axios.get<{ results: string[] }>(`${API_URL}/results`);
  return data.results;
}

export async function getResult(name: string): Promise<StoredResult> {
  const { data } = await axios.get<StoredResult>(`${API_URL}/results/${name}`);
  return data;
}

// ---------------------------------------------------------------------------
// Experiment execution (background job + polling)
// ---------------------------------------------------------------------------
export type JobStatus = {
  job_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress: number;
  message: string;
  config_name: string;
  results: { aggregate: AggregateResults; output_dir: string } | null;
  error: string | null;
};

export async function runExperiment(configName: string): Promise<{ job_id: string }> {
  const { data } = await axios.post<{ job_id: string }>(`${API_URL}/experiment/run`, {
    config_name: configName,
  });
  return data;
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const { data } = await axios.get<JobStatus>(`${API_URL}/experiment/status/${jobId}`);
  return data;
}

// ---------------------------------------------------------------------------
// Interactive graph trace
// ---------------------------------------------------------------------------
export type TraceNode = { id: number; x: number; y: number };

export type FrameMetrics = {
  significance: number;
  community_count: number;
  nodes_moved: number;
  affected_size: number;
  time_ms: number;
  modularity?: number;
  churn_rate?: number;
  periodic_fired?: boolean;
};

export type TraceFrame = {
  batch_idx: number;
  stage: 'initial' | 'updated';
  edges: [number, number][];
  communities: number[];
  communities_before?: number[];
  added: [number, number][];
  deleted: [number, number][];
  affected: number[];
  /** Ordered hop-layers of the affected region: [seeds, 1-hop, adaptive-hop-2, …]. */
  affected_layers: number[][];
  /** Endpoints of the changed edges — the seeds the affected region grew from. */
  seeds: number[];
  moved: number[];
  metrics: FrameMetrics;
};

export type GraphTrace = {
  meta: {
    n: number;
    num_batches: number;
    batch_size: number;
    mu: number;
    seed: number;
    variant: string;
  };
  nodes: TraceNode[];
  frames: TraceFrame[];
};

export type TraceParams = {
  n?: number;
  batches?: number;
  batch_size?: number;
  mu?: number;
  seed?: number;
  variant?: string;
};

export async function getGraphTrace(params: TraceParams = {}): Promise<GraphTrace> {
  const { data } = await axios.get<GraphTrace>(`${API_URL}/graph/trace`, { params });
  return data;
}
