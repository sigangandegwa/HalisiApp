"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import { ArrowRight, ArrowUpRight, Flag } from "lucide-react";
import { Seal } from "@/components/brand/seal";
import { VerdictGlyph } from "@/components/brand/wordmark";
import { buttonVariants } from "@/components/ui/button";
import { ApiError, api } from "@/lib/api";
import { canonicalPhone, canonicalTill, formatAsYouType, paymentParts } from "@/lib/format";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n";
import type { PaymentLookup } from "@/lib/schemas";
import { cn } from "@/lib/utils";

/** "Check a till / phone before you pay" (FRONTEND.md section 6.3, TSK-034). */
export function PayChecker() {
  const { t } = useI18n();
  const id = useId();
  const params = useSearchParams();
  const inputRef = useRef<HTMLInputElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const initial = params.get("value");
  const [text, setText] = useState(() => (initial ? formatAsYouType(initial).text : ""));
  const [submitted, setSubmitted] = useState<string | null>(() => {
    const digits = (initial ?? "").replace(/[^\d+]/g, "");
    return digits ? (canonicalPhone(digits) ?? canonicalTill(digits)) : null;
  });
  const [error, setError] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["payment", submitted],
    queryFn: () => api.verifyPayment(submitted!),
    enabled: Boolean(submitted),
    staleTime: 60_000,
  });

  const submit = (raw: string) => {
    const digits = raw.replace(/[^\d+]/g, "");
    const normalized = canonicalPhone(digits) ?? canonicalTill(digits);
    if (!normalized) {
      setError(t("pay.invalid"));
      return;
    }
    setError(null);
    setSubmitted(normalized);
  };

  useEffect(() => {
    if (query.data) resultRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [query.data]);

  const apiError = query.error instanceof ApiError ? query.error : null;

  return (
    <div className="grid gap-8">
      <form
        noValidate
        onSubmit={(e) => {
          e.preventDefault();
          submit(text);
        }}
        className="grid gap-3"
      >
        <label htmlFor={`${id}-value`} className="type-caption text-fg-2">
          {t("pay.label")}
        </label>
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            ref={inputRef}
            id={`${id}-value`}
            inputMode="tel"
            autoComplete="off"
            enterKeyHint="go"
            placeholder={t("pay.placeholder")}
            value={text}
            onChange={(e) => {
              setText(formatAsYouType(e.target.value).text);
              setError(null);
            }}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? `${id}-error` : undefined}
            className={cn(
              "h-20 min-w-0 flex-1 rounded-pill border bg-bg-2 px-7 font-mono text-[clamp(1.5rem,5vw,2.25rem)] tracking-[0.02em] text-fg tabular-nums",
              "transition-[border-color,background-color,box-shadow] duration-(--dur-ui) ease-quart placeholder:text-fg-3",
              "focus-visible:border-fg focus-visible:bg-bg focus-visible:shadow-[0_0_0_1px_var(--fg)] focus-visible:outline-none",
              error ? "border-fake" : "border-line-strong",
            )}
          />
          <button type="submit" className={cn(buttonVariants({ variant: "primary", size: "lg" }), "h-20 px-9 text-[1.0625rem]")}>
            {query.isFetching ? t("checker.checking") : t("pay.submit")}
            <ArrowRight className="size-5" strokeWidth={1.5} aria-hidden="true" />
          </button>
        </div>
        <div className="min-h-6">
          {error ? (
            <p id={`${id}-error`} role="alert" className="text-small text-fake">
              {error}
            </p>
          ) : apiError ? (
            <p role="alert" className="text-small text-fake">
              {apiError.status === 422 ? t("pay.invalid") : apiError.status === 429 ? t("checker.error.rate") : t("checker.error.generic")}
            </p>
          ) : null}
        </div>
      </form>

      <div ref={resultRef} aria-live="polite" className="scroll-mt-24">
        {query.data ? <PaymentResult lookup={query.data} onAgain={() => { setSubmitted(null); setText(""); inputRef.current?.focus(); }} /> : null}
      </div>
    </div>
  );
}

