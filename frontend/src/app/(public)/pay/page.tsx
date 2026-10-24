import type { Metadata } from "next";
import { Suspense } from "react";
import { PayChecker } from "@/components/pay/pay-checker";
import { getI18n } from "@/lib/i18n/server";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return { title: t("nav.pay"), description: t("pay.sub") };
}

/** One question, one field: is this number really theirs? */
export default async function PayPage() {
  const { t } = await getI18n();
  return (
    <section aria-labelledby="pay-title" className="page-wrap flex min-h-svh flex-col justify-center pt-24 pb-16">
      <p className="type-caption reveal-fade text-fg-3">{t("pay.eyebrow")}</p>
      <h1 id="pay-title" className="type-display-l mt-5 max-w-[12ch]">
        <span className="reveal-line" style={{ ["--i" as string]: 0 }}>
          <span>{t("pay.title1")}</span>
        </span>
        <span className="reveal-line" style={{ ["--i" as string]: 1 }}>
          <span className="text-fg-3">{t("pay.title2")}</span>
        </span>
      </h1>
      <p className="reveal-fade mt-6 max-w-[36ch] text-lede text-fg-2" style={{ ["--i" as string]: 2 }}>
        {t("pay.sub")}
      </p>
      <div className="reveal-fade mt-10 w-full max-w-[40rem]" style={{ ["--i" as string]: 3 }}>
        <Suspense>
          <PayChecker />
        </Suspense>
      </div>
    </section>
  );
}
