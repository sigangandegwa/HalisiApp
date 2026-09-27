import type { MessageKey } from "@/lib/i18n";
import type { Verdict } from "@/lib/schemas";

export type Tone = "real" | "fake" | "warn" | "ink";
export type Glyph = "seal" | "broken" | "triangle" | "circle";

export interface VerdictMeta {
  tone: Tone;
  glyph: Glyph;
  word: MessageKey;
  sub: MessageKey;
  line: MessageKey;
  /** Stamp colour. FEKI uses the fill vermilion on both worlds (large type, 3:1+ on paper). */
  stampColor: string;
}

export const VERDICTS: Record<Verdict, VerdictMeta> = {
  official: { tone: "real", glyph: "seal", word: "verdict.official.word", sub: "verdict.official.sub", line: "line.official", stampColor: "var(--real)" },
  impersonation: { tone: "fake", glyph: "broken", word: "verdict.impersonation.word", sub: "verdict.impersonation.sub", line: "line.impersonation", stampColor: "var(--color-feki)" },
  suspicious: { tone: "warn", glyph: "triangle", word: "verdict.suspicious.word", sub: "verdict.suspicious.sub", line: "line.suspicious", stampColor: "var(--warn)" },
  no_match: { tone: "ink", glyph: "circle", word: "verdict.no_match.word", sub: "verdict.no_match.sub", line: "line.no_match", stampColor: "var(--fg)" },
  error: { tone: "ink", glyph: "circle", word: "verdict.error.word", sub: "verdict.error.sub", line: "line.no_match", stampColor: "var(--fg)" },
};

/** Text colour class per tone (small text: AA-contrast variants). */
export const toneText: Record<Tone, string> = {
  real: "text-real",
  fake: "text-fake",
  warn: "text-warn",
  ink: "text-fg",
};

/** Fill colour class per tone (bars, rails, dots). */
export const toneFill: Record<Tone, string> = {
  real: "bg-real",
  fake: "bg-feki",
  warn: "bg-caution",
  ink: "bg-fg",
};

/** CSS colour value per tone, for inline SVG/style use. */
export const toneColor: Record<Tone, string> = {
  real: "var(--real)",
  fake: "var(--color-feki)",
  warn: "var(--color-caution)",
  ink: "var(--fg)",
};

/** Severity tone for a composite score on the dashboard (70 / 40 thresholds, BACKEND.md 6.8). */
export function scoreTone(score: number, verdict?: Verdict): Tone {
  if (verdict === "official") return "real";
  if (score >= 70) return "fake";
  if (score >= 40) return "warn";
  return "ink";
}
