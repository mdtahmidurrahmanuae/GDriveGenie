"use client";

import { useEffect, useState } from "react";

interface Folder {
  id: string;
  name: string;
  parent_id: string | null;
  created: string;
}

interface FileItem {
  id: string;
  file_name: string;
  size: number;
  mime_type: string | null;
  has_thumbnail: boolean;
}

interface Share {
  id: string;
  folder_id: string;
  share_type: string;
  token: string;
  link: string;
  expires_at: string | null;
  shared_with: string | null;
}

function fmtBytes(b: number) {
  if (b >= 1e9) return (b / 1e9).toFixed(1) + " GB";
  if (b >= 1e6) return (b / 1e6).toFixed(1) + " MB";
  return Math.round(b / 1024) + " KB";
}

export default function FoldersPage() {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<Folder | null>(null);
  const [folderFiles, setFolderFiles] = useState<FileItem[]>([]);
  const [folderShares, setFolderShares] = useState<Share[]>([]);
  const [loading, setLoading] = useState(true);

  // Create folder
  const [newFolderName, setNewFolderName] = useState("");
  const [creating, setCreating] = useState(false);

  // Share creation
  const [showShare, setShowShare] = useState(false);
  const [shareType, setShareType] = useState<"public" | "user" | "password">("public");
  const [shareEmail, setShareEmail] = useState("");
  const [sharePassword, setSharePassword] = useState("");
  const [sharing, setSharing] = useState(false);

  async function loadFolders() {
    setLoading(true);
    const res = await fetch("/api/folders", { credentials: "include" });
    if (res.ok) setFolders(await res.json());
    setLoading(false);
  }

  async function selectFolder(folder: Folder) {
    setSelectedFolder(folder);
    const [filesRes, sharesRes] = await Promise.all([
      fetch(`/api/folders/${folder.id}/files`, { credentials: "include" }),
      fetch(`/api/shares/folder/${folder.id}`, { credentials: "include" }),
    ]);
    if (filesRes.ok) setFolderFiles(await filesRes.json());
    if (sharesRes.ok) setFolderShares(await sharesRes.json());
  }

  async function createFolder(e: React.FormEvent) {
    e.preventDefault();
    if (!newFolderName.trim()) return;
    setCreating(true);
    const res = await fetch("/api/folders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ name: newFolderName.trim() }),
    });
    if (res.ok) {
      setNewFolderName("");
      await loadFolders();
    }
    setCreating(false);
  }

  async function deleteFolder(id: string, name: string) {
    if (!confirm(`Delete folder "${name}"? Files will not be deleted from Google Drive.`)) return;
    await fetch(`/api/folders/${id}`, { method: "DELETE", credentials: "include" });
    if (selectedFolder?.id === id) setSelectedFolder(null);
    await loadFolders();
  }

  async function createShare(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFolder) return;
    setSharing(true);
    const body: Record<string, unknown> = {
      folder_id: selectedFolder.id,
      share_type: shareType,
    };
    if (shareType === "user") body.shared_with_email = shareEmail;
    if (shareType === "password") body.password = sharePassword;

    const res = await fetch("/api/shares", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body),
    });
    if (res.ok) {
      setShowShare(false);
      setShareEmail(""); setSharePassword("");
      await selectFolder(selectedFolder);
    }
    setSharing(false);
  }

  async function revokeShare(shareId: string) {
    await fetch(`/api/shares/${shareId}`, { method: "DELETE", credentials: "include" });
    if (selectedFolder) await selectFolder(selectedFolder);
  }

  useEffect(() => { loadFolders(); }, []);

  const shareBaseUrl = typeof window !== "undefined" ? window.location.origin : "";

  return (
    <div className="flex h-full gap-6 p-6">
      {/* Left: folder list */}
      <div className="flex w-72 flex-shrink-0 flex-col gap-4">
        <h2 className="text-base font-semibold text-gg-text">Folders</h2>

        <form onSubmit={createFolder} className="flex gap-2">
          <input
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            placeholder="New folder name…"
            className="flex-1 rounded-xl border border-gg-border bg-gg-bg px-3 py-2 text-sm text-gg-text outline-none focus:border-violet-500/50"
          />
          <button type="submit" disabled={creating || !newFolderName.trim()}
            className="rounded-xl bg-violet-600 px-3 py-2 text-sm font-semibold text-white hover:bg-violet-500 disabled:opacity-40">
            +
          </button>
        </form>

        {loading ? (
          <div className="flex justify-center py-8">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
          </div>
        ) : folders.length === 0 ? (
          <p className="text-sm text-gg-text3">No folders yet</p>
        ) : (
          <ul className="space-y-1">
            {folders.map((f) => (
              <li key={f.id}>
                <button
                  onClick={() => selectFolder(f)}
                  className={`group flex w-full items-center justify-between rounded-xl px-3 py-2 text-sm transition ${
                    selectedFolder?.id === f.id
                      ? "bg-violet-600/15 text-violet-400"
                      : "text-gg-text hover:bg-gg-s1"
                  }`}
                >
                  <span className="flex items-center gap-2 truncate">
                    <svg className="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v8.25" />
                    </svg>
                    {f.name}
                  </span>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteFolder(f.id, f.name); }}
                    className="hidden text-red-400 group-hover:block hover:text-red-300 text-xs"
                  >
                    ✕
                  </button>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Right: folder contents + shares */}
      {selectedFolder ? (
        <div className="flex-1 space-y-6 overflow-auto">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gg-text">{selectedFolder.name}</h2>
            <button
              onClick={() => setShowShare(true)}
              className="rounded-xl border border-violet-500/30 bg-violet-600/10 px-4 py-2 text-sm font-medium text-violet-400 hover:bg-violet-600/20"
            >
              Share Folder
            </button>
          </div>

          {/* Files */}
          <div>
            <h3 className="mb-3 text-sm font-medium text-gg-text2">Files ({folderFiles.length})</h3>
            {folderFiles.length === 0 ? (
              <p className="text-sm text-gg-text3">No files in this folder. Upload files and assign them here.</p>
            ) : (
              <div className="space-y-2">
                {folderFiles.map((f) => (
                  <div key={f.id} className="flex items-center justify-between rounded-xl border border-gg-border bg-gg-s1 px-4 py-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <svg className="h-4 w-4 flex-shrink-0 text-gg-text2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                      </svg>
                      <span className="truncate text-sm text-gg-text">{f.file_name}</span>
                    </div>
                    <span className="text-xs text-gg-text3 flex-shrink-0 ml-4">{fmtBytes(f.size)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Shares */}
          <div>
            <h3 className="mb-3 text-sm font-medium text-gg-text2">Share Links ({folderShares.length})</h3>
            {folderShares.length === 0 ? (
              <p className="text-sm text-gg-text3">No active share links.</p>
            ) : (
              <div className="space-y-2">
                {folderShares.map((s) => (
                  <div key={s.id} className="flex items-center justify-between rounded-xl border border-gg-border bg-gg-s1 px-4 py-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          s.share_type === "public" ? "bg-green-500/15 text-green-400"
                          : s.share_type === "password" ? "bg-yellow-500/15 text-yellow-400"
                          : "bg-blue-500/15 text-blue-400"
                        }`}>
                          {s.share_type}
                        </span>
                        {s.expires_at && <span className="text-xs text-gg-text3">expires {s.expires_at.split("T")[0]}</span>}
                      </div>
                      <button
                        onClick={() => navigator.clipboard.writeText(`${shareBaseUrl}/shared/${s.token}`)}
                        className="mt-1 truncate text-xs text-violet-400 hover:text-violet-300"
                        title="Click to copy"
                      >
                        {shareBaseUrl}/shared/{s.token}
                      </button>
                    </div>
                    <button onClick={() => revokeShare(s.id)}
                      className="ml-4 flex-shrink-0 text-xs text-red-400 hover:text-red-300">
                      Revoke
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Share modal */}
          {showShare && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
              <div className="w-full max-w-md rounded-2xl border border-gg-border bg-gg-s1 p-6 shadow-2xl">
                <h2 className="mb-4 text-lg font-semibold text-gg-text">Share "{selectedFolder.name}"</h2>
                <form onSubmit={createShare} className="space-y-4">
                  <div className="flex gap-2">
                    {(["public", "user", "password"] as const).map((t) => (
                      <button
                        key={t} type="button"
                        onClick={() => setShareType(t)}
                        className={`flex-1 rounded-xl py-2 text-sm font-medium capitalize transition ${
                          shareType === t
                            ? "bg-violet-600 text-white"
                            : "border border-gg-border text-gg-text2 hover:bg-gg-bg"
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>

                  {shareType === "user" && (
                    <input
                      type="email" required placeholder="User email to share with"
                      value={shareEmail} onChange={(e) => setShareEmail(e.target.value)}
                      className="w-full rounded-xl border border-gg-border bg-gg-bg px-4 py-2.5 text-sm text-gg-text outline-none focus:border-violet-500/50"
                    />
                  )}
                  {shareType === "password" && (
                    <input
                      type="text" required placeholder="Access password"
                      value={sharePassword} onChange={(e) => setSharePassword(e.target.value)}
                      className="w-full rounded-xl border border-gg-border bg-gg-bg px-4 py-2.5 text-sm text-gg-text outline-none focus:border-violet-500/50"
                    />
                  )}
                  {shareType === "public" && (
                    <p className="text-sm text-gg-text2">Anyone with the link can view files in this folder.</p>
                  )}

                  <div className="flex gap-3">
                    <button type="submit" disabled={sharing}
                      className="flex-1 rounded-xl bg-violet-600 py-2.5 text-sm font-semibold text-white hover:bg-violet-500 disabled:opacity-40">
                      {sharing ? "Creating…" : "Create Link"}
                    </button>
                    <button type="button" onClick={() => setShowShare(false)}
                      className="flex-1 rounded-xl border border-gg-border py-2.5 text-sm text-gg-text hover:bg-gg-bg">
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="flex flex-1 items-center justify-center text-gg-text3">
          Select a folder to view its contents and share links
        </div>
      )}
    </div>
  );
}
