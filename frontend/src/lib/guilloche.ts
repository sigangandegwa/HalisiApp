/**
 * Procedural guilloche geometry (FRONTEND.md section 4.5): hypotrochoid rosettes,
 *   x = (R - r) cos t + d cos((R - r) t / r)
 *   y = (R - r) sin t - d sin((R - r) t / r)
 * Pure and deterministic (seeded), memoised, <= 2k points per path. Shared by the React ornament,
 * the seal and the OG images.
 */

export interface RosetteLayer {
  d: string;
  /** Relative stroke opacity for this layer (0..1). */
  weight: number;
}

function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const gcd = (a: number, b: number): number => (b === 0 ? a : gcd(b, a % b));

/** One closed hypotrochoid, scaled to fit `radius`, centred on (cx, cy). */
export function hypotrochoid(
  R: number,
  r: number,
  d: number,
  opts: { cx: number; cy: number; radius: number; rotation?: number; maxPoints?: number },
): string {
  const turns = r / gcd(R, r);
  const extent = R - r + d;
  const scale = opts.radius / extent;
  const steps = Math.min(opts.maxPoints ?? 1800, Math.max(240, Math.round(turns * 90)));
  const rot = opts.rotation ?? 0;
  const cos = Math.cos(rot);
  const sin = Math.sin(rot);
  let path = "";
  for (let i = 0; i <= steps; i++) {
    const t = (i / steps) * Math.PI * 2 * turns;
    const k = ((R - r) / r) * t;
    const x0 = ((R - r) * Math.cos(t) + d * Math.cos(k)) * scale;
    const y0 = ((R - r) * Math.sin(t) - d * Math.sin(k)) * scale;
    const x = opts.cx + x0 * cos - y0 * sin;
    const y = opts.cy + x0 * sin + y0 * cos;
    path += `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
  }
  return `${path}Z`;
}

const cache = new Map<string, RosetteLayer[]>();

/**
 * A banknote-style rosette: several interleaved hypotrochoids with slightly different parameters.
 * `size` is the viewBox edge; `inner` (0..1) leaves an empty centre (for the seal).
 */
export function rosette(seed: number, size = 400, layers = 4, inner = 0): RosetteLayer[] {
  const key = `${seed}|${size}|${layers}|${inner}`;
  const hit = cache.get(key);
  if (hit) return hit;
  const rand = mulberry32(seed);
  const presets: [number, number][] = [
    [96, 36], [100, 35], [90, 33], [84, 30], [105, 42], [120, 45], [72, 27], [110, 40],
  ];
  const out: RosetteLayer[] = [];
  const c = size / 2;
  for (let i = 0; i < layers; i++) {
    const [R, r] = presets[Math.floor(rand() * presets.length)];
    const dRatio = inner > 0 ? 0.35 + rand() * 0.25 : 0.55 + rand() * 0.6;
    const radius = c * (inner > 0 ? 0.98 - i * 0.035 : 0.98 - i * 0.12);
    out.push({
      d: hypotrochoid(R, r, r * dRatio, { cx: c, cy: c, radius, rotation: rand() * Math.PI }),
      weight: 1 - i * (0.5 / Math.max(1, layers)),
    });
  }
  cache.set(key, out);
  return out;
}

/** A thin repeating wave band (certificate borders). */
export function waveBand(width: number, height: number, periods: number, phase = 0, amp = 0.5): string {
  const steps = Math.min(1600, periods * 24);
  let path = "";
  for (let i = 0; i <= steps; i++) {
    const x = (i / steps) * width;
    const y = height / 2 + Math.sin((i / steps) * Math.PI * 2 * periods + phase) * (height * amp);
    path += `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
  }
  return path;
}
