/**
 * Relative asset URLs from the API (`/seed/<file>`, `/media/<file>`, BACKEND.md 5.11) are served by
 * this app: from the backend when it's reachable, else (seed only) from the local seed folder.
 * Strict filenames, image types and a size cap keep this from becoming an open proxy.
 */
import { readSeedAsset } from "@/lib/fixtures";
import { apiBase, markUpstreamDown, upstreamDown } from "@/lib/upstream";

const FILE = /^[A-Za-z0-9._-]{1,120}\.(png|jpe?g|webp)$/;
const MAX_BYTES = 5 * 1024 * 1024;
const TYPES: Record<string, string> = { png: "image/png", jpg: "image/jpeg", jpeg: "image/jpeg", webp: "image/webp" };

export async function serveAsset(kind: "seed" | "media", file: string): Promise<Response> {
  if (!FILE.test(file)) return new Response("Not found", { status: 404 });
  const ext = file.split(".").pop()!.toLowerCase();
  const base = apiBase();
  if (base && !upstreamDown()) {
    try {
      const res = await fetch(`${base}/${kind}/${encodeURIComponent(file)}`, {
        headers: { "ngrok-skip-browser-warning": "1" },
        signal: AbortSignal.timeout(8_000),
        redirect: "manual",
        next: { revalidate: 3600 },
      });
      const type = res.headers.get("content-type") ?? "";
      const length = Number(res.headers.get("content-length") ?? 0);
      if (res.ok && type.startsWith("image/") && length <= MAX_BYTES && !res.headers.has("ngrok-error-code")) {
        return new Response(res.body, { headers: { "content-type": type, "cache-control": "public, max-age=3600" } });
      }
    } catch {
      markUpstreamDown(); // fall through to the local seed copy
    }
  }
  if (kind === "seed") {
    const local = readSeedAsset(file);
    if (local) {
      return new Response(new Uint8Array(local), {
        headers: { "content-type": TYPES[ext] ?? "application/octet-stream", "cache-control": "public, max-age=3600" },
      });
    }
  }
  return new Response("Not found", { status: 404 });
}
