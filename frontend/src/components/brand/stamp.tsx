import type { CSSProperties, ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * SVG filter definitions for the ink stamp (FRONTEND.md section 4.5): feTurbulence +
 * feDisplacementMap bleed the edges, a second noise knocks out specks like a worn rubber stamp.
 * Rendered once in the root layout.
 */
export function InkFilterDefs() {
  return (
    <svg width="0" height="0" aria-hidden="true" focusable="false" style={{ position: "absolute", width: 0, height: 0 }}>
      <defs>
        <filter id="halisi-ink" x="-6%" y="-10%" width="112%" height="120%" colorInterpolationFilters="sRGB">
          <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="3" seed="3" result="warp" />
          <feDisplacementMap in="SourceGraphic" in2="warp" scale="3.5" xChannelSelector="R" yChannelSelector="G" result="bled" />
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="1" seed="11" result="grain" />
          <feColorMatrix in="grain" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -7 5.4" result="holes" />
          <feComposite in="bled" in2="holes" operator="in" />
        </filter>
        <filter id="halisi-ink-wet" x="-10%" y="-15%" width="120%" height="130%" colorInterpolationFilters="sRGB">
          <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="2" seed="5" result="warp" />
          <feDisplacementMap in="SourceGraphic" in2="warp" scale="10" xChannelSelector="R" yChannelSelector="G" result="bled" />
          <feGaussianBlur in="bled" stdDeviation="1.2" />
        </filter>
      </defs>
    </svg>
  );
}

/**
 * Misregistration (4.5): two offset colour plates (vermilion and green at 40 %, +/-2 px) behind
 * the ink layer, like a badly printed counterfeit note. Used on the hero word and FEKI only.
 * `offset` 0 = in register. Plates are aria-hidden; only the top layer is read.
 */
export function Misregister({
  children,
  offset = 2,
  className,
  plateOpacity = 0.4,
  style,
}: {
  children: ReactNode;
  offset?: number;
  className?: string;
  plateOpacity?: number;
  style?: CSSProperties;
}) {
  const plate = "pointer-events-none absolute inset-0 select-none transition-[transform,opacity] duration-(--dur-reveal) ease-out";
  return (
    <span className={cn("relative inline-block", className)} style={style}>
      <span
        aria-hidden="true"
        className={cn(plate, "text-feki")}
        style={{ transform: `translate3d(${-offset}px, ${offset * 0.5}px, 0)`, opacity: offset === 0 ? 0 : plateOpacity }}
      >
        {children}
      </span>
      <span
        aria-hidden="true"
        className={cn(plate, "text-halisi")}
        style={{ transform: `translate3d(${offset}px, ${-offset * 0.5}px, 0)`, opacity: offset === 0 ? 0 : plateOpacity }}
      >
        {children}
      </span>
      <span className="relative">{children}</span>
    </span>
  );
}

export type StampSize = "xl" | "md" | "sm";

const sizes: Record<StampSize, string> = {
  xl: "text-[length:clamp(3.5rem,min(15vw,var(--stamp-fit,13rem)),13rem)]",
  md: "text-[length:clamp(2rem,5vw,3.75rem)]",
  sm: "text-[length:1.375rem]",
};

/**
 * The verdict stamp: the word inside a double-rule rectangle, rotated -2.5 deg, ink-bled.
 * Purely presentational; the Forensic Verdict animates it. `color` comes from the verdict tokens.
 */
export function Stamp({
  word,
  sub,
  color,
  size = "xl",
  misregister = false,
  wet = false,
  className,
  rotate = -2.5,
}: {
  word: string;
  sub?: string;
  color: string;
  size?: StampSize;
  misregister?: boolean;
  /** Heavier bleed used for the first frames of the landing. */
  wet?: boolean;
  className?: string;
  rotate?: number;
}) {
  const chars = word.replace(/\W/g, "").length || 1;
  const style = {
    color,
    rotate: `${rotate}deg`,
    // fit long words (HAIJULIKANI.) into narrow columns
    "--stamp-fit": `${(88 / chars) * 1.55}vw`,
  } as CSSProperties;
  const text = misregister ? <Misregister offset={size === "sm" ? 1 : 2}>{word}</Misregister> : word;
  return (
    <span
      className={cn("inline-flex origin-center flex-col items-stretch leading-none", sizes[size], className)}
      style={style}
    >
      <span
        className="relative block border-current px-[0.14em] pt-[0.1em] pb-[0.06em]"
        style={{ borderWidth: "max(2px, 0.045em)", borderStyle: "solid", filter: `url(#${wet ? "halisi-ink-wet" : "halisi-ink"})` }}
      >
        <span
          aria-hidden="true"
          className="pointer-events-none absolute border-current"
          style={{ inset: "max(3px, 0.05em)", borderWidth: "max(1px, 0.014em)", borderStyle: "solid" }}
        />
        <span className="block font-display font-semibold tracking-[-0.04em] whitespace-nowrap" style={{ fontVariationSettings: '"SOFT" 0, "WONK" 0' }}>
          {text}
        </span>
      </span>
      {sub ? (
        <span className="mt-[0.35em] block text-center font-sans text-[max(0.7rem,0.13em)] font-semibold tracking-[0.12em] uppercase">
          {sub}
        </span>
      ) : null}
    </span>
  );
}
