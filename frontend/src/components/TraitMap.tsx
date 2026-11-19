import type { TraitProfile } from "../types";

/** Fixed-axis 2D map: X = Exploration, Y = Conversational Energy */
export function TraitMap({ profile }: { profile: TraitProfile }) {
  const x = ((profile.exploration - 1) / 8) * 100;
  const y = 100 - ((profile.energy - 1) / 8) * 100;

  return (
    <div>
      <div
        className="relative aspect-square w-full overflow-hidden rounded-md border border-[var(--border)] bg-[linear-gradient(180deg,#f8fafc_0%,#f1f5f9_100%)]"
        role="img"
        aria-label={`Trait map at exploration ${profile.exploration}, energy ${profile.energy}`}
      >
        {/* grid */}
        {[25, 50, 75].map((p) => (
          <div
            key={`v-${p}`}
            className="absolute inset-y-0 border-l border-dashed border-slate-200"
            style={{ left: `${p}%` }}
          />
        ))}
        {[25, 50, 75].map((p) => (
          <div
            key={`h-${p}`}
            className="absolute inset-x-0 border-t border-dashed border-slate-200"
            style={{ top: `${p}%` }}
          />
        ))}

        <div
          className="absolute h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--accent)] shadow-[0_0_0_4px_rgba(15,118,110,0.2)] transition-all duration-300 ease-out"
          style={{ left: `${x}%`, top: `${y}%` }}
        />

        <span className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[10px] font-medium uppercase tracking-wide text-slate-500">
          Exploration →
        </span>
        <span className="absolute left-2 top-1/2 origin-left -translate-y-1/2 -rotate-90 text-[10px] font-medium uppercase tracking-wide text-slate-500">
          Energy →
        </span>
      </div>
      <p className="mt-2 text-center text-[11px] text-[var(--muted)]">
        X {profile.exploration} · Y {profile.energy}
      </p>
    </div>
  );
}
