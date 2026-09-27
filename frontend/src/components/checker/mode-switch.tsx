"use client";

import Link from "next/link";
import { useI18n } from "@/lib/i18n/provider";
import { cn } from "@/lib/utils";

/** `Link | Till / Phone` above the checker: two modes of the same tool, each with its own URL. */
export function ModeSwitch({ mode }: { mode: "link" | "pay" }) {
  const { t } = useI18n();
  const item = (active: boolean) =>
    cn(
      "relative inline-flex h-9 items-center rounded-pill px-4 text-[0.875rem] font-medium transition-colors duration-(--dur-ui) ease-quart pointer-coarse:h-10",
      active ? "bg-fg text-bg" : "text-fg-2 hover:text-fg",
    );
  return (
    <nav aria-label={t("checker.label")} className="inline-flex rounded-pill border border-line-strong p-1">
      <Link href="/" aria-current={mode === "link" ? "page" : undefined} className={item(mode === "link")}>
        {t("checker.tab.link")}
      </Link>
      <Link href="/pay" aria-current={mode === "pay" ? "page" : undefined} className={item(mode === "pay")}>
        {t("checker.tab.pay")}
      </Link>
    </nav>
  );
}
