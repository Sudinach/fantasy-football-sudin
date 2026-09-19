import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { readSnapshot } from "@/lib/snapshot";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FPL Dashboard",
  description: "Personal Fantasy Premier League squad analysis and transfer suggestions",
};

function formatGeneratedAt(iso: string): string {
  return new Date(iso).toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  const snapshot = readSnapshot();

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-50">
        <header className="border-b border-zinc-200 dark:border-zinc-800">
          <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-2 px-4 py-3">
            <nav className="flex gap-4 text-sm font-medium">
              <Link href="/" className="hover:underline">
                Squad
              </Link>
              <Link href="/suggestions" className="hover:underline">
                Suggestions
              </Link>
              <Link href="/trend" className="hover:underline">
                Trend
              </Link>
            </nav>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              GW{snapshot.gameweek.current} &middot; updated {formatGeneratedAt(snapshot.generated_at)}
            </p>
          </div>
        </header>
        <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
