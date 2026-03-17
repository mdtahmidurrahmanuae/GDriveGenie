"use client";

import { useRef, useState } from "react";

export default function UploadZone({ onUploadComplete }: { onUploadComplete: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [lastAccount, setLastAccount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  function uploadFile(file: File) {
    setProgress(0);
    setError(null);
    setLastAccount(null);

    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/files/upload");
    xhr.withCredentials = true;

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        setProgress(Math.round((e.loaded / e.total) * 100));
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status === 201) {
        const data = JSON.parse(xhr.responseText);
        setLastAccount(data.account_index);
        setProgress(null);
        onUploadComplete();
      } else {
        setError("Upload failed. Please try again.");
        setProgress(null);
      }
    });

    xhr.addEventListener("error", () => {
      setError("Network error during upload.");
      setProgress(null);
    });

    xhr.send(formData);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
    e.target.value = "";
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => progress === null && inputRef.current?.click()}
      className={`relative cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition-all ${
        dragging
          ? "border-violet-500/60 bg-violet-600/5 shadow-lg shadow-violet-600/5"
          : "border-gg-border hover:border-violet-500/30 hover:bg-gg-hover"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        onChange={handleFileInput}
      />

      {progress !== null ? (
        <div className="space-y-3">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-violet-600/10">
            <svg className="h-6 w-6 animate-pulse text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
            </svg>
          </div>
          <p className="text-sm text-gg-text2">Uploading… <span className="font-medium text-gg-text">{progress}%</span></p>
          <div className="mx-auto h-1.5 w-48 overflow-hidden rounded-full bg-gg-border">
            <div
              className="h-full rounded-full bg-violet-600 transition-all duration-200"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-gg-border bg-gg-s2">
            <svg className="h-6 w-6 text-gg-text3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
            </svg>
          </div>
          <div>
            <p className="text-sm text-gg-text2">
              Drag & drop or <span className="font-medium text-violet-400">browse</span>
            </p>
            <p className="mt-1 text-xs text-gg-text3">Routed to the account with most free space</p>
          </div>
        </div>
      )}

      {lastAccount !== null && progress === null && (
        <div className="mt-4 inline-flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-3 py-1">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          <p className="text-xs text-emerald-400">Uploaded to account #{lastAccount}</p>
        </div>
      )}
      {error && (
        <p className="mt-4 text-xs text-red-400">{error}</p>
      )}
    </div>
  );
}
