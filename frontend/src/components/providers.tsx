"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ApiError } from "@/lib/api";
import { I18nProvider } from "@/lib/i18n/provider";
import type { Locale, Messages } from "@/lib/i18n";

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: false,
        retry: (count, error) => !(error instanceof ApiError && error.status >= 400 && error.status < 500) && count < 1,
      },
      mutations: { retry: false },
    },
  });
}

/**
 * Lenis smooth scroll: desktop only (pointer: fine) and never under reduced motion
 * (FRONTEND.md sections 3 and 12). Loaded with import() so phones never download it.
 */
function useLenis() {
  useEffect(() => {
    const fine = window.matchMedia("(pointer: fine)").matches;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!fine || reduced) return;
    let raf = 0;
    let destroy: (() => void) | undefined;
    let cancelled = false;
    import("lenis").then(({ default: Lenis }) => {
      if (cancelled) return;
      const lenis = new Lenis({ duration: 1.05, easing: (t) => 1 - Math.pow(1 - t, 4), smoothWheel: true });
      (window as unknown as { __lenis?: unknown }).__lenis = lenis;
      const loop = (time: number) => {
        lenis.raf(time);
        raf = requestAnimationFrame(loop);
      };
      raf = requestAnimationFrame(loop);
      destroy = () => lenis.destroy();
    });
    return () => {
      cancelled = true;
      cancelAnimationFrame(raf);
      destroy?.();
    };
  }, []);
}

export function Providers({ locale, messages, children }: { locale: Locale; messages: Messages; children: ReactNode }) {
  const [client] = useState(makeQueryClient);
  useLenis();
  return (
    <QueryClientProvider client={client}>
      <I18nProvider locale={locale} messages={messages}>
        <TooltipProvider>{children}</TooltipProvider>
      </I18nProvider>
    </QueryClientProvider>
  );
}
