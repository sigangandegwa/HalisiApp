import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Certificate } from "@/components/certificate/certificate";
import { Checker } from "@/components/checker/checker";
import { Guilloche } from "@/components/brand/guilloche";
import { Microprint } from "@/components/brand/microprint";
import { ProofBand } from "@/components/landing/proof-band";
import { Tilt } from "@/components/landing/tilt";
import { MarkFixture } from "@/components/offline-chip";
import { CloneAnatomy } from "@/components/story/clone-anatomy";
import { HeroWord } from "@/components/story/hero-word";
import { buttonVariants } from "@/components/ui/button";
import { fixtures } from "@/lib/fixtures";
import { getI18n } from "@/lib/i18n/server";
import { siteUrl } from "@/lib/result";
import { MerchantPublic, Stats } from "@/lib/schemas";
import { serverGet } from "@/lib/upstream";

export default async function Home() {
  const { t, locale } = await getI18n();
  const [stats, merchant] = await Promise.all([
    serverGet(["stats"], Stats),
    serverGet(["merchants", "nairobi-sneaker-vault"], MerchantPublic),
  ]);
  const sample = fixtures().threats.find((x) => x.verdict === "impersonation");
  const books = sample ? fixtures().playbooks[sample.id]?.[locale] : undefined;

  return (
    <>
      <MarkFixture on={stats.fixture || merchant.fixture} />

      {/* 1. Hero + checker: the checker is the hero */}
      <section aria-labelledby="hero-title" className="relative overflow-x-clip">
        <Guilloche
          seed={7}
          layers={5}
          draw
          opacity={0.09}
          className="absolute -top-[14vw] -right-[30vw] -z-10 w-[92vw] max-w-[1200px] text-fg sm:-right-[18vw] lg:-top-[10vw] lg:-right-[12vw] lg:w-[66vw]"
        />
        <div className="page-grid pt-8 pb-16 sm:pt-12 lg:pt-16 lg:pb-24">
          <p className="reveal-fade type-caption col-span-12 text-fg-2" style={{ ["--i" as string]: 0 }}>
            {t("hero.eyebrow")}
          </p>
          <h1 id="hero-title" className="col-span-12 mt-5 font-display font-medium lg:col-span-11 lg:col-start-1 lg:row-start-2">
            <span className="reveal-line text-[clamp(2.35rem,7.2vw,6.75rem)] leading-[0.98] tracking-[-0.035em]" style={{ ["--i" as string]: 0 }}>
              <span>{t("hero.line1")}</span>
            </span>
            <span className="reveal-line text-[clamp(2.35rem,7.2vw,6.75rem)] leading-[0.98] tracking-[-0.035em]" style={{ ["--i" as string]: 1 }}>
              <span>{t("hero.line2")}</span>
            </span>
            <span className="reveal-line -mt-[0.02em] pb-[0.12em] text-[length:var(--text-display-xl)] leading-[0.9] font-semibold tracking-[-0.045em]" style={{ ["--i" as string]: 2 }}>
              <span className="italic" style={{ fontVariationSettings: '"SOFT" 100' }}>
                <HeroWord word={t("hero.word")} />.
              </span>
            </span>
          </h1>
          <aside className="reveal-fade relative z-10 col-span-12 hidden max-w-[17rem] border-l border-line-strong pl-4 lg:col-span-3 lg:col-start-10 lg:row-start-2 lg:mb-[4vw] lg:block lg:self-end" style={{ ["--i" as string]: 4 }}>
            <p className="font-display text-[1.0625rem] leading-snug text-fg-2 italic" style={{ fontVariationSettings: '"SOFT" 100' }}>
              {t("hero.aside")}
            </p>
          </aside>
          <p className="reveal-fade col-span-12 mt-7 max-w-[44ch] text-lede text-fg-2 md:col-span-8 lg:col-span-6 lg:col-start-2" style={{ ["--i" as string]: 3 }}>
            {t("hero.sub")}
          </p>
          <Checker
            inputClassName="reveal-fade col-span-12 mt-8 md:col-span-10 lg:col-span-7 lg:col-start-2 [--i:4]"
            resultClassName="col-span-12 mt-12 empty:mt-0"
          />
        </div>
      </section>

      {/* 3. Anatomy of a clone */}
      <CloneAnatomy logoUrl={merchant.data?.logo_url ?? null} />

      {/* 4. Proof band */}
      <ProofBand stats={stats.data} />

      {/* 5. For businesses */}
      <section id="business" aria-labelledby="business-title" className="section-y scroll-mt-16">
        <div className="page-grid items-center gap-y-12">
          <div className="col-span-12 lg:col-span-5">
            <p className="type-caption text-fg-3">{t("business.eyebrow")}</p>
            <h2 id="business-title" className="type-display-l mt-4">
              {t("business.title1")}{" "}
              <span className="text-real italic" style={{ fontVariationSettings: '"SOFT" 100' }}>
                {t("business.title2")}
              </span>
            </h2>
            <p className="mt-6 max-w-[42ch] text-lede text-fg-2">{t("business.body")}</p>
            <Link href="/login" className={`${buttonVariants({ variant: "primary", size: "lg" })} mt-8`}>
              {t("business.cta")}
              <ArrowRight className="size-5" strokeWidth={1.5} aria-hidden="true" />
            </Link>
          </div>
          <div className="col-span-12 lg:col-span-7 lg:col-start-6">
            {merchant.data ? (
              <Tilt className="mx-auto max-w-[40rem] lg:mr-0">
                <Link href={`/v/${merchant.data.slug}`} aria-label={t("safe.viewCertificate", { business: merchant.data.business_name })} className="block rounded-doc">
                  <Certificate merchant={merchant.data} url={`${siteUrl()}/v/${merchant.data.slug}`} t={t} compact className="ring-1 ring-line" />
                </Link>
              </Tilt>
            ) : null}
          </div>
        </div>
      </section>

      {/* 6. How protection works */}
      <section aria-labelledby="how-title" className="section-y border-t border-line">
        <div className="page-wrap">
          <h2 id="how-title" className="type-caption text-fg-3">{t("how.eyebrow")}</h2>
          <ol className="mt-10 grid gap-12 lg:grid-cols-3 lg:gap-8">
            {(["1", "2", "3"] as const).map((n) => (
              <li key={n} className="grid content-start gap-5">
                <div className="flex items-baseline gap-4 border-t border-line-strong pt-5">
                  <span className="font-mono text-[0.8125rem] text-fg-3">0{n}</span>
                  <h3 className="type-display-m">{t(`how.${n}.title`)}</h3>
                </div>
                <p className="max-w-[40ch] text-fg-2">{t(`how.${n}.body`)}</p>
                <HowCrop step={n} sample={sample} books={books} />
              </li>
            ))}
          </ol>
        </div>
        <Microprint className="mt-20" />
      </section>
    </>
  );
}

