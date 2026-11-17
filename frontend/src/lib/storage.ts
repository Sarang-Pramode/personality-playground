import type { SavedProfile, TraitProfile } from "../types";

const KEY = "personality-playground.saved-profiles.v1";

export function loadSavedProfiles(): SavedProfile[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as SavedProfile[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function persistSavedProfiles(profiles: SavedProfile[]) {
  localStorage.setItem(KEY, JSON.stringify(profiles));
}

export function saveProfile(
  name: string,
  profile: TraitProfile,
  preset: SavedProfile["preset"],
  existingId?: string,
): SavedProfile[] {
  const list = loadSavedProfiles();
  const now = new Date().toISOString();
  if (existingId) {
    const next = list.map((p) =>
      p.id === existingId ? { ...p, name, profile, preset, updatedAt: now } : p,
    );
    persistSavedProfiles(next);
    return next;
  }
  const entry: SavedProfile = {
    id: crypto.randomUUID(),
    name,
    profile,
    preset,
    updatedAt: now,
  };
  const next = [entry, ...list];
  persistSavedProfiles(next);
  return next;
}

export function deleteSavedProfile(id: string): SavedProfile[] {
  const next = loadSavedProfiles().filter((p) => p.id !== id);
  persistSavedProfiles(next);
  return next;
}

export function exportProfilesJson(profiles: SavedProfile[]): string {
  return JSON.stringify({ exportedAt: new Date().toISOString(), profiles }, null, 2);
}
