import { Badge } from "./ui";

export type OpenAIKeyExpiry = {
  expires_at: string;
  days_remaining: number;
  warn: boolean;
  expired: boolean;
};

type Props = {
  expiry: OpenAIKeyExpiry | null | undefined;
};

/** Admin/local reminder — countdown only; never shows the API key. */
export function KeyExpiryBanner({ expiry }: Props) {
  if (!expiry) return null;

  const { expires_at, days_remaining, warn, expired } = expiry;
  const tone = expired || warn ? "danger" : days_remaining <= 3 ? "warn" : "ok";
  const label = expired
    ? `OpenAI key expired ${Math.abs(days_remaining)} day(s) ago (${expires_at})`
    : days_remaining === 0
      ? `OpenAI key expires today (${expires_at})`
      : `OpenAI key expires in ${days_remaining} day(s) · ${expires_at}`;

  return (
    <div
      className={
        expired || warn
          ? "border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-950"
          : "border-b border-slate-200 bg-slate-50 px-4 py-2 text-xs text-slate-700"
      }
      role="status"
    >
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-2">
        <Badge tone={tone === "ok" ? "ok" : tone === "warn" ? "warn" : "danger"}>
          Key expiry
        </Badge>
        <span className="font-medium">{label}</span>
        <span className="text-[var(--muted)]">
          Set <code className="rounded bg-white/80 px-1">OPENAI_KEY_EXPIRES_AT</code>{" "}
          on Vercel when rotating the 7-day key (ISO date only — key stays server-side).
        </span>
      </div>
    </div>
  );
}
