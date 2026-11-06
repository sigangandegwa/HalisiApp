import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * A numbered chapter of a case file: "02 / Evidence" over a hairline rule. The number is the
 * navigation: merchants talk about "section 3" of a case the way lawyers do.
 */
export function FileSection({
  n,
  title,
  aside,
  children,
  className,
  id,
}: {
  n: number;
  title: string;
  aside?: ReactNode;
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} aria-labelledby={id ? `${id}-h` : undefined} className={cn("grid gap-6", className)}>
      <header className="flex items-end justify-between gap-4 border-b border-line-strong pb-3">
        <h2 id={id ? `${id}-h` : undefined} className="flex items-baseline gap-3">
          <span className="type-caption text-fg-3 tabular-nums">{String(n).padStart(2, "0")}</span>
          <span className="font-display text-[clamp(1.5rem,3vw,2.25rem)] leading-none font-extrabold tracking-[-0.004em] uppercase">{title}</span>
        </h2>
        {aside ? <div className="type-caption text-fg-3">{aside}</div> : null}
      </header>
      {children}
    </section>
  );
}
