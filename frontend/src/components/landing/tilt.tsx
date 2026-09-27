"use client";

import { useRef, type ReactNode } from "react";

/**
 * Pointer tilt (+/-4 deg, desktop fine pointers only, off under reduced motion). Writes the
 * transform directly; no React state per frame.
 */
export function Tilt({ children, max = 4, className }: { children: ReactNode; max?: number; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const frame = useRef(0);

  const onMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.pointerType !== "mouse") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5;
    const y = (e.clientY - r.top) / r.height - 0.5;
    cancelAnimationFrame(frame.current);
    frame.current = requestAnimationFrame(() => {
      el.style.transform = `perspective(1400px) rotateX(${(-y * max * 2).toFixed(2)}deg) rotateY(${(x * max * 2).toFixed(2)}deg)`;
    });
  };
  const reset = () => {
    cancelAnimationFrame(frame.current);
    if (ref.current) ref.current.style.transform = "";
  };

  return (
    <div
      ref={ref}
      onPointerMove={onMove}
      onPointerLeave={reset}
      className={className}
      style={{ transition: "transform 600ms var(--ease-out)", transformStyle: "preserve-3d", willChange: "transform" }}
    >
      {children}
    </div>
  );
}
