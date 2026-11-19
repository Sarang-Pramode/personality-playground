export type TraitKey =
  | "exploration"
  | "structure"
  | "energy"
  | "warmth"
  | "steadiness";

export type TraitProfile = Record<TraitKey, number>;

export type PresetName = "balanced" | "concise" | "explorer" | "supportive";

export const TRAIT_META: {
  key: TraitKey;
  label: string;
  description: string;
}[] = [
  {
    key: "exploration",
    label: "Exploration",
    description: "How many verified alternatives to surface",
  },
  {
    key: "structure",
    label: "Structure & Thoroughness",
    description: "Brevity vs organized eligibility/steps",
  },
  {
    key: "energy",
    label: "Conversational Energy",
    description: "Reserved → animated (still professional)",
  },
  {
    key: "warmth",
    label: "Warmth & Accommodation",
    description: "Direct tact → validating (no flattery)",
  },
  {
    key: "steadiness",
    label: "Emotional Steadiness",
    description: "Calm → explicit grounding under stress",
  },
];

export const LEVELS = [1, 3, 5, 7, 9] as const;

export const LEVEL_LABELS: Record<number, string> = {
  1: "Very Low",
  3: "Low",
  5: "Neutral",
  7: "High",
  9: "Very High",
};

export const PRESETS: Record<PresetName, TraitProfile> = {
  balanced: {
    exploration: 5,
    structure: 7,
    energy: 5,
    warmth: 7,
    steadiness: 9,
  },
  concise: {
    exploration: 3,
    structure: 3,
    energy: 3,
    warmth: 5,
    steadiness: 9,
  },
  explorer: {
    exploration: 9,
    structure: 7,
    energy: 5,
    warmth: 7,
    steadiness: 9,
  },
  supportive: {
    exploration: 5,
    structure: 7,
    energy: 5,
    warmth: 9,
    steadiness: 9,
  },
};

export type ModelInfo = {
  provider: "openai" | "google" | "demo";
  model_id: string;
  label: string;
  available: boolean;
};

export type FixtureCustomer = {
  customer_id: "customer_A" | "customer_B";
  display_name: string;
  segment: string;
  available_balance: number;
  currency: string;
};

export type Scenario = {
  scenario_id: string;
  title: string;
  description: string;
  suggested_prompt: string;
  fixture_ids: string[];
  category?: string;
};

export type TraitCard = {
  key: TraitKey;
  label: string;
  level: number;
  level_name: string;
  description: string;
};

export type PreviewResponse = {
  profile: TraitProfile;
  preset: string | null;
  policy_version: string;
  behavior_summary: string;
  trait_cards?: TraitCard[];
  style_guidance: string;
  system_prompt: string;
  map_position: { x: number; y: number };
  radar: { trait: string; key: TraitKey; value: number }[];
};

export type TraitJudgment = {
  trait: TraitKey;
  score: number | null;
  cited_behaviors: string[];
  rationale: string;
  unable_to_judge: boolean;
  abstain_reason?: string | null;
};

export type BankingCheck = {
  check_id: string;
  passed: boolean;
  detail: string;
  evidence?: string[];
};

export type EvalScoreEntry = {
  score_key?: string;
  scenario_id: string;
  judged: boolean;
  skipped_reason?: string | null;
  judge_model?: string | null;
  judge_prompt_version?: string;
  target_profile?: TraitProfile;
  traits: TraitJudgment[];
  banking_checks: BankingCheck[];
  measured_profile?: TraitProfile | null;
  overall_notes?: string | null;
};

export type EvalAggregate = {
  scored_runs: number;
  judged_runs: number;
  trait_means: Partial<Record<TraitKey, number | null>>;
  measured_profile_approx?: TraitProfile | null;
  banking_pass_rate: number | null;
  banking_passed: number;
  banking_total: number;
};

export type ChatMetadata = {
  profile: TraitProfile;
  preset: string | null;
  prompt_version: string;
  policy_version: string;
  fixture_id: string;
  scenario_id: string | null;
  model_id: string | null;
  provider: string;
  mode: "live" | "scripted_demo" | "error";
  model_label?: string;
  tool_traces: {
    tool: string;
    arguments: Record<string, unknown>;
    result: unknown;
  }[];
  system_prompt: string;
  behavior_summary: string;
  run_id: string;
};

export type ChatResponse = {
  reply: string;
  run_id: string;
  session_id: string;
  error: string | null;
  metadata: ChatMetadata;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  metadata?: ChatMetadata;
};

export type SavedProfile = {
  id: string;
  name: string;
  profile: TraitProfile;
  preset: PresetName | "custom";
  updatedAt: string;
};

export type OpenAIKeyExpiry = {
  expires_at: string;
  days_remaining: number;
  warn: boolean;
  expired: boolean;
};

export type DemoCacheEntry = {
  cache_key: string | null;
  preset: string;
  customer_id: string;
  scenario_id: string;
  provider: string;
  model_id: string;
  prompt_version: string;
  reply: string;
  metadata: {
    profile?: TraitProfile;
    preset?: string | null;
    prompt_version?: string;
    fixture_id?: string;
    scenario_id?: string | null;
    model_id?: string | null;
    provider?: string;
    mode?: string;
    model_label?: string;
    behavior_summary?: string;
    tool_trace_summary?: { tool: string; ok: boolean; error?: string | null }[];
    run_id?: string;
  };
  created_at?: string;
  updated_at?: string;
  cached?: boolean;
};

export type DemoCacheResponse = {
  preset: string;
  customer_id: string;
  provider: string;
  model_id: string;
  prompt_version: string;
  results: {
    scenario_id: string;
    title: string;
    suggested_prompt: string;
    category?: string;
    hit: boolean;
    entry: DemoCacheEntry | null;
    score?: EvalScoreEntry | null;
  }[];
  cached_count: number;
  scored_count?: number;
  total: number;
  aggregate?: EvalAggregate;
  model_aggregate?: EvalAggregate;
  judge_available?: boolean;
  judge_prompt_version?: string;
};

export type DemoRunResponse = {
  preset: string;
  customer_id: string;
  provider: string;
  model_id: string;
  prompt_version: string;
  force: boolean;
  results: {
    scenario_id: string;
    title: string;
    suggested_prompt: string;
    category?: string;
    cache_hit: boolean;
    entry: DemoCacheEntry | null;
    error: string | null;
    score?: EvalScoreEntry | null;
  }[];
  cache_hits: number;
  cache_misses: number;
  scored_count?: number;
  total: number;
  aggregate?: EvalAggregate;
  model_aggregate?: EvalAggregate;
  judge_available?: boolean;
  judge_prompt_version?: string;
};

export type DemoScoresResponse = {
  preset: string;
  customer_id: string;
  provider: string;
  model_id: string;
  prompt_version: string;
  judge_prompt_version: string;
  judge_available: boolean;
  cards: {
    scenario_id: string;
    title: string;
    category?: string;
    suggested_prompt: string;
    score: EvalScoreEntry | null;
  }[];
  aggregate: EvalAggregate;
  model_aggregate: EvalAggregate;
  scored_count: number;
  total: number;
};
