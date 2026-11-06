import type { ReactNode } from "react";

/**
 * One figure in the console's instrument strip. No box: a hairline between figures does the
 * separating, so the row reads like a flight-data bar rather than four cards. Figures must come
 * from the API (PRODUCT_V2 section 8): never a hard-coded number.
 */
export function KpiTile({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="grid content-start gap-1.5 border-l border-line py-4 pl-5 first:border-l-0 first:pl-0 max-sm:odd:border-l-0 max-sm:odd:pl-0">
      <dt className="type-caption text-fg-3">{label}</dt>
      <dd className="type-data text-[clamp(1.5rem,2.6vw,2.25rem)] leading-none text-fg">{value}</dd>
      {hint ? <p className="text-[0.8125rem] text-fg-3">{hint}</p> : null}
    </div>
  );
}
