import { Loader2, Send, RotateCcw } from "lucide-react";
import type {
  ChatMessage,
  FixtureCustomer,
  Scenario,
} from "../types";
import { MarkdownContent } from "./MarkdownContent";
import { Badge, Button, FieldLabel, Panel, Select } from "./ui";

type Props = {
  customers: FixtureCustomer[];
  scenarios: Scenario[];
  customerId: string;
  scenarioId: string;
  messages: ChatMessage[];
  input: string;
  busy: boolean;
  modeLabel: string | null;
  modeTone: "accent" | "warn" | "danger" | "neutral" | "ok";
  onCustomerChange: (id: string) => void;
  onScenarioChange: (id: string) => void;
  onInputChange: (v: string) => void;
  onSend: () => void;
  onReset: () => void;
  onUseSuggested: () => void;
};

export function ChatPanel({
  customers,
  scenarios,
  customerId,
  scenarioId,
  messages,
  input,
  busy,
  modeLabel,
  modeTone,
  onCustomerChange,
  onScenarioChange,
  onInputChange,
  onSend,
  onReset,
  onUseSuggested,
}: Props) {
  const scenario = scenarios.find((s) => s.scenario_id === scenarioId);

  return (
    <Panel
      title="Live Rewards Chat"
      subtitle="Synthetic fixtures · policy-dominated replies"
      actions={
        <div className="flex items-center gap-2">
          {modeLabel ? <Badge tone={modeTone}>{modeLabel}</Badge> : null}
          <Button variant="ghost" onClick={onReset} title="Reset session">
            <RotateCcw size={14} />
          </Button>
        </div>
      }
    >
      <div className="flex h-full min-h-[420px] flex-col gap-3">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <FieldLabel>Customer fixture</FieldLabel>
            <Select
              value={customerId}
              onChange={(e) => onCustomerChange(e.target.value)}
              aria-label="Customer fixture"
            >
              {customers.map((c) => (
                <option key={c.customer_id} value={c.customer_id}>
                  {c.display_name} ({c.customer_id}) · {c.available_balance}{" "}
                  {c.currency}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <FieldLabel>Scenario</FieldLabel>
            <Select
              value={scenarioId}
              onChange={(e) => onScenarioChange(e.target.value)}
              aria-label="Scenario"
            >
              {scenarios.map((s) => (
                <option key={s.scenario_id} value={s.scenario_id}>
                  {s.title}
                </option>
              ))}
            </Select>
          </div>
        </div>

        {scenario ? (
          <div className="rounded-md border border-dashed border-teal-200 bg-teal-50/60 px-3 py-2 text-xs text-teal-900">
            <div className="font-medium">{scenario.description}</div>
            <button
              type="button"
              className="mt-1 text-teal-800 underline-offset-2 hover:underline"
              onClick={onUseSuggested}
            >
              Use suggested: “{scenario.suggested_prompt}”
            </button>
          </div>
        ) : null}

        <div className="min-h-0 flex-1 space-y-3 overflow-auto rounded-md border border-[var(--border)] bg-slate-50/80 p-3">
          {messages.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">
              Send a message to start. Try Explorer vs Concise on the same
              question, then inspect prompts below.
            </p>
          ) : (
            messages.map((m) => (
              <div
                key={m.id}
                className={
                  m.role === "user"
                    ? "ml-8 rounded-md bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-slate-200"
                    : m.role === "system"
                      ? "rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-900 ring-1 ring-amber-200"
                      : "mr-8 rounded-md bg-teal-50 px-3 py-2 text-sm text-slate-800 ring-1 ring-teal-100"
                }
              >
                <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  {m.role}
                  {m.metadata?.mode ? ` · ${m.metadata.mode}` : ""}
                </div>
                {m.role === "assistant" ? (
                  <MarkdownContent content={m.content} />
                ) : (
                  <div className="whitespace-pre-wrap leading-relaxed">
                    {m.content}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            onSend();
          }}
        >
          <input
            className="min-w-0 flex-1 rounded-md border border-[var(--border-strong)] bg-white px-3 py-2 text-sm outline-none focus:border-teal-700"
            placeholder="Ask about balance, redemptions, cards…"
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            disabled={busy}
            aria-label="Chat message"
          />
          <Button type="submit" disabled={busy || !input.trim()}>
            {busy ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            Send
          </Button>
        </form>
      </div>
    </Panel>
  );
}
