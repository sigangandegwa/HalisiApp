import { rosette } from "@/lib/guilloche";
import { cn } from "@/lib/utils";

interface GuillocheProps {
  /** Seed: the same seed always draws the same rosette ("seeded per page"). */
  seed?: number;
  layers?: number;
  /** 0..1: leave an empty centre (used by the seal). */
  inner?: number;
  /** Draw in once on load with stroke-dashoffset (1.6 s, ease.out). Never loops. */
  draw?: boolean;
  /** Stroke opacity of the strongest layer. Spec: 0.5 px ink at 7 %. */
  opacity?: number;
  strokeWidth?: number;
  className?: string;
  /** Colour; defaults to currentColor so the ornament follows the world (ink or paper). */
  color?: string;
}

/**
 * Security-print rosette (FRONTEND.md section 4.5). Decorative: aria-hidden, no pointer events.
 * Server component: the SVG is generated once per seed and memoised.
 */
export function Guilloche({
  seed = 7,
  layers = 4,
  inner = 0,
  draw = false,
  opacity = 0.07,
  strokeWidth = 0.5,
  className,
  color = "currentColor",
}: GuillocheProps) {
  const size = 400;
  const paths = rosette(seed, size, layers, inner);
  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      className={cn("pointer-events-none select-none", className)}
      aria-hidden="true"
      focusable="false"
      fill="none"
    >
      {paths.map((p, i) => (
        <path
          key={i}
          d={p.d}
          stroke={color}
          strokeOpacity={opacity * p.weight}
          strokeWidth={strokeWidth}
          vectorEffect="non-scaling-stroke"
          pathLength={1}
          style={
            draw
              ? {
                  strokeDasharray: 1,
                  strokeDashoffset: 1,
                  animation: `halisi-draw 1.6s var(--ease-out) ${i * 0.12}s forwards`,
                }
              : undefined
          }
        />
      ))}
    </svg>
  );
}
