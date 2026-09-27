"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n/provider";

/** Error boundary (FRONTEND.md section 6.9): honest, calm, with a way forward. */
export default function ErrorBoundary({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const { t } = useI18n();
  useEffect(() => {
    console.error(error);
  }, [error]);
  return (
    <main id="content" className="page-wrap grid min-h-[70dvh] content-center gap-6 py-20">
      <p className="type-caption text-fake">HITILAFU.</p>
      <h1 className="type-display-m max-w-[18ch]">{t("error.title")}</h1>
      <p className="max-w-[44ch] text-lede text-fg-2">{t("error.body")}</p>
      {error.digest ? <p className="font-mono text-[0.75rem] text-fg-3">ref {error.digest}</p> : null}
      <div>
        <Button size="lg" onClick={reset}>
          {t("error.retry")}
        </Button>
      </div>
    </main>
  );
}
