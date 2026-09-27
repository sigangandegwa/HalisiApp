import { cn } from "@/lib/utils";

/** The Halisi wordmark: Fraunces italic with a small seal-ring mark. */
export function Wordmark({ className, suffix }: { className?: string; suffix?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <svg viewBox="0 0 24 24" className="size-[1.05em] shrink-0" aria-hidden="true" focusable="false" fill="none">
        <circle cx="12" cy="12" r="10.5" stroke="currentColor" strokeWidth="1.25" />
        <circle cx="12" cy="12" r="7.25" stroke="currentColor" strokeWidth="0.75" strokeDasharray="1.2 1.4" />
        <path d="M8.2 12.3l2.4 2.4 5.2-5.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="square" />
      </svg>
      <span className="font-display text-[1.45em] leading-none italic tracking-[-0.03em]" style={{ fontVariationSettings: '"SOFT" 100' }}>
        Halisi
      </span>
      {suffix ? <span className="type-caption text-fg-3">{suffix}</span> : null}
    </span>
  );
}

/**
 * Verdict shapes (FRONTEND.md section 11): colour is never the only signal.
 * seal = official, broken seal = fake, triangle = caution, circle = unknown.
 */
export function VerdictGlyph({ glyph, className }: { glyph: "seal" | "broken" | "triangle" | "circle"; className?: string }) {
  const common = { viewBox: "0 0 24 24", className: cn("size-5 shrink-0", className), "aria-hidden": true, focusable: false, fill: "none" } as const;
  switch (glyph) {
    case "seal":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9.5" stroke="currentColor" strokeWidth="1.5" />
          <path d="M7.8 12.4l2.8 2.8 5.6-6" stroke="currentColor" strokeWidth="1.75" strokeLinecap="square" />
        </svg>
      );
    case "broken":
      return (
        <svg {...common}>
          <path d="M11 2.6A9.5 9.5 0 0 0 9.6 21.2" stroke="currentColor" strokeWidth="1.5" />
          <path d="M13.2 2.6a9.5 9.5 0 0 1 1.3 18.7" stroke="currentColor" strokeWidth="1.5" />
          <path d="M12.3 2.5l-2 5 3 3.2-2.4 4.1 1.6 5.9" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="bevel" />
        </svg>
      );
    case "triangle":
      return (
        <svg {...common}>
          <path d="M12 3L21.5 20H2.5L12 3z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="miter" />
          <path d="M12 9.5v5M12 16.6v1.6" stroke="currentColor" strokeWidth="1.75" />
        </svg>
      );
    default:
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9.5" stroke="currentColor" strokeWidth="1.5" />
          <circle cx="12" cy="12" r="1.6" fill="currentColor" />
        </svg>
      );
  }
}
