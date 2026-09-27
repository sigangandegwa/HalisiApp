import { serveAsset } from "@/lib/assets";

/** `/seed/<file>`: seed logos and avatars (backend first, local seed folder as fallback). */
export async function GET(_req: Request, ctx: { params: Promise<{ file: string }> }) {
  const { file } = await ctx.params;
  return serveAsset("seed", file);
}
