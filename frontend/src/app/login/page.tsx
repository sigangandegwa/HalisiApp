import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { getI18n } from "@/lib/i18n/server";
import { Suspense } from "react";
import { LoginForm } from "./login-form";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return { title: t("login.title"), description: t("login.sub") };
}

/**
 * Merchant login (FRONTEND.md section 9.1, MVP).
 * Redesigned following Apple Design principles:
 * - Fluid translucent materials (backdrop-blur-xl glass card with specular edge)
 * - Clean optical typography
 * - Instant press response and spring transitions
 * - Supports business identifier + passcode with live FastAPI/Supabase auth & offline fallback
 */
export default async function LoginPage() {
  const { t, locale } = await getI18n();
  const passcode = process.env.SHOW_DEMO_PASSCODE === "true" ? (process.env.DASHBOARD_PASSCODE ?? "halisi-demo") : null;

  return (
    <div className="theme-night world-night relative flex min-h-dvh flex-col items-center justify-center bg-bg text-fg overflow-hidden px-[var(--gutter)] py-12">
      {/* Ambient background light bloom (Apple materials depth) */}
      <div
        className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 size-[36rem] rounded-full bg-halisi/10 blur-[130px] opacity-35 select-none"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute -bottom-40 left-1/2 -translate-x-1/2 size-[28rem] rounded-full bg-real/5 blur-[120px] opacity-25 select-none"
        aria-hidden="true"
      />

      <main id="content" className="relative z-10 w-full max-w-[27rem]">
        {/* Apple Translucent Glass Card */}
        <div className="relative rounded-2xl border border-line-strong/80 bg-bg-2/80 p-7 sm:p-9 shadow-[0_24px_50px_-12px_rgba(0,0,0,0.7)] backdrop-blur-xl before:absolute before:inset-x-0 before:top-0 before:h-px before:rounded-t-2xl before:bg-gradient-to-r before:from-transparent before:via-white/20 before:to-transparent">
          {/* Card Header */}
          <div className="flex items-center gap-3 mb-5">
            <div className="flex size-10 items-center justify-center rounded-xl border border-line-strong bg-bg-3/60 text-real shadow-inner">
              <ShieldCheck className="size-5" strokeWidth={1.75} />
            </div>
            <div>
              <p className="type-caption font-mono text-[11px] uppercase tracking-[0.16em] text-fg-3">
                {t("login.eyebrow")}
              </p>
              <h1 className="font-display text-2xl font-normal tracking-tight text-fg">
                {t("login.title")}
              </h1>
            </div>
          </div>

          <p className="text-xs text-fg-2 leading-relaxed">
            {t("login.sub")}
          </p>

          <Suspense fallback={<div className="h-48 animate-pulse rounded-xl bg-bg-3/30 mt-6" />}>
            <LoginForm locale={locale} />
          </Suspense>

          {passcode ? (
            <div className="mt-5 rounded-xl border border-line-strong/40 bg-bg-3/30 px-3.5 py-2.5 text-xs text-fg-2 backdrop-blur-sm">
              <span className="font-mono text-fg-3">{t("login.demoHint", { passcode })}</span>
            </div>
          ) : null}
        </div>

        {/* Footer Navigation */}
        <p className="mt-6 flex flex-wrap items-center justify-center gap-1.5 text-xs text-fg-3">
          <span>{t("login.newBusiness")}</span>
          <Link
            href="/onboarding"
            className="inline-flex items-center gap-1 font-medium text-fg underline decoration-line-strong underline-offset-4 hover:decoration-fg transition-colors"
          >
            <span>{t("login.signup")}</span>
            <ArrowRight className="size-3" strokeWidth={1.5} aria-hidden="true" />
          </Link>
        </p>
      </main>
    </div>
  );
}
