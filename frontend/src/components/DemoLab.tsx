import { useCallback, useEffect, useMemo, useState } from "react";
import { getDemoCache, runDemoScenarios } from "../lib/api";
import {
  PRESETS,
  type DemoCacheResponse,
  type DemoRunResponse,
  type FixtureCustomer,
  type ModelInfo,
  type PresetName,
  type Scenario,
} from "../types";
import { Badge, Button, FieldLabel, Panel, Select } from "./ui";

type Props = {
  models: ModelInfo[];
  customers: FixtureCustomer[];
  scenarios: Scenario[];
  defaultProvider: string;
  defaultModelId: string | null;
};

export function DemoLab({
  models,
  customers,
  scenarios,
  defaultProvider,
  defaultModelId,
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
    // Prefer allowlisted OpenAI + demo; keep Google if present
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
      });
      setLastRun(data);
      await loadCache();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo run failed");
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
        hit: r.cache_hit,
        reply: r.entry?.reply ?? null,
        meta: r.entry?.metadata ?? null,
        error: r.error,
        fromRun: true,
      }));
    }
    if (!cacheView) {
      return scenarios.map((s) => ({
        scenario_id: s.scenario_id,
        title: s.title,
        suggested_prompt: s.suggested_prompt,
        hit: false,
        reply: null,
        meta: null,
        error: null,
        fromRun: false,
      }));
    }
    return cacheView.results.map((r) => ({
      scenario_id: r.scenario_id,
      title: r.title,
      suggested_prompt: r.suggested_prompt,
      hit: r.hit,
      reply: r.entry?.reply ?? null,
      meta: r.entry?.metadata ?? null,
      error: null,
      fromRun: false,
    }));
  }, [cacheView, lastRun, preset, customerId, scenarios]);

  return (
    <section className="mx-auto w-full max-w-[1600px] px-3 pb-8" id="demo-lab">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold tracking-wide text-slate-900">
            Demo lab
          </h2>
          <p className="text-xs text-[var(--muted)]">
            Cached preset × fixture × starter scenarios — below the studio (does not
            change the three-column layout).
          </p>
        </div>
        <Button variant="ghost" onClick={() => setOpen((v) => !v)}>
          {open ? "Collapse" : "Expand"}
        </Button>
      </div>

      {open ? (
        <Panel
          title="Preset scenario cache"
          subtitle="Pick preset + model, load cache instantly, or run / refresh all starters."
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
                {busy ? "Running…" : "Run all scenarios"}
              </Button>
              <Button
                variant="secondary"
                disabled={busy || !modelId}
                onClick={() => void runAll(true)}
              >
                Refresh (re-run)
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
              <FieldLabel hint="OpenAI list is allowlisted small models only">
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
                <span>
                  prompt_version · {cacheView.prompt_version}
                </span>
              </>
            ) : null}
            {lastRun ? (
              <Badge tone={lastRun.cache_hits === lastRun.total ? "ok" : "warn"}>
                last run · {lastRun.cache_hits} hits / {lastRun.cache_misses} misses
              </Badge>
            ) : null}
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
                  <span className="font-mono text-[11px] text-slate-500">
                    {row.scenario_id}
                  </span>
                </div>
                <p className="mb-2 text-xs text-[var(--muted)]">
                  Prompt: {row.suggested_prompt}
                </p>
                {row.error ? (
                  <p className="text-sm text-red-700">{row.error}</p>
                ) : row.reply ? (
                  <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-slate-50 p-2 font-mono text-xs text-slate-800">
                    {row.reply}
                  </pre>
                ) : (
                  <p className="text-xs text-slate-500">
                    No cached reply yet — use Run all scenarios.
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
