import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { ResultView } from "@/components/checker/result-view";
import { MarkFixture } from "@/components/offline-chip";
import { getI18n } from "@/lib/i18n/server";
import { CheckResult } from "@/lib/schemas";
import { serverGet } from "@/lib/upstream";
import { VERDICTS } from "@/lib/verdict";

type Props = { params: Promise<{ scanId: string }> };

async function load(scanId: string) {
  return serverGet(["check", scanId], CheckResult);
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { scanId } = await params;
  const { t } = await getI18n();
  const res = await load(scanId);
  if (!res.data) return { title: t("result.notFound"), robots: { index: false } };
  const r = res.data;
  const meta = VERDICTS[r.verdict];
  const title = `${t(meta.word)} @${r.target.handle}`;
  const description = t(meta.line, { business: r.matched_merchant?.business_name ?? "" });
  return {
    title,
    description,
    robots: { index: false },
    openGraph: { title, description, type: "article" },
    twitter: { card: "summary_large_image", title, description },
  };
}

/** Shareable verdict (TSK-023): server-rendered final state, "Replay scan" on demand. */
export default async function ResultPage({ params }: Props) {
  const { scanId } = await params;
  const { t } = await getI18n();
  const res = await load(scanId);

  if (!res.data) {
    return (
      <section className="page-wrap section-y">
        <MarkFixture on={res.fixture} />
        <h1 className="type-display-m max-w-[20ch]">{t("result.notFound")}</h1>
        <Link href="/" className="mt-8 inline-flex items-center gap-2 font-medium underline underline-offset-4">
          <ArrowLeft className="size-4" strokeWidth={1.5} aria-hidden="true" />
          {t("notFound.home")}
        </Link>
      </section>
    );
  }

  const r = res.data;
  return (
    <section className="page-wrap pt-8 pb-20 sm:pt-12">
      <MarkFixture on={res.fixture} />
      <Link href="/" className="type-caption inline-flex items-center gap-2 text-fg-2 hover:text-fg">
        <ArrowLeft className="size-3.5" strokeWidth={1.5} aria-hidden="true" />
        {t("nav.check")}
      </Link>
      <h1 className="mt-5 mb-8 font-display text-[clamp(2rem,5vw,3.5rem)] leading-none font-medium tracking-[-0.03em] break-words">
        {t("result.title", { handle: r.target.handle ?? "" })}
      </h1>
      <ResultView result={r} />
    </section>
  );
}
