"use client";

import { useReducedMotion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { CountUp } from "@/components/checker/count-up";
import { useI18n } from "@/lib/i18n/provider";
import type { Stats } from "@/lib/schemas";

/**
 * Live numbers from /stats (FRONTEND.md 6.1.4), one count-up on first view. No invented market
 * statistics: these are the API's own counts (or the labelled offline demo set).
 */
export function ProofBand({ stats }: { stats: Stats | null }) {
  const { t } = useI18n();
  const ref = useRef<HTMLElement>(null);
  const [seen, setSeen] = useState(false);
  const reduced = useReducedMotion() ?? false;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => e?.isIntersecting && (setSeen(true), io.disconnect()), { threshold: 0.4 });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  if (!stats) return null;
  const items = [
    { label: t("proof.scanned"), value: stats.pages_scanned },
    { label: t("proof.caught"), value: stats.impersonations_blocked_7d },
    { label: t("proof.protected"), value: stats.merchants_protected },
  ];
  return (
    <section ref={ref} aria-labelledby="proof-title" className="border-y border-line bg-bg-2">
      <div className="page-grid gap-y-10 py-14 md:py-20">
        <div className="col-span-12 md:col-span-3">
          <h2 id="proof-title" className="type-caption text-fg-2">{t("proof.eyebrow")}</h2>
          <p className="mt-3 max-w-[24ch] text-small text-fg-3">{t("proof.note")}</p>
        </div>
        <dl className="col-span-12 grid grid-cols-1 gap-8 sm:grid-cols-3 md:col-span-9">
          {items.map((it) => (
            <div key={it.label} className="border-t border-line-strong pt-4">
              <dt className="text-small text-fg-2">{it.label}</dt>
              <dd className="mt-3 type-data text-[clamp(3rem,7vw,5.5rem)] leading-none tracking-[-0.04em]">
                {seen ? <CountUp to={it.value} duration={1200} instant={reduced} /> : <span aria-hidden="true">0</span>}
                <span className="sr-only">{it.value}</span>
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
