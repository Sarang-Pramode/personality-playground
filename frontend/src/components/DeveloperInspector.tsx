import type { ChatMetadata } from "../types";
import { Badge } from "./ui";

type Props = {
  latest: ChatMetadata | null;
  previewPrompt: string;
};

export function DeveloperInspector({ latest, previewPrompt }: Props) {
  return (
    <section className="border border-[var(--border)] bg-white">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border)] px-4 py-2.5">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">
            Developer Details
          </h2>
          <p className="text-xs text-[var(--muted)]">
            Profile snapshots · prompt versions · fixture IDs · model IDs · tool
            traces · run IDs
          </p>
        </div>
        {latest ? (
          <div className="flex flex-wrap gap-1.5">
            <Badge tone="accent">run {latest.run_id.slice(0, 8)}</Badge>
            <Badge>{latest.prompt_version}</Badge>
            <Badge>{latest.fixture_id}</Badge>
            <Badge
              tone={
                latest.mode === "live"
                  ? "ok"
                  : latest.mode === "scripted_demo"
                    ? "warn"
                    : "danger"
              }
            >
              {latest.mode}
            </Badge>
          </div>
        ) : (
          <Badge>No runs yet</Badge>
        )}
      </header>

      <div className="grid gap-0 md:grid-cols-3">
        <InspectorBlock title="Compiled system prompt (preview)">
          <pre className="whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-slate-700">
            {previewPrompt || "Adjust personality to compile a preview."}
          </pre>
        </InspectorBlock>

        <InspectorBlock title="Last run metadata">
          {latest ? (
            <pre className="whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-slate-700">
              {JSON.stringify(
                {
                  run_id: latest.run_id,
                  provider: latest.provider,
                  model_id: latest.model_id,
                  mode: latest.mode,
                  fixture_id: latest.fixture_id,
                  scenario_id: latest.scenario_id,
                  prompt_version: latest.prompt_version,
                  policy_version: latest.policy_version,
                  profile: latest.profile,
                  preset: latest.preset,
                },
                null,
                2,
              )}
            </pre>
          ) : (
            <p className="text-xs text-[var(--muted)]">Send a chat to populate.</p>
          )}
        </InspectorBlock>

        <InspectorBlock title="Tool traces">
          {latest?.tool_traces?.length ? (
            <pre className="whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-slate-700">
              {JSON.stringify(latest.tool_traces, null, 2)}
            </pre>
          ) : (
            <p className="text-xs text-[var(--muted)]">No tool calls yet.</p>
          )}
        </InspectorBlock>
      </div>
    </section>
  );
}

function InspectorBlock({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="max-h-64 overflow-auto border-t border-[var(--border)] p-3 md:border-l md:border-t-0 md:first:border-l-0">
      <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        {title}
      </h3>
      {children}
    </div>
  );
}
