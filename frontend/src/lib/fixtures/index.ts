/**
 * Fixture loader (server-only). Two complete worlds, never mixed:
 *
 *   1. seed/      written by the backend seeder (TSK-007) from the real engine + repository.
 *                 Preferred whenever it contains merchants and checks. Format: one file per
 *                 endpoint response (see seed/README.md). Extras the seed doesn't include
 *                 (simulator combinations, the manual look-alike) come from derived/, which
 *                 frontend/scripts/make_fixtures.py computes with the real engine against the
 *                 SEED merchants.
 *   2. *.json     frontend placeholders (see README.md in this folder), used only without a seed.
 *
 * Files are read at runtime (fs) and cached for a few seconds, so re-running the seeder is picked
 * up without a rebuild. Every file is validated against the contract; invalid files are skipped
 * with a warning rather than taking the demo down.
 */
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { z } from "zod";
import {
  Alert,
  AlertsResponse,
  CheckResult,
  MerchantPublic,
  PaymentLookup,
  Playbooks,
  Stats,
  ThreatDetail,
} from "@/lib/schemas";

import alertsHand from "./alerts.json";
import checksHand from "./checks.json";
import merchantsHand from "./merchants.json";
import paymentsHand from "./payments.json";
import playbooksHand from "./playbooks.json";
import statsHand from "./stats.json";
import threatsHand from "./threats.json";

const FIXTURE_DIR = path.join(process.cwd(), "src", "lib", "fixtures");
export const SEED_DIR = path.join(FIXTURE_DIR, "seed");
const DERIVED_DIR = path.join(FIXTURE_DIR, "derived");

export const FixtureAlert = Alert.extend({ merchant_id: z.string() });
export type FixtureAlert = z.infer<typeof FixtureAlert>;

export const FixtureThreat = ThreatDetail.extend({ id: z.string(), merchant_id: z.string(), first_seen_at: z.string() });
export type FixtureThreat = z.infer<typeof FixtureThreat>;

export const FixtureMerchant = MerchantPublic.extend({ id: z.string() });
export type FixtureMerchant = z.infer<typeof FixtureMerchant>;

const StatsFile = z.object({ global: Stats, merchants: z.record(z.string(), Stats) });
const PlaybooksFile = z.record(z.string(), z.object({ en: Playbooks.optional(), sw: Playbooks.optional() }));

export type FixtureSource = "seed" | "placeholder";

export interface FixtureSet {
  source: FixtureSource;
  checks: CheckResult[];
  threats: FixtureThreat[];
  alerts: FixtureAlert[];
  payments: PaymentLookup[];
  merchants: FixtureMerchant[];
  stats: z.infer<typeof StatsFile>;
  playbooks: z.infer<typeof PlaybooksFile>;
  /** Human-readable provenance, shown on /styleguide. */
  sources: Record<string, string>;
}

function readJson(dir: string, file: string): unknown {
  return JSON.parse(fs.readFileSync(path.join(dir, file), "utf8"));
}

function parseOrWarn<T>(schema: z.ZodType<T>, value: unknown, label: string): T | null {
  const parsed = schema.safeParse(value);
  if (parsed.success) return parsed.data;
  console.warn(`[fixtures] ${label} does not match the API contract; skipped.`, parsed.error.issues.slice(0, 3));
  return null;
}

function list(dir: string, pattern: RegExp): string[] {
  try {
    return fs.readdirSync(dir).filter((f) => pattern.test(f)).sort();
  } catch {
    return [];
  }
}

