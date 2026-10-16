import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { getI18n } from "@/lib/i18n/server";
import { MerchantPublic } from "@/lib/schemas";
import { serverGet } from "@/lib/upstream";
import { SimulatorClient, type SimulatorMerchant } from "./simulator-client";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return { title: t("sim.title"), description: t("sim.sub") };
}

/** The 3 seeded demo merchants (backend/app/ingestion/mock_seeder.py). No "list merchants" endpoint
 * exists in the API contract, so the known slugs are resolved individually, same as the landing page. */
const DEMO_SLUGS = ["nairobi-sneaker-vault", "kilimani-glow", "pwani-threads"] as const;

/**
 * `/simulator` (TSK-027): build a synthetic clone with a few tweaks and score it with the real
 * engine, live, in front of the room. Gated by src/proxy.ts like /dashboard.
 */
export default async function SimulatorPage() {
  const { t, locale } = await getI18n();
  const resolved = await Promise.all(DEMO_SLUGS.map((slug) => serverGet(["merchants", slug], MerchantPublic)));
  const merchants: SimulatorMerchant[] = resolved
    .map((r) => r.data)
    .filter((m): m is MerchantPublic & { id: string } => Boolean(m?.id))
    .map((m) => ({ id: m.id, slug: m.slug, business_name: m.business_name, logo_url: m.logo_url }));

  return (
    <div className="theme-night world-night min-h-dvh bg-bg text-fg">
      <div className="page-wrap py-10 sm:py-14">
        {/* Apple-style Top Navigation & Mode indicator */}
        <div className="flex items-center justify-between pb-6 mb-8 border-b border-line">
          <Link
            href="/dashboard"
            className="group inline-flex items-center gap-2 px-3.5 py-1.5 rounded-pill border border-line bg-fg/[0.03] text-fg-2 hover:text-fg hover:border-line-strong hover:bg-fg/[0.06] text-xs font-medium transition-all duration-100 ease-out active:scale-[0.96]"
          >
            <ArrowLeft className="size-3.5 transition-transform duration-100 group-hover:-translate-x-0.5" />
            <span>Back to Dashboard</span>
          </Link>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-pill bg-fg/[0.04] border border-line text-[11px] font-mono text-fg-2 uppercase tracking-wider">
            <span className="size-1.5 rounded-full bg-caution animate-pulse" aria-hidden="true" />
            <span>Simulator Stage</span>
          </div>
        </div>

        <p className="type-caption text-fg-3">{t("sim.eyebrow")}</p>
        <h1 className="type-display-m mt-4 max-w-[24ch]">{t("sim.title")}</h1>
        <p className="mt-4 max-w-[52ch] text-lede text-fg-2">{t("sim.sub")}</p>
        <div className="mt-12">
          <SimulatorClient merchants={merchants} locale={locale} />
        </div>
      </div>
    </div>
  );
}
