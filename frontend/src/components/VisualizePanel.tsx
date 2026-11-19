import type { TraitProfile } from "../types";
import {
  BehaviorSummary,
  type TraitCard,
} from "./BehaviorSummary";
import { RequestedRadar } from "./RadarChart";
import { TraitMap } from "./TraitMap";
import { Badge, Panel } from "./ui";

type Props = {
  profile: TraitProfile;
  traitCards?: TraitCard[] | null;
  measured?: TraitProfile | null;
};

export function VisualizePanel({ profile, traitCards, measured }: Props) {
  return (
    <Panel
      title="Visualize"
      subtitle="Requested-profile radar · fixed 2D map · behavior summary"
      actions={
        <div className="flex gap-1">
          <Badge>TARGET</Badge>
          {measured ? <Badge tone="warn">MEASURED</Badge> : null}
        </div>
      }
    >
      <div className="space-y-5">
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Requested profile
          </h3>
          <RequestedRadar profile={profile} measured={measured} />
        </div>

        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Personality map
          </h3>
          <TraitMap profile={profile} />
        </div>

        <BehaviorSummary cards={traitCards} profile={profile} />
      </div>
    </Panel>
  );
}
