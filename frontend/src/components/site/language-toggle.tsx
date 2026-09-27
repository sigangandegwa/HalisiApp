"use client";

import { useI18n } from "@/lib/i18n/provider";
import { LOCALES } from "@/lib/i18n";
import { cn } from "@/lib/utils";

/** EN | SW toggle (FRONTEND.md section 10). The locale lives in a cookie; the server re-renders. */
export function LanguageToggle({ className }: { className?: string }) {
  const { locale, setLocale, t, pending } = useI18n();
  return (
    <div role="group" aria-label={t("lang.label")} className={cn("inline-flex items-center rounded-pill border border-line-strong p-0.5", pending && "opacity-70", className)}>
      {LOCALES.map((l) => (
        <button
          key={l}
          type="button"
          lang={l}
          aria-pressed={locale === l}
          onClick={() => setLocale(l)}
          className={cn(
            "h-8 min-w-10 cursor-pointer rounded-pill px-2.5 font-mono text-[0.75rem] font-medium tracking-[0.08em] uppercase transition-colors duration-(--dur-ui) ease-quart pointer-coarse:h-10",
            locale === l ? "bg-fg text-bg" : "text-fg-2 hover:text-fg",
          )}
        >
          {l === "en" ? "EN" : "SW"}
        </button>
      ))}
    </div>
  );
}
