-- Independent judge + banking-check scores for demo lab report cards

CREATE TABLE IF NOT EXISTS eval_scores (
    score_key TEXT PRIMARY KEY,
    cache_key TEXT,
    preset TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_id TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    judge_prompt_version TEXT NOT NULL,
    judge_model TEXT,
    target_profile_json TEXT NOT NULL,
    trait_scores_json TEXT NOT NULL,
    banking_checks_json TEXT NOT NULL,
    judge_raw_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_eval_scores_lookup
    ON eval_scores (preset, customer_id, provider, model_id, prompt_version);

CREATE INDEX IF NOT EXISTS idx_eval_scores_model
    ON eval_scores (provider, model_id, prompt_version);
