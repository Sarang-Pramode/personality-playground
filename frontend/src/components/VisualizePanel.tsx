import type { TraitProfile } from "../types";
import { RequestedRadar } from "./RadarChart";
import { TraitMap } from "./TraitMap";
import { Badge, Panel } from "./ui";

type Props = {
  profile: TraitProfile;
  behaviorSummary: string;
};

export function VisualizePanel({ profile, behaviorSummary }: Props) {
  return (
    <Panel
      title="Visualize"
      subtitle="Requested-profile radar · fixed 2D map · behavior summary"
      actions={<Badge>TARGET</Badge>}
    >
      <div className="space-y-5">
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Requested profile
          </h3>
          <RequestedRadar profile={profile} />
        </div>

        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Personality map
          </h3>
          <TraitMap profile={profile} />
        </div>

        <div className="rounded-md border border-[var(--border)] bg-slate-50 p-3">
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Behavior summary
          </h3>
          <p className="text-sm leading-relaxed text-slate-700">
            {behaviorSummary || "Adjust traits to preview style guidance."}
          </p>
        </div>
      </div>
    </Panel>
  );
}
