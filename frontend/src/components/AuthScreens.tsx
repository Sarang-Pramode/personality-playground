import { useState } from "react";
import {
  googleStartUrl,
  login,
  signup,
  type AuthUser,
} from "../lib/api";
import { Button, FieldLabel, TextInput } from "./ui";

type Mode = "login" | "signup";

export function AuthScreens({
  googleEnabled,
  onAuthed,
}: {
  googleEnabled: boolean;
  onAuthed: (user: AuthUser) => void;
}) {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginId, setLoginId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "signup") {
        const res = await signup({ email, username, password });
        onAuthed(res.user);
      } else {
        const res = await login({ login: loginId, password });
        onAuthed(res.user);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Auth failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center px-4 py-10">
      <div className="w-full max-w-md border border-[var(--border)] bg-white p-6 shadow-sm">
        <div className="mb-6">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-teal-800">
            Personality Playground
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">
            {mode === "login" ? "Sign in" : "Create account"}
          </h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Access is allowlisted. New accounts stay pending until an admin
            approves.
          </p>
        </div>

        <div className="mb-4 flex gap-2">
          <Button
            type="button"
            variant={mode === "login" ? "primary" : "secondary"}
            className="flex-1"
            onClick={() => setMode("login")}
          >
            Login
          </Button>
          <Button
            type="button"
            variant={mode === "signup" ? "primary" : "secondary"}
            className="flex-1"
            onClick={() => setMode("signup")}
          >
            Sign up
          </Button>
        </div>

        <form className="space-y-3" onSubmit={onSubmit}>
          {mode === "signup" ? (
            <>
              <div>
                <FieldLabel>Email</FieldLabel>
                <TextInput
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                />
              </div>
              <div>
                <FieldLabel>Username</FieldLabel>
                <TextInput
                  required
                  minLength={3}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                />
              </div>
            </>
          ) : (
            <div>
              <FieldLabel>Email or username</FieldLabel>
              <TextInput
                required
                value={loginId}
                onChange={(e) => setLoginId(e.target.value)}
                autoComplete="username"
              />
            </div>
          )}
          <div>
            <FieldLabel>Password</FieldLabel>
            <TextInput
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={
                mode === "signup" ? "new-password" : "current-password"
              }
            />
          </div>
          {error ? (
            <p className="text-sm text-red-700" role="alert">
              {error}
            </p>
          ) : null}
          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Sign up"}
          </Button>
        </form>

        {googleEnabled ? (
          <div className="mt-4 border-t border-[var(--border)] pt-4">
            <a
              href={googleStartUrl()}
              className="flex w-full items-center justify-center rounded-md border border-[var(--border-strong)] bg-white px-3 py-2 text-sm font-medium text-slate-800 hover:bg-slate-50"
            >
              Continue with Google
            </a>
          </div>
        ) : (
          <p className="mt-4 text-center text-[11px] text-[var(--muted)]">
            Google Sign-In available when GOOGLE_CLIENT_ID/SECRET are set.
          </p>
        )}
      </div>
    </div>
  );
}

export function PendingScreen({
  user,
  onLogout,
}: {
  user: AuthUser;
  onLogout: () => void;
}) {
  return (
    <div className="flex min-h-full items-center justify-center px-4 py-10">
      <div className="w-full max-w-lg border border-[var(--border)] bg-white p-6">
        <h1 className="text-xl font-semibold text-slate-900">
          Awaiting approval
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          Hi <strong>{user.username}</strong> — your account is{" "}
          <span className="font-medium text-amber-800">{user.status}</span>.
          An admin has been notified. You can use the playground after
          approval.
        </p>
        <Button className="mt-4" variant="secondary" onClick={onLogout}>
          Sign out
        </Button>
      </div>
    </div>
  );
}

export function DeniedScreen({
  user,
  onLogout,
}: {
  user: AuthUser;
  onLogout: () => void;
}) {
  return (
    <div className="flex min-h-full items-center justify-center px-4 py-10">
      <div className="w-full max-w-lg border border-red-200 bg-red-50 p-6">
        <h1 className="text-xl font-semibold text-red-900">Access blocked</h1>
        <p className="mt-2 text-sm text-red-800">
          Account <strong>{user.username}</strong> is {user.status}. Contact
          an administrator if you believe this is a mistake.
        </p>
        <Button className="mt-4" variant="secondary" onClick={onLogout}>
          Sign out
        </Button>
      </div>
    </div>
  );
}
