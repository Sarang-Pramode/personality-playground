import { useEffect, useRef, useState } from "react";
import { PRESETS, type PresetName, type TraitProfile } from "../types";

type TrailPoint = { x: number; y: number; t: number };

function toPct(profile: Pick<TraitProfile, "exploration" | "energy">) {
  return {
    x: ((profile.exploration - 1) / 8) * 100,
    y: 100 - ((profile.energy - 1) / 8) * 100,
  };
}

const PRESET_MARKERS: { name: PresetName; short: string }[] = [
  { name: "balanced", short: "B" },
  { name: "concise", short: "C" },
  { name: "explorer", short: "E" },
  { name: "supportive", short: "S" },
];

/** Fixed-axis 2D map: X = Exploration, Y = Conversational Energy */
export function TraitMap({ profile }: { profile: TraitProfile }) {
  const pos = toPct(profile);
  const [trail, setTrail] = useState<TrailPoint[]>([]);
  const lastKey = useRef("");

  useEffect(() => {
    const key = `${profile.exploration}:${profile.energy}`;
    if (key === lastKey.current) return;
    lastKey.current = key;
    setTrail((prev) => {
      const next = [...prev, { x: pos.x, y: pos.y, t: Date.now() }];
      return next.slice(-12);
    });
  }, [profile.exploration, profile.energy, pos.x, pos.y]);

  return (
    <div>
      <div
        className="relative aspect-square w-full overflow-hidden rounded-md border border-[var(--border)] bg-[radial-gradient(circle_at_30%_20%,#ecfdf5_0%,transparent_45%),linear-gradient(165deg,#f8fafc_0%,#e2e8f0_55%,#f1f5f9_100%)]"
        role="img"
        aria-label={`Trait map at exploration ${profile.exploration}, energy ${profile.energy}`}
      >
        {/* quadrant tint */}
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(90deg,transparent_49.5%,rgba(15,118,110,0.04)_50%),linear-gradient(0deg,transparent_49.5%,rgba(15,118,110,0.04)_50%)]" />

        {[25, 50, 75].map((p) => (
          <div
            key={`v-${p}`}
            className="absolute inset-y-0 border-l border-dashed border-slate-300/80"
            style={{ left: `${p}%` }}
          />
        ))}
        {[25, 50, 75].map((p) => (
          <div
            key={`h-${p}`}
            className="absolute inset-x-0 border-t border-dashed border-slate-300/80"
            style={{ top: `${p}%` }}
          />
        ))}

        {/* axis crosshair */}
        <div className="absolute left-1/2 top-0 h-full w-px bg-slate-300/70" />
        <div className="absolute left-0 top-1/2 h-px w-full bg-slate-300/70" />

        {/* trail */}
        <svg
          className="pointer-events-none absolute inset-0 h-full w-full"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          aria-hidden
        >
          {trail.length > 1
            ? trail.slice(0, -1).map((pt, i) => {
                const next = trail[i + 1];
                const opacity = 0.15 + (i / trail.length) * 0.45;
                return (
                  <line
                    key={`${pt.t}-${i}`}
                    x1={pt.x}
                    y1={pt.y}
                    x2={next.x}
                    y2={next.y}
                    stroke="#0f766e"
                    strokeWidth={0.6}
                    strokeOpacity={opacity}
                    strokeLinecap="round"
                  />
                );
              })
            : null}
          {trail.map((pt, i) => (
            <circle
              key={`c-${pt.t}-${i}`}
              cx={pt.x}
              cy={pt.y}
              r={0.7}
              fill="#0f766e"
              fillOpacity={0.2 + (i / Math.max(trail.length, 1)) * 0.35}
            />
          ))}
        </svg>

        {/* preset markers */}
        {PRESET_MARKERS.map(({ name, short }) => {
          const p = toPct(PRESETS[name]);
          const isActive =
            profile.exploration === PRESETS[name].exploration &&
            profile.energy === PRESETS[name].energy;
          return (
            <div
              key={name}
              className={`absolute flex h-5 w-5 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border text-[9px] font-semibold transition-all duration-300 ${
                isActive
                  ? "border-teal-700 bg-teal-700 text-white shadow-sm"
                  : "border-slate-400/80 bg-white/90 text-slate-600"
              }`}
              style={{ left: `${p.x}%`, top: `${p.y}%` }}
              title={`${name} (X${PRESETS[name].exploration}, Y${PRESETS[name].energy})`}
            >
              {short}
            </div>
          );
        })}

        {/* current position */}
        <div
          className="absolute h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--accent)] shadow-[0_0_0_4px_rgba(15,118,110,0.22)] transition-all duration-300 ease-out"
          style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
        >
          <span className="absolute inset-0 animate-ping rounded-full bg-teal-600/30" />
        </div>

        <span className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[10px] font-medium uppercase tracking-wide text-slate-600">
          Exploration →
        </span>
        <span className="absolute left-2 top-1/2 origin-left -translate-y-1/2 -rotate-90 text-[10px] font-medium uppercase tracking-wide text-slate-600">
          Energy →
        </span>
        <span className="absolute left-2 top-2 text-[9px] uppercase tracking-wide text-slate-400">
          Low / Low
        </span>
        <span className="absolute right-2 top-2 text-[9px] uppercase tracking-wide text-slate-400">
          High X
        </span>
        <span className="absolute bottom-7 left-2 text-[9px] uppercase tracking-wide text-slate-400">
          High Y
        </span>
      </div>
      <div className="mt-2 flex flex-wrap items-center justify-center gap-2 text-[11px] text-[var(--muted)]">
        <span>
          Current · X {profile.exploration} · Y {profile.energy}
        </span>
        <span className="text-slate-300">·</span>
        <span className="inline-flex flex-wrap gap-1">
          {PRESET_MARKERS.map(({ name, short }) => (
            <span key={name} className="rounded bg-slate-100 px-1.5 py-0.5 text-slate-600">
              {short}={name}
            </span>
          ))}
        </span>
      </div>
    </div>
  );
}
