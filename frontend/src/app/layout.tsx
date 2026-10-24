import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import { InkFilterDefs } from "@/components/brand/stamp";
import { OfflineChip } from "@/components/offline-chip";
import { Providers } from "@/components/providers";
import { Toaster } from "@/components/ui/sonner";
import { getI18n } from "@/lib/i18n/server";
import "./globals.css";

// Local fonts ensure zero network dependencies during production build (Netlify).
// Variable names are deliberately distinct from the Tailwind theme names (--font-sans etc.),
// otherwise `--font-sans: var(--font-sans)` resolves to itself and the font never applies.
const geistSans = localFont({
  src: [
    { path: "../assets/fonts/Geist-Medium.woff", weight: "500", style: "normal" },
    { path: "../assets/fonts/Geist-SemiBold.woff", weight: "600", style: "normal" },
  ],
  variable: "--font-geist-sans",
  display: "swap",
});

const geistMono = localFont({
  src: [{ path: "../assets/fonts/GeistMono-Medium.woff", weight: "500", style: "normal" }],
  variable: "--font-geist-mono",
  display: "swap",
});

// Monumental condensed capitals: the verdict words and every display headline.
const bigShoulders = localFont({
  src: [
    { path: "../assets/fonts/BigShoulders-700.woff2", weight: "700", style: "normal" },
    { path: "../assets/fonts/BigShoulders-800.woff2", weight: "800", style: "normal" },
    { path: "../assets/fonts/BigShoulders-900.woff2", weight: "900", style: "normal" },
  ],
  variable: "--font-big-shoulders",
  display: "swap",
});

// The single editorial voice: one italic word per headline.
const instrument = localFont({
  src: [
    { path: "../assets/fonts/InstrumentSerif-Regular.woff2", weight: "400", style: "normal" },
    { path: "../assets/fonts/InstrumentSerif-Italic.woff2", weight: "400", style: "italic" },
  ],
  variable: "--font-instrument",
  display: "swap",
});

function getMetadataBase(): URL {
  const env = (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000").trim();
  const validUrl = /^https?:\/\//i.test(env) ? env : `https://${env}`;
  try {
    return new URL(validUrl);
  } catch {
    return new URL("http://localhost:3000");
  }
}

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getI18n();
  return {
    metadataBase: getMetadataBase(),
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
