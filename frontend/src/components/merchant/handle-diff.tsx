"use client";

import { diffChars } from "diff";
import { useMemo } from "react";
import { cn } from "@/lib/utils";

/**
 * The look-alike handle with every character that differs from the closest official one marked
 * in signal red with a wavy underline: the "spot the difference" moment in one line.
 */
export function HandleDiff({ target, officials, className }: { target: string; officials: string[]; className?: string }) {
  // The closest official by length is the one the clone was most likely derived from.
  const official = useMemo(() => {
    if (!officials.length) return "";
    return officials.reduce((a, b) => (Math.abs(a.length - target.length) < Math.abs(b.length - target.length) ? a : b));
  }, [target, officials]);

  const diff = useMemo(() => diffChars(official, target), [official, target]);

  return (
    <div className={cn("type-data flex flex-wrap items-center break-all text-fg", className)} aria-label={`Handle: ${target}`}>
      <span aria-hidden="true" className="text-fg-3">@</span>
      {diff.map((part, i) => {
        if (part.added) {
          return (
            <span key={i} className="text-fake underline decoration-feki decoration-wavy underline-offset-[0.28em]">
              {part.value}
            </span>
          );
        }
        if (part.removed) return null;
        return <span key={i}>{part.value}</span>;
      })}
    </div>
  );
}
