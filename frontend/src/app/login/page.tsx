import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { getI18n } from "@/lib/i18n/server";
import { Suspense } from "react";
import { LoginForm } from "./login-form";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return { title: t("login.title"), description: t("login.sub") };
}

/**
 * Merchant login (FRONTEND.md section 9.1, MVP). Night Desk, standalone: the gateway to
 * `/dashboard` and `/simulator`, not part of the paper world's nav/footer. `src/proxy.ts`
 * redirects here with `?next=`, which the form reads to return the merchant where they were going.
 *
 * The demo passcode hint (below the form) is opt-in via `SHOW_DEMO_PASSCODE=true` so judges can
 * log in without asking anyone. Never set that flag on a deployment with a real merchant behind it.
 */
export default async function LoginPage() {
  const { t, locale } = await getI18n();
  const passcode = process.env.SHOW_DEMO_PASSCODE === "true" ? process.env.DASHBOARD_PASSCODE : null;
  return (
    <div className="theme-night world-night flex min-h-dvh flex-col bg-bg text-fg">
      <main id="content" className="grid flex-1 place-items-center px-[var(--gutter)] py-16">
        <div className="w-full max-w-[26rem]">
          <p className="type-caption text-fg-3">{t("login.eyebrow")}</p>
          <h1 className="type-display-m mt-3">{t("login.title")}</h1>
          <p className="mt-3 max-w-[36ch] text-fg-2">{t("login.sub")}</p>
          <Suspense>
            <LoginForm locale={locale} />
          </Suspense>
          {passcode ? (
            <p className="mt-6 rounded-doc border border-line-strong bg-bg-2 px-4 py-3 text-small text-fg-2">
              {t("login.demoHint", { passcode })}
            </p>
          ) : null}
          <p className="mt-6 flex flex-wrap items-center gap-2 text-small text-fg-2">
            {t("login.newBusiness")}
            <Link href="/onboarding" className="inline-flex items-center gap-1 font-medium text-fg underline decoration-line-strong underline-offset-4 hover:decoration-fg">
              {t("login.signup")}
              <ArrowRight className="size-3.5" strokeWidth={1.5} aria-hidden="true" />
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
