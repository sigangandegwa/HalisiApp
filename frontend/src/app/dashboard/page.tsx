"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight } from "lucide-react";
import { useReducedMotion } from "motion/react";
import { CountUp } from "@/components/checker/count-up";
import { Seal } from "@/components/brand/seal";
import { useAlertDrawer } from "@/components/merchant/alert-context";
import { FileSection } from "@/components/merchant/file-section";
import { KpiTile } from "@/components/merchant/kpi-tile";
import { ThreatRow } from "@/components/merchant/threat-row";
import { TrustChip } from "@/components/merchant/trust-chip";
import { WatchlistPanel } from "@/components/merchant/watchlist-panel";
import { api, qk } from "@/lib/api";
import { isOpen } from "@/lib/case";
import { formatMs, paymentParts } from "@/lib/format";
import { merchantStatus } from "@/lib/schemas";
import { cn } from "@/lib/utils";

type Filter = "open" | "closed" | "all";

/**
 * The Strike Console. One number leads (open cases), because the first question a merchant has is
 * "is anyone imitating me right now?". Then the ledger, then the tools to act on it.
 */
export default function DashboardPage() {
  const { merchantId, merchantSlug } = useAlertDrawer();
  const reduced = useReducedMotion() ?? false;
  const [filter, setFilter] = useState<Filter>("open");

  const { data: stats } = useQuery({
    queryKey: qk.stats(merchantId),
    queryFn: () => api.getStats(merchantId),
    refetchInterval: 5000,
  });
  const { data: merchant } = useQuery({ queryKey: qk.merchant(merchantSlug), queryFn: () => api.getMerchant(merchantSlug) });
  const { data: threats, isLoading } = useQuery({
    queryKey: qk.threats(merchantId),
    queryFn: () => api.listThreats(merchantId),
    refetchInterval: 5000,
  });

  const status = merchant ? merchantStatus(merchant) : null;
  const all = threats ?? [];
  const open = all.filter((t) => isOpen(t.status));
  const closed = all.filter((t) => !isOpen(t.status));
  const shown = filter === "open" ? open : filter === "closed" ? closed : all;
  const officials = merchant?.official_handles.map((h) => h.handle) ?? [];
  const payment = merchant ? paymentParts(merchant.payment) : null;
  const sorted = [...shown].sort((a, b) => b.composite_score - a.composite_score);

  const tabs: { key: Filter; label: string; count: number }[] = [
    { key: "open", label: "Open", count: open.length },
    { key: "closed", label: "Closed", count: closed.length },
    { key: "all", label: "All", count: all.length },
  ];

  return (
    <div className="grid gap-[clamp(3rem,6vw,5.5rem)]">
      {/* 00: the lead */}
      <header className="grid gap-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="type-caption text-fg-3">Strike Console · {merchant?.business_name ?? "…"}</p>
          {status ? <TrustChip status={status} /> : null}
        </div>

        <div className="flex flex-wrap items-end gap-x-[0.18em] gap-y-2">
          <h1 className="sr-only">{open.length} open cases</h1>
          <span aria-hidden="true" className={cn("font-display text-[clamp(7rem,26vw,20rem)] leading-[0.74] font-black tracking-[-0.012em] tabular-nums", open.length > 0 ? "text-fake" : "text-fg")}>
            <CountUp to={open.length} instant={reduced} duration={900} />
          </span>
          <span aria-hidden="true" className="font-display pb-[0.05em] text-[clamp(2rem,6vw,4.75rem)] leading-[0.86] font-extrabold uppercase">
            open {open.length === 1 ? "case" : "cases"}<span className="text-fg-3">.</span>
          </span>
        </div>

        <p className="measure text-lede text-fg-2">
          {open.length === 0
            ? `Halisi is watching ${officials.length || "your"} official account${officials.length === 1 ? "" : "s"}. Nothing imitating you is open right now.`
            : "Each case is a page imitating your brand. Open one, check the evidence, and prepare the reports. You send them; Halisi writes them."}
        </p>

        <dl className="grid grid-cols-2 gap-y-2 border-y border-line sm:grid-cols-4">
          <KpiTile label="Pages checked" value={stats?.pages_scanned ?? "–"} />
          <KpiTile label="Threats found" value={stats?.threats_detected ?? "–"} />
          <KpiTile label="Resolved" value={stats?.resolved ?? closed.filter((t) => t.status === "resolved").length} />
          <KpiTile label="Median check time" value={stats ? formatMs(stats.median_detection_ms) : "–"} hint="Measured, not estimated" />
        </dl>
      </header>

      {/* claimed merchants are inert: say so before anything else */}
      {status === "claimed" ? (
        <aside className="grid gap-4 border border-dashed border-line-strong p-6 sm:grid-cols-[1fr_auto] sm:items-center sm:p-8">
          <div className="grid gap-2">
            <p className="font-display text-[clamp(1.5rem,3vw,2.25rem)] leading-none font-extrabold uppercase">Protection is paused.</p>
            <p className="measure text-fg-2">
              Until you prove you own this brand, Halisi will not flag clones of it and will not issue a certificate. It takes one line in your bio.
            </p>
          </div>
          <Link href="/dashboard/verify" className="inline-flex h-12 items-center justify-center gap-2 border border-fg bg-fg px-6 text-[0.9375rem] font-semibold text-bg active:scale-[0.98]">
            Verify ownership <ArrowUpRight className="size-4" aria-hidden="true" />
          </Link>
        </aside>
      ) : null}

      <div className="grid gap-[clamp(2.5rem,5vw,5rem)] lg:grid-cols-[minmax(0,1fr)_minmax(0,25rem)]">
        {/* 01: the ledger */}
        <FileSection n={1} title="Cases" aside={`${sorted.length} shown`}>
          <div role="tablist" aria-label="Filter cases" className="flex gap-1">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                role="tab"
                type="button"
                aria-selected={filter === tab.key}
                onClick={() => setFilter(tab.key)}
                className={cn(
                  "type-caption h-10 cursor-pointer border px-4 transition-colors duration-(--dur-micro)",
                  filter === tab.key ? "border-fg bg-fg text-bg" : "border-line text-fg-2 hover:border-line-strong hover:text-fg",
                )}
              >
                {tab.label} <span className="tabular-nums opacity-70">{tab.count}</span>
              </button>
            ))}
          </div>

          {isLoading ? (
            <div className="grid gap-3">
              <div className="skeleton-ink h-24" />
              <div className="skeleton-ink h-24" />
            </div>
          ) : sorted.length === 0 ? (
            <div className="border border-dashed border-line-strong p-10">
              <p className="font-display text-[clamp(2rem,5vw,3.5rem)] leading-none font-extrabold uppercase">
                {filter === "open" ? "All quiet." : "Nothing here."}
              </p>
              <p className="mt-3 max-w-[40ch] text-fg-2">
                {filter === "open"
                  ? "No open cases. When a customer checks a page that imitates you, or a look-alike scan finds one, it lands here and your phone buzzes."
                  : "Cases you resolve or dismiss are kept here as your record."}
              </p>
            </div>
          ) : (
            <ul className="border-t border-line">
              {sorted.map((t, i) => (
                <ThreatRow key={t.id} threat={t} merchantHandles={officials} index={i} />
              ))}
            </ul>
          )}
        </FileSection>

        {/* rail: what Halisi protects + the watchlist */}
        <div className="grid content-start gap-[clamp(2.5rem,5vw,4rem)]">
          <FileSection n={2} title="Protected">
            <div className="flex items-center gap-5">
              <div className="size-20 shrink-0">
                <Seal logoUrl={merchant?.logo_url ?? undefined} name={merchant?.business_name ?? ""} />
              </div>
              <div className="min-w-0">
                <p className="type-heading truncate">{merchant?.business_name}</p>
                {payment ? (
                  <p className="type-data mt-1 text-[0.9375rem] text-fg-2">
                    {payment.label} {payment.value}
                  </p>
                ) : null}
              </div>
            </div>
            <ul className="grid gap-2">
              {merchant?.official_handles.map((h, i) => (
                <li key={`${h.platform}-${h.handle}-${i}`} className="type-data flex items-center justify-between border-b border-line pb-2 text-[0.9375rem]">
                  <span>@{h.handle}</span>
                  <span className="type-caption text-fg-3">{h.platform}</span>
                </li>
              ))}
            </ul>
            {status !== "claimed" ? (
              <Link
                href={`/v/${merchant?.slug ?? merchantSlug}`}
                target="_blank"
                rel="noopener noreferrer"
                className="group inline-flex h-12 items-center justify-between border border-line-strong px-5 text-[0.9375rem] font-medium transition-colors duration-(--dur-micro) hover:bg-bg-2 active:scale-[0.98]"
              >
                Public certificate
                <ArrowUpRight className="size-4 opacity-60 transition-transform duration-(--dur-ui) group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:opacity-100" aria-hidden="true" />
              </Link>
            ) : null}
          </FileSection>

          <FileSection n={3} title="Look-alikes">
            <WatchlistPanel merchantId={merchantId} />
          </FileSection>
        </div>
      </div>
    </div>
  );
}
