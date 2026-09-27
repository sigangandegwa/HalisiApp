/**
 * Offline demo backend (server-only). When the real API is unreachable and DEMO_FALLBACK is on,
 * the proxy asks this module for the fixture that matches the request (FRONTEND.md section 9.1).
 *
 * Honesty rules:
 *  - Only precomputed engine results are ever returned. Unknown pages get 502 TARGET_UNREACHABLE
 *    (the manual fallback), manual submissions and onboarding get 503 ENGINE_OFFLINE. Nothing is
 *    scored on the fly, and every response carries `x-halisi-fixture: 1` so the UI shows the chip.
 *  - Mutations (status changes, mark-read, simulator threats) live in process memory only, so a
 *    rehearsal on `next start` behaves like the live system until the server restarts.
 */
import { randomUUID } from "node:crypto";
import {
  CheckRequest,
  MarkRead,
  ReportCreate,
  SimulatorRequest,
  ThreatUpdate,
  type Alert,
  type CheckResult,
  type PaymentLookup,
  type Stats,
  type ThreatStatus,
  type ThreatSummary,
} from "@/lib/schemas";
import { canonicalPhone, canonicalTill, looksLikePayment, maskPhone, parseTarget } from "@/lib/format";
import { fixtures, simulatorFixtures, type FixtureAlert, type FixtureThreat } from "./index";

export interface FixtureResponse {
  status: number;
  body: unknown;
}

interface DemoStore {
  status: Map<string, { status: ThreatStatus; history: { status: ThreatStatus; at: string }[] }>;
  readAt: Map<string, string>;
  extraThreats: Map<string, FixtureThreat>;
  extraAlerts: FixtureAlert[];
  extraScans: Map<string, CheckResult>;
  playbookLog: Map<string, Record<string, unknown>[]>;
}

const globalStore = globalThis as unknown as { __halisiDemoStore?: DemoStore };
const store: DemoStore = (globalStore.__halisiDemoStore ??= {
  status: new Map(),
  readAt: new Map(),
  extraThreats: new Map(),
  extraAlerts: [],
  extraScans: new Map(),
  playbookLog: new Map(),
});

/** Handles whose manual-input result was precomputed by the real engine (scripts/make_fixtures.py). */
const MANUAL_DEMO_HANDLES = new Set(["sneakervault_resale_ke"]);

const err = (status: number, code: string, message: string): FixtureResponse => ({
  status,
  body: { error: { code, message } },
});

const nowIso = () => new Date().toISOString().replace(/\.\d{3}Z$/, "Z");

// --- state views ------------------------------------------------------------------------------

function allThreats(): FixtureThreat[] {
  const base = fixtures().threats.filter((t) => !store.extraThreats.has(t.id));
  return [...base, ...store.extraThreats.values()].map((t) => {
    const override = store.status.get(t.id);
    const playbooks = store.playbookLog.get(t.id) ?? [];
    return override
      ? { ...t, status: override.status, status_history: [...t.status_history, ...override.history.map((h) => ({ ...h, note: null }))], playbooks_generated: [...t.playbooks_generated, ...playbooks] }
      : { ...t, playbooks_generated: [...t.playbooks_generated, ...playbooks] };
  });
}

function summary(t: FixtureThreat): ThreatSummary {
  return {
    id: t.id,
    platform: t.target.platform ?? "instagram",
    target_handle: t.target.handle ?? "",
    target_url: t.target.url ?? "",
    avatar_url: t.target.avatar_url,
    composite_score: t.score,
    verdict: t.verdict,
    status: t.status,
    first_seen_at: t.first_seen_at,
    top_reason: t.reasons[0] ?? null,
  };
}

function allAlerts(): FixtureAlert[] {
  const threats = new Map(allThreats().map((t) => [t.id, t]));
  return [...fixtures().alerts, ...store.extraAlerts].map((a) => {
    const t = threats.get(a.threat_id);
    return { ...a, read_at: store.readAt.get(a.id) ?? a.read_at, threat: t ? summary(t) : a.threat };
  });
}

/** Strip the fixture-only merchant_id so responses match BACKEND.md section 8.2 exactly. */
function publicAlert(alert: FixtureAlert): Alert {
  const copy: Partial<FixtureAlert> = { ...alert };
  delete copy.merchant_id;
  return copy as Alert;
}

function findScan(id: string): CheckResult | undefined {
  return fixtures().checks.find((c) => c.scan_id === id) ?? store.extraScans.get(id);
}

function paymentLookup(value: string): PaymentLookup | null {
  const phone = canonicalPhone(value);
  const till = phone ? null : canonicalTill(value);
  const normalized = phone ?? till;
  if (!normalized) return null;
  const known = fixtures().payments.find((p) => p.normalized === normalized);
  if (known) return known;
  return {
    kind: phone ? "phone" : "till",
    normalized,
    display: phone ? maskPhone(phone) : normalized,
    status: "unknown",
    merchant: null,
    report_count: 0,
    linked_threats: 0,
  };
}

