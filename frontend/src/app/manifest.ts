import type { MetadataRoute } from "next";

/**
 * Installable app + share target (PRODUCT_V2 section 6.3, TSK-051). Once installed, "Share" in
 * Instagram/TikTok/Facebook lists Halisi; the link arrives at /share, which opens the checker pre-filled.
 */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Halisi: check before you lipa",
    short_name: "Halisi",
    description: "Paste a shop's link, handle, Till or phone number. Halisi tells you if it looks real.",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: "#07070A",
    theme_color: "#07070A",
    icons: [
      { src: "/pwa-icon/192", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/pwa-icon/512", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/pwa-icon/512", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
    share_target: {
      action: "/share",
      method: "GET",
      params: { title: "title", text: "text", url: "url" },
    },
  };
}
