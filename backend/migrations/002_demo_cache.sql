-- Cached preset × fixture × scenario demo replies (no secrets)

CREATE TABLE IF NOT EXISTS demo_cache (
    cache_key TEXT PRIMARY KEY,
    preset TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_id TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    reply TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_demo_cache_lookup
    ON demo_cache (preset, customer_id, provider, model_id, prompt_version);
