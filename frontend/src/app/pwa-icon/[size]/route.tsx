import { ImageResponse } from "next/og";

const SIZES = new Set([192, 512]);

/** Install icon: ink square, bone "H" with a verdict-red tick, drawn with plain shapes (no font load). */
export async function GET(_req: Request, ctx: { params: Promise<{ size: string }> }) {
  const { size: raw } = await ctx.params;
  const size = Number(raw);
  if (!SIZES.has(size)) return new Response("Not found", { status: 404 });
  const bar = size * 0.12;
  const h = size * 0.5;
  const w = size * 0.42;
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", background: "#07070A" }}>
        <div style={{ position: "relative", display: "flex", width: w, height: h }}>
          <div style={{ position: "absolute", left: 0, top: 0, width: bar, height: h, background: "#F1EEE6" }} />
          <div style={{ position: "absolute", right: 0, top: 0, width: bar, height: h, background: "#F1EEE6" }} />
          <div style={{ position: "absolute", left: 0, top: h / 2 - bar / 2, width: w, height: bar, background: "#F1EEE6" }} />
          <div style={{ position: "absolute", right: -bar * 0.2, top: -bar * 0.9, width: bar * 0.9, height: bar * 0.9, background: "#1FBF84" }} />
        </div>
      </div>
    ),
    { width: size, height: size },
  );
}
