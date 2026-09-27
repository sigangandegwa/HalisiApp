/**
 * Merchant passcode login (FRONTEND.md section 9.1, MVP; Supabase Auth is P2).
 *   POST   { passcode }  -> constant-time compare with DASHBOARD_PASSCODE, sets a signed httpOnly cookie
 *   DELETE               -> logs out
 */
import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";
import { demoMerchants } from "@/lib/fixtures";
import { MerchantPublic } from "@/lib/schemas";
import { serverGet } from "@/lib/upstream";
import { SESSION_COOKIE, SESSION_TTL_SECONDS, safeEqual, sessionConfigured, signSession } from "@/lib/session";

export const dynamic = "force-dynamic";

const Body = z.object({ passcode: z.string().min(1).max(200) });

const DEV_PASSCODE = "halisi-demo";
const DEFAULT_SLUG = "nairobi-sneaker-vault"; // the demo merchant
const attempts = new Map<string, { count: number; reset: number }>();
const WINDOW_MS = 60_000;
const MAX_ATTEMPTS = 8;

function passcode(): string | null {
  const configured = process.env.DASHBOARD_PASSCODE;
  if (configured) return configured;
  return process.env.NODE_ENV === "development" ? DEV_PASSCODE : null;
}

/**
 * The merchant this passcode unlocks: DASHBOARD_MERCHANT_ID/SLUG if set; otherwise the demo merchant,
 * with its id taken from the live API (GET /merchants/{slug} returns `id`, BACKEND.md 5.11) and the
 * fixtures as the offline fallback.
 */
async function sessionMerchant(): Promise<{ mid: string; slug: string } | null> {
  const id = process.env.DASHBOARD_MERCHANT_ID;
  const slug = process.env.DASHBOARD_MERCHANT_SLUG ?? DEFAULT_SLUG;
  if (id) return { mid: id, slug };
  const live = await serverGet(["merchants", slug], MerchantPublic, { revalidate: 0 });
  if (live.data?.id) return { mid: live.data.id, slug: live.data.slug };
  const merchants = demoMerchants();
  const m = merchants.find((x) => x.slug === slug) ?? merchants[0];
  return m ? { mid: m.id, slug: m.slug } : null;
}

function limited(ip: string): boolean {
  const now = Date.now();
  const entry = attempts.get(ip);
  if (!entry || entry.reset < now) {
    attempts.set(ip, { count: 1, reset: now + WINDOW_MS });
    return false;
  }
  entry.count += 1;
  return entry.count > MAX_ATTEMPTS;
}

export async function POST(req: NextRequest) {
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "local";
  if (limited(ip)) {
    return NextResponse.json({ error: { code: "RATE_LIMITED", message: "Too many attempts. Wait a minute and try again." } }, { status: 429 });
  }
  const expected = passcode();
  const merchant = await sessionMerchant();
  if (!expected || !sessionConfigured() || !merchant) {
    return NextResponse.json(
      { error: { code: "NOT_CONFIGURED", message: "Merchant login isn't configured on this server (DASHBOARD_PASSCODE, SESSION_SECRET)." } },
      { status: 503 },
    );
  }
  const parsed = Body.safeParse(await req.json().catch(() => null));
  if (!parsed.success || !safeEqual(parsed.data.passcode, expected)) {
    await new Promise((r) => setTimeout(r, 400)); // blunt brute force a little
    return NextResponse.json({ error: { code: "INVALID_PASSCODE", message: "That passcode isn't right." } }, { status: 401 });
  }
  attempts.delete(ip);
  const token = await signSession(merchant);
  const res = NextResponse.json({ ok: true, merchant_slug: merchant.slug });
  res.cookies.set(SESSION_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production" && !req.nextUrl.hostname.match(/^(localhost|127\.0\.0\.1)$/),
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_TTL_SECONDS,
  });
  return res;
}

export async function DELETE() {
  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE, "", { httpOnly: true, sameSite: "lax", path: "/", maxAge: 0 });
  return res;
}
