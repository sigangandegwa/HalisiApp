"use client";

import { useEffect, useSyncExternalStore } from "react";
import { demoData } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";

/**
 * "Offline demo data" chip (FRONTEND.md section 6.9): shown whenever the last API answer came
 * from fixtures. Honest on stage: small, fixed, never hidden.
 */
export function OfflineChip() {
  const on = useSyncExternalStore(demoData.subscribe, demoData.get, demoData.getServer);
  const { t } = useI18n();
  if (!on) return null;
  return (
    <div
      role="status"
      title={t("offline.title")}
      className="fixed bottom-4 left-4 z-40 inline-flex items-center gap-2 rounded-pill border border-line-strong bg-bg-2 px-3 py-1.5 font-mono text-[0.6875rem] tracking-[0.06em] text-fg-2 uppercase shadow-[0_0_0_4px_var(--bg)]"
      style={{ animation: "halisi-fade 320ms var(--ease-quart) both" }}
    >
      <span className="size-1.5 rounded-full bg-caution" aria-hidden="true" />
      {t("offline.chip")}
    </div>
  );
}

/** Server pages that rendered fixtures mount this so the chip appears without a client fetch. */
export function MarkFixture({ on }: { on: boolean }) {
  useEffect(() => {
    if (on) demoData.set(true);
  }, [on]);
  return null;
}
