import type { CSSProperties } from "react";
import { diffBits, hexToBits, isHash } from "@/lib/hash";
import { cn } from "@/lib/utils";

/**
 * 8x8 perceptual-hash grid (FRONTEND.md section 7). The bits are the real 64-bit pHash from the
 * API; cells stagger in by diagonal ((row+col)*12 ms) and differing bits flash the verdict colour
 * twice. CSS-only animation (cheap on mid-range phones). `instant` renders the final state.
 */
export function HashGrid({
  hex,
  compareHex,
  color = "var(--color-feki)",
  size = 112,
  delay = 0,
  instant = false,
  label,
  className,
}: {
  hex: string;
  compareHex?: string | null;
  color?: string;
  size?: number;
  delay?: number;
  instant?: boolean;
  label: string;
  className?: string;
}) {
  if (!isHash(hex)) return null;
  const bits = hexToBits(hex);
  const diff = compareHex && isHash(compareHex) ? diffBits(hex, compareHex) : new Set<number>();
  const gap = Math.max(1, Math.round(size / 56));
  return (
    <figure className={cn("m-0", className)}>
      <div
        role="img"
        aria-label={`${label}: ${hex}${diff.size ? `, ${diff.size} bits differ` : ""}`}
        className="grid grid-cols-8"
        style={{ width: size, height: size, gap }}
      >
        {bits.map((on, i) => {
          const row = Math.floor(i / 8);
          const col = i % 8;
          const differs = diff.has(i);
          const style: CSSProperties = instant
            ? {}
            : {
                animation: `halisi-cell 280ms var(--ease-out) both`,
                animationDelay: `${delay + (row + col) * 12}ms`,
              };
          return (
            <span key={i} className="relative block" style={style}>
              <span className={cn("absolute inset-0 rounded-[1px]", on ? "bg-fg" : "bg-bg-3")} />
              {differs ? (
                <span
                  className="absolute inset-0 rounded-[1px]"
                  style={{
                    background: color,
                    opacity: on ? 1 : 0.42,
                    ["--o" as string]: on ? 1 : 0.42,
                    animation: instant ? undefined : `halisi-flash 520ms var(--ease-quart) both`,
                    animationDelay: instant ? undefined : `${delay + 260 + (row + col) * 12}ms`,
                  }}
                />
              ) : null}
            </span>
          );
        })}
      </div>
      <figcaption className="mt-2 max-w-[var(--w)] truncate font-mono text-[0.6875rem] text-fg-3" style={{ ["--w" as string]: `${size}px` }}>
        {hex}
      </figcaption>
    </figure>
  );
}
