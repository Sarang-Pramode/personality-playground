import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as ReRadar,
  ResponsiveContainer,
} from "recharts";
import type { TraitProfile } from "../types";
import { TRAIT_META } from "../types";

export function RequestedRadar({ profile }: { profile: TraitProfile }) {
  const data = TRAIT_META.map((t) => ({
    trait: t.label.replace(" & ", "\n& "),
    value: profile[t.key],
    fullMark: 9,
  }));

  return (
    <div className="h-64 w-full" role="img" aria-label="Requested personality radar">
      <ResponsiveContainer width="100%" height="100%">
        <ReRadar data={data} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="#cbd5e1" />
          <PolarAngleAxis
            dataKey="trait"
            tick={{ fill: "#475569", fontSize: 11 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 9]}
            tickCount={6}
            tick={{ fill: "#94a3b8", fontSize: 10 }}
          />
          <Radar
            name="Requested"
            dataKey="value"
            stroke="#0f766e"
            fill="#0f766e"
            fillOpacity={0.25}
            isAnimationActive
            animationDuration={450}
          />
        </ReRadar>
      </ResponsiveContainer>
      <p className="text-center text-[11px] text-[var(--muted)]">
        Requested profile only · Measured overlays reserved for Phase 2
      </p>
    </div>
  );
}
