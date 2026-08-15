// TypeScript types mirroring the backend API contract.
// See backend/app/schemas.py and .agents/skills/api-contracts/SKILL.md.

export type ModelStatusValue = "not_loaded" | "loading" | "ready" | "error";

export interface DeviceInfo {
  cuda_available: boolean;
  device_count: number;
  gpu_name: string | null;
  cuda_version: string | null;
  torch_version: string | null;
  device: string;
}

export interface ModelStatus {
  key: string;
  name: string;
  version: string;
  kind: string;
  revision: string | null;
  status: ModelStatusValue;
  device: string | null;
  loaded: boolean;
  loaded_at: number | null;
  error: string | null;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  app_version: string;
  python_version: string;
  environment: string;
  feature_version: string | null;
  device: DeviceInfo;
  models: Record<string, ModelStatus>;
  timestamp: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown> | null;
  };
}

export type EvidenceValue = "low" | "medium" | "high" | "uncertain";

export interface SignalEvidence {
  feature: string;
  value: number;
  baseline_mean: number;
  baseline_std: number;
  z_score: number | null;
  direction: "lower" | "higher" | "typical" | "unknown";
  evidence: EvidenceValue;
  summary: string;
}

export interface SentenceEvidence {
  index: number;
  text: string;
  signals: SignalEvidence[];
  signal_count: number;
  evidence_strength: EvidenceValue;
  summary: string;
}

export interface PassageEvidence {
  sentence_indices: number[];
  signals: SignalEvidence[];
  signal_count: number;
  evidence_strength: EvidenceValue;
  summary: string;
}

export interface AnalysisSummary {
  sentence_count: number;
  signal_sentences: number;
  high: number;
  medium: number;
  low: number;
  uncertain: number;
}

export interface AnalysisResult {
  analysis_id: string;
  timestamp: string;
  feature_version: string;
  model_version: string;
  baselines_version: string;
  dataset_version: string | null;
  essay_word_count: number;
  essay_token_count: number;
  length_bucket: string;
  baseline_bucket: string;
  summary: AnalysisSummary;
  sentences: SentenceEvidence[];
  passages: PassageEvidence[];
  limitations: string[];
}