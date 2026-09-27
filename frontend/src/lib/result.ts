import type { CheckResult, MatchedMerchant } from "@/lib/schemas";

/** The merchant's official handle on the checked platform (or its first handle). */
export function officialHandle(merchant: MatchedMerchant | null, platform?: string | null) {
  if (!merchant) return null;
  return merchant.official_handles.find((h) => h.platform === platform) ?? merchant.official_handles[0] ?? null;
}

export function availableSignals(result: CheckResult): number {
  return result.dimensions.filter((d) => d.available).length;
}

/** Public origin. NEXT_PUBLIC_SITE_URL wins on both server and client so SSR and hydration agree. */
export function siteUrl(): string {
  const env = process.env.NEXT_PUBLIC_SITE_URL;
  if (env) return env.replace(/\/+$/, "");
  if (typeof window !== "undefined") return window.location.origin;
  return "http://localhost:3000";
}

export function resultUrl(scanId: string): string {
  return `${siteUrl()}/check/${scanId}`;
}

export function whatsappUrl(text: string): string {
  return `https://wa.me/?text=${encodeURIComponent(text)}`;
}

/** Evidence evidence strings and reasons never contain full third-party numbers; this is a belt-and-braces mask. */
export function maskNumbersInText(text: string): string {
  return text.replace(/(\+?254|0)([17]\d{2})[\s-]?(\d{3})[\s-]?(\d{3})/g, (_m, _p, a: string, _b, c: string) => `0${a} *** ${c}`);
}
