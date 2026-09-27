"use client";

import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useCallback, useEffect, useRef, useState } from "react";
import { bezier } from "@/lib/motion";

/**
 * The hero word (FRONTEND.md section 6.1): *halisi* first renders misregistered as "ha1isi", the
 * counterfeit. After 900 ms the colour plates snap into register and the 1 becomes an l.
 * Typosquatting, demonstrated in one word. Replays on hover (fine pointers only); never loops.
 * The visual word is aria-hidden; screen readers get the real word.
 */
export function HeroWord({ word = "halisi" }: { word?: string }) {
  const reduced = useReducedMotion();
  const [registered, setRegistered] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  const idx = word.indexOf("l");

  const settle = useCallback((delay: number) => {
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setRegistered(true), delay);
  }, []);

  useEffect(() => {
    if (reduced) return;
    settle(900);
    return () => window.clearTimeout(timer.current);
  }, [reduced, settle]);

  const replay = () => {
    if (reduced || !window.matchMedia("(pointer: fine)").matches || !registered) return;
    setRegistered(false);
    settle(900);
  };

  if (idx < 0) return <span>{word}</span>;
  const before = word.slice(0, idx);
  const after = word.slice(idx + 1);
  const inRegister = registered || Boolean(reduced);
  const offset = inRegister ? 0 : 1;

  const layer = (cls: string, dx: number, dy: number, opacity: number, key: string) => (
    <motion.span
      key={key}
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 select-none ${cls}`}
      initial={false}
      animate={{ x: `${dx * offset}em`, y: `${dy * offset}em`, opacity: offset ? opacity : 0 }}
      transition={{ duration: 0.42, ease: bezier("out") }}
    >
      <Glyphs before={before} after={after} registered={inRegister} />
    </motion.span>
  );

  return (
    <span className="relative inline-block" onPointerEnter={replay}>
      <span className="sr-only">{word}</span>
      {layer("text-feki", -0.016, 0.008, 0.55, "plate-r")}
      {layer("text-halisi", 0.016, -0.008, 0.45, "plate-g")}
      <span aria-hidden="true" className="relative">
        <Glyphs before={before} after={after} registered={inRegister} />
      </span>
    </span>
  );
}

function Glyphs({ before, after, registered }: { before: string; after: string; registered: boolean }) {
  const t = { duration: 0.42, ease: bezier("out") };
  return (
    <span className="inline-flex items-baseline">
      <span>{before}</span>
      <span className="relative inline-flex">
        <AnimatePresence initial={false} mode="popLayout">
          <motion.span
            key={registered ? "l" : "1"}
            className="inline-block"
            initial={{ y: "-0.28em", opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: "0.22em", opacity: 0 }}
            transition={t}
          >
            {registered ? "l" : "1"}
          </motion.span>
        </AnimatePresence>
      </span>
      <motion.span layout="position" transition={t} className="inline-block">
        {after}
      </motion.span>
    </span>
  );
}
