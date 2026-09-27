/**
 * Shared pieces for next/og images (share cards, certificate OG, badges). Server-only.
 * Fonts are committed WOFF files (OFL: Fraunces, Geist, Geist Mono) so rendering needs no network.
 */
import { readFile } from "node:fs/promises";
import path from "node:path";
import { rosette } from "@/lib/guilloche";

const FONT_DIR = path.join(process.cwd(), "src", "assets", "fonts");

export const INK = "#12130F";
export const PAPER = "#F2EEE3";
export const PAPER_2 = "#E8E2D2";
export const FEKI = "#E4412A";
export const HALISI = "#1D5C43";
export const CAUTION_INK = "#8A5A00";

let fontCache: Promise<{ name: string; data: Buffer; weight: 500 | 600; style: "normal" | "italic" }[]> | null = null;

export function ogFonts() {
  fontCache ??= Promise.all([
    readFile(path.join(FONT_DIR, "Fraunces-SemiBold.woff")).then((data) => ({ name: "Fraunces", data, weight: 600 as const, style: "normal" as const })),
    readFile(path.join(FONT_DIR, "Fraunces-Italic-500.woff")).then((data) => ({ name: "Fraunces", data, weight: 500 as const, style: "italic" as const })),
    readFile(path.join(FONT_DIR, "Geist-Medium.woff")).then((data) => ({ name: "Geist", data, weight: 500 as const, style: "normal" as const })),
    readFile(path.join(FONT_DIR, "Geist-SemiBold.woff")).then((data) => ({ name: "Geist", data, weight: 600 as const, style: "normal" as const })),
    readFile(path.join(FONT_DIR, "GeistMono-Medium.woff")).then((data) => ({ name: "Geist Mono", data, weight: 500 as const, style: "normal" as const })),
  ]);
  return fontCache;
}

/** A guilloche rosette as an inline SVG element (Satori renders SVG paths). */
export function OgRosette({ size, seed = 7, color = INK, opacity = 0.1, layers = 4 }: { size: number; seed?: number; color?: string; opacity?: number; layers?: number }) {
  const paths = rosette(seed, 400, layers);
  return (
    <svg width={size} height={size} viewBox="0 0 400 400" fill="none">
      {paths.map((p, i) => (
        <path key={i} d={p.d} stroke={color} strokeOpacity={opacity * p.weight} strokeWidth={0.8} />
      ))}
    </svg>
  );
}

export function OgWordmark({ color = INK, size = 34 }: { color?: string; size?: number }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, color }}>
      <svg width={size * 0.95} height={size * 0.95} viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10.5" stroke={color} strokeWidth="1.4" />
        <path d="M8.2 12.3l2.4 2.4 5.2-5.4" stroke={color} strokeWidth="1.7" />
      </svg>
      <span style={{ fontFamily: "Fraunces", fontStyle: "italic", fontWeight: 500, fontSize: size, letterSpacing: "-0.02em" }}>Halisi</span>
    </div>
  );
}

/** The verdict stamp for OG images: double-rule rectangle, rotated. */
export function OgStamp({ word, color, fontSize = 190 }: { word: string; color: string; fontSize?: number }) {
  return (
    <div
      style={{
        display: "flex",
        border: `${Math.max(4, fontSize * 0.045)}px solid ${color}`,
        padding: `${fontSize * 0.06}px ${fontSize * 0.14}px ${fontSize * 0.02}px`,
        transform: "rotate(-2.5deg)",
        color,
        position: "relative",
      }}
    >
      <div style={{ position: "absolute", top: 6, left: 6, right: 6, bottom: 6, border: `2px solid ${color}`, display: "flex" }} />
      <span style={{ fontFamily: "Fraunces", fontWeight: 600, fontSize, lineHeight: 1, letterSpacing: "-0.04em" }}>{word}</span>
    </div>
  );
}

export function siteHost(): string {
  try {
    return new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000").host;
  } catch {
    return "halisi";
  }
}
