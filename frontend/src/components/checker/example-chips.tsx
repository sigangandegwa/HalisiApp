"use client";

import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n";
import { bezier } from "@/lib/motion";
import { cn } from "@/lib/utils";

export interface Example {
  key: MessageKey;
  handle: string;
  tone: "fake" | "real" | "ink" | "warn";
  /**
   * Manual-input example (BACKEND.md 7.2 tier 3): the row uploads this picture and bio instead of
   * fetching the page. The live engine scores it for real; offline, the same inputs were
   * precomputed by the engine (scripts/make_fixtures.py). Must match that script exactly.
   */
  manual?: { display_name: string; bio: string; avatar: string };
}

/** Demo examples (vital for judges). Clone pages are fictional; handles match the backend seed. */
export const EXAMPLES: Example[] = [
  { key: "chip.clone", handle: "nairobi_sneakervault_official_ke", tone: "fake" },
  { key: "chip.real", handle: "nairobisneakervault", tone: "real" },
  { key: "chip.competitor", handle: "nairobisneakerhub", tone: "ink" },
  { key: "chip.subtle", handle: "nairobisneakervau1t", tone: "fake" },
  {
    key: "chip.lookalike",
    handle: "sneakervault_resale_ke",
    tone: "warn",
    manual: {
      display_name: "Sneaker Vault Resale KE",
      bio: "Pre-owned and new kicks. Viewing by appointment in Nairobi.",
      avatar: "/fixtures/lookalike/sneakervault_resale_ke.png",
    },
  },
];

const dot: Record<Example["tone"], string> = {
  fake: "bg-feki",
  real: "bg-halisi",
  ink: "bg-haijulikani",
  warn: "bg-onyo",
};

/** One quiet link that opens a plain list. Collapsed by default so the first screen stays empty. */
export function ExampleChips({ onPick, disabled }: { onPick: (example: Example) => void; disabled?: boolean }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  return (
    <div>
      <button
        type="button"
        aria-expanded={open}
        aria-controls="example-list"
        disabled={disabled}
        onClick={() => setOpen((v) => !v)}
        className="inline-flex h-11 cursor-pointer items-center gap-2 pl-6 font-mono text-[0.8125rem] tracking-[0.08em] text-fg-3 uppercase underline decoration-line-strong decoration-1 underline-offset-[0.35em] transition-colors duration-(--dur-ui) ease-quart hover:text-fg disabled:opacity-40"
      >
        {t("checker.examples")}
      </button>
      <AnimatePresence initial={false}>
        {open ? (
          <motion.ul
            id="example-list"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.4, ease: bezier("out") }}
            className="overflow-hidden"
          >
            {EXAMPLES.map((ex) => (
              <li key={ex.handle} className="border-t border-line first:mt-2">
                <button
                  type="button"
                  disabled={disabled}
                  onClick={() => {
                    setOpen(false);
                    onPick(ex);
                  }}
                  className={cn(
                    "flex min-h-14 w-full cursor-pointer items-center gap-3 py-2 pl-6 text-left transition-colors duration-(--dur-ui) ease-quart hover:bg-bg-2",
                    "disabled:pointer-events-none disabled:opacity-40",
                  )}
                >
                  <span aria-hidden="true" className={cn("size-2 shrink-0 rounded-full", dot[ex.tone])} />
                  <span className="grid min-w-0">
                    <span className="text-[0.8125rem] text-fg-3">{t(ex.key)}</span>
                    <span className="truncate font-mono text-[0.9375rem]">@{ex.handle}</span>
                  </span>
                </button>
              </li>
            ))}
          </motion.ul>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
