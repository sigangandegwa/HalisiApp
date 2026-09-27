import { SiteFooter } from "@/components/site/site-footer";
import { SiteNav } from "@/components/site/site-nav";
import { getI18n } from "@/lib/i18n/server";

/** Paper world: landing, checker, result, pay, report, certificate. */
export default async function PublicLayout({ children }: { children: React.ReactNode }) {
  const { t } = await getI18n();
  return (
    <div className="paper-grain flex min-h-dvh flex-col">
      <SiteNav />
      <main id="content" tabIndex={-1} className="flex-1 outline-none">
        {children}
      </main>
      <SiteFooter t={t} />
    </div>
  );
}
