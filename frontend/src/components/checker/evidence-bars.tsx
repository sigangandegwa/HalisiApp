"use client";

import type { Dimension, DimensionKey } from "@/lib/schemas";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { CountUp } from "./count-up";

const ORDER: DimensionKey[] = ["visual", "identity", "payment", "language", "account"];
const LABEL: Record<DimensionKey, MessageKey> = {
  visual: "dim.visual",
  identity: "dim.identity",
  payment: "dim.payment",
  language: "dim.language",
  account: "dim.account",
};

/**
 * Five evidence rows in weight order (FRONTEND.md sections 7 and 8): label + weight, a bar that
 * scales from 0, the mono score counting up, and the backend's evidence string. Unavailable
 * signals get a dashed empty bar and "No data". The bars are the real sub-scores.
 */
export function EvidenceBars({
  dimensions,
  color,
  delay = 0,
  instant = false,
  dense = false,
}: {
  dimensions: Dimension[];
  color: string;
  delay?: number;
  instant?: boolean;
  dense?: boolean;
}) {
  const { t } = useI18n();
  const byKey = new Map(dimensions.map((d) => [d.key, d]));
  const rows = ORDER.map((k) => byKey.get(k)).filter((d): d is Dimension => Boolean(d));
  if (!rows.length) return null;
  return (
    <ol className={cn("grid", dense ? "gap-4" : "gap-5")}>
      {rows.map((d, i) => {
        const rowDelay = delay + i * 90;
        const value = Math.max(0, Math.min(100, d.score));
        return (
          <li key={d.key} className="grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-x-4 gap-y-2">
            <p className="flex items-baseline gap-2">
              <span className="text-[0.9375rem] font-semibold">{t(LABEL[d.key])}</span>
              <span className="font-mono text-[0.6875rem] tracking-[0.06em] text-fg-3 uppercase" aria-label={`${t("evidence.weight")} ${Math.round(d.weight * 100)}%`}>
                {Math.round(d.weight * 100)}%
              </span>
            </p>
            <p className="type-data text-[0.9375rem] tabular-nums">
              {d.available ? (
                <>
                  <CountUp to={value} delay={rowDelay} duration={800} instant={instant} />
                  <span className="sr-only">{Math.round(value)} / 100</span>
                </>
              ) : (
                <span className="text-fg-3">{t("evidence.noData")}</span>
              )}
            </p>
            <div className="col-span-2 h-2 overflow-hidden rounded-[1px]" aria-hidden="true">
              {d.available ? (
                <div className="relative h-full bg-bg-3">
                  <div
                    className="absolute inset-y-0 left-0 w-full origin-left"
                    style={{
                      background: color,
                      transform: `scaleX(${value / 100})`,
                      animation: instant ? undefined : `halisi-bar 800ms var(--ease-out) both`,
                      animationDelay: instant ? undefined : `${rowDelay}ms`,
                      ["--to" as string]: value / 100,
                    }}
                  />
                </div>
              ) : (
                <div className="h-full border border-dashed border-line-strong" />
              )}
            </div>
            <p className="col-span-2 font-mono text-[0.75rem] leading-snug break-words text-fg-3">
              {d.available ? d.evidence : t("evidence.noData")}
            </p>
          </li>
        );
      })}
    </ol>
  );
}