function merchantStats(merchantId: string): Stats | null {
  const base = fixtures().stats.merchants[merchantId];
  if (!base) return null;
  const threats = allThreats().filter((t) => t.merchant_id === merchantId);
  return {
    ...base,
    threats_detected: threats.length,
    active_threats: threats.filter((t) => t.status !== "resolved" && t.status !== "false_positive").length,
    resolved: threats.filter((t) => t.status === "resolved").length,
  };
}

// --- router -----------------------------------------------------------------------------------

/**
 * Resolve a proxied request to a fixture response. `segments` are the path parts after
 * `/api/halisi/`; the caller has already applied the allowlist and the session check.
 */
export function resolveFixture(
  method: string,
  segments: readonly string[],
  search: URLSearchParams,
  body: unknown,
): FixtureResponse {
  const m = method.toUpperCase();
  const [a, b, c, d] = segments;

  if (a === "health") {
    return { status: 200, body: { status: "offline", version: "fixtures", demo_mode: true, engine: { hash: "fixtures" }, llm: "templates", db: "memory" } };
  }

  if (a === "check" && m === "POST") {
    const parsed = CheckRequest.safeParse(body);
    if (!parsed.success) return err(422, "INVALID_INPUT", "Send a link or a handle.");
    const req = parsed.data;
    const raw = (req.url ?? req.handle ?? "").trim();
    if (looksLikePayment(raw) || /wa\.me\//i.test(raw)) {
      return err(422, "PAYMENT_INPUT", "That's a phone number or till: check it on the payment page.");
    }
    const target = req.url ? parseTarget(req.url) : req.handle ? parseTarget(req.handle) : null;
    if (!target) return err(422, "UNSUPPORTED_PLATFORM", "Paste an Instagram, Facebook, TikTok or X link, or a @handle.");
    const hit = [...fixtures().checks].find((r) => r.target.handle?.toLowerCase() === target.handle);
    if (hit && !req.manual) return { status: 200, body: hit };
    // A precomputed manual-input result (the look-alike demo): same handle and a picture uploaded.
    if (hit && req.manual?.avatar_base64 && MANUAL_DEMO_HANDLES.has(target.handle)) return { status: 200, body: hit };
    if (req.manual) {
      return err(503, "ENGINE_OFFLINE", "The detection engine is offline, so manual checks can't run right now. The demo examples still work.");
    }
    return err(502, "TARGET_UNREACHABLE", "We couldn't open that page. The engine is offline, so only the demo examples can be checked right now.");
  }

  if (a === "check" && b && m === "GET") {
    const scan = findScan(b);
    return scan ? { status: 200, body: scan } : err(404, "NOT_FOUND", "We couldn't find that result.");
  }

  if (a === "verify" && b === "payment") {
    const lookup = paymentLookup(search.get("value") ?? "");
    return lookup ? { status: 200, body: lookup } : err(422, "INVALID_INPUT", "Enter a Kenyan phone number or a 5 to 7 digit till.");
  }

  if (a === "merchants" && !b && m === "POST") {
    // multipart onboarding can't be scored offline
    return err(503, "ENGINE_OFFLINE", "Onboarding needs the live Halisi engine to fingerprint your logo.");
  }

  if (a === "merchants" && b && !c && m === "GET") {
    const merchant = fixtures().merchants.find((x) => x.slug === b || x.id === b);
    return merchant ? { status: 200, body: merchant } : err(404, "NOT_FOUND", "No verified business with that name.");
  }

  if (a === "merchants" && b && c === "threats") {
    const status = search.get("status");
    const list = allThreats()
      .filter((t) => t.merchant_id === b && (!status || t.status === status))
      .map(summary)
      .sort((x, y) => y.composite_score - x.composite_score);
    return { status: 200, body: list };
  }

  if (a === "merchants" && b && c === "alerts" && !d) {
    const since = search.get("since");
    const unread = search.get("unread") === "true";
    const limit = Math.min(100, Math.max(1, Number(search.get("limit") ?? 20) || 20));
    const mine = allAlerts().filter((x) => x.merchant_id === b);
    const list = mine
      .filter((x) => (!since || x.created_at > since) && (!unread || !x.read_at))
      .sort((x, y) => y.created_at.localeCompare(x.created_at))
      .slice(0, limit)
      .map(publicAlert);
    return {
      status: 200,
      body: { alerts: list, unread_count: mine.filter((x) => !x.read_at).length, server_time: nowIso() },
    };
  }

  if (a === "merchants" && b && c === "alerts" && d === "read") {
    const parsed = MarkRead.safeParse(body);
    if (!parsed.success) return err(422, "INVALID_INPUT", "Send { ids } or { all: true }.");
    const at = nowIso();
    const mine = allAlerts().filter((x) => x.merchant_id === b);
    const ids = "all" in parsed.data ? mine.map((x) => x.id) : parsed.data.ids;
    for (const id of ids) if (mine.some((x) => x.id === id && !x.read_at)) store.readAt.set(id, at);
    return { status: 200, body: { unread_count: allAlerts().filter((x) => x.merchant_id === b && !x.read_at).length } };
  }

  if (a === "threats" && b && !c) {
    const threat = allThreats().find((t) => t.id === b);
    if (!threat) return err(404, "NOT_FOUND", "Threat not found.");
    if (m === "GET") return { status: 200, body: threat };
    const parsed = ThreatUpdate.safeParse(body);
    if (!parsed.success) return err(422, "INVALID_INPUT", "Unknown status.");
    const prev = store.status.get(b);
    store.status.set(b, {
      status: parsed.data.status,
      history: [...(prev?.history ?? []), { status: parsed.data.status, at: nowIso() }],
    });
    return { status: 200, body: allThreats().find((t) => t.id === b) };
  }

  if (a === "threats" && b && c === "playbooks") {
    const lang = search.get("lang") === "sw" ? "sw" : "en";
    const books = fixtures().playbooks[b]?.[lang];
    if (!books) return err(503, "ENGINE_OFFLINE", "Playbooks for this threat need the live engine.");
    const log = store.playbookLog.get(b) ?? [];
    log.push({ generator: books.generator, language: lang, created_at: nowIso() });
    store.playbookLog.set(b, log);
    return { status: 200, body: books };
  }

  if (a === "stats") {
    const merchantId = search.get("merchant_id");
    if (merchantId) {
      const s = merchantStats(merchantId);
      return s ? { status: 200, body: s } : err(404, "NOT_FOUND", "Unknown merchant.");
    }
    return { status: 200, body: fixtures().stats.global };
  }

  if (a === "reports" && m === "POST") {
    const parsed = ReportCreate.safeParse(body);
    if (!parsed.success) return err(422, "INVALID_INPUT", "Add a link, handle, phone number or till.");
    return { status: 201, body: { id: randomUUID(), status: "pending" } };
  }

  if (a === "simulator" && b === "clone") {
    const parsed = SimulatorRequest.safeParse(body);
    if (!parsed.success) return err(422, "INVALID_INPUT", "Invalid simulator tweaks.");
    const { merchant_id, tweaks } = parsed.data;
    const slug = fixtures().merchants.find((x) => x.id === merchant_id)?.slug;
    if (!slug) return err(404, "NOT_FOUND", "Unknown merchant.");
    const key = `${slug}|${tweaks.handle_style}|${tweaks.logo}|${tweaks.payment}|${tweaks.bio_tokens ? 1 : 0}`;
    const result = simulatorFixtures()[key];
    if (!result) return err(503, "ENGINE_OFFLINE", "That merchant isn't in the offline demo set.");
    recordSimulatedThreat(merchant_id, result);
    return { status: 200, body: result };
  }

  return err(404, "NOT_FOUND", "Not found.");
}

