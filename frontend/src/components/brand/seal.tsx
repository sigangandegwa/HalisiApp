import { rosette } from "@/lib/guilloche";
import { cn } from "@/lib/utils";
import { LogoImage } from "./logo-image";
import { MicroprintRing } from "./microprint";

/**
 * The Halisi seal (4.5): a circular guilloche ring with microprint and the merchant logo in the
 * centre. Used on /v/[slug], the badge and the dashboard protection summary.
 */
export function Seal({
  logoUrl,
  name,
  size = 200,
  seed = 11,
  className,
  tone = "real",
}: {
  logoUrl: string | null | undefined;
  name: string;
  size?: number;
  seed?: number;
  className?: string;
  tone?: "real" | "ink";
}) {
  const layers = rosette(seed, 400, 5, 0.6);
  const color = tone === "real" ? "var(--real)" : "var(--fg)";
  const id = `seal-ring-${seed}-${size}`;
  return (
    <div className={cn("relative shrink-0", className)} style={{ width: size, height: size, color }}>
      <svg viewBox="0 0 400 400" className="absolute inset-0 size-full" aria-hidden="true" focusable="false" fill="none">
        <circle cx="200" cy="200" r="198" stroke="currentColor" strokeOpacity="0.55" strokeWidth="1" vectorEffect="non-scaling-stroke" />
        <circle cx="200" cy="200" r="190" stroke="currentColor" strokeOpacity="0.35" strokeWidth="0.75" vectorEffect="non-scaling-stroke" />
        {layers.map((l, i) => (
          <path key={i} d={l.d} stroke="currentColor" strokeOpacity={0.5 * l.weight} strokeWidth="0.6" vectorEffect="non-scaling-stroke" />
        ))}
        <circle cx="200" cy="200" r="118" stroke="currentColor" strokeOpacity="0.6" strokeWidth="1" vectorEffect="non-scaling-stroke" />
      </svg>
      <MicroprintRing id={id} size={400} radius={128} className="absolute inset-0 size-full opacity-70" />
      <div className="absolute inset-[31%] overflow-hidden rounded-full ring-1 ring-current/40">
        <LogoImage src={logoUrl} alt={`${name} logo`} size={Math.round(size * 0.38)} className="size-full" />
      </div>
    </div>
  );
}
