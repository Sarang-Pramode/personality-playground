import { useEffect, useState } from "react";
import {
  listAdminUsers,
  setAdminUserStatus,
  type AuthUser,
} from "../lib/api";
import { Badge, Button, Panel, Select } from "./ui";

export function AdminPanel() {
  const [filter, setFilter] = useState<string>("pending");
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function refresh(status = filter) {
    setError(null);
    try {
      const res = await listAdminUsers(status || undefined);
      setUsers(res.users);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load users");
    }
  }

  useEffect(() => {
    void refresh(filter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  async function updateStatus(id: string, status: AuthUser["status"]) {
    setBusyId(id);
    try {
      await setAdminUserStatus(id, status);
      await refresh(filter);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <Panel
      title="Admin allowlist"
      subtitle="Approve, deny, or revoke playground access"
      actions={<Badge tone="accent">admin</Badge>}
    >
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Select
          className="max-w-[200px]"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          aria-label="Filter by status"
        >
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="denied">Denied</option>
          <option value="revoked">Revoked</option>
          <option value="">All</option>
        </Select>
        <Button variant="secondary" onClick={() => void refresh(filter)}>
          Refresh
        </Button>
      </div>
      {error ? (
        <p className="mb-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      ) : null}
      {users.length === 0 ? (
        <p className="text-sm text-[var(--muted)]">No users in this filter.</p>
      ) : (
        <ul className="divide-y divide-slate-100 border border-[var(--border)]">
          {users.map((u) => (
            <li
              key={u.id}
              className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-sm"
            >
              <div>
                <div className="font-medium text-slate-900">
                  {u.username}{" "}
                  <span className="text-xs font-normal text-slate-500">
                    {u.email}
                  </span>
                </div>
                <div className="text-[11px] text-slate-500">
                  {u.role} · {u.status}
                  {u.oauth_provider ? ` · ${u.oauth_provider}` : ""}
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5">
                <Button
                  variant="primary"
                  disabled={busyId === u.id || u.status === "approved"}
                  onClick={() => void updateStatus(u.id, "approved")}
                >
                  Approve
                </Button>
                <Button
                  variant="danger"
                  disabled={busyId === u.id}
                  onClick={() => void updateStatus(u.id, "denied")}
                >
                  Deny
                </Button>
                <Button
                  variant="secondary"
                  disabled={busyId === u.id}
                  onClick={() => void updateStatus(u.id, "revoked")}
                >
                  Revoke
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
