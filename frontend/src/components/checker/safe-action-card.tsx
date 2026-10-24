"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { paymentParts } from "@/lib/format";
import { useI18n } from "@/lib/i18n/provider";
import { officialHandle } from "@/lib/result";
import type { CheckResult } from "@/lib/schemas";
import { cn } from "@/lib/utils";

/**
 * "What to do instead": always shown with a verdict. When there is a real business behind the
 * answer, the official till is the biggest thing in the block; otherwise it is one honest sentence.
 */
export function SafeActionCard({ result, className }: { result: CheckResult; className?: string }) {
  const { t, locale } = useI18n();
  const m = result.matched_merchant;
  const handle = officialHandle(m, result.target.platform);
  const pay = m ? paymentParts(m.payment) : null;
  const safeText = result.safe_action ? (locale === "sw" ? result.safe_action.text_sw : result.safe_action.text) : null;

  if (!m || result.verdict === "no_match" || result.verdict === "error") {
    const scammy = result.verdict === "suspicious";
    return (
      <section aria-labelledby="safe-title" className={cn("grid gap-3 border-t border-line pt-6", className)}>
        <h3 id="safe-title" className="text-[1.25rem] leading-snug font-semibold">
          {scammy ? t("safe.suspicious.title") : t("safe.no_match.title")}
        </h3>
        <p className="text-fg-2">{t("safe.no_match.body")}</p>
        <Link href="/pay" className="inline-flex h-11 w-fit items-center gap-1.5 font-medium underline decoration-line-strong underline-offset-4 hover:decoration-fg">
          {t("safe.checkNumber")}
          <ArrowUpRight className="size-4" strokeWidth={1.75} aria-hidden="true" />
        </Link>
      </section>
    );
  }

  const title =
    result.verdict === "impersonation" ? t("safe.impersonation.title") : result.verdict === "suspicious" ? t("safe.suspicious.title") : t("safe.official.title");

  return (
    <section aria-labelledby="safe-title" className={cn("grid gap-4 border-t border-line pt-6", className)}>
      <h3 id="safe-title" className="text-[1.25rem] leading-snug font-semibold">
        {title}
      </h3>
      {result.verdict !== "official" && handle ? (
        <p className="text-fg-2">
          {t("safe.impersonation.real", { business: m.business_name })}{" "}
          <a href={handle.url ?? "#"} target="_blank" rel="noopener noreferrer" className="font-mono text-fg underline decoration-line-strong underline-offset-4 hover:decoration-fg">
            @{handle.handle}
          </a>
        </p>
      ) : null}
      {pay ? (
        <div className="grid gap-1">
          <p className="type-caption text-fg-3">{pay.label}</p>
          <p className="font-mono text-[clamp(2rem,9vw,3rem)] leading-none font-medium tracking-[-0.02em]">{pay.value}</p>
          {m.payment.account_name ? <p className="font-mono text-small text-fg-3">{m.payment.account_name}</p> : null}
        </div>
      ) : null}
      {safeText ? (
        <p className="text-small text-fg-3" lang={locale}>
          {safeText}
        </p>
      ) : null}
      <Link
        href={`/v/${m.slug}`}
        className="inline-flex h-11 w-fit items-center gap-1.5 font-medium underline decoration-line-strong underline-offset-4 hover:decoration-fg"
      >
        {t("safe.viewCertificate", { business: m.business_name })}
        <ArrowUpRight className="size-4" strokeWidth={1.75} aria-hidden="true" />
      </Link>
    </section>
  );
}
