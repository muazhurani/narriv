export type Platform =
  | "linkedin"
  | "twitter"
  | "x"
  | "instagram"
  | "threads"
  | "general";

export type OptimizeRequest = {
  topic: string;
  source_material?: string;
  platform: Platform;
  audience: string;
  goal: string;
  tone: string;
  constraints: {
    max_chars?: number;
    include_cta: boolean;
    hashtag_limit?: number;
    hard_max_length?: number;
  };
  candidate_count: number;
  refine_winner: boolean;
};

export type CandidateVariant = {
  id: string;
  strategy: string;
  tone: string;
  text: string;
};

export type ScoreOnlyRequest = {
  platform: Platform;
  tone?: string;
  constraints: {
    max_chars?: number;
    include_cta: boolean;
    hashtag_limit?: number;
    hard_max_length?: number;
  };
  candidates: CandidateVariant[];
};

export type RankedScores = {
  brainscore: number;
  hook_score: number;
  sustained_response_score: number;
  clarity_stability_score: number;
  end_strength_score: number;
  novelty_spike_score: number;
  platform_fit_score: number;
  readability_score: number;
  constraint_compliance_score: number;
  final_score: number;
};

export type CandidateDiagnostics = {
  strongest_sentence: number | null;
  weakest_sentence: number | null;
  dropoff_after_sentence: number | null;
};

export type RawFeatures = {
  raw_shape_t: number;
  raw_shape_v: number;
  global_mean: number;
  global_peak: number;
  global_std: number;
  early_mean: number;
  mid_mean: number;
  late_mean: number;
  dropoff: number;
  sustainability: number;
  spikiness: number;
  variance_over_time: number;
  peak_time: number;
};

export type SentenceFeature = {
  sentence_index: number;
  text: string;
  start_t: number;
  end_t: number;
  mean_energy: number;
  peak_energy: number;
  relative_contribution: number;
};

export type RankedCandidate = {
  id: string;
  strategy: string;
  tone: string;
  text: string;
  scores: RankedScores;
  diagnostics: CandidateDiagnostics;
  reason: string;
  raw_features: RawFeatures;
  sentence_features: SentenceFeature[];
  temporal_energy: number[];
};

export type OptimizeResponse = {
  run_id: string;
  platform: string;
  candidates: RankedCandidate[];
  recommended_candidate_id: string;
  winner_text: string;
  explanation: string;
  llm_model: string;
  log_file_path: string | null;
  experimental_score: boolean;
};

export type ScoreOnlyResponse = {
  run_id: string;
  platform: string;
  candidates: RankedCandidate[];
  recommended_candidate_id: string;
  winner_text: string;
  explanation: string;
  llm_model: string;
  log_file_path: string | null;
  experimental_score: boolean;
};

export type RefineRequest = {
  platform: Platform;
  tone?: string;
  constraints: {
    max_chars?: number;
    include_cta: boolean;
    hashtag_limit?: number;
    hard_max_length?: number;
  };
  text: string;
  refinement_goal: string;
};

export type RefineResponse = {
  final_text: string;
  explanation: string;
  llm_model: string;
  log_file_path: string | null;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function optimizePosts(
  payload: OptimizeRequest,
): Promise<OptimizeResponse> {
  return requestJson<OptimizeResponse>("/optimize", payload);
}

export async function scoreCandidates(
  payload: ScoreOnlyRequest,
): Promise<ScoreOnlyResponse> {
  return requestJson<ScoreOnlyResponse>("/optimize/score", payload);
}

export async function refinePost(
  payload: RefineRequest,
): Promise<RefineResponse> {
  return requestJson<RefineResponse>("/refine", payload);
}

async function requestJson<TResponse>(
  path: string,
  payload: unknown,
): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const error = (await response.json()) as { detail?: string };
      if (error.detail) {
        message = error.detail;
      }
    } catch {
      // Keep the generic message if the response is not JSON.
    }
    throw new Error(message);
  }

  return (await response.json()) as TResponse;
}
