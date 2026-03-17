"use client";

import Link from "next/link";
import { useTheme } from "@/contexts/ThemeContext";

/* ─── Feature data ──────────────────────────────────────────────── */
const features = [
  {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375" />
      </svg>
    ),
    color: "text-violet-400",
    bg: "bg-violet-600/10",
    border: "border-violet-500/20",
    title: "Unified Storage Pool",
    desc: "Combine unlimited Google Drive accounts into one dashboard. N accounts × 15 GB = effectively unlimited free cloud storage.",
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
      </svg>
    ),
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
    title: "Smart Upload Routing",
    desc: "Least-Used-Space strategy automatically routes every upload to the account with the most free space. Zero manual management.",
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
      </svg>
    ),
    color: "text-sky-400",
    bg: "bg-sky-500/10",
    border: "border-sky-500/20",
    title: "Folder Navigation",
    desc: "Full folder hierarchy with breadcrumb bar, grid & list views, search, sort, and file type filters across all accounts.",
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 0 0-1.883 2.542l.857 6a2.25 2.25 0 0 0 2.227 1.932H19.05a2.25 2.25 0 0 0 2.227-1.932l.857-6a2.25 2.25 0 0 0-1.883-2.542m-16.5 0V6A2.25 2.25 0 0 1 6 3.75h3.879a1.5 1.5 0 0 1 1.06.44l2.122 2.12a1.5 1.5 0 0 0 1.06.44H18A2.25 2.25 0 0 1 20.25 9v.776" />
      </svg>
    ),
    color: "text-violet-400",
    bg: "bg-violet-500/10",
    border: "border-violet-500/20",
    title: "Drag-to-Folder Panel",
    desc: "Start dragging any file and a panel slides in showing every folder. Drop to move instantly — auto-scrolls for long lists.",
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M7.217 10.907a2.25 2.25 0 1 0 0 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186 9.566-5.314m-9.566 7.5 9.566 5.314m0 0a2.25 2.25 0 1 0 3.935 2.186 2.25 2.25 0 0 0-3.935-2.186zm0-12.814a2.25 2.25 0 1 0 3.933-2.185 2.25 2.25 0 0 0-3.933 2.185z" />
      </svg>
    ),
    color: "text-indigo-400",
    bg: "bg-indigo-500/10",
    border: "border-indigo-500/20",
    title: "Shared with Me",
    desc: "Browse and navigate into folders that others have shared with your Drive accounts. Download directly from the shared view.",
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
      </svg>
    ),
    color: "text-rose-400",
    bg: "bg-rose-500/10",
    border: "border-rose-500/20",
    title: "Trash Management",
    desc: "Delete sends files to Drive trash — nothing is gone for good. Restore any file or permanently delete from the Trash page.",
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    title: "Secure Local Access",
    desc: "PIN-protected with bcrypt hashing. Secrets live in the database — no .env files, no cloud auth service, no telemetry.",
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
    color: "text-violet-400",
    bg: "bg-violet-600/10",
    border: "border-violet-500/20",
    title: "Rich Analytics",
    desc: "Storage breakdown per account, file type distribution, weekly upload activity, and per-type storage bars — all client-side.",
  },
  {
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
      </svg>
    ),
    color: "text-pink-400",
    bg: "bg-pink-500/10",
    border: "border-pink-500/20",
    title: "Open Source",
    desc: "100% free and open source. Self-hosted, privacy-first. Inspect every line, contribute improvements, or fork it for your needs.",
  },
];

/* ─── App logo icon ─────────────────────────────────────────────── */
function AppIcon({ size = 8, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      className={`h-${size} w-${size} ${className}`}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="appIconBg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#7c3aed" />
          <stop offset="100%" stopColor="#4338ca" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="7" fill="url(#appIconBg)" />
      <rect width="32" height="16" rx="7" fill="rgba(255,255,255,0.15)" />
      <path
        d="M7 22a8.5 8.5 0 01-2.3-16.7 11 11 0 0121.4-2.3 6 6 0 018.1 8A7.9 7.9 0 0137 22"
        stroke="white"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="rgba(255,255,255,0.1)"
      />
      <path
        d="M34 6l1.3 4 4 1.3-4 1.3L34 16.5 32.7 12.6l-4-1.3 4-1.3z"
        fill="white"
        opacity="0.9"
      />
    </svg>
  );
}

