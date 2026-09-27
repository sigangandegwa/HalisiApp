/**
 * Formatting helpers (FRONTEND.md section 3.1): Kenyan phones, tills, dates in Africa/Nairobi.
 * Pure and isomorphic (used by server, client and the fixture router).
 */
import type { MerchantPayment } from "@/lib/schemas";

const TZ = "Africa/Nairobi";

/** Any Kenyan mobile format -> E.164 (`+254712345678`), or null. */
export function canonicalPhone(value: string): string | null {
  const digits = value.replace(/\D/g, "");
  if (/^0[17]\d{8}$/.test(digits)) return `+254${digits.slice(1)}`;
  if (/^254[17]\d{8}$/.test(digits)) return `+${digits}`;
  if (/^[17]\d{8}$/.test(digits)) return `+254${digits}`;
  return null;
}

/** Till / Paybill: 5 to 7 digits. */
export function canonicalTill(value: string): string | null {
  const digits = value.replace(/\D/g, "");
  return /^\d{5,7}$/.test(digits) ? digits : null;
}

/** `+254712345678` -> `0712 345 678`. */
export function formatPhone(e164: string): string {
  const phone = canonicalPhone(e164);
  if (!phone) return e164;
  const local = `0${phone.slice(4)}`;
  return `${local.slice(0, 4)} ${local.slice(4, 7)} ${local.slice(7)}`;
}

/** Public-safe display (FRONTEND.md section 13): `+254798999111` -> `0798 *** 111`. */
export function maskPhone(e164: string): string {
  const phone = canonicalPhone(e164);
  if (!phone) return e164;
  const local = `0${phone.slice(4)}`;
  return `${local.slice(0, 4)} *** ${local.slice(7)}`;
}

/** `543210` -> `543 210`. */
export function formatTill(value: string): string {
  const d = value.replace(/\D/g, "");
  if (d.length <= 3) return d;
  return `${d.slice(0, d.length - 3)} ${d.slice(-3)}`;
}

export type PaymentKind = "phone" | "till";

/** Live formatting for the /pay input: phones as `0712 345 678`, tills as `543 210`. */
export function formatAsYouType(input: string): { text: string; kind: PaymentKind | null } {
  const raw = input.replace(/[^\d+]/g, "");
  const digits = raw.replace(/\D/g, "");
  if (!digits) return { text: raw.startsWith("+") ? "+" : "", kind: null };
  if (raw.startsWith("+254") || digits.startsWith("254")) {
    const rest = digits.slice(3, 12);
    const parts = [rest.slice(0, 3), rest.slice(3, 6), rest.slice(6, 9)].filter(Boolean);
    return { text: `+254 ${parts.join(" ")}`.trim(), kind: "phone" };
  }
  if (/^0[17]/.test(digits) || digits === "0") {
    const d = digits.slice(0, 10);
    const parts = [d.slice(0, 4), d.slice(4, 7), d.slice(7, 10)].filter(Boolean);
    return { text: parts.join(" "), kind: "phone" };
  }
  const d = digits.slice(0, 7);
  return { text: formatTill(d), kind: "till" };
}

export function paymentParts(payment: MerchantPayment): { label: string; value: string } | null {
  if (!payment.number || payment.type === "none") return null;
  switch (payment.type) {
    case "till":
      return { label: "Till", value: formatTill(payment.number) };
    case "paybill":
      return { label: "Paybill", value: formatTill(payment.number) };
    case "pochi":
      return { label: "Pochi la Biashara", value: formatPhone(payment.number) };
    default:
      return null;
  }
}

const dateFmt = new Intl.DateTimeFormat("en-KE", { timeZone: TZ, day: "numeric", month: "short", year: "numeric" });
const timeFmt = new Intl.DateTimeFormat("en-KE", { timeZone: TZ, hour: "2-digit", minute: "2-digit", hour12: false });

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso.length === 10 ? `${iso}T12:00:00Z` : iso);
  return Number.isNaN(d.getTime()) ? iso : dateFmt.format(d);
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return `${dateFmt.format(d)}, ${timeFmt.format(d)} EAT`;
}

export function timeAgo(iso: string, now: number = Date.now()): string {
  const seconds = Math.max(0, Math.round((now - new Date(iso).getTime()) / 1000));
  if (seconds < 45) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.round(hours / 24);
  return days === 1 ? "yesterday" : `${days} days ago`;
}

export function formatMs(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(ms < 10_000 ? 1 : 0)} s`;
}

export function shortId(id: string): string {
  return id.replace(/-/g, "").slice(0, 8).toUpperCase();
}

/** Parse a pasted link or handle into { platform, handle } (mirrors BACKEND.md section 7.1). */
export function parseTarget(input: string): { platform: string; handle: string } | null {
  const value = input.trim();
  if (!value) return null;
  const handleOnly = /^@?([A-Za-z0-9._]{1,60})$/.exec(value);
  if (handleOnly && !/^\d+$/.test(handleOnly[1])) return { platform: "instagram", handle: handleOnly[1].toLowerCase() };
  let url: URL;
  try {
    url = new URL(/^https?:\/\//i.test(value) ? value : `https://${value}`);
  } catch {
    return null;
  }
  const host = url.hostname.toLowerCase().replace(/^(www|m|mobile)\./, "");
  const first = url.pathname.split("/").filter(Boolean)[0] ?? "";
  const platform =
    host === "instagram.com" ? "instagram"
    : host === "facebook.com" || host === "fb.com" ? "facebook"
    : host === "tiktok.com" ? "tiktok"
    : host === "x.com" || host === "twitter.com" ? "x"
    : null;
  if (!platform) return null;
  if (platform === "facebook" && first === "profile.php") {
    const id = url.searchParams.get("id");
    return id ? { platform, handle: id } : null;
  }
  const handle = first.replace(/^@/, "").toLowerCase();
  if (!/^[a-z0-9._]{1,60}$/.test(handle)) return null;
  return { platform, handle };
}

/** Whether the input looks like a phone or till rather than a page (the checker routes it to /pay). */
export function looksLikePayment(input: string): boolean {
  const v = input.trim();
  return /^[+\d][\d\s-]{4,15}$/.test(v) && (canonicalPhone(v) !== null || canonicalTill(v) !== null);
}
