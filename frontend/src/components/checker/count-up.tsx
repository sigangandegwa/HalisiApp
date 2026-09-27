"use client";

import { useEffect, useRef } from "react";
import { ease } from "@/lib/motion";

/** Cubic-bezier easing evaluated numerically (same curves as the CSS/Motion tokens). */
export function bezierEase([x1, y1, x2, y2]: readonly [number, number, number, number]) {
  const sample = (a: number, b: number, t: number) => ((1 - 3 * b + 3 * a) * t + (3 * b - 6 * a)) * t * t + 3 * a * t;
  return (x: number) => {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    let lo = 0;
    let hi = 1;
    let t = x;
    for (let i = 0; i < 14; i++) {
      const cx = sample(x1, x2, t);
      if (Math.abs(cx - x) < 1e-4) break;
      if (cx < x) lo = t;
      else hi = t;
      t = (lo + hi) / 2;
    }
    return sample(y1, y2, t);
  };
}

const easeOut = bezierEase(ease.out);

/**
 * A number that counts from `from` to `to`. Writes textContent directly from rAF, so a dozen of
 * these don't re-render React 60 times a second. `instant` renders the final value (skip /
 * reduced motion / returning visitors).
 */
export function CountUp({
  to,
  from = 0,
  delay = 0,
  duration = 800,
  decimals = 0,
  instant = false,
  className,
  suffix = "",
}: {
  to: number;
  from?: number;
  delay?: number;
  duration?: number;
  decimals?: number;
  instant?: boolean;
  className?: string;
  suffix?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const fmt = (v: number) => `${v.toFixed(decimals)}${suffix}`;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (instant) {
      el.textContent = fmt(to);
      return;
    }
    el.textContent = fmt(from);
    let raf = 0;
    const start = performance.now() + delay;
    const tick = (now: number) => {
      const p = Math.min(1, Math.max(0, (now - start) / duration));
      el.textContent = fmt(from + (to - from) * easeOut(p));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [to, from, delay, duration, instant, decimals]);

  return (
    <span ref={ref} className={className} aria-hidden="true">
      {fmt(instant ? to : from)}
    </span>
  );
}
