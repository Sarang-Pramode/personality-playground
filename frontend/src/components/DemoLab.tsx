import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getDemoCache,
  judgeDemoCache,
  runDemoScenarios,
} from "../lib/api";
import {
  PRESETS,
  type DemoCacheResponse,
  type DemoRunResponse,
  type EvalAggregate,
  type EvalScoreEntry,
  type FixtureCustomer,
  type ModelInfo,
  type PresetName,
  type Scenario,
  type TraitKey,
  type TraitProfile,
} from "../types";
import { Badge, Button, FieldLabel, Panel, Select } from "./ui";

type Props = {
  models: ModelInfo[];
  customers: FixtureCustomer[];
  scenarios: Scenario[];
  defaultProvider: string;
  defaultModelId: string | null;
  onMeasuredChange?: (measured: TraitProfile | null) => void;
};

function bankingSummary(score: EvalScoreEntry | null | undefined) {
  const checks = score?.banking_checks ?? [];
  if (!checks.length) return null;
  const passed = checks.filter((c) => c.passed).length;
  return `${passed}/${checks.length} banking checks`;
}

function traitScoreLine(score: EvalScoreEntry | null | undefined) {
  if (!score) return "No scores yet";
  if (!score.judged) {
    return score.skipped_reason || "Personality judge skipped";
  }
  return (score.traits || [])
    .map((t) => {
      if (t.unable_to_judge || t.score == null) return `${t.trait}: —`;
      return `${t.trait}: ${t.score}`;
    })
    .join(" · ");
}

function AggregateStrip({
  label,
  aggregate,
}: {
  label: string;
  aggregate?: EvalAggregate | null;
}) {
  if (!aggregate || !aggregate.scored_runs) return null;
  const means = aggregate.trait_means || {};
  const keys = Object.keys(means) as TraitKey[];
  return (
    <div className="rounded-md border border-teal-100 bg-teal-50/50 px-3 py-2 text-xs text-teal-950">
      <div className="mb-1 font-semibold">{label}</div>
      <div className="flex flex-wrap gap-2">
        {keys.map((k) => (
          <Badge key={k} tone={means[k] == null ? "neutral" : "accent"}>
            {k} {means[k] == null ? "—" : means[k]}
          </Badge>
        ))}
        {aggregate.banking_pass_rate != null ? (
          <Badge tone="ok">
            banking {(aggregate.banking_pass_rate * 100).toFixed(0)}% (
            {aggregate.banking_passed}/{aggregate.banking_total})
          </Badge>
        ) : null}
      </div>
      {!aggregate.judged_runs ? (
        <p className="mt-1 text-[11px] text-amber-800">
          Banking checks only — set OPENAI_API_KEY + JUDGE_MODEL for personality
          scores (no fabricated Measured radar).
        </p>
      ) : null}
    </div>
  );
}

