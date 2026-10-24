"use client";

import { useI18n } from "@/lib/i18n/provider";
import { LOCALES } from "@/lib/i18n";
import { cn } from "@/lib/utils";

/** EN / SW: two words, the active one bright. The locale lives in a cookie; the server re-renders. */
export function LanguageToggle({ className }: { className?: string }) {
  const { locale, setLocale, t, pending } = useI18n();
  return (
    <div role="group" aria-label={t("lang.label")} className={cn("flex items-center font-mono text-[0.8125rem] tracking-[0.1em]", pending && "opacity-70", className)}>
      {LOCALES.map((l, i) => (
        <span key={l} className="flex items-center">
          {i > 0 ? <span aria-hidden="true" className="px-0.5 opacity-40">/</span> : null}
          <button
            type="button"
            lang={l}
            aria-pressed={locale === l}
            onClick={() => setLocale(l)}
            className={cn(
              "inline-flex h-11 min-w-9 cursor-pointer items-center justify-center uppercase transition-opacity duration-(--dur-ui) ease-quart",
              locale === l ? "opacity-100" : "opacity-45 hover:opacity-80",
            )}
          >
            {l}
          </button>
        </span>
      ))}
    </div>
  );
}
