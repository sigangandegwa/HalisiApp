"use client";

import { Stamp, type StampSize } from "@/components/brand/stamp";
import { useI18n } from "@/lib/i18n/provider";
import type { Verdict } from "@/lib/schemas";
import { VERDICTS } from "@/lib/verdict";

/**
 * Verdict stamp (FRONTEND.md section 7): HALISI. / FEKI. / TAHADHARI. / HAIJULIKANI. with the
 * English (or Swahili) subline. FEKI is misregistered, like a badly printed counterfeit.
 */
export function VerdictStamp({
  verdict,
  size = "xl",
  className,
  rotate,
}: {
  verdict: Verdict;
  size?: StampSize;
  className?: string;
  rotate?: number;
}) {
  const { t } = useI18n();
  const meta = VERDICTS[verdict];
  return (
    <Stamp
      word={t(meta.word)}
      sub={t(meta.sub)}
      color={meta.stampColor}
      size={size}
      misregister={verdict === "impersonation"}
      className={className}
      rotate={rotate}
    />
  );
}
