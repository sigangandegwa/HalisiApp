"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { paymentParts } from "@/lib/format";
import { useI18n } from "@/lib/i18n/provider";
import { officialHandle } from "@/lib/result";
import type { CheckResult } from "@/lib/schemas";
import { cn } from "@/lib/utils";

/**
 * Always rendered with a verdict (FRONTEND.md section 7): what to do instead. Uses the backend's
 * safe_action text (EN/SW) and the merchant's official payment at data size.
 */
export function SafeActionCard({ result, className }: { result: CheckResult; className?: string }) {
  const { t, locale } = useI18n();
  const m = result.matched_merchant;
  const handle = officialHandle(m, result.target.platform);
  const pay = m ? paymentParts(m.payment) : null;
  const safeText = result.safe_action ? (locale === "sw" ? result.safe_action.text_sw : result.safe_action.text) : null;

  if (result.verdict === "no_match" || !m) {
    return (
      <section aria-labelledby="safe-title" className={cn("rounded-doc border border-line bg-bg-2 p-5 sm:p-6", className)}>
        <h3 id="safe-title" className="text-[1.0625rem] font-semibold">{t("safe.no_match.title")}</h3>
        <p className="mt-1.5 text-fg-2">{t("safe.no_match.body")}</p>
        <Link href="/pay" className={cn(buttonVariants({ variant: "secondary", size: "md" }), "mt-4")}>
          {t("safe.checkNumber")}
        </Link>
      </section>
    );
  }

  const tone =
    result.verdict === "impersonation" ? "border-feki before:bg-feki" : result.verdict === "suspicious" ? "border-caution before:bg-caution" : "border-halisi before:bg-real";
  const title =
    result.verdict === "impersonation" ? t("safe.impersonation.title") : result.verdict === "suspicious" ? t("safe.suspicious.title") : t("safe.official.title");

  return (
    <section
      aria-labelledby="safe-title"
      className={cn("relative overflow-hidden rounded-doc border bg-bg p-5 pl-7 before:absolute before:inset-y-0 before:left-0 before:w-1 sm:p-6 sm:pl-8", tone, className)}
    >
      <h3 id="safe-title" className={cn("text-[1.125rem] font-semibold", result.verdict === "impersonation" && "text-fake")}>
        {title}
      </h3>
      {result.verdict !== "official" && handle ? (
        <p className="mt-2 text-fg-2">
          {t("safe.impersonation.real", { business: m.business_name })}{" "}
          <a href={handle.url ?? "#"} target="_blank" rel="noopener noreferrer" className="type-data text-fg underline decoration-line-strong underline-offset-4 hover:decoration-fg">
            @{handle.handle}
          </a>
        </p>
      ) : null}
      {pay ? (
        <p className="mt-4 flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <span className="type-caption text-fg-3">{pay.label}</span>
          <span className="type-data text-[clamp(1.5rem,3.2vw,2rem)] leading-none tracking-[-0.01em]">{pay.value}</span>
          {m.payment.account_name ? <span className="type-data text-small text-fg-2">{m.payment.account_name}</span> : null}
        </p>
      ) : null}
      {safeText ? <p className="mt-3 text-small text-fg-2" lang={locale}>{safeText}</p> : null}
      <Link
        href={`/v/${m.slug}`}
        className="mt-4 inline-flex items-center gap-1.5 text-small font-medium underline decoration-line-strong underline-offset-4 hover:decoration-fg"
      >
        {t("safe.viewCertificate", { business: m.business_name })}
        <ArrowUpRight className="size-4" strokeWidth={1.5} aria-hidden="true" />
      </Link>
    </section>
  );
}
