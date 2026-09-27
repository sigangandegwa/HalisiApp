import { ImageResponse } from "next/og";
import { en } from "@/lib/i18n/en";
import { CAUTION_INK, FEKI, HALISI, INK, OgRosette, OgStamp, OgWordmark, PAPER, ogFonts, siteHost } from "@/lib/og";
import { CheckResult, type Verdict } from "@/lib/schemas";
import { serverGet } from "@/lib/upstream";

export const alt = "Halisi verdict";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const WORD: Record<Verdict, { word: string; color: string; sub: string }> = {
  impersonation: { word: en["verdict.impersonation.word"], color: FEKI, sub: en["verdict.impersonation.sub"] },
  official: { word: en["verdict.official.word"], color: HALISI, sub: en["verdict.official.sub"] },
  suspicious: { word: en["verdict.suspicious.word"], color: CAUTION_INK, sub: en["verdict.suspicious.sub"] },
  no_match: { word: en["verdict.no_match.word"], color: INK, sub: en["verdict.no_match.sub"] },
  error: { word: en["verdict.error.word"], color: INK, sub: en["verdict.error.sub"] },
};

/** WhatsApp / social preview (FRONTEND.md section 6.2): the stamp does the viral work. */
export default async function Image({ params }: { params: Promise<{ scanId: string }> }) {
  const { scanId } = await params;
  const [res, fonts] = await Promise.all([serverGet(["check", scanId], CheckResult), ogFonts()]);
  const r = res.data;
  const v = WORD[r?.verdict ?? "error"];
  const long = v.word.length > 8;
  const business = r?.matched_merchant?.business_name;
  const line =
    r?.verdict === "impersonation" && business
      ? `Impersonating ${business}. Don’t send money.`
      : r?.verdict === "official" && business
        ? `The official page of ${business}.`
        : r?.verdict === "suspicious" && business
          ? `Looks like ${business}. Confirm before paying.`
          : "Not a Halisi-verified page.";

  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", background: PAPER, color: INK, padding: "56px 64px", position: "relative", fontFamily: "Geist" }}>
        <div style={{ position: "absolute", top: -160, right: -170, display: "flex" }}>
          <OgRosette size={720} seed={7} layers={5} opacity={0.12} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <OgWordmark />
          <span style={{ fontFamily: "Geist Mono", fontSize: 20, letterSpacing: "0.08em", color: "#5c5c55", textTransform: "uppercase" }}>
            {v.sub}
          </span>
        </div>
        <div style={{ display: "flex", flex: 1, alignItems: "center", paddingTop: 10 }}>
          <OgStamp word={v.word} color={v.color} fontSize={long ? 118 : 196} />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <span style={{ fontFamily: "Geist Mono", fontSize: 40, letterSpacing: "-0.01em" }}>@{r?.target.handle ?? "unknown"}</span>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
            <span style={{ fontSize: 30, fontWeight: 600, color: "#3a3a34", maxWidth: 820 }}>{line}</span>
            <span style={{ fontFamily: "Geist Mono", fontSize: 22, color: "#5c5c55" }}>
              {r && r.verdict !== "official" ? `Score ${Math.round(r.score)}/100 · ` : ""}
              {siteHost()}
            </span>
          </div>
        </div>
      </div>
    ),
    { ...size, fonts },
  );
}
