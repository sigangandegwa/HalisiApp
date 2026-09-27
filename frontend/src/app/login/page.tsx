import type { Metadata } from "next";
import { Suspense } from "react";
import { getI18n } from "@/lib/i18n/server";
import { LoginForm } from "./login-form";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return { title: t("login.title"), description: t("login.sub") };
}

/**
 * Merchant login (FRONTEND.md section 9.1, MVP). Night Desk, standalone: the gateway to
 * `/dashboard` and `/simulator`, not part of the paper world's nav/footer. `src/proxy.ts`
 * redirects here with `?next=`, which the form reads to return the merchant where they were going.
 */
export default async function LoginPage() {
  const { t, locale } = await getI18n();
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
        </div>
      </main>
    </div>
  );
}
