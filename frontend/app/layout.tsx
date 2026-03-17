import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/contexts/ThemeContext";

export const metadata: Metadata = {
  title: "GDriveGenie — Multiply Your Free Cloud Storage",
  description: "Aggregate multiple Google Drive accounts into one unified storage pool. Smart upload routing, drag-to-folder, analytics, and more. Free and self-hosted.",
  icons: { icon: "/favicon.svg" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
