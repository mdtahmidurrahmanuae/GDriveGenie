"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import Navbar from "@/components/Navbar";
import { UploadProvider } from "@/contexts/UploadContext";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);

  useEffect(() => {
    fetch("/api/auth/me", { credentials: "include" })
      .then((r) => r.ok ? r.json() : null)
      .then((d) => { if (d?.is_super_admin) setIsSuperAdmin(true); })
      .catch(() => {});
  }, []);

  return (
    <UploadProvider>
      <div className="flex h-screen overflow-hidden bg-gg-bg">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} isSuperAdmin={isSuperAdmin} />
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <Navbar onMenuOpen={() => setSidebarOpen(true)} />
          <main id="gg-scroll" className="flex-1 overflow-y-auto p-4 lg:p-8">
            {children}
          </main>
        </div>
      </div>
    </UploadProvider>
  );
}
