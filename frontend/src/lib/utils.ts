import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

const customTwMerge = extendTailwindMerge({
  extend: {
    classGroups: {
      "font-size": [
        {
          text: [
            "display-xl",
            "display-l",
            "display-m",
            "heading",
            "lede",
            "body",
            "small",
            "caption",
            "micro",
          ],
        },
      ],
      "text-color": [
        {
          text: [
            "bg",
            "bg-2",
            "bg-3",
            "fg",
            "fg-2",
            "fg-3",
            "line",
            "line-strong",
            "real",
            "fake",
            "warn",
            "focus",
            "paper",
            "paper-2",
            "paper-3",
            "ink",
            "ink-2",
            "ink-3",
            "halisi",
            "halisi-glow",
            "feki",
            "feki-ink",
            "caution",
            "caution-ink",
            "night",
            "night-2",
            "night-3",
          ],
        },
      ],
      rounded: [{ rounded: ["doc", "pill"] }],
    },
  },
});

/** Merge class names, resolving Tailwind conflicts (last one wins). */
export function cn(...inputs: ClassValue[]): string {
  return customTwMerge(clsx(inputs));
}
