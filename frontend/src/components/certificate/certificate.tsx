import { QRCodeSVG } from "qrcode.react";
import { Guilloche } from "@/components/brand/guilloche";
import { Microprint } from "@/components/brand/microprint";
import { Seal } from "@/components/brand/seal";
import { formatDate, paymentParts, shortId } from "@/lib/format";
import { waveBand } from "@/lib/guilloche";
import type { T } from "@/lib/i18n";
import type { MerchantPublic } from "@/lib/schemas";
import { cn } from "@/lib/utils";

const PLATFORM: Record<string, string> = { instagram: "Instagram", facebook: "Facebook", tiktok: "TikTok", x: "X", whatsapp: "WhatsApp", website: "Website" };

/** Engraved wave border (four bands) around the certificate, like a banknote frame. */
function Frame() {
  const band = (phase: number) => waveBand(1000, 14, 60, phase, 0.42);
  return (
    <svg className="pointer-events-none absolute inset-0 size-full text-real" viewBox="0 0 1000 640" preserveAspectRatio="none" aria-hidden="true" focusable="false" fill="none">
      {[0, Math.PI].map((p, i) => (
        <g key={i} stroke="currentColor" strokeOpacity={0.45 - i * 0.15} strokeWidth="0.6" vectorEffect="non-scaling-stroke">
          <path d={band(p)} transform="translate(0 6)" vectorEffect="non-scaling-stroke" />
          <path d={band(p)} transform="translate(0 620)" vectorEffect="non-scaling-stroke" />
        </g>
      ))}
      <rect x="10" y="26" width="980" height="590" stroke="currentColor" strokeOpacity="0.5" strokeWidth="1" vectorEffect="non-scaling-stroke" />
      <rect x="16" y="32" width="968" height="578" stroke="currentColor" strokeOpacity="0.3" strokeWidth="0.6" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

/**
 * Halisi Verified certificate (FRONTEND.md section 6.4): designed like a title deed. The official
 * payment method is the largest data on the page. `compact` renders the landing preview.
 */
export function Certificate({
  merchant,
  url,
  t,
  compact = false,
  className,
}: {
  merchant: MerchantPublic;
  url: string;
  t: T;
  compact?: boolean;
  className?: string;
}) {
  const pay = paymentParts(merchant.payment);
  const Title = compact ? "h3" : "h1";
  const serial = shortId(merchant.id ?? merchant.slug);
  return (
    <article
      aria-label={`${t("cert.eyebrow")}: ${merchant.business_name}`}
      className={cn("theme-paper relative isolate overflow-hidden rounded-doc bg-paper text-ink paper-grain", compact ? "p-6 sm:p-8" : "p-6 sm:p-10 lg:p-14", className)}
    >
      <Frame />
      <Guilloche seed={29} layers={5} opacity={0.08} className="absolute -right-[12%] -bottom-[30%] -z-10 w-[70%] text-halisi" />

      <header className="relative flex flex-wrap items-baseline justify-between gap-3 pt-3">
        <p className="type-caption text-halisi">{t("cert.eyebrow")}</p>
        <p className="font-mono text-[0.75rem] tracking-[0.08em] text-ink-2 uppercase">
          {t("cert.serial")} <span className="text-ink">{serial}</span>
        </p>
      </header>

      <div className={cn("relative mt-8 grid items-center gap-8", compact ? "sm:grid-cols-[auto_minmax(0,1fr)]" : "md:grid-cols-[auto_minmax(0,1fr)] md:gap-12")}>
        <Seal logoUrl={merchant.logo_url} name={merchant.business_name} size={compact ? 132 : 208} seed={merchant.slug.length + 11} />
        <div className="min-w-0">
          <Title className={cn("text-ink", compact ? "font-display text-[clamp(2rem,4vw,3rem)] leading-[0.95] font-medium tracking-[-0.03em]" : "type-display-l")}>
            {merchant.business_name}
          </Title>
          <p className="mt-3 flex items-center gap-2 text-small font-medium text-halisi">
            <svg viewBox="0 0 24 24" className="size-4" aria-hidden="true" fill="none">
              <circle cx="12" cy="12" r="9.5" stroke="currentColor" strokeWidth="1.6" />
              <path d="M7.8 12.4l2.8 2.8 5.6-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="square" />
            </svg>
            {merchant.is_verified
              ? t("cert.since", { date: formatDate(merchant.verified_since) || "" })
              : t("cert.unverified")}
          </p>
          {!compact ? (
            <dl className="mt-6 grid grid-cols-2 gap-x-6 gap-y-3 text-small sm:grid-cols-3">
              {merchant.category ? (
                <div>
                  <dt className="type-caption text-ink-2">{t("cert.category")}</dt>
                  <dd className="mt-1">{merchant.category}</dd>
                </div>
              ) : null}
              {merchant.location ? (
                <div>
                  <dt className="type-caption text-ink-2">{t("cert.location")}</dt>
                  <dd className="mt-1">{merchant.location}</dd>
                </div>
              ) : null}
              {merchant.established_on ? (
                <div>
                  <dt className="type-caption text-ink-2">{t("cert.est")}</dt>
                  <dd className="mt-1">{merchant.established_on.slice(0, 4)}</dd>
                </div>
              ) : null}
            </dl>
          ) : null}
        </div>
      </div>

      {pay ? (
        <section className={cn("relative border-y border-[color-mix(in_oklab,var(--color-halisi)_35%,transparent)]", compact ? "mt-7 py-4" : "mt-10 py-6")}>
          <p className="type-caption text-ink-2">{t("cert.payment")}</p>
          <p className="mt-2 flex flex-wrap items-baseline gap-x-4 gap-y-1">
            <span className={cn("font-mono font-medium tabular-nums tracking-[-0.02em]", compact ? "text-[clamp(1.5rem,3vw,2.25rem)]" : "text-[clamp(2.25rem,6vw,4.5rem)] leading-none")}>
              <span className="text-ink-2">{pay.label}</span> {pay.value}
            </span>
            {merchant.payment.account_name ? (
              <span className={cn("font-mono tracking-[0.04em] text-ink-2 uppercase", compact ? "text-[0.75rem]" : "text-small")}>
                · {merchant.payment.account_name}
              </span>
            ) : null}
          </p>
        </section>
      ) : null}

      <div className={cn("relative grid gap-8", compact ? "mt-6" : "mt-10 md:grid-cols-[minmax(0,1fr)_auto] md:items-end")}>
        <section>
          <p className="type-caption text-ink-2">{t("cert.handles")}</p>
          <ul className="mt-3 flex flex-wrap gap-2">
            {merchant.official_handles.map((h) => (
              <li key={`${h.platform}-${h.handle}`}>
                {compact ? (
                  // the compact preview sits inside a link: no nested anchors
                  <span className="inline-flex h-11 items-center gap-2 rounded-pill border border-[color-mix(in_oklab,var(--color-halisi)_45%,transparent)] px-4">
                    <span className="type-caption text-ink-2">{PLATFORM[h.platform] ?? h.platform}</span>
                    <span className="font-mono text-[0.875rem]">@{h.handle}</span>
                  </span>
                ) : (
                  <a
                    href={h.url ?? "#"}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex h-11 items-center gap-2 rounded-pill border border-[color-mix(in_oklab,var(--color-halisi)_45%,transparent)] px-4 transition-colors duration-(--dur-ui) ease-quart hover:bg-paper-2"
                  >
                    <span className="type-caption text-ink-2">{PLATFORM[h.platform] ?? h.platform}</span>
                    <span className="font-mono text-[0.875rem]">@{h.handle}</span>
                  </a>
                )}
              </li>
            ))}
          </ul>
        </section>
        {!compact ? (
          <figure className="m-0 flex items-end gap-4">
            <div className="rounded-doc bg-paper p-2 ring-1 ring-[color-mix(in_oklab,var(--color-halisi)_35%,transparent)]">
              <QRCodeSVG value={url} size={112} bgColor="#F2EEE3" fgColor="#12130F" level="M" title={t("cert.qr")} />
            </div>
            <figcaption className="max-w-[12ch] text-small text-ink-2">{t("cert.qr")}</figcaption>
          </figure>
        ) : null}
      </div>

      <footer className={cn("relative", compact ? "mt-6" : "mt-12")}>
        <p className={cn("font-display italic", compact ? "text-[1.0625rem]" : "text-[clamp(1.25rem,2.4vw,1.75rem)]")} style={{ fontVariationSettings: '"SOFT" 100' }}>
          “{t("cert.footer")}”
        </p>
        <Microprint className="mt-4 text-halisi opacity-80" />
      </footer>
    </article>
  );
}
