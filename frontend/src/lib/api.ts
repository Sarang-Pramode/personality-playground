import type {
  ChatResponse,
  DemoCacheResponse,
  DemoRunResponse,
  DemoScoresResponse,
  FixtureCustomer,
  ModelInfo,
  OpenAIKeyExpiry,
  PreviewResponse,
  Scenario,
  TraitProfile,
} from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "";

export type AuthUser = {
  id: string;
  email: string;
  username: string;
  status: "pending" | "approved" | "denied" | "revoked";
  role: "user" | "admin";
  oauth_provider: string | null;
  created_at: string;
  updated_at: string;
};

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    let detail = `Request failed: ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) {
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export function getHealth() {
  return request<{
    status: string;
    llm: { openai: boolean; google: boolean; any_live: boolean };
    models: ModelInfo[];
    openai_allowed_models?: string[];
    openai_key_expiry?: OpenAIKeyExpiry | null;
    prompt_version?: string;
  }>("/api/health");
}

export function getAuthConfig() {
  return request<{
    auth_enabled?: boolean;
    google_oauth: boolean;
    bootstrap_admin?: boolean;
    admin_email_domain_hint?: string | null;
  }>("/api/auth/config");
}

export function getMe() {
  return request<{ authenticated: boolean; user: AuthUser | null }>(
    "/api/auth/me",
  );
}

export function signup(body: {
  email: string;
  username: string;
  password: string;
}) {
  return request<{ user: AuthUser }>("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function login(body: { login: string; password: string }) {
  return request<{ user: AuthUser }>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function bootstrapAdminPassword(body: {
  email: string;
  password: string;
  bootstrap_token: string;
}) {
  return request<{
    user: AuthUser;
    bootstrap_complete: boolean;
    next_step: string;
  }>("/api/auth/bootstrap-admin-password", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function logout() {
  return request<{ ok: boolean }>("/api/auth/logout", { method: "POST" });
}

export function googleStartUrl() {
  return `${API_BASE}/api/auth/google/start`;
}

export function listAdminUsers(status?: string) {
  const q = status ? `?status=${encodeURIComponent(status)}` : "";
  return request<{ users: AuthUser[] }>(`/api/admin/users${q}`);
}

export function setAdminUserStatus(
  userId: string,
  status: AuthUser["status"],
) {
  return request<{ user: AuthUser }>(`/api/admin/users/${userId}/status`, {
    method: "POST",
    body: JSON.stringify({ status }),
  });
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

export function getDemoCache(params: {
  preset: string;
  customer_id: string;
  provider: string;
  model_id: string;
}) {
  const q = new URLSearchParams(params);
  return request<DemoCacheResponse>(`/api/demo/cache?${q.toString()}`);
}

export function runDemoScenarios(body: {
  preset: string;
  customer_id: string;
  provider: string;
  model_id: string;
  force?: boolean;
  scenario_ids?: string[];
  auto_judge?: boolean;
}) {
  return request<DemoRunResponse>("/api/demo/run", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getDemoScores(params: {
  preset: string;
  customer_id: string;
  provider: string;
  model_id: string;
}) {
  const q = new URLSearchParams(params);
  return request<DemoScoresResponse>(`/api/demo/scores?${q.toString()}`);
}

export function judgeDemoCache(body: {
  preset: string;
  customer_id: string;
  provider: string;
  model_id: string;
  force?: boolean;
  scenario_ids?: string[];
}) {
  return request<DemoScoresResponse & { results?: unknown[]; aggregate?: unknown }>(
    "/api/demo/judge",
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

export function getEvaluationStatus() {
  return request<{
    phase: number;
    implemented: boolean;
    judge_prompt_version?: string;
    judge_model?: string;
    judge_available?: boolean;
    message: string;
  }>("/api/evaluation/status");
}
