import type { ThreatStatus } from "@/lib/schemas";

/** How a case's status reads to a merchant. Plain verbs: what has been done, not a pipeline state. */
export const STATUS_LABEL: Record<ThreatStatus, string> = {
  detected: "Detected",
  advisory_sent: "Customers warned",
  takedown_filed: "Report filed",
  resolved: "Resolved",
  false_positive: "False alarm",
};

/** The order a case normally moves through. `false_positive` is a side exit, not a step. */
export const STATUS_STEPS = ["detected", "advisory_sent", "takedown_filed", "resolved"] as const satisfies readonly ThreatStatus[];

export const OPEN_STATUSES: readonly ThreatStatus[] = ["detected", "advisory_sent", "takedown_filed"];

export function isOpen(status: ThreatStatus): boolean {
  return OPEN_STATUSES.includes(status);
}
