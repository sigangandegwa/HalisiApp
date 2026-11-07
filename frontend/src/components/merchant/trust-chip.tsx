import { cn } from "@/lib/utils";
import type { VerificationStatus } from "@/lib/schemas";

const LABEL: Record<VerificationStatus, string> = {
  curated: "Curated by Halisi",
  verified: "Verified owner",
  claimed: "Not verified yet",
};

/**
 * Trust tier as a plain label. Colour is reserved for verdicts, so the tier is carried by the border
 * (solid = Halisi stands behind this brand, dashed = it does not yet) and by words.
 */
export function TrustChip({ status, className }: { status: VerificationStatus; className?: string }) {
  const proven = status !== "claimed";
  return (
    <span
      className={cn(
        "type-caption inline-flex items-center gap-2 border px-2.5 py-1 text-fg-2",
        proven ? "border-line-strong" : "border-dashed border-line-strong",
        className,
      )}
    >
      <span aria-hidden="true" className={cn("size-1.5 rounded-full", proven ? "bg-fg" : "border border-fg-3")} />
      {LABEL[status]}
    </span>
  );
}
