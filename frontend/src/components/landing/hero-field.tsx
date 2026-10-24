"use client";

import { useReducedMotion } from "motion/react";
import { useEffect, useRef } from "react";

/**
 * An ambient field of 64-bit "fingerprint" cells behind the hero: tiny squares that flicker like
 * the bits of a perceptual hash, with a slow wave through them and a bright ripple that follows the
 * pointer. Pure canvas 2D, capped at 30 fps and 1.5x pixel ratio, paused when off-screen or when the
 * tab is hidden. Under reduced motion it paints one still frame. It carries no information.
 */
export function HeroField({ className }: { className?: string }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const reduced = useReducedMotion() ?? false;

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    const coarse = window.matchMedia("(pointer: coarse)").matches;
    const style = getComputedStyle(document.documentElement);
    const rgb = "241,238,230"; // bone
    void style;

    let w = 0;
    let h = 0;
    let cols = 0;
    let rows = 0;
    let bits: Uint8Array = new Uint8Array(0);
    const cell = coarse ? 26 : 22;
    const pointer = { x: -9999, y: -9999, active: false };
    let raf = 0;
    let last = 0;
    let visible = true;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      w = rect.width;
      h = rect.height;
      canvas.width = Math.max(1, Math.floor(w * dpr));
      canvas.height = Math.max(1, Math.floor(h * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cols = Math.ceil(w / cell);
      rows = Math.ceil(h / cell);
      bits = new Uint8Array(cols * rows);
      for (let i = 0; i < bits.length; i++) bits[i] = Math.random() < 0.5 ? 1 : 0;
      draw(0);
    };

    const draw = (t: number) => {
      ctx.clearRect(0, 0, w, h);
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const i = r * cols + c;
          const x = c * cell + cell / 2;
          const y = r * cell + cell / 2;
          const wave = 0.5 + 0.5 * Math.sin(c * 0.22 + r * 0.14 - t * 0.0008);
          let alpha = (bits[i] ? 0.1 : 0.035) + wave * 0.05;
          let size = bits[i] ? 3 : 2;
          if (pointer.active) {
            const dx = x - pointer.x;
            const dy = y - pointer.y;
            const d = Math.hypot(dx, dy);
            if (d < 150) {
              const k = 1 - d / 150;
              alpha += k * 0.55;
              size += k * 3;
            }
          }
          ctx.fillStyle = `rgba(${rgb},${Math.min(alpha, 0.7)})`;
          ctx.fillRect(x - size / 2, y - size / 2, size, size);
        }
      }
    };

    const tick = (now: number) => {
      raf = requestAnimationFrame(tick);
      if (!visible || document.hidden || now - last < 33) return;
      last = now;
      // a few bits flip every frame, like a hash being recomputed
      for (let n = 0; n < 6; n++) {
        const i = (Math.random() * bits.length) | 0;
        bits[i] = bits[i] ? 0 : 1;
      }
      draw(now);
    };

    const onMove = (e: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      pointer.x = e.clientX - rect.left;
      pointer.y = e.clientY - rect.top;
      pointer.active = true;
    };
    const onLeave = () => (pointer.active = false);

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);
    const io = new IntersectionObserver(([e]) => (visible = Boolean(e?.isIntersecting)));
    io.observe(canvas);
    if (!reduced) {
      raf = requestAnimationFrame(tick);
      if (!coarse) {
        window.addEventListener("pointermove", onMove, { passive: true });
        document.addEventListener("pointerleave", onLeave);
      }
    }
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      io.disconnect();
      window.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerleave", onLeave);
    };
  }, [reduced]);

  return <canvas ref={ref} aria-hidden="true" className={className} />;
}
