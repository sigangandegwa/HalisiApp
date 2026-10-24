"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Wordmark } from "@/components/brand/wordmark";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { LanguageToggle } from "./language-toggle";

const LINKS: { href: string; key: MessageKey }[] = [
  { href: "/", key: "nav.check" },
  { href: "/pay", key: "nav.pay" },
  { href: "/onboarding", key: "nav.business" },
  { href: "/report", key: "nav.report" },
  { href: "/login", key: "nav.login" },
];

/**
 * Three things on the bar: the name, the language, and a menu. Everything else lives in the menu,
 * a full-screen list of big words. `mix-blend-difference` keeps the bar legible over the
 * full-colour verdict panels without ever changing the page's colours.
 */
export function SiteNav() {
  const { t } = useI18n();
  const pathname = usePathname() ?? "/";
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const lenis = (window as unknown as { __lenis?: { stop: () => void; start: () => void } }).__lenis;
    const prev = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    lenis?.stop();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => {
      document.documentElement.style.overflow = prev;
      lenis?.start();
      window.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <>
      <header className="pointer-events-none fixed inset-x-0 top-0 z-40 text-white mix-blend-difference">
        <nav aria-label="Main" className="page-wrap pointer-events-auto flex h-16 items-center justify-between">
          <Link href="/" aria-label={t("nav.home")} className="text-[1rem]">
            <Wordmark />
          </Link>
          <div className="flex items-center gap-1">
            <LanguageToggle />
            <button
              type="button"
              aria-expanded={open}
              aria-controls="site-menu"
              onClick={() => setOpen((v) => !v)}
              className="inline-flex h-11 cursor-pointer items-center gap-2.5 pl-3 font-mono text-[0.8125rem] tracking-[0.1em] uppercase"
            >
              {open ? t("nav.close") : t("nav.menu")}
              <span aria-hidden="true" className="grid gap-[5px]">
                <span className={cn("block h-px w-5 bg-current transition-transform duration-(--dur-ui) ease-out", open && "translate-y-[3px] rotate-45")} />
                <span className={cn("block h-px w-5 bg-current transition-transform duration-(--dur-ui) ease-out", open && "-translate-y-[3px] -rotate-45")} />
              </span>
            </button>
          </div>
        </nav>
      </header>

      {open
        ? createPortal(
            <div id="site-menu" role="dialog" aria-modal="true" aria-label={t("nav.menu")} className="fixed inset-0 z-30 flex flex-col bg-bg pt-20 pb-8">
              <ul className="page-wrap grid flex-1 content-center gap-1">
                {LINKS.map((l, i) => {
                  const active = l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
                  return (
                    <li key={l.key} className="reveal-fade" style={{ ["--i" as string]: i }}>
                      <Link
                        href={l.href}
                        onClick={() => setOpen(false)}
                        aria-current={active ? "page" : undefined}
                        className="group flex items-baseline gap-4 py-1.5 font-display text-[clamp(2.75rem,12vw,6rem)] leading-[0.95] font-black uppercase aria-[current=page]:text-fg-3"
                      >
                        <span className="font-mono text-[0.75rem] font-medium tracking-[0.1em] text-fg-3">0{i + 1}</span>
                        <span className="transition-transform duration-(--dur-ui) ease-out group-hover:translate-x-2">{t(l.key)}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
              <p className="page-wrap text-small text-fg-3">{t("footer.privacy")}</p>
            </div>,
            document.body,
          )
        : null}
    </>
  );
}
