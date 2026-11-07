"use client";

import { ReactNode, useState } from "react";
import { AlertProvider } from "@/components/merchant/alert-context";
import { AlertBell } from "@/components/merchant/alert-bell";
import { AlertDrawer } from "@/components/merchant/alert-drawer";
import { Wordmark } from "@/components/brand/wordmark";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ExternalLink, LogOut } from "lucide-react";
import { toast } from "sonner";
import { useQuery } from "@tanstack/react-query";
import { api, qk } from "@/lib/api";

export function DashboardShell({
  merchantId,
  merchantSlug,
  children,
}: {
  merchantId: string;
  merchantSlug: string;
  children: ReactNode;
}) {
  const pathname = usePathname() ?? "/dashboard";
  const router = useRouter();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const { data: merchant } = useQuery({
    queryKey: qk.merchant(merchantSlug),
    queryFn: () => api.getMerchant(merchantSlug),
    enabled: Boolean(merchantSlug),
  });

  const proven = merchant ? merchant.is_verified : true;
  const nav = [
    {
      name: "Cases",
      href: "/dashboard",
      isExternal: false,
      match: (p: string) => p === "/dashboard" || p.startsWith("/dashboard/threat"),
    },
    {
      name: proven ? "Ownership" : "Verify",
      href: "/dashboard/verify",
      isExternal: false,
      match: (p: string) => p.startsWith("/dashboard/verify"),
    },
    {
      name: "Simulator",
      href: "/simulator",
      isExternal: false,
      match: (p: string) => p.startsWith("/simulator"),
    },
    ...(proven
      ? [
          {
            name: "Certificate",
            href: `/v/${merchantSlug}`,
            isExternal: true,
            match: (p: string) => p === `/v/${merchantSlug}`,
          },
        ]
      : []),
  ];

  async function handleLogout() {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    try {
      const res = await fetch("/api/session", { method: "DELETE" });
      if (res.ok) {
        toast.success("Logged out successfully.");
        router.push("/login");
        router.refresh();
      } else {
        toast.error("Failed to log out. Please try again.");
        setIsLoggingOut(false);
      }
    } catch {
      toast.error("Failed to log out. Please try again.");
      setIsLoggingOut(false);
    }
  }

  return (
    <AlertProvider merchantId={merchantId} merchantSlug={merchantSlug}>
      <div className="theme-night world-night min-h-screen flex flex-col font-sans text-fg bg-bg selection:bg-fg selection:text-bg">
        {/* Apple-style Translucent Floating Header with light-catching top edge */}
        <header className="sticky top-0 z-40 border-b border-line bg-bg/85 backdrop-blur-xl">
          <div className="page-wrap flex h-16 items-center justify-between gap-2 sm:gap-4">
            {/* Left: Brand */}
            <div className="flex items-center shrink-0">
              <Link
                href="/dashboard"
                className="flex items-center gap-2 rounded-sm focus-visible transition-transform duration-100 ease-out active:scale-[0.96]"
              >
                <Wordmark className="h-6 text-fg" />
                <span className="type-caption text-fg-3 hidden xs:inline">
                  Strike Console
                </span>
              </Link>
            </div>

            {/* Center: Seamless Navigation */}
            <nav
              aria-label="Merchant Navigation"
              className="flex items-center gap-1 sm:gap-1.5 overflow-x-auto no-scrollbar py-1"
            >
              {nav.map((item) => {
                const active = item.match(pathname);
                if (item.isExternal) {
                  return (
                    <a
                      key={item.name}
                      href={item.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group type-caption inline-flex h-11 items-center gap-1.5 px-3 text-fg-3 transition-colors duration-(--dur-micro) hover:text-fg shrink-0"
                    >
                      <span>{item.name}</span>
                      <ExternalLink
                        className="size-3 sm:size-3.5 opacity-60 transition-opacity group-hover:opacity-100"
                        aria-hidden="true"
                      />
                    </a>
                  );
                }

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={`type-caption relative inline-flex h-11 items-center px-3 transition-colors duration-(--dur-micro) shrink-0 after:absolute after:inset-x-3 after:bottom-1 after:h-px after:origin-left after:transition-transform after:duration-(--dur-ui) ${
                      active
                        ? "text-fg after:scale-x-100 after:bg-fg"
                        : "text-fg-3 hover:text-fg after:scale-x-0 after:bg-fg"
                    }`}
                  >
                    {item.name}
                  </Link>
                );
              })}
            </nav>

            {/* Right Area: Merchant Identity, Alerts Bell, Logout */}
            <div className="flex items-center justify-end gap-1.5 sm:gap-3 shrink-0">
              {/* Merchant Identity Badge */}
              <div
                className="hidden lg:inline-flex items-center gap-2 px-3 py-1 rounded-pill bg-fg/[0.04] border border-line text-xs font-mono text-fg-2 tracking-tight max-w-[190px]"
                title={`Signed in as ${merchant?.business_name || merchantSlug}`}
              >
                <span
                  className="size-1.5 rounded-full bg-fg shrink-0"
                  aria-hidden="true"
                />
                <span className="truncate font-sans font-medium text-fg">
                  {merchant?.business_name || merchantSlug}
                </span>
              </div>

              {/* In-app Alert Bell */}
              <AlertBell />

              {/* Dedicated Logout Button */}
              <button
                type="button"
                onClick={handleLogout}
                disabled={isLoggingOut}
                className="group inline-flex items-center gap-1.5 px-3 py-1.5 rounded-pill text-xs font-medium text-fg-2 hover:text-fg hover:bg-fg/5 border border-transparent hover:border-line transition-all duration-100 ease-out active:scale-[0.96] cursor-pointer disabled:opacity-50"
                title="Log out of merchant session"
                aria-label="Log out"
              >
                <LogOut
                  className="size-3.5 sm:size-4 transition-transform duration-100 group-hover:translate-x-0.5"
                  aria-hidden="true"
                />
                <span className="hidden sm:inline">Log out</span>
              </button>
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
