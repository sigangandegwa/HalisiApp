import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Certificate } from "@/components/certificate/certificate";
import { MarkFixture } from "@/components/offline-chip";
import { buttonVariants } from "@/components/ui/button";
import { paymentParts } from "@/lib/format";
import { getI18n } from "@/lib/i18n/server";
import { siteUrl } from "@/lib/result";
import { MerchantPublic } from "@/lib/schemas";
import { serverGet } from "@/lib/upstream";

type Props = { params: Promise<{ slug: string }> };

const load = (slug: string) => serverGet(["merchants", slug], MerchantPublic);

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const res = await load(slug);
  if (!res.data) return { title: "Not found", robots: { index: false } };
  const m = res.data;
  const pay = paymentParts(m.payment);
  const title = `${m.business_name} · Halisi Verified`;
  const description = pay ? `Official ${pay.label} ${pay.value}${m.payment.account_name ? ` · ${m.payment.account_name}` : ""}. If a page asks you to pay any other number, it is not ${m.business_name}.` : `The official accounts of ${m.business_name}.`;
  return { title, description, openGraph: { title, description } };
}

/** Public Halisi Verified certificate (TSK-024): the QR target on badges and stickers. */
export default async function CertificatePage({ params }: Props) {
  const { slug } = await params;
  const { t } = await getI18n();
  const res = await load(slug);

  if (!res.data) {
    return (
      <section className="page-wrap section-y">
        <MarkFixture on={res.fixture} />
        <h1 className="type-display-m">{t("cert.notFound")}</h1>
        <Link href="/" className={`${buttonVariants({ variant: "secondary" })} mt-8`}>
          {t("notFound.home")}
        </Link>
      </section>
    );
  }

  const m = res.data;
  return (
    <section className="page-wrap pt-8 pb-20 sm:pt-12">
      <MarkFixture on={res.fixture} />
      <div style={{ animation: "halisi-fade-up 800ms var(--ease-out) both" }}>
        <Certificate merchant={m} url={`${siteUrl()}/v/${m.slug}`} t={t} className="ring-1 ring-line" />
      </div>
      <div className="mt-8 flex flex-wrap items-center gap-4">
        <Link href="/" className={buttonVariants({ variant: "secondary", size: "md" })}>
          {t("cert.check", { business: m.business_name })}
          <ArrowRight className="size-4" strokeWidth={1.5} aria-hidden="true" />
        </Link>
      </div>
    </section>
  );
}
