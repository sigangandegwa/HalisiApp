/**
 * Merchant session login & logout (FRONTEND.md section 9.1).
 *   POST   { identifier?, passcode } -> verifies against FastAPI/Supabase /api/v1/auth/login,
 *                                       falls back to fixtures/allMerchants(), signs JWT session cookie.
 *   DELETE                           -> calls upstream /api/v1/auth/logout, clears session cookie.
 */
import { NextResponse, type NextRequest } from "next/server";
import { z } from "zod";
import { allMerchants } from "@/lib/fixtures/router";
import { callUpstream, demoFallbackEnabled } from "@/lib/upstream";
import { SESSION_COOKIE, SESSION_TTL_SECONDS, safeEqual, sessionConfigured, signSession } from "@/lib/session";

export const dynamic = "force-dynamic";

const Body = z.object({
  identifier: z.string().trim().min(1).max(200).optional(),
  passcode: z.string().min(1).max(200),
});

const DEV_PASSCODE = "halisi-demo";
const DEFAULT_SLUG = "nairobi-sneaker-vault"; // the demo merchant
const attempts = new Map<string, { count: number; reset: number }>();
const WINDOW_MS = 60_000;
const MAX_ATTEMPTS = 8;

function expectedPasscode(): string | null {
  const configured = process.env.DASHBOARD_PASSCODE;
  if (configured) return configured;
  return process.env.NODE_ENV === "development" ? DEV_PASSCODE : null;
}

function resolveFallbackMerchant(identifier?: string): { mid: string; slug: string; business_name: string } | null {
  const merchants = allMerchants();
  if (identifier?.trim()) {
    const q = identifier.trim().toLowerCase().replace(/^@+/, "");
    const match =
      merchants.find(
        (m) =>
          m.slug.toLowerCase() === q ||
          m.business_name.toLowerCase() === q ||
          m.id.toLowerCase() === q ||
          m.official_handles.some((h) => h.handle.toLowerCase().replace(/^@+/, "") === q),
      ) ??
      merchants.find(
        (m) =>
          m.business_name.toLowerCase().includes(q) ||
          m.slug.toLowerCase().includes(q),
      );
    if (match) return { mid: match.id, slug: match.slug, business_name: match.business_name };
    return null;
  }

  const envMid = process.env.DASHBOARD_MERCHANT_ID;
  const envSlug = process.env.DASHBOARD_MERCHANT_SLUG ?? DEFAULT_SLUG;
  if (envMid) {
    const match = merchants.find((m) => m.id === envMid || m.slug === envSlug);
    return { mid: envMid, slug: envSlug, business_name: match?.business_name ?? "Verified Merchant" };
  }
  const defaultMerchant = merchants.find((m) => m.slug === envSlug) ?? merchants[0];
  if (defaultMerchant) {
    return { mid: defaultMerchant.id, slug: defaultMerchant.slug, business_name: defaultMerchant.business_name };
  }
  return null;
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
    return NextResponse.json(
      { error: { code: "RATE_LIMITED", message: "Too many attempts. Wait a minute and try again." } },
      { status: 429 },
    );
  }

  if (!sessionConfigured()) {
    return NextResponse.json(
      { error: { code: "NOT_CONFIGURED", message: "Merchant login isn't configured on this server (SESSION_SECRET)." } },
      { status: 503 },
    );
  }

  const rawJson = await req.json().catch(() => null);
  const parsed = Body.safeParse(rawJson);
  if (!parsed.success) {
    return NextResponse.json(
      { error: { code: "INVALID_INPUT", message: "Please provide a valid passcode." } },
      { status: 400 },
    );
  }

  const { identifier, passcode } = parsed.data;

  // 1. Attempt live FastAPI/Supabase backend verification upstream
  let resolved: { mid: string; slug: string; business_name: string } | null = null;
  const upstreamBody = new TextEncoder().encode(JSON.stringify({ identifier, passcode })).buffer;

  const upstreamRes = await callUpstream({
    method: "POST",
    upstreamPath: "/api/v1/auth/login",
    contentType: "application/json",
    body: upstreamBody,
    clientIp: ip,
  });

  if (upstreamRes !== null) {
    if (upstreamRes.ok) {
      const data = await upstreamRes.json().catch(() => null);
      if (data) {
        const mid = data.merchant_id ?? data.id;
        const slug = data.merchant_slug ?? data.slug;
        const business_name = data.business_name ?? data.name ?? slug;
        if (mid && slug) {
          resolved = { mid: String(mid), slug: String(slug), business_name: String(business_name) };
        }
      }
    } else if (upstreamRes.status !== 404) {
      await new Promise((r) => setTimeout(r, 400));
      const errData = await upstreamRes.json().catch(() => null);
      return NextResponse.json(
        errData ?? { error: { code: "INVALID_PASSCODE", message: "That passcode isn't right." } },
        { status: upstreamRes.status },
      );
    }
  }

  // 2. If backend is offline, returned 404, or demo fallback is active
  if (!resolved) {
    if (!demoFallbackEnabled() && upstreamRes === null) {
      return NextResponse.json(
        { error: { code: "BACKEND_UNAVAILABLE", message: "Backend authentication service is unavailable." } },
        { status: 503 },
      );
    }

    const expected = expectedPasscode();
    if (!expected || !safeEqual(passcode, expected)) {
      await new Promise((r) => setTimeout(r, 400));
      return NextResponse.json(
        { error: { code: "INVALID_PASSCODE", message: "That passcode isn't right." } },
        { status: 401 },
      );
    }

    resolved = resolveFallbackMerchant(identifier);
    if (!resolved) {
      return NextResponse.json(
        {
          error: {
            code: "MERCHANT_NOT_FOUND",
            message: identifier ? `No verified merchant matches "${identifier}".` : "No merchants available.",
          },
        },
        { status: 404 },
      );
    }
  }

  attempts.delete(ip);
  const token = await signSession({ mid: resolved.mid, slug: resolved.slug });
  const res = NextResponse.json({
    ok: true,
    merchant_id: resolved.mid,
    merchant_slug: resolved.slug,
    business_name: resolved.business_name,
  });

  res.cookies.set(SESSION_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production" && !req.nextUrl.hostname.match(/^(localhost|127\.0\.0\.1)$/),
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_TTL_SECONDS,
  });

  return res;
}

export async function DELETE(req: NextRequest) {
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "local";
  await callUpstream({
    method: "POST",
    upstreamPath: "/api/v1/auth/logout",
    clientIp: ip,
  }).catch(() => null);

  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE, "", { httpOnly: true, sameSite: "lax", path: "/", maxAge: 0 });
  return res;
}
