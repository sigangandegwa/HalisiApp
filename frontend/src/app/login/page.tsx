import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Suspense } from "react";
import { Wordmark } from "@/components/brand/wordmark";
import { HeroField } from "@/components/landing/hero-field";
import { LanguageToggle } from "@/components/site/language-toggle";
import { getI18n } from "@/lib/i18n/server";
import { LoginForm } from "./login-form";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return { title: t("login.title"), description: t("login.sub") };
}

/**
 * Merchant login (FRONTEND.md section 9.1), in the Case File language: the door to the evidence room.
 * One statement in display type, two ruled lines to fill in, one bar to press. No card, no glass.
 * Phone first: the headline, both fields and the button fit a 360 px screen without scrolling far.
 *
 * The demo passcode and quick-fill businesses are rendered only when SHOW_DEMO_PASSCODE=true, and the
 * passcode reaches the browser only through that prop (it is no longer hard-coded in the client).
 */
export default async function LoginPage() {
  const { t, locale } = await getI18n();
  const demoPasscode = process.env.SHOW_DEMO_PASSCODE === "true" ? (process.env.DASHBOARD_PASSCODE ?? "halisi-demo") : null;
  const title2 = t("login.title2");

  return (
    <div className="theme-night world-night relative isolate flex min-h-dvh flex-col overflow-hidden bg-bg text-fg">
      <HeroField className="absolute inset-0 -z-10 size-full [mask-image:linear-gradient(to_bottom,black,transparent_60%)] lg:[mask-image:linear-gradient(100deg,black_15%,transparent_62%)]" />

      <header className="page-wrap reveal-fade flex h-16 shrink-0 items-center justify-between md:h-20">
        <Link href="/" aria-label={t("login.back")} className="-ml-1 inline-flex h-11 items-center px-1 text-[0.8125rem]">
          <Wordmark />
        </Link>
        <LanguageToggle />
      </header>

      <main
        id="content"
        className="page-wrap grid flex-1 content-center gap-x-(--gutter) gap-y-12 py-8 lg:grid-cols-12 lg:items-end lg:py-16"
      >
        <div className="lg:col-span-7">
          <p className="type-caption reveal-fade text-fg-3" style={{ ["--i" as string]: 0 }}>
            {t("login.eyebrow")}
          </p>
          <h1 className="mt-5 font-display text-[clamp(3.75rem,19vw,5.5rem)] leading-[0.82] font-black tracking-[-0.012em] uppercase lg:text-[clamp(6rem,10.5vw,12.5rem)]">
            <span className="reveal-line" style={{ ["--i" as string]: 0 }}>
              <span>{t("login.title1")}</span>
            </span>
            <span className="reveal-line" style={{ ["--i" as string]: 1 }}>
              <span>
                {title2 ? `${title2} ` : null}
                <span className="text-outline">{t("login.word")}.</span>
              </span>
            </span>
          </h1>
          <p className="reveal-fade mt-6 max-w-[34ch] text-[1.0625rem] leading-snug text-fg-2 md:text-lede lg:mt-8" style={{ ["--i" as string]: 3 }}>
            {t("login.sub")}
          </p>
        </div>

        <div className="reveal-fade lg:col-span-5 xl:col-span-4 xl:col-start-9" style={{ ["--i" as string]: 4 }}>
          <Suspense fallback={<div className="skeleton-ink h-72" />}>
            <LoginForm locale={locale} demoPasscode={demoPasscode} />
          </Suspense>
        </div>
      </main>

      <footer className="page-wrap reveal-fade shrink-0" style={{ ["--i" as string]: 6 }}>
        <div className="flex flex-col gap-3 border-t border-line py-5 text-[0.8125rem] text-fg-3 sm:flex-row sm:items-center sm:justify-between">
          <p>{t("login.pin")}</p>
          <p className="flex flex-wrap items-center gap-x-2">
            <span>{t("login.newBusiness")}</span>
            <Link
              href="/onboarding"
              className="group inline-flex min-h-11 items-center gap-1.5 font-medium text-fg underline decoration-line-strong underline-offset-4 transition-colors duration-(--dur-micro) hover:decoration-fg"
            >
              {t("login.signup")}
              <ArrowRight className="size-3.5 transition-transform duration-(--dur-ui) ease-out group-hover:translate-x-1" strokeWidth={1.75} aria-hidden="true" />
            </Link>
          </p>
        </div>
      </footer>
    </div>
  );
}