/** Persist a simulator result like the backend does (scan + threat + alert), in memory. */
function recordSimulatedThreat(merchantId: string, result: CheckResult): void {
  store.extraScans.set(result.scan_id, result);
  if (!result.threat_id || !result.matched_merchant) return;
  const at = nowIso();
  const threat: FixtureThreat = {
    ...result,
    id: result.threat_id,
    merchant_id: merchantId,
    first_seen_at: store.extraThreats.get(result.threat_id)?.first_seen_at ?? at,
    last_checked_at: at,
    resolved_at: null,
    status: "detected",
    status_history: [{ status: "detected", at, note: "Simulator" }],
    extracted_phones: [],
    extracted_tills: [],
    playbooks_generated: [],
  };
  const isNew = !store.extraThreats.has(threat.id);
  store.extraThreats.set(threat.id, threat);
  store.status.delete(threat.id);
  // Mirrors the backend (5.10): repeating the same tweaks re-scores the same handle, no new alert.
  if (result.verdict !== "impersonation" || !isNew) return;
  store.extraAlerts.push({
    id: randomUUID(),
    merchant_id: merchantId,
    threat_id: threat.id,
    kind: "new_threat",
    title: `Impersonator detected: @${result.target.handle}`,
    body: result.reasons[0]?.text ?? "A page is imitating your business.",
    score: result.score,
    created_at: at,
    read_at: null,
    threat: summary(threat),
  });
}
