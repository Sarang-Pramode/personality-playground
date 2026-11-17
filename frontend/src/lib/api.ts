import type {
  ChatResponse,
  FixtureCustomer,
  ModelInfo,
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
  }>("/api/health");
}

export function getAuthConfig() {
  return request<{ google_oauth: boolean }>("/api/auth/config");
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
