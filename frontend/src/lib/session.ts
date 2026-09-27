/**
 * Merchant session (FRONTEND.md section 9.1): a passcode login that sets a signed, httpOnly JWT
 * cookie. Shared by `src/proxy.ts` (route gate) and the route handlers. Server-only.
 */
import { SignJWT, jwtVerify } from "jose";

export const SESSION_COOKIE = "halisi_session";
export const SESSION_TTL_SECONDS = 12 * 60 * 60; // 12 h

export interface MerchantSession {
  /** Merchant UUID used for `/merchants/{id}/...` API paths. */
  mid: string;
  /** Merchant slug, used for the public profile (`/merchants/{slug}`) and badge. */
  slug: string;
}

const DEV_SECRET = "halisi-dev-only-secret-do-not-deploy-000000";

/**
 * The signing key. Production requires SESSION_SECRET (32+ chars); `next dev` falls back to a
 * fixed development secret so the app can be explored without any configuration.
 */
function secretKey(): Uint8Array | null {
  const secret = process.env.SESSION_SECRET;
  if (secret && secret.length >= 32) return new TextEncoder().encode(secret);
  if (process.env.NODE_ENV === "development") return new TextEncoder().encode(DEV_SECRET);
  return null;
}

export function sessionConfigured(): boolean {
  return secretKey() !== null;
}

export async function signSession(session: MerchantSession): Promise<string> {
  const key = secretKey();
  if (!key) throw new Error("SESSION_SECRET is not configured (32+ characters required).");
  return new SignJWT({ mid: session.mid, slug: session.slug })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setSubject("merchant")
    .setExpirationTime(`${SESSION_TTL_SECONDS}s`)
    .sign(key);
}

/** Verify a session token. Returns null for missing, expired, tampered or unsigned tokens. */
export async function verifySession(token: string | undefined | null): Promise<MerchantSession | null> {
  const key = secretKey();
  if (!token || !key) return null;
  try {
    const { payload } = await jwtVerify(token, key, { algorithms: ["HS256"], subject: "merchant" });
    if (typeof payload.mid !== "string" || typeof payload.slug !== "string") return null;
    return { mid: payload.mid, slug: payload.slug };
  } catch {
    return null;
  }
}

/** Constant-time string comparison (length is not secret here: the passcode is fixed). */
export function safeEqual(a: string, b: string): boolean {
  const enc = new TextEncoder();
  const x = enc.encode(a);
  const y = enc.encode(b);
  let diff = x.length ^ y.length;
  const n = Math.max(x.length, y.length);
  for (let i = 0; i < n; i++) diff |= (x[i] ?? 0) ^ (y[i] ?? 0);
  return diff === 0;
}
