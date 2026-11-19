import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as ReRadar,
  ResponsiveContainer,
} from "recharts";
import type { TraitProfile } from "../types";
import { TRAIT_META } from "../types";

type Props = {
  profile: TraitProfile;
  /** Only pass when independent judges produced a complete measured profile. */
  measured?: TraitProfile | null;
};

export function RequestedRadar({ profile, measured }: Props) {
  const data = TRAIT_META.map((t) => ({
    trait: t.label.replace(" & ", "\n& "),
    requested: profile[t.key],
    measured: measured ? measured[t.key] : undefined,
    fullMark: 9,
  }));

  const showMeasured = Boolean(measured);

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
            dataKey="requested"
            stroke="#0f766e"
            fill="#0f766e"
            fillOpacity={0.25}
            isAnimationActive
            animationDuration={450}
          />
          {showMeasured ? (
            <Radar
              name="Measured"
              dataKey="measured"
              stroke="#b45309"
              fill="#b45309"
              fillOpacity={0.12}
              isAnimationActive
              animationDuration={450}
            />
          ) : null}
          {showMeasured ? (
            <Legend wrapperStyle={{ fontSize: 11 }} />
          ) : null}
        </ReRadar>
      </ResponsiveContainer>
      <p className="text-center text-[11px] text-[var(--muted)]">
        {showMeasured
          ? "Requested vs Measured (from independent judges)"
          : "Requested profile only · Measured appears after real judge scores"}
      </p>
    </div>
  );
}