export function DemoLab({
  models,
  customers,
  scenarios,
  defaultProvider,
  defaultModelId,
  onMeasuredChange,
}: Props) {
  const [open, setOpen] = useState(true);
  const [preset, setPreset] = useState<PresetName>("balanced");
  const [customerId, setCustomerId] = useState("customer_A");
  const [selectionOverride, setSelectionOverride] = useState<{
    provider: string;
    modelId: string | null;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cacheView, setCacheView] = useState<DemoCacheResponse | null>(null);
  const [lastRun, setLastRun] = useState<DemoRunResponse | null>(null);

  const provider = selectionOverride?.provider ?? defaultProvider;
  const modelId = selectionOverride?.modelId ?? defaultModelId;

  const modelOptions = useMemo(() => {
    return models.length
      ? models
      : [
          {
            provider: "demo" as const,
            model_id: "scripted-demo",
            label: "Scripted demo mode (no LLM)",
            available: true,
          },
        ];
  }, [models]);

  const selectedKey = `${provider}:${modelId ?? ""}`;

  const loadCache = useCallback(async () => {
    if (!modelId) return;
    setError(null);
    try {
      const data = await getDemoCache({
        preset,
        customer_id: customerId,
        provider,
        model_id: modelId,
      });
      setCacheView(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load demo cache");
    }
  }, [preset, customerId, provider, modelId]);

  useEffect(() => {
    if (!open || !modelId) return;
    void loadCache();
  }, [open, loadCache, modelId]);

  const measuredFromAgg = useMemo(() => {
    const agg =
      lastRun?.aggregate?.measured_profile_approx ||
      cacheView?.aggregate?.measured_profile_approx ||
      null;
    return agg ?? null;
  }, [lastRun, cacheView]);

  useEffect(() => {
    onMeasuredChange?.(measuredFromAgg);
  }, [measuredFromAgg, onMeasuredChange]);

  async function runAll(force: boolean) {
    if (!modelId || busy) return;
    setBusy(true);
    setError(null);
    try {
      const data = await runDemoScenarios({
        preset,
        customer_id: customerId,
        provider,
        model_id: modelId,
        force,
        auto_judge: true,
      });
      setLastRun(data);
      await loadCache();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo run failed");
    } finally {
      setBusy(false);
    }
  }

  async function scoreCached() {
    if (!modelId || busy) return;
    setBusy(true);
    setError(null);
    try {
      await judgeDemoCache({
        preset,
        customer_id: customerId,
        provider,
        model_id: modelId,
        force: false,
      });
      await loadCache();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Judge run failed");
    } finally {
      setBusy(false);
    }
  }

  const displayRows = useMemo(() => {
    if (lastRun && lastRun.preset === preset && lastRun.customer_id === customerId) {
      return lastRun.results.map((r) => ({
        scenario_id: r.scenario_id,
        title: r.title,
        suggested_prompt: r.suggested_prompt,
        category: r.category,
        hit: r.cache_hit,
        reply: r.entry?.reply ?? null,
        meta: r.entry?.metadata ?? null,
        error: r.error,
        score: r.score ?? null,
        fromRun: true,
      }));
    }
    if (!cacheView) {
      return scenarios.map((s) => ({
        scenario_id: s.scenario_id,
        title: s.title,
        suggested_prompt: s.suggested_prompt,
        category: s.category,
        hit: false,
        reply: null,
        meta: null,
        error: null,
        score: null,
        fromRun: false,
      }));
    }
    return cacheView.results.map((r) => ({
      scenario_id: r.scenario_id,
      title: r.title,
      suggested_prompt: r.suggested_prompt,
      category: r.category,
      hit: r.hit,
      reply: r.entry?.reply ?? null,
      meta: r.entry?.metadata ?? null,
      error: null,
      score: r.score ?? null,
      fromRun: false,
    }));
  }, [cacheView, lastRun, preset, customerId, scenarios]);

  const aggregate =
    lastRun?.aggregate ?? cacheView?.aggregate ?? null;
  const modelAggregate =
    lastRun?.model_aggregate ?? cacheView?.model_aggregate ?? null;

  return (
    <section className="mx-auto w-full max-w-[1600px] px-3 pb-8" id="demo-lab">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold tracking-wide text-slate-900">
            Demo lab
          </h2>
          <p className="text-xs text-[var(--muted)]">
            Cached runs + automatic report cards (independent judges · banking
            checks). Below the studio — three-column layout unchanged.
          </p>
        </div>
        <Button variant="ghost" onClick={() => setOpen((v) => !v)}>
          {open ? "Collapse" : "Expand"}
        </Button>
      </div>

      {open ? (
        <Panel
          title="Preset scenario cache & report cards"
          subtitle="Run all scenarios to cache replies and auto-score. Scores persist in Postgres."
          actions={
            <div className="flex flex-wrap gap-2">
              <Button
                variant="secondary"
                disabled={busy || !modelId}
                onClick={() => void loadCache()}
              >
                Load cache
              </Button>
              <Button
                disabled={busy || !modelId}
                onClick={() => void runAll(false)}
              >
                {busy ? "Running…" : "Run all + score"}
              </Button>
              <Button
                variant="secondary"
                disabled={busy || !modelId}
                onClick={() => void runAll(true)}
              >
                Refresh (re-run)
              </Button>
              <Button
                variant="secondary"
                disabled={busy || !modelId}
                onClick={() => void scoreCached()}
              >
                Score cached only
              </Button>
            </div>
          }
        >
          <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <FieldLabel>Preset</FieldLabel>
              <Select
                value={preset}
                onChange={(e) => {
                  setPreset(e.target.value as PresetName);
                  setLastRun(null);
                }}
                aria-label="Demo lab preset"
              >
                {(Object.keys(PRESETS) as PresetName[]).map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <FieldLabel>Customer fixture</FieldLabel>
              <Select
                value={customerId}
                onChange={(e) => {
                  setCustomerId(e.target.value);
                  setLastRun(null);
                }}
                aria-label="Demo lab customer"
              >
                {customers.map((c) => (
                  <option key={c.customer_id} value={c.customer_id}>
                    {c.display_name} ({c.customer_id})
                  </option>
                ))}
              </Select>
            </div>
            <div className="sm:col-span-2">
              <FieldLabel hint="OpenAI list is allowlisted experiment models">
                Model
              </FieldLabel>
              <Select
                value={selectedKey}
                onChange={(e) => {
                  const [p, ...rest] = e.target.value.split(":");
                  setSelectionOverride({
                    provider: p,
                    modelId: rest.join(":") || null,
                  });
                  setLastRun(null);
                }}
                aria-label="Demo lab model"
              >
                {modelOptions.map((m) => (
                  <option
                    key={`${m.provider}:${m.model_id}`}
                    value={`${m.provider}:${m.model_id}`}
                    disabled={!m.available && m.provider !== "demo"}
                  >
                    {m.label}
                  </option>
                ))}
              </Select>
            </div>
          </div>

          <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-slate-600">
            {cacheView ? (
              <>
                <Badge tone="accent">
                  {cacheView.cached_count}/{cacheView.total} cached
                </Badge>
                <Badge tone="ok">
                  {cacheView.scored_count ?? 0}/{cacheView.total} scored
                </Badge>
                <span>prompt_version · {cacheView.prompt_version}</span>
                {cacheView.judge_prompt_version ? (
                  <span>judge · {cacheView.judge_prompt_version}</span>
                ) : null}
              </>
            ) : null}
            {lastRun ? (
              <Badge tone={lastRun.cache_hits === lastRun.total ? "ok" : "warn"}>
                last run · {lastRun.cache_hits} hits / {lastRun.cache_misses}{" "}
                misses
              </Badge>
            ) : null}
            {cacheView && cacheView.judge_available === false ? (
              <Badge tone="warn">judge unavailable</Badge>
            ) : null}
          </div>

          <div className="mb-4 space-y-2">
            <AggregateStrip
              label="Aggregate · this preset × fixture × model"
              aggregate={aggregate}
            />
            <AggregateStrip
              label="Aggregate · all presets for this model"
              aggregate={modelAggregate}
            />
          </div>

          {error ? (
            <p className="mb-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
              {error}
            </p>
          ) : null}

          <ul className="space-y-3">
            {displayRows.map((row) => (
              <li
                key={row.scenario_id}
                className="border border-[var(--border)] bg-white px-3 py-3"
              >
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <h3 className="text-sm font-semibold text-slate-900">
                    {row.title}
                  </h3>
                  <Badge tone={row.hit ? "ok" : "neutral"}>
                    {row.hit ? "cache hit" : "not cached"}
                  </Badge>
                  {row.category ? (
                    <Badge tone="accent">{row.category}</Badge>
                  ) : null}
                  {row.score ? (
                    <Badge tone={row.score.judged ? "ok" : "warn"}>
                      {row.score.judged ? "judged" : "banking only / skipped"}
                    </Badge>
                  ) : (
                    <Badge>unscored</Badge>
                  )}
                  <span className="font-mono text-[11px] text-slate-500">
                    {row.scenario_id}
                  </span>
                </div>
                <p className="mb-2 text-xs text-[var(--muted)]">
                  Prompt: {row.suggested_prompt}
                </p>

                {/* Report card */}
                <div className="mb-2 grid gap-2 rounded-md border border-slate-200 bg-slate-50 p-2 sm:grid-cols-2">
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                      Personality (independent judge)
                    </div>
                    <p className="mt-1 text-xs text-slate-800">
                      {traitScoreLine(row.score)}
                    </p>
                    {row.score?.traits?.some((t) => t.cited_behaviors?.length) ? (
                      <ul className="mt-1 list-disc pl-4 text-[11px] text-slate-600">
                        {row.score.traits
                          .flatMap((t) =>
                            (t.cited_behaviors || []).slice(0, 1).map((c) => ({
                              trait: t.trait,
                              c,
                            })),
                          )
                          .slice(0, 4)
                          .map((x, i) => (
                            <li key={i}>
                              <span className="font-medium">{x.trait}:</span>{" "}
                              {x.c}
                            </li>
                          ))}
                      </ul>
                    ) : null}
                  </div>
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                      Banking checks
                    </div>
                    <p className="mt-1 text-xs text-slate-800">
                      {bankingSummary(row.score) ?? "—"}
                    </p>
                    {row.score?.banking_checks?.length ? (
                      <ul className="mt-1 space-y-0.5 text-[11px]">
                        {row.score.banking_checks.map((c) => (
                          <li
                            key={c.check_id}
                            className={
                              c.passed ? "text-teal-800" : "text-amber-800"
                            }
                          >
                            {c.passed ? "✓" : "✗"} {c.check_id}: {c.detail}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                </div>

                {row.error ? (
                  <p className="text-sm text-red-700">{row.error}</p>
                ) : row.reply ? (
                  <pre className="max-h-40 overflow-auto whitespace-pre-wrap rounded bg-slate-50 p-2 font-mono text-xs text-slate-800">
                    {row.reply}
                  </pre>
                ) : (
                  <p className="text-xs text-slate-500">
                    No cached reply yet — use Run all + score.
                  </p>
                )}
                {row.meta?.tool_trace_summary?.length ? (
                  <p className="mt-2 text-[11px] text-slate-500">
                    Tools:{" "}
                    {row.meta.tool_trace_summary
                      .map((t) => `${t.tool}${t.ok ? "" : "(!)"}`)
                      .join(", ")}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </Panel>
      ) : null}
    </section>
  );
}
