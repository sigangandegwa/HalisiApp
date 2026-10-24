import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Checker } from "@/components/checker/checker";
import { HeroField } from "@/components/landing/hero-field";
import { VerdictPanels } from "@/components/landing/verdict-panels";
import { MarkFixture } from "@/components/offline-chip";
import { buttonVariants } from "@/components/ui/button";
import { getI18n } from "@/lib/i18n/server";
import { Stats } from "@/lib/schemas";
import { serverGet } from "@/lib/upstream";

/**
 * Five screens, one idea each:
 *   1. the question and the one field   2-5. the four answers   6. what Halisi can't see   7. for businesses
 * Phone first: everything below is designed at 360 px and only gains room on larger screens.
 */
export default async function Home() {
  const { t } = await getI18n();
  const stats = await serverGet(["stats"], Stats);
  const checked = stats.data?.pages_scanned ?? 0;
  const line1 = t("hero.line1").split(" ");

  return (
    <>
      <MarkFixture on={stats.fixture} />

      {/* 1. The question */}
      <section aria-labelledby="hero-title" className="relative isolate flex min-h-svh flex-col justify-end overflow-hidden pt-24 pb-8 md:justify-center md:pb-16">
        <HeroField className="absolute inset-0 -z-10 size-full [mask-image:linear-gradient(to_bottom,transparent,black_30%,black_70%,transparent)]" />
        <div className="page-wrap">
          <h1
            id="hero-title"
            className="font-display text-[clamp(4.25rem,23vw,5.75rem)] leading-[0.82] font-black tracking-[-0.012em] uppercase md:text-[clamp(6rem,11.2vw,13.5rem)]"
          >
            <span className="reveal-line" style={{ ["--i" as string]: 0 }}>
              <span>
                {line1.map((w, i) => (
                  <span key={`${w}-${i}`} className="block md:inline">
                    {w}
                    {i < line1.length - 1 ? <span className="hidden md:inline">&nbsp;</span> : null}
                  </span>
                ))}
              </span>
            </span>
            <span className="reveal-line" style={{ ["--i" as string]: 1 }}>
              <span>
                {t("hero.line2")} <span className="text-outline">{t("hero.word")}.</span>
              </span>
            </span>
          </h1>

          <p className="reveal-fade mt-6 max-w-[34ch] text-[1.0625rem] leading-snug text-fg-2 md:mt-8 md:text-lede" style={{ ["--i" as string]: 3 }}>
            {t("hero.sub")}
          </p>

          <Checker
            inputClassName="reveal-fade mt-7 w-full max-w-[40rem] [--i:4]"
            resultClassName="mt-10 w-full empty:mt-0"
          />

          {checked > 0 ? (
            <p className="reveal-fade mt-8 font-mono text-[0.75rem] tracking-[0.1em] text-fg-3 uppercase" style={{ ["--i" as string]: 6 }}>
              {t("hero.counter", { n: checked.toLocaleString("en-KE") })}
            </p>
          ) : null}
        </div>
      </section>

      {/* 2-5. The four answers */}
      <VerdictPanels t={t} />

      {/* 6. What Halisi can't see */}
      <section aria-labelledby="limits-title" className="relative z-10 bg-bg section-y">
        <div className="page-wrap">
          <p className="type-caption text-fg-3">{t("limits.eyebrow")}</p>
          <h2 id="limits-title" className="type-display-l mt-5 max-w-[10ch]">
            {t("limits.title1")} <span className="text-outline">{t("limits.title2")}</span>
          </h2>
          <p className="mt-8 max-w-[44ch] text-lede text-fg-2">{t("limits.body")}</p>
          <dl className="mt-14 grid gap-px border-y border-line md:grid-cols-3 md:border-x">
            {(["see", "cant", "never"] as const).map((k) => (
              <div key={k} className="grid gap-3 border-b border-line py-8 last:border-b-0 md:border-r md:border-b-0 md:px-8 md:py-10 md:last:border-r-0">
                <dt className="type-caption text-fg-3">{t(`limits.${k}.title`)}</dt>
                <dd className="text-[1.25rem] leading-snug">{t(`limits.${k}.body`)}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* 7. For businesses */}
      <section aria-labelledby="business-title" className="relative z-10 border-t border-line bg-bg section-y">
        <div className="page-wrap grid gap-10 md:grid-cols-[1.2fr_1fr] md:items-end md:gap-16">
          <div>
            <p className="type-caption text-fg-3">{t("business.eyebrow")}</p>
            <h2 id="business-title" className="type-display-xl mt-5 text-[clamp(3.75rem,17vw,12rem)]">
              {t("business.title1")} <span className="text-outline">{t("business.title2")}</span>
            </h2>
          </div>
          <div className="grid gap-8">
            <p className="max-w-[38ch] text-lede text-fg-2">{t("business.body")}</p>
            <div className="grid gap-4">
              <Link href="/onboarding" className={`${buttonVariants({ variant: "primary", size: "lg" })} w-full md:w-fit`}>
                {t("business.cta")}
                <ArrowRight className="size-5" strokeWidth={1.75} aria-hidden="true" />
              </Link>
              <p className="text-small text-fg-3">{t("business.note")}</p>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
