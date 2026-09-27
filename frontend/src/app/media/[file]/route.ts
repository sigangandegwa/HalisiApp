import { serveAsset } from "@/lib/assets";

/** `/media/<file>`: logos uploaded through onboarding, served by the backend. */
export async function GET(_req: Request, ctx: { params: Promise<{ file: string }> }) {
  const { file } = await ctx.params;
  return serveAsset("media", file);
}