function PaymentResult({ lookup, onAgain }: { lookup: PaymentLookup; onAgain: () => void }) {
  const { t } = useI18n();
  const kindKey: MessageKey = lookup.kind === "paybill" ? "pay.kind.paybill" : lookup.kind === "till" ? "pay.kind.till" : "pay.kind.phone";
  const reportHref = `/report?${new URLSearchParams(lookup.kind === "phone" ? { phone: lookup.normalized } : { till: lookup.normalized })}`;
  const again = (
    <button type="button" onClick={onAgain} className="cursor-pointer text-small font-medium underline decoration-line-strong underline-offset-4 hover:decoration-fg">
      {t("pay.again")}
    </button>
  );

  if (lookup.status === "official" && lookup.merchant) {
    const m = lookup.merchant;
    const pay = paymentParts(m.payment);
    return (
      <section className="relative overflow-hidden rounded-doc border border-halisi bg-bg p-6 pl-8 before:absolute before:inset-y-0 before:left-0 before:w-1.5 before:bg-real sm:p-8 sm:pl-10" style={{ animation: "halisi-fade-up 600ms var(--ease-out) both" }}>
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center">
          <Seal logoUrl={m.logo_url} name={m.business_name} size={112} />
          <div className="min-w-0">
            <p className="flex items-center gap-2 text-real">
              <VerdictGlyph glyph="seal" />
              <span className="type-caption">HALISI.</span>
            </p>
            <h2 className="mt-2 font-display text-[clamp(1.75rem,4vw,2.75rem)] leading-tight font-medium tracking-[-0.02em]">
              {t("pay.official.title", { business: m.business_name })}
            </h2>
            <p className="mt-2 text-fg-2">{t("pay.official.body", { business: m.business_name, kind: t(kindKey) })}</p>
          </div>
        </div>
        <dl className="mt-6 grid gap-4 border-t border-line pt-5 sm:grid-cols-2">
          <div>
            <dt className="type-caption text-fg-3">{pay?.label ?? t(kindKey)}</dt>
            <dd className="mt-1 type-data text-[1.75rem] leading-none">{pay?.value ?? lookup.display}</dd>
          </div>
          {m.payment.account_name ? (
            <div>
              <dt className="type-caption text-fg-3">{t("pay.official.account")}</dt>
              <dd className="mt-1 type-data text-[1.25rem] leading-tight">{m.payment.account_name}</dd>
            </div>
          ) : null}
        </dl>
        <div className="mt-6 flex flex-wrap items-center gap-5">
          <Link href={`/v/${m.slug}`} className={buttonVariants({ variant: "real", size: "md" })}>
            {t("pay.official.link")}
            <ArrowUpRight className="size-4" strokeWidth={1.5} aria-hidden="true" />
          </Link>
          {again}
        </div>
      </section>
    );
  }

  if (lookup.status === "reported") {
    return (
      <section className="relative overflow-hidden rounded-doc border border-feki bg-bg p-6 pl-8 before:absolute before:inset-y-0 before:left-0 before:w-1.5 before:bg-feki sm:p-8 sm:pl-10" style={{ animation: "halisi-fade-up 600ms var(--ease-out) both" }}>
        <p className="flex items-center gap-2 text-fake">
          <VerdictGlyph glyph="broken" />
          <span className="type-caption">{t("verdict.impersonation.word")}</span>
        </p>
        <p className="mt-3 type-data text-[clamp(2rem,6vw,3.25rem)] leading-none">{lookup.display}</p>
        <h2 className="mt-4 font-display text-[clamp(1.75rem,4vw,2.75rem)] leading-tight font-medium tracking-[-0.02em]">
          {lookup.report_count === 1 ? t("pay.reported.title.one") : t("pay.reported.title.other", { n: lookup.report_count })}
        </h2>
        <p className="mt-2 text-[1.25rem] font-semibold text-fake">{t("pay.reported.body")}</p>
        {lookup.linked_threats > 0 ? <p className="mt-3 text-fg-2">{t("pay.reported.linked", { n: lookup.linked_threats })}</p> : null}
        <div className="mt-6">{again}</div>
      </section>
    );
  }

  return (
    <section className="rounded-doc border border-line-strong bg-bg-2 p-6 sm:p-8" style={{ animation: "halisi-fade-up 600ms var(--ease-out) both" }}>
      <p className="flex items-center gap-2 text-fg-2">
        <VerdictGlyph glyph="circle" />
        <span className="type-caption">{t("verdict.no_match.word")}</span>
      </p>
      <p className="mt-3 type-data text-[clamp(2rem,6vw,3.25rem)] leading-none">{lookup.display}</p>
      <h2 className="mt-4 font-display text-[clamp(1.75rem,4vw,2.75rem)] leading-tight font-medium tracking-[-0.02em]">{t("pay.unknown.title")}</h2>
      <p className="mt-2 max-w-[56ch] text-fg-2">{t("pay.unknown.body")}</p>
      {lookup.linked_threats > 0 ? <p className="mt-3 font-medium text-warn">{t("pay.unknown.linked", { n: lookup.linked_threats })}</p> : null}
      <div className="mt-6 flex flex-wrap items-center gap-5">
        <Link href={reportHref} className={buttonVariants({ variant: "secondary", size: "md" })}>
          <Flag className="size-4" strokeWidth={1.5} aria-hidden="true" />
          {t("pay.unknown.report")}
        </Link>
        {again}
      </div>
    </section>
  );
}
