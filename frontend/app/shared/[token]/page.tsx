"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

interface FileItem {
  id: string;
  file_name: string;
  size: number;
  mime_type: string | null;
}

interface ShareInfo {
  folder_name: string;
  share_type: string;
  files: FileItem[];
  requires_password?: boolean;
}

function fmtBytes(b: number) {
  if (b >= 1e9) return (b / 1e9).toFixed(1) + " GB";
  if (b >= 1e6) return (b / 1e6).toFixed(1) + " MB";
  return Math.round(b / 1024) + " KB";
}

export default function SharedFolderPage() {
  const { token } = useParams<{ token: string }>();
  const [info, setInfo] = useState<ShareInfo | null>(null);
  const [needsPassword, setNeedsPassword] = useState(false);
  const [password, setPassword] = useState("");
  const [pwError, setPwError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    const res = await fetch(`/api/shares/view/${token}`);
    if (res.ok) {
      const data = await res.json();
      if (data.requires_password) {
        setNeedsPassword(true);
      } else {
        setInfo(data);
      }
    } else {
      const d = await res.json().catch(() => ({}));
      setError(d.detail || "Share not found or expired");
    }
    setLoading(false);
  }

  async function unlock(e: React.FormEvent) {
    e.preventDefault();
    setPwError("");
    const res = await fetch(`/api/shares/view/${token}/unlock`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    if (res.ok) {
      setInfo(await res.json());
      setNeedsPassword(false);
    } else {
      setPwError("Incorrect password");
    }
  }

  useEffect(() => { load(); }, [token]);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
      </main>
    );
  }

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center px-4">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-gg-text">Link Unavailable</h1>
          <p className="mt-2 text-sm text-gg-text2">{error}</p>
        </div>
      </main>
    );
  }

  if (needsPassword) {
    return (
      <main className="flex min-h-screen items-center justify-center px-4"
        style={{ background: "radial-gradient(ellipse at 50% 0%, rgba(139,92,246,0.12) 0%, var(--gg-bg) 60%)" }}
      >
        <div className="w-full max-w-sm rounded-2xl border border-gg-border bg-gg-s1 p-8 shadow-2xl">
          <h1 className="mb-2 text-xl font-semibold text-gg-text">Password Protected</h1>
          <p className="mb-6 text-sm text-gg-text2">Enter the password to access this shared folder.</p>
          <form onSubmit={unlock} className="space-y-4">
            <input
              type="password" placeholder="Password" required
              value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-gg-border bg-gg-bg px-4 py-3 text-sm text-gg-text outline-none focus:border-violet-500/50"
            />
            {pwError && <p className="text-sm text-red-400">{pwError}</p>}
            <button type="submit"
              className="w-full rounded-xl bg-violet-600 py-3 text-sm font-semibold text-white hover:bg-violet-500">
              Unlock
            </button>
          </form>
        </div>
      </main>
    );
  }

  if (!info) return null;

  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-1">
          <svg className="h-5 w-5 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v8.25" />
          </svg>
          <h1 className="text-2xl font-semibold text-gg-text">{info.folder_name}</h1>
        </div>
        <p className="text-sm text-gg-text2">{info.files.length} file{info.files.length !== 1 ? "s" : ""}</p>
      </div>

      <div className="space-y-2">
        {info.files.map((f) => (
          <div key={f.id} className="flex items-center justify-between rounded-xl border border-gg-border bg-gg-s1 px-4 py-3">
            <div className="flex items-center gap-3 min-w-0">
              <svg className="h-4 w-4 flex-shrink-0 text-gg-text2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
              </svg>
              <span className="truncate text-sm text-gg-text">{f.file_name}</span>
              <span className="flex-shrink-0 text-xs text-gg-text3">{fmtBytes(f.size)}</span>
            </div>
            <a
              href={`/api/shares/view/${token}/${f.id}/download`}
              className="ml-4 flex-shrink-0 rounded-lg border border-gg-border px-3 py-1.5 text-xs font-medium text-gg-text hover:bg-gg-bg transition"
            >
              Download
            </a>
          </div>
        ))}
      </div>

      {info.files.length === 0 && (
        <p className="text-center text-sm text-gg-text3 py-12">This folder is empty.</p>
      )}
    </main>
  );
}
