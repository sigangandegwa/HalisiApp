"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { CheckResult } from "@/lib/schemas";
import { ScanSequence } from "./scan-sequence";

/** Shared result: final state for returning visitors, with "Replay scan" (FRONTEND.md 6.2). */
export function ResultView({ result }: { result: CheckResult }) {
  const router = useRouter();
  const [run, setRun] = useState(0);
  return (
    <ScanSequence
      key={run}
      result={result}
      instant={run === 0}
      onReplay={() => setRun((n) => n + 1)}
      onAgain={() => router.push("/#hero-title")}
    />
  );
}
