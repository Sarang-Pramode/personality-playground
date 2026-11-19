import { Badge, Select } from "./ui";
import type { ModelInfo } from "../types";

type Props = {
  models: ModelInfo[];
  provider: string;
  modelId: string | null;
  onProviderChange: (provider: string, modelId: string | null) => void;
  healthOk: boolean | null;
  llmLive: boolean;
};

export function Header({
  models,
  provider,
  modelId,
  onProviderChange,
  healthOk,
  llmLive,
}: Props) {
  const selectedKey = `${provider}:${modelId ?? ""}`;

  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] bg-white/90 px-4 py-3 backdrop-blur">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-semibold tracking-tight text-slate-900">
            Personality Playground
          </h1>
          <Badge tone="accent">Phase 1 MVP</Badge>
        </div>
        <p className="text-xs text-[var(--muted)]">
          Interactive LLM personality studio · synthetic banking rewards
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <nav className="hidden items-center gap-1 sm:flex" aria-label="Primary">
          <span className="rounded-md bg-slate-900 px-2.5 py-1 text-xs font-medium text-white">
            Live Studio
          </span>
          <span
            className="cursor-not-allowed rounded-md px-2.5 py-1 text-xs text-slate-400"
            title="Coming in Phase 2"
            aria-disabled="true"
          >
            Batch Evaluation — Phase 2
          </span>
        </nav>

        <div className="flex items-center gap-2">
          <label className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            Model
          </label>
          <Select
            className="min-w-[220px]"
            value={selectedKey}
            onChange={(e) => {
              const [p, ...rest] = e.target.value.split(":");
              onProviderChange(p, rest.join(":") || null);
            }}
            aria-label="LLM model switcher"
          >
            {models.map((m) => (
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

        <div className="flex items-center gap-1.5">
          {healthOk === null ? (
            <Badge>API…</Badge>
          ) : healthOk ? (
            <Badge tone="ok">API ok</Badge>
          ) : (
            <Badge tone="danger">API down</Badge>
          )}
          {llmLive ? (
            <Badge tone="accent">Live LLM</Badge>
          ) : (
            <Badge tone="warn">No live keys</Badge>
          )}
        </div>
      </div>
    </header>
  );
}
