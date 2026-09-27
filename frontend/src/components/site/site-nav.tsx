"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Menu } from "lucide-react";
import { Wordmark } from "@/components/brand/wordmark";
import { Microprint } from "@/components/brand/microprint";
import { buttonVariants } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { LanguageToggle } from "./language-toggle";

const LINKS: { href: string; key: MessageKey; match: (p: string) => boolean }[] = [
  { href: "/", key: "nav.check", match: (p) => p === "/" || p.startsWith("/check") },
  { href: "/pay", key: "nav.pay", match: (p) => p.startsWith("/pay") },
  { href: "/#business", key: "nav.business", match: (p) => p.startsWith("/v/") },
  { href: "/report", key: "nav.report", match: (p) => p.startsWith("/report") },
];

/** Paper top nav (FRONTEND.md section 5). Mobile: wordmark + language + menu sheet. */
export function SiteNav() {
  const { t } = useI18n();
  const pathname = usePathname() ?? "/";
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "sticky top-0 z-40 transition-[background-color,border-color] duration-(--dur-ui) ease-quart",
        scrolled ? "border-b border-line bg-[color-mix(in_oklab,var(--bg)_92%,transparent)] backdrop-blur-[6px]" : "border-b border-transparent",
      )}
    >
      <nav aria-label="Main" className="page-wrap flex h-14 items-center gap-6 md:h-16">
        <Link href="/" aria-label={t("nav.home")} className="rounded-pill text-[1rem] text-fg md:text-[1.0625rem]">
          <Wordmark />
        </Link>

        <ul className="ml-auto hidden items-center gap-1 lg:flex">
          {LINKS.map((l) => {
            const active = l.match(pathname);
            return (
              <li key={l.key}>
                <Link
                  href={l.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "relative inline-flex h-10 items-center rounded-pill px-3.5 text-[0.9375rem] font-medium transition-colors duration-(--dur-ui) ease-quart",
                    active ? "text-fg" : "text-fg-2 hover:text-fg",
                  )}
                >
                  {t(l.key)}
                  <span
                    aria-hidden="true"
                    className={cn(
                      "absolute inset-x-3.5 bottom-1.5 h-px origin-left bg-fg transition-transform duration-(--dur-ui) ease-out",
                      active ? "scale-x-100" : "scale-x-0",
                    )}
                  />
                </Link>
              </li>
            );
          })}
        </ul>

        <div className="ml-auto flex items-center gap-3 lg:ml-2">
          <LanguageToggle />
          <Link href="/login" className={cn(buttonVariants({ variant: "secondary", size: "sm" }), "hidden sm:inline-flex")}>
            {t("nav.login")}
          </Link>
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger
              aria-label={t("nav.menu")}
              className={cn(buttonVariants({ variant: "ghost", size: "icon" }), "lg:hidden")}
            >
              <Menu className="size-5" strokeWidth={1.5} />
            </SheetTrigger>
            <SheetContent closeLabel={t("nav.close")} className="paper-grain">
              <SheetTitle className="sr-only">{t("nav.menu")}</SheetTitle>
              <div className="flex h-full flex-col px-6 pt-20 pb-8">
                <ul className="grid gap-1">
                  {LINKS.map((l, i) => (
                    <li key={l.key} className="reveal-fade" style={{ ["--i" as string]: i }}>
                      <Link
                        href={l.href}
                        onClick={() => setOpen(false)}
                        aria-current={l.match(pathname) ? "page" : undefined}
                        className="block rounded-doc py-2 font-display text-[2.25rem] leading-tight tracking-[-0.03em] aria-[current=page]:italic"
                      >
                        {t(l.key)}
                      </Link>
                    </li>
                  ))}
                </ul>
                <div className="mt-auto grid gap-4">
                  <Link href="/login" onClick={() => setOpen(false)} className={buttonVariants({ variant: "primary", size: "lg" })}>
                    {t("nav.login")}
                  </Link>
                  <Microprint />
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </nav>
    </header>
  );
}
