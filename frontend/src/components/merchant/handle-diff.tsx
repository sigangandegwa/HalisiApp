"use client";

import { diffChars } from "diff";
import { useMemo } from "react";

export function HandleDiff({ target, officials }: { target: string; officials: string[] }) {
  // Find closest official by length
  const official = useMemo(() => {
     if (!officials.length) return "";
     return officials.reduce((a, b) => Math.abs(a.length - target.length) < Math.abs(b.length - target.length) ? a : b);
  }, [target, officials]);

  const diff = useMemo(() => diffChars(official, target), [official, target]);

  return (
    <div className="type-data text-fg flex items-center flex-wrap" aria-label={`Handle: ${target}`}>
      @
      {diff.map((part, i) => {
        if (part.added) {
          // If it's just an added affix like _official, make it ink-3. Otherwise wavy vermilion.
          // For simplicity, any added part is highlighted. Let's say if it contains letters, it's wavy.
          return (
             <span key={i} className="text-[var(--color-feki)] decoration-wavy underline decoration-[var(--color-feki-ink)]">
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
