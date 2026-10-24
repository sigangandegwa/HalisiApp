import type { Metadata, Viewport } from "next";
import { Big_Shoulders, Geist, Geist_Mono, Instrument_Serif } from "next/font/google";
import { InkFilterDefs } from "@/components/brand/stamp";
import { OfflineChip } from "@/components/offline-chip";
import { Providers } from "@/components/providers";
import { Toaster } from "@/components/ui/sonner";
import { getI18n } from "@/lib/i18n/server";
import "./globals.css";

// Variable names are deliberately distinct from the Tailwind theme names (--font-sans etc.),
// otherwise `--font-sans: var(--font-sans)` resolves to itself and the font never applies.
const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"], display: "swap" });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"], display: "swap" });
// Monumental condensed capitals: the verdict words and every display headline.
const bigShoulders = Big_Shoulders({
  variable: "--font-big-shoulders",
  subsets: ["latin"],
  weight: ["700", "800", "900"],
  display: "swap",
});
// The single editorial voice: one italic word per headline.
const instrument = Instrument_Serif({
  variable: "--font-instrument",
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
  display: "swap",
});

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return {
    metadataBase: new URL(siteUrl),
    title: { default: t("meta.title"), template: "%s · Halisi" },
    description: t("meta.description"),
    applicationName: "Halisi",
    openGraph: { siteName: "Halisi", type: "website", locale: "en_KE" },
    icons: { icon: [{ url: "/favicon.svg", type: "image/svg+xml" }] },
  };
}

export const viewport: Viewport = {
  themeColor: [{ color: "#07070A" }],
  width: "device-width",
  initialScale: 1,
};

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const { locale, messages, t } = await getI18n();
  return (
    <html lang={locale} className={`${geistSans.variable} ${geistMono.variable} ${bigShoulders.variable} ${instrument.variable}`} suppressHydrationWarning>
      <body className="min-h-dvh">
        <a
          href="#content"
          className="fixed top-3 left-3 z-60 -translate-y-24 rounded-pill bg-fg px-5 py-3 text-small font-medium text-bg transition-transform duration-(--dur-ui) ease-out focus-visible:translate-y-0"
        >
          {t("nav.skip")}
        </a>
        <InkFilterDefs />
        <Providers locale={locale} messages={messages}>
          {children}
          <OfflineChip />
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