/* ─── Dashboard app preview illustration ───────────────────────── */
function DashboardPreview() {
  return (
    <div className="relative mx-auto max-w-4xl">
      {/* Glow behind the window */}
      <div className="absolute inset-0 -z-10 rounded-3xl bg-violet-600/10 blur-3xl" />
      <div className="absolute -inset-4 -z-10 rounded-3xl bg-indigo-600/5 blur-2xl" />

      {/* Browser window frame */}
      <div className="overflow-hidden rounded-2xl border border-gg-border bg-gg-s1 shadow-2xl shadow-black/50">
        {/* Title bar */}
        <div className="flex items-center gap-2 border-b border-gg-border bg-gg-sidebar px-4 py-3">
          <div className="flex gap-1.5">
            <div className="h-3 w-3 rounded-full bg-rose-500/70" />
            <div className="h-3 w-3 rounded-full bg-amber-500/70" />
            <div className="h-3 w-3 rounded-full bg-emerald-500/70" />
          </div>
          <div className="mx-auto flex w-56 items-center gap-1.5 rounded-md border border-gg-border bg-gg-s2 px-3 py-1">
            <svg className="h-3 w-3 text-gg-text3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5a6 6 0 11-12 0 6 6 0 0112 0zM21 21l-4.35-4.35" />
            </svg>
            <span className="text-xs text-gg-text3">app.gdriveGenie.local</span>
          </div>
          <div className="w-16" />
        </div>

        {/* App layout */}
        <div className="flex" style={{ height: 340 }}>
          {/* Sidebar */}
          <div className="flex w-44 flex-shrink-0 flex-col border-r border-gg-border bg-gg-sidebar px-3 py-4">
            {/* Logo */}
            <div className="mb-5 flex items-center gap-2 px-1">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-violet-600/20 border border-violet-500/30">
                <svg className="h-3 w-3 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z" />
                </svg>
              </div>
              <span className="text-xs font-semibold text-gg-text">GDriveGenie</span>
            </div>

            {/* Nav items */}
            {[
              { label: "Overview", active: true, color: "text-violet-400 bg-violet-600/10" },
              { label: "Files", active: false, color: "" },
              { label: "Shared", active: false, color: "" },
              { label: "Trash", active: false, color: "" },
              { label: "Analytics", active: false, color: "" },
              { label: "Settings", active: false, color: "" },
            ].map((item) => (
              <div
                key={item.label}
                className={`mb-0.5 flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs transition ${
                  item.active
                    ? "font-semibold text-violet-400 bg-violet-600/10"
                    : "text-gg-text3"
                }`}
              >
                <div className={`h-1.5 w-1.5 rounded-full ${item.active ? "bg-violet-400" : "bg-gg-text3/40"}`} />
                {item.label}
              </div>
            ))}

            {/* Storage bar at bottom */}
            <div className="mt-auto px-1">
              <div className="mb-1 flex justify-between text-[10px] text-gg-text3">
                <span>Storage Pool</span>
                <span>47%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-gg-s2">
                <div className="h-full w-[47%] rounded-full bg-gradient-to-r from-violet-600 to-indigo-500" />
              </div>
              <div className="mt-1 text-[10px] text-gg-text3">42.3 GB / 90 GB used</div>
            </div>
          </div>

          {/* Main content */}
          <div className="flex-1 overflow-hidden bg-gg-bg p-4">
            {/* Stat cards row */}
            <div className="mb-4 grid grid-cols-3 gap-3">
              {[
                { label: "Total Files", value: "2,847", icon: "📁", color: "text-violet-400" },
                { label: "Storage Used", value: "42.3 GB", icon: "💾", color: "text-sky-400" },
                { label: "Accounts", value: "6", icon: "🔗", color: "text-emerald-400" },
              ].map((card) => (
                <div key={card.label} className="rounded-xl border border-gg-border bg-gg-s1 p-3">
                  <div className="mb-1 text-[10px] text-gg-text3">{card.label}</div>
                  <div className={`text-base font-bold ${card.color}`}>{card.value}</div>
                </div>
              ))}
            </div>

            {/* Account storage bars */}
            <div className="mb-4 rounded-xl border border-gg-border bg-gg-s1 p-3">
              <div className="mb-2.5 text-xs font-medium text-gg-text">Account Storage</div>
              {[
                { email: "user1@gmail.com", used: 78, color: "from-violet-600 to-indigo-500" },
                { email: "user2@gmail.com", used: 52, color: "from-sky-500 to-blue-600" },
                { email: "user3@gmail.com", used: 34, color: "from-emerald-500 to-teal-600" },
              ].map((acc) => (
                <div key={acc.email} className="mb-2 last:mb-0">
                  <div className="mb-1 flex justify-between text-[10px]">
                    <span className="text-gg-text2 truncate max-w-[120px]">{acc.email}</span>
                    <span className="text-gg-text3">{acc.used}%</span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-gg-s2">
                    <div
                      className={`h-full rounded-full bg-gradient-to-r ${acc.color}`}
                      style={{ width: `${acc.used}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Recent files mini list */}
            <div className="rounded-xl border border-gg-border bg-gg-s1 p-3">
              <div className="mb-2 text-xs font-medium text-gg-text">Recent Files</div>
              {[
                { name: "presentation.pdf", size: "12.4 MB", type: "pdf" },
                { name: "photo_vacation.jpg", size: "8.1 MB", type: "img" },
                { name: "audio_track.mp3", size: "44.2 MB", type: "aud" },
              ].map((f) => (
                <div key={f.name} className="flex items-center gap-2 py-1.5 border-b border-gg-border/50 last:border-0">
                  <div className="flex h-5 w-5 items-center justify-center rounded text-[8px] font-bold bg-gg-s2 text-gg-text3 flex-shrink-0">
                    {f.type.toUpperCase()}
                  </div>
                  <span className="flex-1 truncate text-[10px] text-gg-text2">{f.name}</span>
                  <span className="text-[10px] text-gg-text3">{f.size}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── How it works steps ─────────────────────────────────────────── */
const steps = [
  {
    n: "01",
    title: "Create Google OAuth Credentials",
    desc: "Set up a Google Cloud project and create OAuth 2.0 credentials for each Gmail account you want to pool. Takes about 5 minutes per account.",
    color: "text-violet-400",
    bg: "bg-violet-600/10",
    border: "border-violet-500/20",
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
      </svg>
    ),
  },
  {
    n: "02",
    title: "Generate Secrets & Start Servers",
    desc: "Run the one-time setup script to create your dashboard PIN, JWT secret, and encryption key. Then start the backend and frontend with a single docker compose up.",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 7.5l3 2.25-3 2.25m4.5 0h3m-9 8.25h13.5A2.25 2.25 0 0021 18V6a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003 6v12a2.25 2.25 0 002.25 2.25z" />
      </svg>
    ),
  },
  {
    n: "03",
    title: "Connect Accounts & Go",
    desc: "Open the dashboard, add your Google Drive accounts via OAuth, and start uploading. GDriveGenie routes every file to the account with the most free space automatically.",
    color: "text-sky-400",
    bg: "bg-sky-500/10",
    border: "border-sky-500/20",
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
      </svg>
    ),
  },
];

/* ─── Dashboard views showcase data ─────────────────────────────── */
const views = [
  {
    label: "Overview",
    color: "text-violet-400",
    bg: "bg-violet-600/10",
    border: "border-violet-500/20",
    desc: "Stats cards, per-account storage bars, file type breakdown, and recent files at a glance.",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
      </svg>
    ),
  },
  {
    label: "Files",
    color: "text-sky-400",
    bg: "bg-sky-500/10",
    border: "border-sky-500/20",
    desc: "Upload, browse, rename, move via drag panel, download, and trash files across all accounts.",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
      </svg>
    ),
  },
  {
    label: "Shared with Me",
    color: "text-violet-400",
    bg: "bg-violet-500/10",
    border: "border-violet-500/20",
    desc: "Browse files and navigate into folders that other people have shared with your Drive accounts.",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M7.217 10.907a2.25 2.25 0 1 0 0 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186 9.566-5.314m-9.566 7.5 9.566 5.314m0 0a2.25 2.25 0 1 0 3.935 2.186 2.25 2.25 0 0 0-3.935-2.186zm0-12.814a2.25 2.25 0 1 0 3.933-2.185 2.25 2.25 0 0 0-3.933 2.185z" />
      </svg>
    ),
  },
  {
    label: "Trash",
    color: "text-rose-400",
    bg: "bg-rose-500/10",
    border: "border-rose-500/20",
    desc: "See all trashed files across every account, restore them to Drive, or permanently delete.",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
      </svg>
    ),
  },
  {
    label: "Analytics",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    desc: "Weekly upload activity, storage by account, file type distribution, and per-type bars — Recharts-powered.",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
  },
  {
    label: "Settings",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
    desc: "Connect or disconnect Drive accounts, view quotas per account, and manage your profile.",
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
      </svg>
    ),
  },
];

/* ─── GitHub star count display ─────────────────────────────────── */
function GitHubIcon() {
  return (
    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.02 10.02 0 0 0 22 12.017C22 6.484 17.522 2 12 2z" />
    </svg>
  );
}

/* ─── Main page ──────────────────────────────────────────────────── */
export default function LandingPage() {
  const { theme, toggle } = useTheme();

  return (
    <div className="min-h-screen bg-gg-bg text-gg-text">

      {/* ── Navbar ───────────────────────────────────────────── */}
      <nav className="sticky top-0 z-50 border-b border-gg-border/60 bg-gg-bg/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3.5 sm:px-6">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-600/15 border border-violet-500/25">
              <svg className="h-4 w-4 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z" />
              </svg>
            </div>
            <span className="text-sm font-bold tracking-tight text-gg-text">GDriveGenie</span>
          </div>

          {/* Nav links + actions */}
          <div className="flex items-center gap-2">
            <Link href="/docs" className="hidden rounded-md px-3 py-1.5 text-xs text-gg-text2 transition hover:bg-gg-hover hover:text-gg-text sm:inline">
              Docs
            </Link>
            <Link href="/docs#faq" className="hidden rounded-md px-3 py-1.5 text-xs text-gg-text2 transition hover:bg-gg-hover hover:text-gg-text md:inline">
              FAQ
            </Link>

            <button
              onClick={toggle}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-gg-border text-gg-text2 transition hover:bg-gg-hover hover:text-gg-text"
              title="Toggle theme"
            >
              {theme === "dark" ? (
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" />
                </svg>
              ) : (
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.72 9.72 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z" />
                </svg>
              )}
            </button>

            <a
              href="https://github.com/saimon4u/GDriveGenie"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 rounded-lg border border-gg-border px-3 py-1.5 text-xs text-gg-text2 transition hover:border-violet-500/40 hover:bg-gg-hover hover:text-gg-text"
            >
              <GitHubIcon />
              <span className="hidden sm:inline">GitHub</span>
            </a>

            <Link
              href="/login"
              className="flex items-center gap-1.5 rounded-lg bg-violet-600 px-4 py-1.5 text-xs font-semibold text-white shadow-md shadow-violet-600/25 transition hover:bg-violet-500"
            >
              Open App
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="relative overflow-hidden pb-0 pt-16 md:pt-24">
        {/* Background effects */}
        <div className="dot-bg absolute inset-0 opacity-60" />
        <div className="absolute -top-32 left-1/2 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-violet-600/10 blur-3xl" />
        <div className="absolute top-20 right-[10%] h-72 w-72 rounded-full bg-indigo-600/8 blur-3xl" />
        <div className="absolute top-40 left-[5%] h-56 w-56 rounded-full bg-purple-600/8 blur-3xl" />
        <div className="absolute bottom-0 inset-x-0 h-48 bg-gradient-to-b from-transparent to-gg-bg" />

        <div className="relative mx-auto max-w-6xl px-4 sm:px-6">
          {/* Badge */}
          <div className="animate-fade-up mb-6 flex justify-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/25 bg-violet-600/8 px-4 py-1.5 shadow-sm shadow-violet-600/10">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-violet-400 opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-violet-500" />
              </span>
              <span className="text-xs font-medium text-violet-400">Open Source · Free Forever · Self-Hosted</span>
            </div>
          </div>

          {/* Headline */}
          <div className="animate-fade-up-d1 mb-6 text-center">
            <h1 className="text-5xl font-extrabold leading-[1.1] tracking-tight text-gg-text md:text-7xl">
              Your Storage,{" "}
              <span className="gradient-text">Multiplied.</span>
            </h1>
          </div>

          {/* Subtitle */}
          <p className="animate-fade-up-d2 mx-auto mb-10 max-w-2xl text-center text-lg leading-relaxed text-gg-text2">
            GDriveGenie aggregates multiple Google Drive accounts into one unified dashboard.
            Get up to <strong className="font-semibold text-gg-text">N × 15 GB</strong> free cloud storage
            with smart routing, folder navigation, analytics, and more — all self-hosted.
          </p>

          {/* CTAs */}
          <div className="animate-fade-up-d3 mb-14 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/login"
              className="flex items-center gap-2 rounded-xl bg-violet-600 px-7 py-3.5 text-sm font-semibold text-white shadow-xl shadow-violet-600/30 transition hover:bg-violet-500 hover:shadow-violet-500/40"
            >
              Open Dashboard
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </Link>
            <Link
              href="/docs"
              className="flex items-center gap-2 rounded-xl border border-gg-border bg-gg-s1 px-7 py-3.5 text-sm font-semibold text-gg-text transition hover:border-violet-500/40 hover:bg-gg-hover"
            >
              <svg className="h-4 w-4 text-gg-text2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
              </svg>
              Setup Guide
            </Link>
            <a
              href="https://github.com/saimon4u/GDriveGenie"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-xl border border-gg-border bg-gg-s1 px-5 py-3.5 text-sm font-semibold text-gg-text2 transition hover:border-violet-500/40 hover:bg-gg-hover hover:text-gg-text"
            >
              <GitHubIcon />
              Star on GitHub
            </a>
          </div>

          {/* Dashboard preview */}
          <div className="animate-fade-up-d4">
            <DashboardPreview />
          </div>
        </div>
      </section>

      {/* ── Stats strip ──────────────────────────────────────── */}
      <section className="border-y border-gg-border bg-gg-s1/50 py-10">
        <div className="mx-auto max-w-4xl px-6">
          <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
            {[
              { value: "15 GB", label: "Free per Drive account", color: "text-violet-400" },
              { value: "∞", label: "Accounts you can connect", color: "text-sky-400" },
              { value: "$0", label: "Cost — free forever", color: "text-emerald-400" },
              { value: "0", label: "Bytes of your data shared", color: "text-pink-400" },
            ].map((s) => (
              <div key={s.label} className="text-center">
                <div className={`text-3xl font-extrabold ${s.color}`}>{s.value}</div>
                <div className="mt-1 text-xs text-gg-text3">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
        <div className="mb-14 text-center">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-sky-500/20 bg-sky-500/5 px-3.5 py-1">
            <span className="text-xs font-medium text-sky-400">Setup in 15 minutes</span>
          </div>
          <h2 className="text-3xl font-bold text-gg-text md:text-4xl">
            How it works
          </h2>
          <p className="mt-4 text-gg-text2">Three steps from zero to unlimited cloud storage.</p>
        </div>

        <div className="relative grid gap-8 md:grid-cols-3">
          {/* Connecting line (desktop) */}
          <div className="absolute left-[calc(16.67%+1rem)] right-[calc(16.67%+1rem)] top-10 hidden h-px bg-gradient-to-r from-gg-border via-violet-500/30 to-gg-border md:block" />

          {steps.map((step) => (
            <div key={step.n} className="relative flex flex-col items-center text-center">
              {/* Step number circle */}
              <div className={`relative mb-6 flex h-20 w-20 items-center justify-center rounded-2xl border ${step.border} ${step.bg} shadow-lg`}>
                <span className={step.color}>{step.icon}</span>
                <span className={`absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full border ${step.border} bg-gg-s1 text-xs font-bold ${step.color}`}>
                  {step.n}
                </span>
              </div>
              <h3 className="mb-2 text-base font-semibold text-gg-text">{step.title}</h3>
              <p className="text-sm leading-relaxed text-gg-text2">{step.desc}</p>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <Link
            href="/docs"
            className="inline-flex items-center gap-2 rounded-xl border border-gg-border bg-gg-s1 px-6 py-3 text-sm font-semibold text-gg-text transition hover:border-violet-500/40 hover:bg-gg-hover"
          >
            <svg className="h-4 w-4 text-gg-text2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
            </svg>
            Read the Full Setup Guide
          </Link>
        </div>
      </section>

      {/* ── Features grid ────────────────────────────────────── */}
      <section className="border-t border-gg-border bg-gg-s1/40 py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mb-14 text-center">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-600/5 px-3.5 py-1">
              <span className="text-xs font-medium text-violet-400">Fully-featured</span>
            </div>
            <h2 className="text-3xl font-bold text-gg-text md:text-4xl">
              Everything you need,{" "}
              <span className="gradient-text">nothing you don&apos;t</span>
            </h2>
            <p className="mt-4 max-w-xl mx-auto text-gg-text2">
              A focused set of features built for power users who want more from their free cloud storage.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f) => (
              <div
                key={f.title}
                className={`group relative overflow-hidden rounded-2xl border ${f.border} bg-gg-s1/80 p-5 backdrop-blur-sm transition hover:bg-gg-hover hover:shadow-xl hover:shadow-black/20`}
              >
                {/* Corner glow */}
                <div className="absolute right-0 top-0 h-20 w-20 rounded-bl-full bg-gradient-to-bl from-white/[0.02] to-transparent opacity-0 transition group-hover:opacity-100" />

                <div className={`mb-4 inline-flex rounded-xl p-2.5 ${f.bg}`}>
                  <span className={f.color}>{f.icon}</span>
                </div>
                <h3 className="mb-1.5 font-semibold text-gg-text">{f.title}</h3>
                <p className="text-sm leading-relaxed text-gg-text2">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Dashboard views showcase ─────────────────────────── */}
      <section className="py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mb-14 text-center">
            <h2 className="text-3xl font-bold text-gg-text md:text-4xl">
              Six dedicated views,{" "}
              <span className="gradient-text">one coherent app</span>
            </h2>
            <p className="mt-4 text-gg-text2">
              Every section of GDriveGenie is purpose-built — no bloat, no clutter.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {views.map((v) => (
              <div
                key={v.label}
                className={`rounded-2xl border ${v.border} bg-gg-s1/60 p-5 transition hover:bg-gg-hover`}
              >
                <div className="mb-3 flex items-center gap-2.5">
                  <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${v.bg}`}>
                    <span className={v.color}>{v.icon}</span>
                  </div>
                  <span className={`text-sm font-semibold ${v.color}`}>{v.label}</span>
                </div>
                <p className="text-sm leading-relaxed text-gg-text2">{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Tech stack strip ─────────────────────────────────── */}
      <section className="border-y border-gg-border bg-gg-s1/40 py-12">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <p className="mb-8 text-xs font-medium uppercase tracking-widest text-gg-text3">Built with</p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            {[
              { label: "Next.js 15", color: "text-gg-text2", bg: "bg-gg-s2", border: "border-gg-border" },
              { label: "React 19", color: "text-sky-400", bg: "bg-sky-500/5", border: "border-sky-500/20" },
              { label: "FastAPI", color: "text-emerald-400", bg: "bg-emerald-500/5", border: "border-emerald-500/20" },
              { label: "Cloudflare D1", color: "text-amber-400", bg: "bg-amber-500/5", border: "border-amber-500/20" },
              { label: "Google Drive API", color: "text-blue-400", bg: "bg-blue-500/5", border: "border-blue-500/20" },
              { label: "Recharts", color: "text-violet-400", bg: "bg-violet-600/5", border: "border-violet-500/20" },
              { label: "Tailwind CSS", color: "text-cyan-400", bg: "bg-cyan-500/5", border: "border-cyan-500/20" },
              { label: "TypeScript", color: "text-blue-300", bg: "bg-blue-500/5", border: "border-blue-400/20" },
            ].map((tech) => (
              <div
                key={tech.label}
                className={`rounded-full border ${tech.border} ${tech.bg} px-4 py-1.5 text-xs font-medium ${tech.color}`}
              >
                {tech.label}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Open Source CTA ──────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
        <div className="relative overflow-hidden rounded-3xl border border-violet-500/25 bg-gradient-to-br from-violet-600/8 via-gg-s1 to-indigo-600/8 p-12 text-center shadow-2xl shadow-violet-600/5">
          {/* Decorative elements */}
          <div className="absolute inset-0 dot-bg opacity-20" />
          <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-violet-600/8 blur-3xl" />
          <div className="absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-indigo-600/8 blur-3xl" />

          {/* Corner stars */}
          <div className="absolute right-12 top-10 opacity-60">
            <svg width="24" height="24" fill="none" viewBox="0 0 24 24">
              <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z" fill="#a78bfa" opacity="0.6"/>
            </svg>
          </div>
          <div className="absolute left-10 bottom-10 opacity-40">
            <svg width="16" height="16" fill="none" viewBox="0 0 24 24">
              <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z" fill="#818cf8" opacity="0.6"/>
            </svg>
          </div>

          <div className="relative">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-600/10 px-4 py-1.5">
              <GitHubIcon />
              <span className="text-xs font-medium text-violet-400">Open Source Initiative</span>
            </div>
            <h2 className="mb-4 text-3xl font-bold text-gg-text md:text-4xl">
              Built in the open, for everyone
            </h2>
            <p className="mx-auto mb-8 max-w-xl text-gg-text2">
              GDriveGenie is free software. Inspect every line, contribute improvements, report issues,
              or fork it for your own use. No vendor lock-in. No subscription. No data harvesting.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3">
              <a
                href="https://github.com/saimon4u/GDriveGenie"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 rounded-xl border border-violet-500/30 bg-violet-600/10 px-6 py-3 text-sm font-semibold text-violet-400 transition hover:bg-violet-600/20"
              >
                <GitHubIcon />
                View on GitHub
              </a>
              <Link
                href="/login"
                className="rounded-xl bg-violet-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-violet-600/25 transition hover:bg-violet-500"
              >
                Start Using GDriveGenie →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────── */}
      <footer className="border-t border-gg-border bg-gg-s1 py-10">
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-between">
            {/* Logo */}
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg border border-violet-500/20 bg-violet-600/10">
                <svg className="h-3.5 w-3.5 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z" />
                </svg>
              </div>
              <span className="text-sm font-semibold text-gg-text">GDriveGenie</span>
            </div>

            {/* Links */}
            <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-gg-text3">
              <Link href="/docs" className="transition hover:text-gg-text2">Docs</Link>
              <Link href="/docs#faq" className="transition hover:text-gg-text2">FAQ</Link>
              <a href="https://github.com/saimon4u/GDriveGenie" target="_blank" rel="noopener noreferrer" className="transition hover:text-gg-text2">GitHub</a>
              <a href="https://github.com/saimon4u/GDriveGenie/issues" target="_blank" rel="noopener noreferrer" className="transition hover:text-gg-text2">Issues</a>
            </div>

            <p className="text-xs text-gg-text3">
              Free &amp; open source · Self-hosted Google Drive aggregator
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
