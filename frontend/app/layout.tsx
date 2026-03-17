import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/contexts/ThemeContext";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(BASE_URL),
  title: {
    default: "GDriveGenie — Multiply Your Free Cloud Storage",
    template: "%s · GDriveGenie",
  },
  description:
    "Aggregate multiple Google Drive accounts into one unified storage pool. Smart upload routing, drag-to-folder, analytics, and more. Free and self-hosted.",
  keywords: ["Google Drive", "cloud storage", "storage aggregator", "self-hosted", "open source", "file manager"],
  authors: [{ name: "GDriveGenie" }],
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
    apple: "/apple-touch-icon.svg",
  },
  openGraph: {
    type: "website",
    url: BASE_URL,
    title: "GDriveGenie — Multiply Your Free Cloud Storage",
    description:
      "Aggregate multiple Google Drive accounts into one unified dashboard. Get N × 15 GB free storage with smart routing, analytics, and more.",
    images: [{ url: "/og-image.svg", width: 1200, height: 630, alt: "GDriveGenie — Your Storage, Multiplied" }],
    siteName: "GDriveGenie",
  },
  twitter: {
    card: "summary_large_image",
    title: "GDriveGenie — Multiply Your Free Cloud Storage",
    description: "Aggregate multiple Google Drive accounts into one unified dashboard. Free, open source, self-hosted.",
    images: ["/og-image.svg"],
  },
  robots: { index: true, follow: true },
  themeColor: "#7c3aed",
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
