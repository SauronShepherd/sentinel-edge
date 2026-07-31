// generated; do not edit

export interface AnalyzerV1 {
  bundle_id: string;
  inputs: unknown[];
  limitations: unknown[];
  source_spans: unknown[];
  claims: unknown[];
  media_records: unknown[];
  derivation: Record<string, unknown>;
  trust_factors: Record<string, unknown>;
}

export interface ApiV1 {
  resource: string;
  pagination: Record<string, unknown>;
  cursor: unknown;
  audit_context: Record<string, unknown>;
  errors: unknown[];
}

export interface CollectorV1 {
  observation_id: string;
  observed_at: string;
  clock_quality: unknown;
  replay: boolean;
  units: string;
  source_health: Record<string, unknown>;
  acquisition_audit: Record<string, unknown>;
  policy: Record<string, unknown>;
}

export interface IncidentV1 {
  incident_id: string;
  expected_version: number;
  projection_version: number;
  inputs: unknown[];
  commands: unknown[];
  transitions: unknown[];
  reviews: unknown[];
  effects: unknown[];
}

export interface RuntimeV1 {
  job_id: string;
  model_hash: string;
  profile_hash: string;
  deterministic: boolean;
  abstained: boolean;
  results: unknown[];
  hazard_inference: Record<string, unknown>;
  lifecycle: Record<string, unknown>;
  health: Record<string, unknown>;
  benchmark_samples: unknown[];
}

