import Link from "next/link";
import { Guilloche } from "@/components/brand/guilloche";
import { Stamp } from "@/components/brand/stamp";
import { SiteFooter } from "@/components/site/site-footer";
import { SiteNav } from "@/components/site/site-nav";
import { buttonVariants } from "@/components/ui/button";
import { getI18n } from "@/lib/i18n/server";

/** 404: an on-brand joke (FRONTEND.md section 6.9). */
export default async function NotFound() {
  const { t } = await getI18n();
  return (
    <div className="paper-grain flex min-h-dvh flex-col">
      <SiteNav />
      <main id="content" className="relative flex-1 overflow-x-clip">
        <Guilloche seed={404} layers={5} draw opacity={0.08} className="absolute -top-40 -right-60 -z-10 w-[900px] text-fg" />
        <div className="page-wrap grid gap-10 py-20 md:py-28">
          <div style={{ animation: "halisi-fade 400ms var(--ease-quart) both" }}>
            <Stamp word="FEKI." color="var(--color-feki)" misregister size="xl" />
          </div>
          <div>
            <h1 className="type-display-m">
              {t("notFound.title")}{" "}
              <span className="italic" style={{ fontVariationSettings: '"SOFT" 100' }}>
                {t("notFound.word")}
              </span>
            </h1>
            <p className="mt-4 max-w-[44ch] text-lede text-fg-2">{t("notFound.body")}</p>
            <Link href="/" className={`${buttonVariants({ variant: "primary", size: "lg" })} mt-8`}>
              {t("notFound.home")}
            </Link>
          </div>
        </div>
      </main>
      <SiteFooter t={t} />
    </div>
  );
}
