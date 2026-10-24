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
  const title = `${meta.stamp} @${r.target.handle}`;
  const lineKey = r.verdict === "suspicious" && !r.matched_merchant ? "line.suspicious.nobody" : meta.line;
  const description = t(lineKey, { business: r.matched_merchant?.business_name ?? "" });
  return {
    title,
    description,
    robots: { index: false },
    openGraph: { title, description, type: "article" },
    twitter: { card: "summary_large_image", title, description },
  };
}

/** A shared verdict: the word, the sentence, what to do instead. Server-rendered, final state. */
export default async function ResultPage({ params }: Props) {
  const { scanId } = await params;
  const { t } = await getI18n();
  const res = await load(scanId);

  const back = (
    <Link href="/" className="inline-flex h-11 items-center gap-2 font-mono text-[0.8125rem] tracking-[0.1em] text-fg-3 uppercase hover:text-fg">
      <ArrowLeft className="size-4" strokeWidth={1.75} aria-hidden="true" />
      {t("nav.check")}
    </Link>
  );

  if (!res.data) {
    return (
      <section className="page-wrap flex min-h-svh flex-col justify-center gap-8 pt-24 pb-16">
        <MarkFixture on={res.fixture} />
        <h1 className="type-display-m max-w-[14ch]">{t("result.notFound")}</h1>
        {back}
      </section>
    );
  }

  return (
    <section className="page-wrap pt-24 pb-20 sm:pt-28">
      <MarkFixture on={res.fixture} />
      <div className="mx-auto mb-6 w-full max-w-[40rem]">{back}</div>
      <ResultView result={res.data} />
    </section>
  );
}
