"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useMemo, useTransition, type ReactNode } from "react";
import { LOCALE_COOKIE, translator, type Locale, type Messages, type T } from "./index";

interface I18nValue {
  locale: Locale;
  t: T;
  setLocale: (locale: Locale) => void;
  pending: boolean;
}

const I18nContext = createContext<I18nValue | null>(null);

/**
 * Receives only the active dictionary from the server (keeps the bundle lean). Switching locale
 * writes the cookie and refreshes the server components, which re-render with the new strings.
 */
export function I18nProvider({ locale, messages, children }: { locale: Locale; messages: Messages; children: ReactNode }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const t = useMemo(() => translator(messages), [messages]);

  const setLocale = useCallback(
    (next: Locale) => {
      if (next === locale) return;
      document.cookie = `${LOCALE_COOKIE}=${next}; path=/; max-age=31536000; samesite=lax`;
      document.documentElement.lang = next;
      startTransition(() => router.refresh());
    },
    [locale, router],
  );

  const value = useMemo(() => ({ locale, t, setLocale, pending }), [locale, t, setLocale, pending]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used inside <I18nProvider>");
  return ctx;
}
