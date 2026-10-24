import Link from "next/link";
import { Wordmark } from "@/components/brand/wordmark";
import type { T } from "@/lib/i18n";

/** The footer says three things: who we are, where to go, and what we keep. Nothing else. */
export function SiteFooter({ t }: { t: T }) {
  return (
    <footer className="border-t border-line">
      <div className="page-wrap grid gap-10 py-14 md:grid-cols-[1fr_auto] md:items-end md:py-20">
        <div className="grid gap-6">
          <Wordmark className="text-[1.25rem]" />
          <p className="max-w-[44ch] text-small text-fg-3">{t("footer.privacy")}</p>
          <p className="max-w-[44ch] text-small text-fg-3">{t("footer.demo")}</p>
        </div>
        <nav aria-label="Footer" className="grid gap-1 text-[1.0625rem] md:justify-items-end">
          <Link href="/pay" className="inline-flex h-11 items-center hover:text-fg-2">{t("nav.pay")}</Link>
          <Link href="/report" className="inline-flex h-11 items-center hover:text-fg-2">{t("nav.report")}</Link>
          <Link href="/onboarding" className="inline-flex h-11 items-center hover:text-fg-2">{t("nav.business")}</Link>
          <Link href="/login" className="inline-flex h-11 items-center hover:text-fg-2">{t("nav.login")}</Link>
        </nav>
      </div>
      <p className="page-wrap pb-8 font-mono text-[0.6875rem] tracking-[0.08em] text-fg-3 uppercase">{t("footer.credit")}</p>
    </footer>
  );
}
