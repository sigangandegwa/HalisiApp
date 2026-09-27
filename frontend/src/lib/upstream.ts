/**
 * Server-only access to the Halisi FastAPI backend, shared by the `/api/halisi/*` proxy and by
 * server components (`/check/[scanId]`, `/v/[slug]`). Adds the API key, the ngrok bypass header
 * and a 10 s timeout; falls back to fixtures when the backend is down and DEMO_FALLBACK is on.
 */
import type { z } from "zod";
import { resolveFixture } from "@/lib/fixtures/router";

export const FIXTURE_HEADER = "x-halisi-fixture";
const TIMEOUT_MS = 10_000;

export function apiBase(): string | null {
  const url = process.env.HALISI_API_URL?.trim();
  return url ? url.replace(/\/+$/, "") : null;
}

/**
 * Circuit breaker: after a network failure, skip the backend for a short window so an offline demo
 * answers from fixtures instantly instead of waiting out a 10 s timeout on every request.
 */
const BREAKER_MS = 15_000;
const breaker = globalThis as unknown as { __halisiDownUntil?: number };
export function upstreamDown(): boolean {
  return (breaker.__halisiDownUntil ?? 0) > Date.now();
}
export function markUpstreamDown(): void {
  breaker.__halisiDownUntil = Date.now() + BREAKER_MS;
}

export function demoFallbackEnabled(): boolean {
  return (process.env.DEMO_FALLBACK ?? "true").toLowerCase() !== "false";
}

export interface UpstreamRequest {
  method: string;
  /** Path on the backend, e.g. "/api/v1/check". */
  upstreamPath: string;
  search?: string;
  body?: ArrayBuffer;
  contentType?: string | null;
  clientIp?: string | null;
  /** Server components: cache for this many seconds. The proxy never caches. */
  revalidate?: number;
}

/**
 * Call the backend. Returns the Response for any HTTP answer the backend itself produced, or null
 * when the backend is unreachable (network error, timeout, ngrok tunnel offline, 5xx that isn't a
 * domain error). A null result means "use fixtures if allowed".
 */
export async function callUpstream(req: UpstreamRequest): Promise<Response | null> {
  const base = apiBase();
  if (!base || upstreamDown()) return null;
  const headers = new Headers({ accept: "application/json", "ngrok-skip-browser-warning": "1" });
  const key = process.env.HALISI_API_KEY;
  if (key) headers.set("X-Halisi-Key", key);
  if (req.contentType) headers.set("content-type", req.contentType);
  if (req.clientIp) headers.set("X-Forwarded-For", req.clientIp);
  try {
    const res = await fetch(`${base}${req.upstreamPath}${req.search ?? ""}`, {
      method: req.method,
      headers,
      body: req.body && req.body.byteLength > 0 ? req.body : undefined,
      signal: AbortSignal.timeout(TIMEOUT_MS),
      redirect: "manual",
      ...(req.revalidate ? { next: { revalidate: req.revalidate } } : { cache: "no-store" as const }),
    });
    // ngrok answers for an offline tunnel with its own error page and this header.
    if (res.headers.has("ngrok-error-code")) {
      markUpstreamDown();
      return null;
    }
    if (res.status >= 500) {
      // 502 TARGET_UNREACHABLE is a real answer (the page couldn't be fetched): pass it through.
      const text = await res.clone().text();
      if (res.status === 502 && text.includes("TARGET_UNREACHABLE")) return res;
      return null;
    }
    return res;
  } catch {
    markUpstreamDown();
    return null;
  }
}

export interface ServerResult<T> {
  data: T | null;
  status: number;
  fixture: boolean;
}

/**
 * For server components: GET a backend path and parse it. Uses fixtures when the backend is
 * unreachable (and DEMO_FALLBACK is on). `segments` are the proxy-style path parts.
 */
export async function serverGet<T>(
  segments: string[],
  schema: z.ZodType<T>,
  opts: { search?: URLSearchParams; revalidate?: number } = {},
): Promise<ServerResult<T>> {
  const search = opts.search?.toString() ? `?${opts.search.toString()}` : "";
  const res = await callUpstream({
    method: "GET",
    upstreamPath: segments[0] === "health" ? "/health" : `/api/v1/${segments.map(encodeURIComponent).join("/")}`,
    search,
    revalidate: opts.revalidate ?? 60,
  });
  if (res) {
    if (!res.ok) return { data: null, status: res.status, fixture: false };
    const parsed = schema.safeParse(await res.json());
    if (parsed.success) return { data: parsed.data, status: res.status, fixture: false };
    console.error("[halisi] contract mismatch on", segments.join("/"), parsed.error.issues.slice(0, 3));
    return { data: null, status: 500, fixture: false };
  }
  if (!demoFallbackEnabled()) return { data: null, status: 503, fixture: false };
  const fx = resolveFixture("GET", segments, opts.search ?? new URLSearchParams(), undefined);
  if (fx.status >= 400) return { data: null, status: fx.status, fixture: true };
  return { data: schema.parse(fx.body), status: fx.status, fixture: true };
}
