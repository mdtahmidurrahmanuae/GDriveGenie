"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface User {
  id: string;
  email: string;
  display_name: string | null;
  is_super_admin: boolean;
  storage_limit_bytes: number;
  storage_used_bytes: number;
}

interface Stats {
  total_users: number;
  total_files: number;
  connected_accounts: number;
  total_storage_used_bytes: number;
  total_storage_limit_bytes: number;
}

function fmtBytes(b: number) {
  if (b >= 1e12) return (b / 1e12).toFixed(1) + " TB";
  if (b >= 1e9) return (b / 1e9).toFixed(1) + " GB";
  if (b >= 1e6) return (b / 1e6).toFixed(1) + " MB";
  return Math.round(b / 1024) + " KB";
}

export default function AdminPage() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Create user form
  const [showCreate, setShowCreate] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [newPass, setNewPass] = useState("");
  const [newName, setNewName] = useState("");
  const [newLimit, setNewLimit] = useState(15);
  const [newSuperAdmin, setNewSuperAdmin] = useState(false);
  const [creating, setCreating] = useState(false);

  // Edit storage
  const [editingUserId, setEditingUserId] = useState<string | null>(null);
  const [editLimit, setEditLimit] = useState(15);

  async function load() {
    setLoading(true);
    try {
      const [usersRes, statsRes] = await Promise.all([
        fetch("/api/admin/users", { credentials: "include" }),
        fetch("/api/admin/stats", { credentials: "include" }),
      ]);
      if (usersRes.status === 403) {
        router.push("/dashboard");
        return;
      }
      if (usersRes.ok) setUsers(await usersRes.json());
      if (statsRes.ok) setStats(await statsRes.json());
    } catch {
      setError("Failed to load admin data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function createUser(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    try {
      const res = await fetch("/api/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          email: newEmail,
          password: newPass,
          display_name: newName,
          storage_limit_bytes: newLimit * 1073741824,
          is_super_admin: newSuperAdmin,
        }),
      });
      if (res.ok) {
        setShowCreate(false);
        setNewEmail(""); setNewPass(""); setNewName(""); setNewLimit(15); setNewSuperAdmin(false);
        await load();
      } else {
        const d = await res.json().catch(() => ({}));
        setError(d.detail || "Failed to create user");
      }
    } finally {
      setCreating(false);
    }
  }

  async function saveStorageLimit(userId: string) {
    await fetch(`/api/admin/users/${userId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ storage_limit_bytes: editLimit * 1073741824 }),
    });
    setEditingUserId(null);
    await load();
  }

  async function deleteUser(userId: string, email: string) {
    if (!confirm(`Delete user ${email}? This cannot be undone.`)) return;
    await fetch(`/api/admin/users/${userId}`, { method: "DELETE", credentials: "include" });
    await load();
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-8 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gg-text">Admin Panel</h1>
          <p className="mt-1 text-sm text-gg-text2">Manage users and storage quotas</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-500"
        >
          + New User
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            { label: "Users", value: stats.total_users },
            { label: "Files", value: stats.total_files },
            { label: "Connected Accounts", value: stats.connected_accounts },
            { label: "Total Storage Used", value: fmtBytes(stats.total_storage_used_bytes) },
          ].map((s) => (
            <div key={s.label} className="rounded-xl border border-gg-border bg-gg-s1 p-4">
              <p className="text-xs text-gg-text2">{s.label}</p>
              <p className="mt-1 text-xl font-semibold text-gg-text">{s.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Create user modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div className="w-full max-w-md rounded-2xl border border-gg-border bg-gg-s1 p-6 shadow-2xl">
            <h2 className="mb-4 text-lg font-semibold text-gg-text">Create New User</h2>
            <form onSubmit={createUser} className="space-y-3">
              <input
                type="email" placeholder="Email" required
                value={newEmail} onChange={(e) => setNewEmail(e.target.value)}
                className="w-full rounded-xl border border-gg-border bg-gg-bg px-4 py-2.5 text-sm text-gg-text outline-none focus:border-violet-500/50"
              />
              <input
                type="password" placeholder="Password (min 8 chars)" required minLength={8}
                value={newPass} onChange={(e) => setNewPass(e.target.value)}
                className="w-full rounded-xl border border-gg-border bg-gg-bg px-4 py-2.5 text-sm text-gg-text outline-none focus:border-violet-500/50"
              />
              <input
                type="text" placeholder="Display name (optional)"
                value={newName} onChange={(e) => setNewName(e.target.value)}
                className="w-full rounded-xl border border-gg-border bg-gg-bg px-4 py-2.5 text-sm text-gg-text outline-none focus:border-violet-500/50"
              />
              <div className="flex items-center gap-3">
                <label className="text-sm text-gg-text2">Storage limit (GB)</label>
                <input
                  type="number" min={1} max={10000} required
                  value={newLimit} onChange={(e) => setNewLimit(Number(e.target.value))}
                  className="w-24 rounded-xl border border-gg-border bg-gg-bg px-3 py-2 text-sm text-gg-text outline-none focus:border-violet-500/50"
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-gg-text2">
                <input type="checkbox" checked={newSuperAdmin} onChange={(e) => setNewSuperAdmin(e.target.checked)} />
                Super Admin
              </label>
              <div className="flex gap-3 pt-2">
                <button type="submit" disabled={creating}
                  className="flex-1 rounded-xl bg-violet-600 py-2.5 text-sm font-semibold text-white hover:bg-violet-500 disabled:opacity-40">
                  {creating ? "Creating…" : "Create"}
                </button>
                <button type="button" onClick={() => setShowCreate(false)}
                  className="flex-1 rounded-xl border border-gg-border py-2.5 text-sm text-gg-text hover:bg-gg-bg">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Users table */}
      <div className="overflow-hidden rounded-xl border border-gg-border">
        <table className="w-full text-sm">
          <thead className="border-b border-gg-border bg-gg-s1">
            <tr>
              {["Email", "Name", "Storage Used", "Limit", "Role", "Actions"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-gg-text2">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gg-border bg-gg-bg">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-gg-s1/40 transition-colors">
                <td className="px-4 py-3 text-gg-text">{u.email}</td>
                <td className="px-4 py-3 text-gg-text2">{u.display_name || "—"}</td>
                <td className="px-4 py-3 text-gg-text2">{fmtBytes(u.storage_used_bytes)}</td>
                <td className="px-4 py-3">
                  {editingUserId === u.id ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="number" min={1} max={10000}
                        value={editLimit}
                        onChange={(e) => setEditLimit(Number(e.target.value))}
                        className="w-20 rounded border border-gg-border bg-gg-s1 px-2 py-1 text-xs text-gg-text outline-none"
                      />
                      <span className="text-xs text-gg-text2">GB</span>
                      <button onClick={() => saveStorageLimit(u.id)}
                        className="rounded bg-violet-600 px-2 py-1 text-xs text-white hover:bg-violet-500">Save</button>
                      <button onClick={() => setEditingUserId(null)}
                        className="text-xs text-gg-text2 hover:text-gg-text">×</button>
                    </div>
                  ) : (
                    <button
                      onClick={() => { setEditingUserId(u.id); setEditLimit(Math.round(u.storage_limit_bytes / 1073741824)); }}
                      className="rounded px-2 py-1 text-xs text-gg-text2 hover:bg-gg-s1 hover:text-gg-text"
                    >
                      {fmtBytes(u.storage_limit_bytes)} ✏
                    </button>
                  )}
                </td>
                <td className="px-4 py-3">
                  {u.is_super_admin
                    ? <span className="rounded-full bg-violet-600/15 px-2 py-0.5 text-xs font-medium text-violet-400">Super Admin</span>
                    : <span className="rounded-full bg-gg-s1 px-2 py-0.5 text-xs text-gg-text2">User</span>
                  }
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => deleteUser(u.id, u.email)}
                    className="text-xs text-red-400 hover:text-red-300"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
