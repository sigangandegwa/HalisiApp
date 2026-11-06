import { NextResponse, type NextRequest } from "next/server";

const LINK = /https?:\/\/[^\s<>"']+/i;

/**
 * PWA share-target landing. Social apps put the link in `url`, or inside `text` ("Look at this shop
 * https://..."). We pull the first link out and hand it to the checker as a prefill; if there is none we
 * pass the trimmed text through, because a bare handle is also a valid thing to check.
 */
export function GET(req: NextRequest) {
  const p = req.nextUrl.searchParams;
  const candidates = [p.get("url"), p.get("text"), p.get("title")].filter((v): v is string => Boolean(v && v.trim()));
  let q = "";
  for (const c of candidates) {
    const m = LINK.exec(c);
    if (m) {
      q = m[0];
      break;
    }
  }
  if (!q && candidates[0]) q = candidates[0].trim();
  const target = new URL("/", req.nextUrl.origin);
  if (q) target.searchParams.set("q", q.slice(0, 2048));
  return NextResponse.redirect(target, 303);
}
