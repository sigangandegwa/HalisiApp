import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The repo root has no package.json; pin Turbopack to this app so it doesn't guess.
  turbopack: { root: path.resolve(__dirname) },
  // Fixtures are read at runtime (seed/ preferred, simulator.json.gz): ship them with the server bundle.
  // OG images and badges read the committed WOFF fonts from src/assets/fonts.
  outputFileTracingIncludes: {
    "/**": ["./src/lib/fixtures/**/*", "./src/assets/fonts/**/*"],
  },
  poweredByHeader: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "SAMEORIGIN" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
      {
        source: "/sw.js",
        headers: [
          { key: "Cache-Control", value: "no-cache" },
          { key: "Service-Worker-Allowed", value: "/" },
        ],
      },
    ];
  },
};

export default nextConfig;
