/**
 * Typed browser client (FRONTEND.md section 9.2). Every call goes through the Next.js proxy at
 * /api/halisi/* (which holds the API key) and every response is parsed with the contract schema.
 */
import type { z } from "zod";
import {
  AlertsResponse,
  ApiErrorBody,
  CheckResult,
  Health,
  MarkReadResponse,
  MerchantCreated,
  MerchantPublic,
  PaymentLookup,
  Playbooks,
  ReportCreated,
  Stats,
  ThreatDetail,
  ThreatSummary,
  type CheckRequest,
  type MerchantCreate,
  type ReportCreate,
  type SimulatorRequest,
  type ThreatStatus,
} from "@/lib/schemas";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public fixture = false,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// --- "Offline demo data" signal ---------------------------------------------------------------
// Any response served from fixtures flips this on; the OfflineChip subscribes to it.

let usingFixtures = false;
const listeners = new Set<() => void>();

export const demoData = {
  get: () => usingFixtures,
  getServer: () => false,
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  set(value: boolean) {
    if (value === usingFixtures) return;
    usingFixtures = value;
    listeners.forEach((l) => l());
  },
};

// --- core request -----------------------------------------------------------------------------

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH";
  json?: unknown;
  form?: FormData;
  search?: Record<string, string | number | boolean | null | undefined>;
  signal?: AbortSignal;
}

async function request<S extends z.ZodTypeAny>(path: string, schema: S, opts: RequestOptions = {}): Promise<z.output<S>> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(opts.search ?? {})) if (v !== null && v !== undefined && v !== "") qs.set(k, String(v));
  const url = `/api/halisi/${path}${qs.size ? `?${qs}` : ""}`;
  let res: Response;
  try {
    res = await fetch(url, {
      method: opts.method ?? (opts.json !== undefined || opts.form ? "POST" : "GET"),
      headers: opts.json !== undefined ? { "content-type": "application/json" } : undefined,
      body: opts.form ?? (opts.json !== undefined ? JSON.stringify(opts.json) : undefined),
      signal: opts.signal,
      credentials: "same-origin",
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") throw err;
    throw new ApiError(0, "NETWORK", "We couldn’t reach Halisi. Check your connection.");
  }
  const fixture = res.headers.get("x-halisi-fixture") === "1";
  demoData.set(fixture);
  const body: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const parsed = ApiErrorBody.safeParse(body);
    throw new ApiError(
      res.status,
      parsed.success ? parsed.data.error.code : `HTTP_${res.status}`,
      parsed.success ? (parsed.data.error.message ?? parsed.data.error.code) : res.statusText,
      fixture,
    );
  }
  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    console.error(`[halisi] ${path} does not match the API contract`, parsed.error.issues.slice(0, 5));
    throw new ApiError(500, "CONTRACT_MISMATCH", "Unexpected response from Halisi.", fixture);
  }
  return parsed.data;
}

// --- endpoints (BACKEND.md section 5) ---------------------------------------------------------

export const api = {
  health: () => request("health", Health),
  check: (input: CheckRequest, signal?: AbortSignal) => request("check", CheckResult, { json: input, signal }),
  getScan: (scanId: string) => request(`check/${encodeURIComponent(scanId)}`, CheckResult),
  verifyPayment: (value: string) => request("verify/payment", PaymentLookup, { search: { value } }),
  getMerchant: (slug: string) => request(`merchants/${encodeURIComponent(slug)}`, MerchantPublic),
  createMerchant: (data: MerchantCreate, logo: File) => {
    const form = new FormData();
    form.set("data", JSON.stringify(data));
    form.set("logo", logo);
    return request("merchants", MerchantCreated, { form });
  },
  listThreats: (merchantId: string, status?: ThreatStatus) =>
    request(`merchants/${encodeURIComponent(merchantId)}/threats`, ThreatSummary.array(), { search: { status } }),
  getThreat: (id: string) => request(`threats/${encodeURIComponent(id)}`, ThreatDetail),
  updateThreat: (id: string, status: ThreatStatus) =>
    request(`threats/${encodeURIComponent(id)}`, ThreatDetail, { method: "PATCH", json: { status } }),
  generatePlaybooks: (id: string, lang: "en" | "sw") =>
    request(`threats/${encodeURIComponent(id)}/playbooks`, Playbooks, { method: "POST", json: {}, search: { lang } }),
  createReport: (body: ReportCreate) => request("reports", ReportCreated, { json: body }),
  getStats: (merchantId?: string) => request("stats", Stats, { search: { merchant_id: merchantId } }),
  simulateClone: (body: SimulatorRequest) => request("simulator/clone", CheckResult, { json: body }),
  listAlerts: (merchantId: string, opts: { since?: string | null; unread?: boolean; limit?: number } = {}) =>
    request(`merchants/${encodeURIComponent(merchantId)}/alerts`, AlertsResponse, {
      search: { since: opts.since, unread: opts.unread ? "true" : undefined, limit: opts.limit },
    }),
  markAlertsRead: (merchantId: string, body: { ids: string[] } | { all: true }) =>
    request(`merchants/${encodeURIComponent(merchantId)}/alerts/read`, MarkReadResponse, { json: body }),
};

/** TanStack Query keys (FRONTEND.md section 9.2). */
export const qk = {
  scan: (id: string) => ["scan", id] as const,
  threats: (merchantId: string, status?: string) => ["threats", merchantId, status ?? "all"] as const,
  threat: (id: string) => ["threat", id] as const,
  stats: (merchantId?: string) => ["stats", merchantId ?? "global"] as const,
  merchant: (slug: string) => ["merchant", slug] as const,
  alerts: (merchantId: string) => ["alerts", merchantId] as const,
};
