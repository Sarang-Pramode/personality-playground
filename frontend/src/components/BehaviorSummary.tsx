import { LEVEL_LABELS, TRAIT_META, type TraitProfile } from "../types";
import { Badge } from "./ui";

export type TraitCard = {
  key: keyof TraitProfile;
  label: string;
  level: number;
  level_name: string;
  description: string;
};

/** Fallback cards from profile when preview has not returned trait_cards yet. */
export function cardsFromProfile(profile: TraitProfile): TraitCard[] {
  return TRAIT_META.map((t) => ({
    key: t.key,
    label: t.label,
    level: profile[t.key],
    level_name: LEVEL_LABELS[profile[t.key]] ?? String(profile[t.key]),
    description: t.description,
  }));
}

export function BehaviorSummary({
  cards,
  profile,
}: {
  cards?: TraitCard[] | null;
  profile: TraitProfile;
}) {
  const list = cards?.length ? cards : cardsFromProfile(profile);

  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Behavior summary
      </h3>
      <ul className="grid gap-2">
        {list.map((card) => (
          <li
            key={card.key}
            className="border border-[var(--border)] bg-white px-3 py-2 transition-colors duration-200 hover:border-teal-200"
          >
            <div className="mb-1 flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium text-slate-900">
                {card.label}
              </span>
              <Badge tone="accent">
                {card.level_name} · {card.level}
              </Badge>
            </div>
            <p className="text-xs leading-relaxed text-slate-600">
              {card.description}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
