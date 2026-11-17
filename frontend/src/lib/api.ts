import type {
  ChatResponse,
  FixtureCustomer,
  ModelInfo,
  PreviewResponse,
  Scenario,
  TraitProfile,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function getHealth() {
  return request<{
    status: string;
    llm: { openai: boolean; google: boolean; any_live: boolean };
    models: ModelInfo[];
  }>("/api/health");
}

export function getFixtures() {
  return request<{ customers: FixtureCustomer[]; scenarios: Scenario[] }>(
    "/api/fixtures",
  );
}

export function getModels() {
  return request<{ models: ModelInfo[] }>("/api/models");
}

export function previewPersonality(body: {
  profile?: TraitProfile;
  preset?: string;
}) {
  return request<PreviewResponse>("/api/personality/preview", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function sendChat(body: {
  message: string;
  customer_id: string;
  scenario_id?: string | null;
  session_id?: string | null;
  reset_session?: boolean;
  personality?: TraitProfile;
  preset?: string | null;
  provider: string;
  model_id?: string | null;
}) {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
