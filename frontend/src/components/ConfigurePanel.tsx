import { Download, Save, Trash2 } from "lucide-react";
import {
  LEVEL_LABELS,
  LEVELS,
  PRESETS,
  TRAIT_META,
  type PresetName,
  type SavedProfile,
  type TraitKey,
  type TraitProfile,
} from "../types";
import { Badge, Button, FieldLabel, TextInput, Panel, Select } from "./ui";

type Props = {
  profile: TraitProfile;
  activePreset: PresetName | "custom";
  saved: SavedProfile[];
  saveName: string;
  onSaveNameChange: (v: string) => void;
  onTraitChange: (key: TraitKey, value: number) => void;
  onPreset: (name: PresetName) => void;
  onSave: () => void;
  onLoad: (id: string) => void;
  onDelete: (id: string) => void;
  onExport: () => void;
};

export function ConfigurePanel({
  profile,
  activePreset,
  saved,
  saveName,
  onSaveNameChange,
  onTraitChange,
  onPreset,
  onSave,
  onLoad,
  onDelete,
  onExport,
}: Props) {
  return (
    <Panel
      title="Configure"
      subtitle="Requested personality · levels 1 / 3 / 5 / 7 / 9"
      actions={<Badge tone="accent">{activePreset}</Badge>}
    >
      <div className="space-y-5">
        <div>
          <FieldLabel>Presets</FieldLabel>
          <div className="grid grid-cols-2 gap-2">
            {(Object.keys(PRESETS) as PresetName[]).map((name) => (
              <Button
                key={name}
                variant={activePreset === name ? "primary" : "secondary"}
                className="capitalize"
                onClick={() => onPreset(name)}
              >
                {name}
              </Button>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          {TRAIT_META.map((trait) => {
            const value = profile[trait.key];
            return (
              <div key={trait.key}>
                <FieldLabel hint={LEVEL_LABELS[value]}>
                  {trait.label}
                </FieldLabel>
                <p className="mb-2 text-[11px] text-[var(--muted)]">
                  {trait.description}
                </p>
                <input
                  type="range"
                  min={1}
                  max={9}
                  step={2}
                  value={value}
                  aria-label={trait.label}
                  onChange={(e) =>
                    onTraitChange(trait.key, Number(e.target.value))
                  }
                  className="w-full accent-teal-700"
                  list={`ticks-${trait.key}`}
                />
                <datalist id={`ticks-${trait.key}`}>
                  {LEVELS.map((l) => (
                    <option key={l} value={l} />
                  ))}
                </datalist>
                <div className="mt-1 flex justify-between text-[10px] text-slate-400">
                  {LEVELS.map((l) => (
                    <span key={l}>{l}</span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        <div className="border-t border-[var(--border)] pt-4">
          <FieldLabel>Save / load (localStorage)</FieldLabel>
          <div className="flex gap-2">
            <TextInput
              placeholder="Profile name"
              value={saveName}
              onChange={(e) => onSaveNameChange(e.target.value)}
              aria-label="Saved profile name"
            />
            <Button onClick={onSave} disabled={!saveName.trim()} title="Save">
              <Save size={14} /> Save
            </Button>
          </div>

          {saved.length > 0 ? (
            <div className="mt-3 space-y-2">
              <Select
                defaultValue=""
                onChange={(e) => {
                  if (e.target.value) onLoad(e.target.value);
                }}
                aria-label="Load saved profile"
              >
                <option value="">Load saved…</option>
                {saved.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.preset})
                  </option>
                ))}
              </Select>
              <div className="flex flex-wrap gap-2">
                {saved.map((p) => (
                  <Button
                    key={p.id}
                    variant="danger"
                    className="text-xs"
                    onClick={() => onDelete(p.id)}
                    title={`Delete ${p.name}`}
                  >
                    <Trash2 size={12} /> {p.name}
                  </Button>
                ))}
              </div>
            </div>
          ) : (
            <p className="mt-2 text-xs text-[var(--muted)]">No saved profiles yet.</p>
          )}

          <Button variant="secondary" className="mt-3 w-full" onClick={onExport}>
            <Download size={14} /> Export profiles JSON
          </Button>
        </div>
      </div>
    </Panel>
  );
}