/** Small, real UI crops of the Night Desk (not illustrations): the alert, the warning, the report kit. */
function HowCrop({
  step,
  sample,
  books,
}: {
  step: "1" | "2" | "3";
  sample: ReturnType<typeof fixtures>["threats"][number] | undefined;
  books: ReturnType<typeof fixtures>["playbooks"][string]["en"] | undefined;
}) {
  if (!sample) return null;
  const frame = "theme-night desk-panel relative overflow-hidden p-5 text-small";
  if (step === "1") {
    return (
      <div className={frame} aria-hidden="true">
        <div className="relative rounded-doc border border-line bg-bg-3 py-4 pr-4 pl-6 before:absolute before:inset-y-0 before:left-0 before:w-[3px] before:bg-feki">
          <p className="font-semibold">Impersonator detected: @{sample.target.handle}</p>
          <p className="mt-1 text-fg-2">{sample.reasons[0]?.text}</p>
          <div className="mt-3 flex items-center justify-between">
            <span className="font-mono text-[0.6875rem] text-fg-3 uppercase">Score {Math.round(sample.score)} · just now</span>
            <span className="inline-flex h-8 items-center rounded-pill bg-fg px-3 text-[0.75rem] font-medium text-bg">Open</span>
          </div>
        </div>
      </div>
    );
  }
  if (step === "2") {
    return (
      <div className={frame} aria-hidden="true">
        <div className="flex items-center justify-between">
          <span className="type-caption text-fg-3">Customers</span>
          <span className="inline-flex rounded-pill border border-line-strong p-0.5 font-mono text-[0.625rem]">
            <span className="rounded-pill bg-fg px-2 py-0.5 text-bg">EN</span>
            <span className="px-2 py-0.5 text-fg-2">SW</span>
          </span>
        </div>
        <div className="theme-paper mt-3 rounded-doc bg-paper p-4 text-ink">
          <p className="font-semibold">{books?.consumer_warning.title}</p>
          <p className="mt-2 line-clamp-4 text-ink-2">{books?.consumer_warning.body}</p>
        </div>
      </div>
    );
  }
  return (
    <div className={frame} aria-hidden="true">
      <ul className="grid gap-2">
        {["Instagram impersonation form", "Safaricom fraud report", "KE-CIRT/CC incident report"].map((label) => (
          <li key={label} className="flex items-center justify-between rounded-doc border border-line bg-bg-3 px-3 py-2.5">
            <span>{label}</span>
            <span className="font-mono text-[0.6875rem] text-real uppercase">Drafted</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 font-mono text-[0.6875rem] text-fg-3 uppercase">Standard template · review before sending</p>
    </div>
  );
}
