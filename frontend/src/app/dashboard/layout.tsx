"use client";

import { ReactNode } from "react";
import { AlertProvider } from "@/components/merchant/alert-context";
import { AlertBell } from "@/components/merchant/alert-bell";
import { AlertDrawer } from "@/components/merchant/alert-drawer";
import { Wordmark } from "@/components/brand/wordmark";
import Link from "next/link";
import { usePathname } from "next/navigation";

// For the demo, we will use a fixed merchantId
const DEMO_MERCHANT_ID = "432ea21d-fcd0-57a7-bbc2-5f61d034526e"; // nairobi-sneaker-vault

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  const nav = [
    { name: "Overview", href: "/dashboard" },
    { name: "Onboarding", href: "/onboarding" },
    { name: "Simulator", href: "/simulator" },
  ];

  return (
    <AlertProvider merchantId={DEMO_MERCHANT_ID}>
      <div className="theme-night world-night min-h-screen flex flex-col font-sans text-fg bg-bg">
        <header className="sticky top-0 z-40 border-b border-line bg-bg/80 backdrop-blur-xl">
          <div className="page-grid h-16 items-center">
            <div className="col-span-3 flex items-center">
              <Link href="/dashboard" className="flex items-center gap-2 focus-visible rounded-sm">
                <Wordmark className="h-6 text-fg" />
                <span className="type-caption text-fg-2">Dashboard</span>
              </Link>
            </div>
            <nav className="col-span-6 flex items-center justify-center gap-6 type-caption">
              {nav.map((item) => (
                <Link 
                  key={item.name} 
                  href={item.href} 
                  className={`transition-colors hover:text-fg ${pathname === item.href ? 'text-fg' : 'text-fg-2'}`}
                >
                  {item.name}
                </Link>
              ))}
            </nav>
            <div className="col-span-3 flex items-center justify-end gap-4">
              <AlertBell />
            </div>
          </div>
        </header>
        <main className="flex-1 section-y page-wrap">
          {children}
        </main>
        <AlertDrawer />
      </div>
    </AlertProvider>
  );
}
