import { useEffect, useMemo, useRef, useState } from "react";
import { PRESETS, type PresetName, type TraitProfile } from "../types";

type TrailPoint = { x: number; y: number; t: number };

/** Percent inset so edge markers (h-5/w-5) stay fully inside the chart. */
const PLOT_PAD = 10;

function toPct(profile: Pick<TraitProfile, "exploration" | "energy">) {
  const span = 100 - 2 * PLOT_PAD;
  return {
    x: PLOT_PAD + ((profile.exploration - 1) / 8) * span,
    // High energy → top (low CSS top%)
    y: PLOT_PAD + (1 - (profile.energy - 1) / 8) * span,
  };
}

const PRESET_MARKERS: { name: PresetName; short: string }[] = [
  { name: "balanced", short: "B" },
  { name: "concise", short: "C" },
  { name: "explorer", short: "E" },
  { name: "supportive", short: "S" },
];

/** Fan out markers that share the same exploration/energy so all letters stay visible. */
function markerOffsets(count: number, index: number): { dx: number; dy: number } {
  if (count <= 1) return { dx: 0, dy: 0 };
  const radius = 4.5;
  const angle = (Math.PI * 2 * index) / count - Math.PI / 2;
  return { dx: Math.cos(angle) * radius, dy: Math.sin(angle) * radius };
}

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

  const presetLayout = useMemo(() => {
    const groups = new Map<string, number>();
    return PRESET_MARKERS.map(({ name, short }) => {
      const preset = PRESETS[name];
      const cell = `${preset.exploration}:${preset.energy}`;
      const indexInGroup = groups.get(cell) ?? 0;
      groups.set(cell, indexInGroup + 1);
      const base = toPct(preset);
      return { name, short, preset, base, cell, indexInGroup };
    }).map((entry) => {
      const count = groups.get(entry.cell) ?? 1;
      const { dx, dy } = markerOffsets(count, entry.indexInGroup);
      return {
        ...entry,
        x: entry.base.x + dx,
        y: entry.base.y + dy,
      };
    });
  }, []);

  const gridLines = [3, 5, 7];
  const center = toPct({ exploration: 5, energy: 5 });

  return (
    <div>
      <div
        className="relative aspect-square w-full overflow-hidden rounded-md border border-[var(--border)] bg-[radial-gradient(circle_at_30%_20%,#ecfdf5_0%,transparent_45%),linear-gradient(165deg,#f8fafc_0%,#e2e8f0_55%,#f1f5f9_100%)]"
        role="img"
        aria-label={`Trait map at exploration ${profile.exploration}, energy ${profile.energy}`}
      >
        {/* quadrant tint aligned to plot center (trait 5/5) */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background: [
              `linear-gradient(90deg,transparent calc(${center.x}% - 0.5px),rgba(15,118,110,0.04) calc(${center.x}% - 0.5px))`,
              `linear-gradient(0deg,transparent calc(${center.y}% - 0.5px),rgba(15,118,110,0.04) calc(${center.y}% - 0.5px))`,
            ].join(","),
          }}
        />

        {gridLines.map((level) => {
          const x = toPct({ exploration: level, energy: 5 }).x;
          const y = toPct({ exploration: 5, energy: level }).y;
          return (
            <div key={`grid-${level}`}>
              <div
                className="absolute border-l border-dashed border-slate-300/80"
                style={{ left: `${x}%`, top: `${PLOT_PAD}%`, bottom: `${PLOT_PAD}%` }}
              />
              <div
                className="absolute border-t border-dashed border-slate-300/80"
                style={{ top: `${y}%`, left: `${PLOT_PAD}%`, right: `${PLOT_PAD}%` }}
              />
            </div>
          );
        })}

        {/* axis crosshair at neutral (5, 5) */}
        <div
          className="absolute w-px bg-slate-300/70"
          style={{
            left: `${center.x}%`,
            top: `${PLOT_PAD}%`,
            bottom: `${PLOT_PAD}%`,
          }}
        />
        <div
          className="absolute h-px bg-slate-300/70"
          style={{
            top: `${center.y}%`,
            left: `${PLOT_PAD}%`,
            right: `${PLOT_PAD}%`,
          }}
        />

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
        {presetLayout.map(({ name, short, preset, x, y }) => {
          const isActive =
            profile.exploration === preset.exploration &&
            profile.energy === preset.energy;
          return (
            <div
              key={name}
              className={`absolute flex h-5 w-5 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border text-[9px] font-semibold transition-all duration-300 ${
                isActive
                  ? "border-teal-700 bg-teal-700 text-white shadow-sm"
                  : "border-slate-400/80 bg-white/90 text-slate-600"
              }`}
              style={{ left: `${x}%`, top: `${y}%` }}
              title={`${name} (X${preset.exploration}, Y${preset.energy})`}
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
        {/* Corners: X→ right (Exploration), Y→ up (Energy) */}
        <span className="absolute left-2 top-2 text-[9px] uppercase tracking-wide text-slate-400">
          Low X / High Y
        </span>
        <span className="absolute right-2 top-2 text-[9px] uppercase tracking-wide text-slate-400">
          High X / High Y
        </span>
        <span className="absolute bottom-7 left-2 text-[9px] uppercase tracking-wide text-slate-400">
          Low X / Low Y
        </span>
        <span className="absolute bottom-7 right-2 text-[9px] uppercase tracking-wide text-slate-400">
          High X / Low Y
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
