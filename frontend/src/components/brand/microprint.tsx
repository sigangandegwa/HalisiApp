import { cn } from "@/lib/utils";

const PHRASE = "HALISI · AUTHENTIC · HALISI · HALISI VERIFIED · ";

/**
 * Banknote-style microtext along a section rule (FRONTEND.md section 4.5): 6 px Geist Mono.
 * Decorative and aria-hidden. Reads as a hairline from a distance, as text up close.
 */
export function Microprint({ className, text = PHRASE, repeat = 24 }: { className?: string; text?: string; repeat?: number }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "pointer-events-none overflow-hidden whitespace-nowrap font-mono text-[6px] leading-[8px] tracking-[0.18em] text-fg-3 select-none",
        className,
      )}
    >
      {text.repeat(repeat)}
    </div>
  );
}

/** Microtext around a circle (the seal ring). */
export function MicroprintRing({
  size = 200,
  radius = 88,
  text = PHRASE,
  className,
  id,
}: {
  size?: number;
  radius?: number;
  text?: string;
  className?: string;
  id: string;
}) {
  const c = size / 2;
  const circumference = 2 * Math.PI * radius;
  const perChar = 3.9; // 6px mono at 0.18em tracking, measured
  const repeats = Math.max(1, Math.floor(circumference / (text.length * perChar)));
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className={cn("pointer-events-none", className)} aria-hidden="true" focusable="false">
      <defs>
        <path id={id} d={`M ${c},${c} m -${radius},0 a ${radius},${radius} 0 1,1 ${radius * 2},0 a ${radius},${radius} 0 1,1 -${radius * 2},0`} />
      </defs>
      <text className="fill-current font-mono" fontSize="6" letterSpacing="1.1">
        <textPath href={`#${id}`} textLength={circumference - 2} lengthAdjust="spacing">
          {text.repeat(repeats)}
        </textPath>
      </text>
    </svg>
  );
}
