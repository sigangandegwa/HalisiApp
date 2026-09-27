"use client";

import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export interface Example {
  key: MessageKey;
  handle: string;
  tone: "fake" | "real" | "ink" | "warn";
  /**
   * Manual-input example (BACKEND.md 7.2 tier 3): the chip uploads this picture and bio instead of
   * fetching the page. The live engine scores it for real; offline, the same inputs were
   * precomputed by the engine (scripts/make_fixtures.py). Must match that script exactly.
   */
  manual?: { display_name: string; bio: string; avatar: string };
}

/** Demo examples (vital for judges). All fictional businesses; handles match the backend seed. */
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

const dot: Record<(typeof EXAMPLES)[number]["tone"], string> = {
  fake: "bg-feki",
  real: "bg-real",
  ink: "bg-fg-3",
  warn: "bg-caution",
};

export function ExampleChips({ onPick, disabled }: { onPick: (example: Example) => void; disabled?: boolean }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-baseline sm:gap-4">
      <p id="examples-label" className="type-caption shrink-0 text-fg-3">
        {t("checker.examples")}
      </p>
      <ul aria-labelledby="examples-label" className="no-scrollbar -mx-[var(--gutter)] flex snap-x gap-2 overflow-x-auto px-[var(--gutter)] pb-1 sm:mx-0 sm:flex-wrap sm:overflow-visible sm:px-0">
        {EXAMPLES.map((ex) => (
          <li key={ex.handle} className="snap-start">
            <button
              type="button"
              disabled={disabled}
              onClick={() => onPick(ex)}
              className={cn(
                "group inline-flex h-11 cursor-pointer items-center gap-2 rounded-pill border border-line-strong bg-transparent px-4 whitespace-nowrap",
                "transition-[background-color,border-color] duration-(--dur-ui) ease-quart hover:border-fg hover:bg-bg-2 disabled:pointer-events-none disabled:opacity-50",
              )}
            >
              <span aria-hidden="true" className={cn("size-1.5 rounded-full", dot[ex.tone])} />
              <span className="text-[0.8125rem] font-medium text-fg-2 group-hover:text-fg">{t(ex.key)}</span>
              <span className="font-mono text-[0.8125rem] text-fg">@{ex.handle}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