/** The backend seed, adapted to the in-memory shape. Null when there is no usable seed. */
function loadSeed(): FixtureSet | null {
  const merchantFiles = list(SEED_DIR, /^merchant-.+\.json$/);
  const checkFiles = list(SEED_DIR, /^check-.+\.json$/);
  if (!merchantFiles.length || !checkFiles.length) return null;
  const safe = <T>(label: string, fn: () => T | null): T | null => {
    try {
      return fn();
    } catch (err) {
      console.warn(`[fixtures] could not read seed/${label}:`, (err as Error).message);
      return null;
    }
  };

  const merchants = merchantFiles
    .map((f) => safe(f, () => parseOrWarn(FixtureMerchant, readJson(SEED_DIR, f), `seed/${f}`)))
    .filter((m): m is FixtureMerchant => m !== null);
  const idBySlug = new Map(merchants.map((m) => [m.slug, m.id]));

  const checks = checkFiles
    .map((f) => safe(f, () => parseOrWarn(CheckResult, readJson(SEED_DIR, f), `seed/${f}`)))
    .filter((c): c is CheckResult => c !== null);
  for (const f of list(DERIVED_DIR, /^lookalike\.json$/)) {
    const extra = safe(f, () => parseOrWarn(z.array(CheckResult), readJson(DERIVED_DIR, f), `derived/${f}`));
    if (extra) checks.push(...extra);
  }

  const threats = list(SEED_DIR, /^threat-.+\.json$/)
    .map((f) =>
      safe(f, () => {
        const raw = readJson(SEED_DIR, f) as Record<string, unknown>;
        const detail = parseOrWarn(ThreatDetail, raw, `seed/${f}`);
        if (!detail) return null;
        const id = detail.id ?? detail.threat_id;
        const merchantId = detail.matched_merchant?.id;
        if (!id || !merchantId) return null;
        return { ...detail, id, merchant_id: merchantId, first_seen_at: detail.first_seen_at ?? detail.status_history[0]?.at ?? "" };
      }),
    )
    .filter((t): t is FixtureThreat => t !== null);

  const alerts: FixtureAlert[] = [];
  for (const f of list(SEED_DIR, /^alerts-.+\.json$/)) {
    const slug = f.replace(/^alerts-/, "").replace(/\.json$/, "");
    const merchantId = idBySlug.get(slug);
    const res = safe(f, () => parseOrWarn(AlertsResponse, readJson(SEED_DIR, f), `seed/${f}`));
    if (res && merchantId) alerts.push(...res.alerts.map((a) => ({ ...a, merchant_id: merchantId })));
  }

  const paymentsRaw = safe("verify-payment.json", () => readJson(SEED_DIR, "verify-payment.json")) as Record<string, unknown> | null;
  const payments = Object.values(paymentsRaw ?? {})
    .map((p, i) => parseOrWarn(PaymentLookup, p, `seed/verify-payment.json[${i}]`))
    .filter((p): p is PaymentLookup => p !== null);

  const global = safe("stats.json", () => parseOrWarn(Stats, readJson(SEED_DIR, "stats.json"), "seed/stats.json"));
  const merchantStats: Record<string, Stats> = {};
  for (const f of list(SEED_DIR, /^stats-.+\.json$/)) {
    const slug = f.replace(/^stats-/, "").replace(/\.json$/, "");
    const s = safe(f, () => parseOrWarn(Stats, readJson(SEED_DIR, f), `seed/${f}`));
    const id = idBySlug.get(slug);
    if (s && id) merchantStats[id] = s;
  }

  const playbooks: z.infer<typeof PlaybooksFile> = {};
  for (const f of list(SEED_DIR, /^playbooks-.+-(en|sw)\.json$/)) {
    const m = /^playbooks-(.+)-(en|sw)\.json$/.exec(f)!;
    const books = safe(f, () => parseOrWarn(Playbooks, readJson(SEED_DIR, f), `seed/${f}`));
    if (books) (playbooks[m[1]] ??= {})[m[2] as "en" | "sw"] = books;
  }

  return {
    source: "seed",
    merchants,
    checks,
    threats,
    alerts,
    payments,
    stats: {
      global: global ?? { pages_scanned: 0, threats_detected: 0, impersonations_blocked_7d: 0, merchants_protected: merchants.length, median_detection_ms: 0, top_platforms: [], active_threats: null, resolved: null, customers_warned_estimate: null },
      merchants: merchantStats,
    },
    playbooks,
    sources: {
      world: "seed (backend engine + repository)",
      files: `${merchants.length} merchants, ${checks.length} checks, ${threats.length} threats, ${alerts.length} alerts, ${payments.length} payment lookups`,
      derived: "simulator + look-alike from scripts/make_fixtures.py",
    },
  };
}

function loadPlaceholders(): FixtureSet {
  return {
    source: "placeholder",
    checks: z.array(CheckResult).parse(checksHand),
    threats: z.array(FixtureThreat).parse(threatsHand),
    alerts: z.array(FixtureAlert).parse(alertsHand),
    payments: z.array(PaymentLookup).parse(paymentsHand),
    merchants: z.array(FixtureMerchant).parse(merchantsHand),
    stats: StatsFile.parse(statsHand),
    playbooks: PlaybooksFile.parse(playbooksHand),
    sources: { world: "frontend placeholders (scripts/make_fixtures.py)" },
  };
}

let cache: { at: number; set: FixtureSet } | null = null;
const TTL_MS = 5_000;

/** The current fixture set (seed preferred). Cheap to call: cached for a few seconds. */
export function fixtures(): FixtureSet {
  const now = Date.now();
  if (cache && now - cache.at < TTL_MS) return cache.set;
  const set = loadSeed() ?? loadPlaceholders();
  cache = { at: now, set };
  return set;
}

const simulatorCache = new Map<FixtureSource, Record<string, CheckResult>>();

/** Precomputed simulator results keyed `${merchant_slug}|${handle_style}|${logo}|${payment}|${0|1}`. */
export function simulatorFixtures(): Record<string, CheckResult> {
  const source = fixtures().source;
  const hit = simulatorCache.get(source);
  if (hit) return hit;
  const file = source === "seed" ? path.join(DERIVED_DIR, "simulator.json.gz") : path.join(FIXTURE_DIR, "simulator.json.gz");
  let data: Record<string, CheckResult> = {};
  try {
    const raw = zlib.gunzipSync(fs.readFileSync(file)).toString("utf8");
    data = z.record(z.string(), CheckResult).parse(JSON.parse(raw));
  } catch (err) {
    console.warn("[fixtures] simulator fixtures unavailable:", (err as Error).message);
  }
  simulatorCache.set(source, data);
  return data;
}

/** Merchants the dashboard session and simulator can use (id + display data). */
export function demoMerchants(): FixtureMerchant[] {
  return fixtures().merchants;
}

/** Serve a seed asset (logos/avatars referenced as /seed/<file>) from disk. */
export function readSeedAsset(file: string): Buffer | null {
  if (!/^[A-Za-z0-9._-]{1,120}\.(png|jpe?g|webp)$/.test(file)) return null;
  const p = path.join(SEED_DIR, "assets", file);
  try {
    return fs.readFileSync(p);
  } catch {
    return null;
  }
}
