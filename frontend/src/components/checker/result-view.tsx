"use client";

import { useRouter } from "next/navigation";
import type { CheckResult } from "@/lib/schemas";
import { ResultCase } from "./result-case";

/** A shared result: the final state, straight away. */
export function ResultView({ result }: { result: CheckResult }) {
  const router = useRouter();
  return <ResultCase result={result} instant onAgain={() => router.push("/")} />;
}
