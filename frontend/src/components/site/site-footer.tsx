import Link from "next/link";
import { Microprint } from "@/components/brand/microprint";
import { Wordmark } from "@/components/brand/wordmark";
import type { T } from "@/lib/i18n";

/** Footer (FRONTEND.md 6.1.7): microprint rule, tagline, credit, privacy note. */
export function SiteFooter({ t }: { t: T }) {
  return (
    <footer className="mt-auto border-t border-line">
      <Microprint className="py-1.5" />
      <div className="page-grid gap-y-10 pt-14 pb-10 md:pt-20">
        <div className="col-span-12 md:col-span-7">
          <p className="type-display-m max-w-[16ch] italic" style={{ fontVariationSettings: '"SOFT" 100' }} lang="sw">
            {t("footer.tagline")}
          </p>
          <p className="mt-3 text-fg-2">{t("footer.taglineSub")}</p>
        </div>
        <div className="col-span-12 grid gap-4 text-small text-fg-2 md:col-span-4 md:col-start-9">
          <p className="measure">{t("footer.privacy")}</p>
          <p>{t("footer.demo")}</p>
        </div>
        <div className="col-span-12 flex flex-wrap items-center justify-between gap-4 border-t border-line pt-6 text-small text-fg-3">
          <Wordmark className="text-fg" />
          <nav aria-label="Footer" className="flex flex-wrap gap-x-5 gap-y-2">
            <Link href="/" className="hover:text-fg">{t("nav.check")}</Link>
            <Link href="/pay" className="hover:text-fg">{t("nav.pay")}</Link>
            <Link href="/report" className="hover:text-fg">{t("nav.report")}</Link>
            <Link href="/login" className="hover:text-fg">{t("nav.login")}</Link>
          </nav>
          <p>{t("footer.credit")}</p>
        </div>
      </div>
    </footer>
  );
}
