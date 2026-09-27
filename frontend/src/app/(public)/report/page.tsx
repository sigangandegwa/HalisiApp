import type { Metadata } from "next";
import { Suspense } from "react";
import { Microprint } from "@/components/brand/microprint";
import { ReportForm } from "@/components/report/report-form";
import { getI18n } from "@/lib/i18n/server";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return { title: t("nav.report"), description: t("report.sub") };
}

export default async function ReportPage() {
  const { t } = await getI18n();
  return (
    <section aria-labelledby="report-title">
      <div className="page-grid gap-y-10 pt-10 pb-24 sm:pt-14 lg:pt-20">
        <div className="col-span-12 lg:col-span-5">
          <p className="type-caption text-fg-2">{t("report.eyebrow")}</p>
          <h1 id="report-title" className="type-display-l mt-4">
            <span className="reveal-line" style={{ ["--i" as string]: 0 }}>
              <span>{t("report.title1")}</span>
            </span>
            <span className="reveal-line" style={{ ["--i" as string]: 1 }}>
              <span className="italic" style={{ fontVariationSettings: '"SOFT" 100' }}>
                {t("report.title2")}
              </span>
            </span>
          </h1>
          <p className="reveal-fade mt-6 max-w-[40ch] text-lede text-fg-2" style={{ ["--i" as string]: 2 }}>
            {t("report.sub")}
          </p>
          <Microprint className="mt-10 hidden lg:block" repeat={8} />
        </div>
        <div className="reveal-fade col-span-12 rounded-doc border border-line-strong bg-bg p-5 sm:p-8 lg:col-span-6 lg:col-start-7" style={{ ["--i" as string]: 3 }}>
          <Suspense>
            <ReportForm />
          </Suspense>
        </div>
      </div>
    </section>
  );
}
