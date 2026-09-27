import { ImageResponse } from "next/og";
import { paymentParts } from "@/lib/format";
import { HALISI, INK, OgRosette, OgWordmark, PAPER, ogFonts, siteHost } from "@/lib/og";
import { MerchantPublic } from "@/lib/schemas";
import { serverGet } from "@/lib/upstream";

export const alt = "Halisi Verified certificate";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/** Certificate share card: business name, official payment at data size, the seal colour. */
export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const [res, fonts] = await Promise.all([serverGet(["merchants", slug], MerchantPublic), ogFonts()]);
  const m = res.data;
  const pay = m ? paymentParts(m.payment) : null;
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", background: PAPER, color: INK, padding: 56, position: "relative", fontFamily: "Geist" }}>
        <div style={{ position: "absolute", inset: 22, border: `2px solid ${HALISI}`, display: "flex", opacity: 0.6 }} />
        <div style={{ position: "absolute", inset: 30, border: `1px solid ${HALISI}`, display: "flex", opacity: 0.4 }} />
        <div style={{ position: "absolute", right: -120, bottom: -180, display: "flex" }}>
          <OgRosette size={640} seed={29} layers={5} color={HALISI} opacity={0.16} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 16px" }}>
          <OgWordmark />
          <span style={{ fontSize: 20, letterSpacing: "0.1em", color: HALISI, fontWeight: 600, textTransform: "uppercase" }}>Halisi Verified</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", flex: 1, justifyContent: "center", padding: "0 16px" }}>
          <span style={{ fontFamily: "Fraunces", fontWeight: 600, fontSize: 92, letterSpacing: "-0.035em", lineHeight: 1 }}>{m?.business_name ?? "Unknown business"}</span>
          {pay ? (
            <span style={{ fontFamily: "Geist Mono", fontSize: 54, marginTop: 28, letterSpacing: "-0.01em" }}>
              {pay.label} {pay.value}
            </span>
          ) : null}
          {m?.payment.account_name ? <span style={{ fontFamily: "Geist Mono", fontSize: 26, color: "#4a4a44", marginTop: 8 }}>{m.payment.account_name}</span> : null}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", padding: "0 16px 6px", fontSize: 24 }}>
          <span style={{ fontFamily: "Fraunces", fontStyle: "italic", fontWeight: 500 }}>If a page asks you to pay any other number, it is not us.</span>
          <span style={{ fontFamily: "Geist Mono", color: "#4a4a44" }}>{siteHost()}</span>
        </div>
      </div>
    ),
    { ...size, fonts },
  );
}
