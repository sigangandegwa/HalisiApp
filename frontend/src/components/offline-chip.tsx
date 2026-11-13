"use client";

import { useEffect } from "react";
import { demoData } from "@/lib/api";

/**
 * Server pages that rendered fixtures mount this so the client store knows the data is recorded.
 * The on-screen "Offline demo data" chip was removed on 2026-11-13 at the lead's request; the flag
 * is kept so the indicator can be brought back without touching the pages.
 */
export function MarkFixture({ on }: { on: boolean }) {
  useEffect(() => {
    if (on) demoData.set(true);
  }, [on]);
  return null;
}
