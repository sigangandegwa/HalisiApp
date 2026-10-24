"use client";

import { motion, useReducedMotion } from "motion/react";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n";
import { bezier } from "@/lib/motion";
import { cn } from "@/lib/utils";

/**
 * The boot console shown while the engine works: a terminal that lists what Halisi is doing.
 * The lines are time-paced, not tied to backend phases, so they describe activity and never
 * show a percentage or pretend to measure progress. Under reduced motion it is just a static list.
 */
export function ScanConsole({
  target,
  steps,
  active,
  className,
}: {
  target: string;
  steps: readonly MessageKey[];
  /** Index of the line currently running; earlier lines are done, later ones haven't started. */
  active: number;
  className?: string;
}) {
  const { t } = useI18n();
  const reduced = useReducedMotion() ?? false;
  const ease = bezier("out");

  return (
    <motion.div
      role="status"
      aria-live="polite"
      initial={reduced ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease }}
      className={cn("corner-marks border border-line bg-bg-2/70 p-4 font-mono text-[0.8125rem] leading-relaxed sm:p-5", className)}
    >
      <p className="flex items-center justify-between text-fg-3">
        <span className="tracking-[0.1em] uppercase">{t("console.engine")}</span>
        <span aria-hidden="true" className="size-1.5 rounded-full bg-fg animate-pulse" />
      </p>
      <p className="mt-3 truncate">
        <span className="text-fg-3">{t("console.target")}</span> <span className="text-fg">{target}</span>
      </p>
      <ul className="mt-2 grid gap-1">
        {steps.map((key, i) => {
          if (i > active) return null;
          const running = i === active;
          return (
            <motion.li
              key={key}
              initial={reduced ? false : { opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.35, ease }}
              className={cn("flex items-baseline gap-2", running ? "text-fg" : "text-fg-3")}
            >
              <span aria-hidden="true" className="w-3 shrink-0">
                {running ? ">" : "·"}
              </span>
              <span>{t(key)}</span>
              {running ? <span aria-hidden="true" className="caret" /> : null}
            </motion.li>
          );
        })}
      </ul>
    </motion.div>
  );
}
