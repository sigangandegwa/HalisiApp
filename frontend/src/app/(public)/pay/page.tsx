import type { Metadata } from "next";
import { Suspense } from "react";
import { Guilloche } from "@/components/brand/guilloche";
import { ModeSwitch } from "@/components/checker/mode-switch";
import { PayChecker } from "@/components/pay/pay-checker";
import { getI18n } from "@/lib/i18n/server";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return { title: t("nav.pay"), description: t("pay.sub") };
}

export default async function PayPage() {
  const { t } = await getI18n();
  return (
    <section aria-labelledby="pay-title" className="relative overflow-x-clip">
      <Guilloche seed={13} layers={4} draw opacity={0.08} className="absolute -top-[20vw] -right-[30vw] -z-10 w-[80vw] max-w-[1000px] text-fg lg:-right-[14vw] lg:w-[56vw]" />
      <div className="page-grid pt-8 pb-24 sm:pt-12 lg:pt-16">
        <div className="col-span-12 lg:col-span-10 lg:col-start-2">
          <ModeSwitch mode="pay" />
          <p className="type-caption mt-10 text-fg-2">{t("pay.eyebrow")}</p>
          <h1 id="pay-title" className="type-display-l mt-4">
            <span className="reveal-line" style={{ ["--i" as string]: 0 }}>
              <span>{t("pay.title1")}</span>
            </span>
            <span className="reveal-line" style={{ ["--i" as string]: 1 }}>
              <span className="italic" style={{ fontVariationSettings: '"SOFT" 100' }}>
                {t("pay.title2")}
              </span>
            </span>
          </h1>
          <p className="reveal-fade mt-6 max-w-[46ch] text-lede text-fg-2" style={{ ["--i" as string]: 2 }}>
            {t("pay.sub")}
          </p>
          <div className="reveal-fade mt-10 max-w-[52rem]" style={{ ["--i" as string]: 3 }}>
            <Suspense>
              <PayChecker />
            </Suspense>
          </div>
        </div>
      </div>
    </section>
  );
}
