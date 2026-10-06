/**
 * Server proxy to the Halisi API (FRONTEND.md section 9.1, TSK-033).
 *
 *  - Only allowlisted method + path combinations pass (src/lib/allowlist.ts); everything else 404s.
 *  - Merchant paths need a valid session cookie, and `/merchants/{id}/...` must be the session's merchant.
 *  - Adds X-Halisi-Key, ngrok-skip-browser-warning and X-Forwarded-For; 10 s timeout.
 *  - Backend unreachable + DEMO_FALLBACK=true: serves fixtures with `x-halisi-fixture: 1`.
 */
import { NextResponse, type NextRequest } from "next/server";
import { classify } from "@/lib/allowlist";
import { resolveFixture } from "@/lib/fixtures/router";
import { SESSION_COOKIE, SESSION_TTL_SECONDS, signSession, verifySession } from "@/lib/session";
import { FIXTURE_HEADER, callUpstream, demoFallbackEnabled } from "@/lib/upstream";

export const dynamic = "force-dynamic";

const MAX_BODY_BYTES = 6 * 1024 * 1024; // logo uploads are capped at 5 MB by the backend

type Ctx = { params: Promise<{ path: string[] }> };

function error(status: number, code: string, message: string, extra?: HeadersInit) {
  return NextResponse.json({ error: { code, message } }, { status, headers: { "cache-control": "no-store", ...extra } });
}

function clientIp(req: NextRequest): string | null {
  const fwd = req.headers.get("x-forwarded-for");
  if (fwd) return fwd.split(",")[0]!.trim();
  return req.headers.get("x-real-ip");
}

async function handle(req: NextRequest, ctx: Ctx): Promise<Response> {
  const { path } = await ctx.params;
  const search = req.nextUrl.searchParams;
  const route = classify(req.method, path, search);
  if (!route) return error(404, "NOT_FOUND", "Not found.");

  if (route.access === "merchant") {
    const session = await verifySession(req.cookies.get(SESSION_COOKIE)?.value);
    if (!session) return error(401, "UNAUTHORIZED", "Merchant login required.");
    if (route.merchantId && route.merchantId !== session.mid) return error(403, "FORBIDDEN", "Not your merchant account.");
    const merchantParam = search.get("merchant_id");
    if (merchantParam && merchantParam !== session.mid) return error(403, "FORBIDDEN", "Not your merchant account.");
  }

  let body: ArrayBuffer | undefined;
  if (req.method !== "GET" && req.method !== "HEAD") {
    const declared = Number(req.headers.get("content-length") ?? 0);
    if (declared > MAX_BODY_BYTES) return error(413, "PAYLOAD_TOO_LARGE", "That upload is too large (5 MB max).");
    body = await req.arrayBuffer();
    if (body.byteLength > MAX_BODY_BYTES) return error(413, "PAYLOAD_TOO_LARGE", "That upload is too large (5 MB max).");
  }

  const contentType = req.headers.get("content-type");
  const upstream = await callUpstream({
    method: req.method,
    upstreamPath: route.upstream,
    search: req.nextUrl.search,
    body,
    contentType,
    clientIp: clientIp(req),
  });

  if (upstream) {
    const headers = new Headers({ "cache-control": "no-store" });
    const type = upstream.headers.get("content-type");
    if (type) headers.set("content-type", type);
    const retry = upstream.headers.get("retry-after");
    if (retry) headers.set("retry-after", retry);

    // Signup: registering a business and being logged into its dashboard is one request. Read the
    // body to sign a session for the merchant that was just created, then still forward the exact
    // same body and status to the client (so onboarding sees the normal MerchantCreated response).
    if (path.length === 1 && path[0] === "merchants" && req.method === "POST" && upstream.ok) {
      const bodyText = await upstream.text();
      const res = new NextResponse(bodyText, { status: upstream.status, headers });
      try {
        const created: unknown = JSON.parse(bodyText);
        const mid = created && typeof created === "object" && "id" in created ? String((created as { id: unknown }).id) : null;
        const slug = created && typeof created === "object" && "slug" in created ? String((created as { slug: unknown }).slug) : null;
        if (mid && slug) {
          const token = await signSession({ mid, slug });
          res.cookies.set(SESSION_COOKIE, token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === "production" && !req.nextUrl.hostname.match(/^(localhost|127\.0\.0\.1)$/),
            sameSite: "lax",
            path: "/",
            maxAge: SESSION_TTL_SECONDS,
          });
        }
      } catch {
        // Malformed body or SESSION_SECRET not configured: the merchant was still created
        // successfully, they just won't be auto-logged in. Let the response through either way.
      }
      return res;
    }

    return new Response(upstream.body, { status: upstream.status, headers });
  }

  if (!demoFallbackEnabled()) {
    return error(503, "API_UNAVAILABLE", "Halisi is temporarily unavailable. Please try again shortly.");
  }

  let json: unknown = undefined;
  if (body && body.byteLength > 0 && contentType?.includes("application/json")) {
    try {
      json = JSON.parse(new TextDecoder().decode(body));
    } catch {
      return error(422, "INVALID_INPUT", "Malformed JSON.", { [FIXTURE_HEADER]: "1" });
    }
  }
  const fx = resolveFixture(req.method, path, search, json);
  return NextResponse.json(fx.body, {
    status: fx.status,
    headers: { "cache-control": "no-store", [FIXTURE_HEADER]: "1" },
  });
}

export const GET = handle;
export const POST = handle;
export const PATCH = handle;
