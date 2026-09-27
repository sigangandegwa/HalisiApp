/**
 * Next.js 16 Proxy (formerly `middleware.ts`; the convention was renamed in v16 and the exported
 * function must be called `proxy`). Gates the merchant pages and merchant API paths.
 * The route handler re-checks the session: the proxy is a first line, not the only one.
 */
import { NextResponse, type NextRequest } from "next/server";
import { classify, isMerchantPage } from "@/lib/allowlist";
import { SESSION_COOKIE, verifySession } from "@/lib/session";

export async function proxy(request: NextRequest) {
  const { pathname, search, searchParams } = request.nextUrl;
  const session = await verifySession(request.cookies.get(SESSION_COOKIE)?.value);

  if (isMerchantPage(pathname) && !session) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", pathname + search);
    return NextResponse.redirect(login);
  }

  if (pathname === "/login" && session) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  if (pathname.startsWith("/api/halisi/")) {
    const segments = pathname.slice("/api/halisi/".length).split("/").filter(Boolean);
    const route = classify(request.method, segments, searchParams);
    if (route?.access === "merchant" && !session) {
      return NextResponse.json(
        { error: { code: "UNAUTHORIZED", message: "Merchant login required." } },
        { status: 401 },
      );
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/simulator/:path*", "/login", "/api/halisi/:path*"],
};
