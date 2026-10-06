/**
 * Path allowlist for the server proxy (FRONTEND.md section 9.1). The proxy holds the API key, so
 * anything not listed here must 404, otherwise the proxy becomes an open door to the backend.
 */

export type Access = "public" | "merchant";

export interface AllowedRoute {
  access: Access;
  /** Backend path, relative to the API origin (e.g. "/api/v1/check" or "/health"). */
  upstream: string;
  /** For merchant routes scoped to one merchant: the `{id}` segment, checked against the session. */
  merchantId?: string;
}

const SEGMENT = /^[A-Za-z0-9._~-]{1,128}$/;

/**
 * Classify a proxied request. `segments` are the path parts after `/api/halisi/`.
 * Returns null when the method + path combination is not allowed.
 */
export function classify(
  method: string,
  segments: readonly string[],
  search: URLSearchParams,
): AllowedRoute | null {
  if (segments.length === 0 || segments.length > 4) return null;
  if (!segments.every((s) => SEGMENT.test(s))) return null;
  const m = method.toUpperCase();
  const [a, b, c, d] = segments;
  const v1 = (p: string) => `/api/v1/${p}`;
  const path = segments.join("/");

  switch (segments.length) {
    case 1:
      if (a === "health" && m === "GET") return { access: "public", upstream: "/health" };
      if (a === "check" && m === "POST") return { access: "public", upstream: v1(path) };
      if (a === "reports" && m === "POST") return { access: "public", upstream: v1(path) };
      if (a === "stats" && m === "GET") {
        return { access: search.has("merchant_id") ? "merchant" : "public", upstream: v1(path) };
      }
      // Public: this is signup. src/app/api/halisi/[...path]/route.ts signs a session for the
      // merchant it just created, so registering and being logged into your own dashboard is the
      // same request — there's no separate account system to gate this behind.
      if (a === "merchants" && m === "POST") return { access: "public", upstream: v1(path) };
      return null;
    case 2:
      if (a === "check" && m === "GET") return { access: "public", upstream: v1(path) };
      if (a === "verify" && b === "payment" && m === "GET") return { access: "public", upstream: v1(path) };
      if (a === "merchants" && m === "GET") return { access: "public", upstream: v1(path) };
      if (a === "threats" && (m === "GET" || m === "PATCH")) return { access: "merchant", upstream: v1(path) };
      if (a === "simulator" && b === "clone" && m === "POST") return { access: "merchant", upstream: v1(path) };
      return null;
    case 3:
      if (a === "merchants" && (c === "threats" || c === "alerts") && m === "GET") {
        return { access: "merchant", upstream: v1(path), merchantId: b };
      }
      if (a === "threats" && c === "playbooks" && m === "POST") return { access: "merchant", upstream: v1(path) };
      return null;
    case 4:
      if (a === "merchants" && c === "alerts" && d === "read" && m === "POST") {
        return { access: "merchant", upstream: v1(path), merchantId: b };
      }
      return null;
    default:
      return null;
  }
}

/** Page routes gated by the proxy (redirect to /login without a valid session). */
export function isMerchantPage(pathname: string): boolean {
  return /^\/(dashboard|simulator)(\/|$)/.test(pathname);
}
