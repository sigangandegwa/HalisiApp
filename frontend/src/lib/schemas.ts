/**
 * Runtime schemas for the FROZEN API contract (docs/BACKEND.md section 5 and 8.2).
 * Every response the frontend reads is parsed with one of these. Unknown keys are stripped, so
 * additive backend changes don't break the UI; missing or mistyped required keys do (loudly).
 *
 * Where the contract is silent about a shape (ThreatDetail.status_history, playbooks_generated,
 * Alert.merchant_id), the choice made here is marked "CONTRACT GAP" and reported to the lead.
 */
import { z } from "zod";

// --- primitives -----------------------------------------------------------------------------

export const Verdict = z.enum(["official", "impersonation", "suspicious", "no_match", "error"]);
export type Verdict = z.infer<typeof Verdict>;

export const DimensionKey = z.enum(["visual", "identity", "payment", "language", "account"]);
export type DimensionKey = z.infer<typeof DimensionKey>;

export const ThreatStatus = z.enum(["detected", "advisory_sent", "takedown_filed", "resolved", "false_positive"]);
export type ThreatStatus = z.infer<typeof ThreatStatus>;

export const MpesaType = z.enum(["till", "paybill", "pochi", "none"]);
export type MpesaType = z.infer<typeof MpesaType>;

const nullableString = z.string().nullable().optional().transform((v) => v ?? null);
const nullableInt = z.number().int().nullable().optional().transform((v) => v ?? null);

// --- shared objects -------------------------------------------------------------------------

export const OfficialHandle = z.object({
  platform: z.string(),
  handle: z.string(),
  url: nullableString,
});
export type OfficialHandle = z.infer<typeof OfficialHandle>;

export const MerchantPayment = z.object({
  type: MpesaType,
  number: nullableString,
  account_name: nullableString,
});
export type MerchantPayment = z.infer<typeof MerchantPayment>;

export const MatchedMerchant = z.object({
  id: z.string(),
  business_name: z.string(),
  slug: z.string(),
  logo_url: nullableString,
  official_handles: z.array(OfficialHandle),
  payment: MerchantPayment,
});
export type MatchedMerchant = z.infer<typeof MatchedMerchant>;

export const Target = z.object({
  platform: nullableString,
  handle: nullableString,
  display_name: nullableString,
  url: nullableString,
  avatar_url: nullableString,
  follower_count: nullableInt,
  post_count: nullableInt,
  account_created_on: nullableString,
  fetched_via: nullableString,
});
export type Target = z.infer<typeof Target>;

export const Dimension = z.object({
  key: DimensionKey,
  label: z.string(),
  score: z.number(),
  weight: z.number(),
  available: z.boolean(),
  evidence: z.string(),
});
export type Dimension = z.infer<typeof Dimension>;

export const Reason = z.object({
  code: z.string(),
  severity: z.string(), // "high" | "medium" today; kept open so a new level can't break the page
  text: z.string(),
  text_sw: z.string(),
});
export type Reason = z.infer<typeof Reason>;

export const Hashes = z.object({
  target_phash: nullableString,
  reference_phash: nullableString,
  hamming_distance: nullableInt,
});
export type Hashes = z.infer<typeof Hashes>;

export const SafeAction = z.object({ text: z.string(), text_sw: z.string() });
export type SafeAction = z.infer<typeof SafeAction>;

// --- 5.2 check ------------------------------------------------------------------------------

export const CheckRequest = z.object({
  url: z.string().max(2048).nullable().optional(),
  handle: z.string().max(100).nullable().optional(),
  platform: z.string().nullable().optional(),
  manual: z
    .object({
      display_name: z.string().max(200).nullable().optional(),
      bio: z.string().max(2200).nullable().optional(),
      avatar_base64: z.string().nullable().optional(),
    })
    .nullable()
    .optional(),
});
export type CheckRequest = z.infer<typeof CheckRequest>;

export const CheckResult = z.object({
  scan_id: z.string(),
  verdict: Verdict,
  score: z.number(),
  confidence: z.number(),
  target: Target,
  matched_merchant: MatchedMerchant.nullable().optional().transform((v) => v ?? null),
  dimensions: z.array(Dimension).default([]),
  reasons: z.array(Reason).default([]),
  hashes: Hashes.nullable().optional().transform((v) => v ?? null),
  safe_action: SafeAction.nullable().optional().transform((v) => v ?? null),
  threat_id: nullableString,
  elapsed_ms: nullableInt,
});
export type CheckResult = z.infer<typeof CheckResult>;

// --- 5.3 payment lookup ---------------------------------------------------------------------

// --- 5.4 public merchant profile ------------------------------------------------------------

export const MerchantPublic = z.object({
  /** 5.11: now returned by the API (the dashboard needs it for /merchants/{id}/...) */
  id: z.string().optional(),
  business_name: z.string(),
  slug: z.string(),
  logo_url: nullableString,
  category: nullableString,
  location: nullableString,
  established_on: nullableString,
  is_verified: z.boolean(),
  official_handles: z.array(OfficialHandle),
  payment: MerchantPayment,
  verified_since: nullableString,
});
export type MerchantPublic = z.infer<typeof MerchantPublic>;

export const PaymentLookup = z.object({
  kind: z.string(), // "phone" | "till" | "paybill"
  normalized: z.string(),
  display: z.string(),
  status: z.enum(["official", "reported", "unknown"]),
  merchant: MerchantPublic.nullable().optional().transform((v) => v ?? null),
  report_count: z.number().int(),
  linked_threats: z.number().int(),
});
export type PaymentLookup = z.infer<typeof PaymentLookup>;

// --- 5.5 onboarding -------------------------------------------------------------------------

export const MerchantCreate = z.object({
  business_name: z.string().min(2).max(120),
  slug: z.string().regex(/^[a-z0-9-]{3,60}$/),
  aliases: z.array(z.string()).default([]),
  category: z.string().nullable().optional(),
  location: z.string().nullable().optional(),
  established_on: z.string().nullable().optional(),
  mpesa_type: MpesaType,
  mpesa_number: z.string().nullable().optional(),
  mpesa_account_name: z.string().nullable().optional(),
  phone_numbers: z.array(z.string()).default([]),
  handles: z.array(z.object({ platform: z.string(), handle: z.string() })),
});
export type MerchantCreate = z.infer<typeof MerchantCreate>;

export const MerchantCreated = MerchantPublic.extend({
  id: z.string(),
  logo_phash: nullableString,
  logo_dhash: nullableString,
  clip: z.boolean().optional(),
});
export type MerchantCreated = z.infer<typeof MerchantCreated>;

// --- 5.6 threats ----------------------------------------------------------------------------

export const ThreatSummary = z.object({
  id: z.string(),
  platform: z.string(),
  target_handle: z.string(),
  target_url: z.string(),
  avatar_url: nullableString,
  composite_score: z.number(),
  verdict: Verdict,
  status: ThreatStatus,
  first_seen_at: z.string(),
  top_reason: Reason.nullable().optional().transform((v) => v ?? null),
});
export type ThreatSummary = z.infer<typeof ThreatSummary>;

/** 5.11: `{status, at}` (note is a frontend-only optional). */
export const StatusEvent = z.object({
  status: ThreatStatus,
  at: z.string(),
  note: nullableString,
});
export type StatusEvent = z.infer<typeof StatusEvent>;

export const ThreatDetail = CheckResult.extend({
  /** CONTRACT GAP: "every CheckResult field plus ..." has no `id` / `first_seen_at`; both optional here. */
  id: z.string().optional(),
  first_seen_at: z.string().optional(),
  /** 5.11 additions */
  last_checked_at: nullableString,
  resolved_at: nullableString,
  status: ThreatStatus,
  status_history: z.array(StatusEvent).default([]),
  extracted_phones: z.array(z.string()).default([]),
  extracted_tills: z.array(z.string()).default([]),
  /** 5.11: {playbook_type, language, generator, prompt_id, model, created_at} */
  playbooks_generated: z.array(z.record(z.string(), z.unknown())).default([]),
});
export type ThreatDetail = z.infer<typeof ThreatDetail>;

export const ThreatUpdate = z.object({ status: ThreatStatus });

// --- 5.7 playbooks --------------------------------------------------------------------------

const PerBook = { generator: z.enum(["llm", "template"]).optional() };

export const Playbooks = z.object({
  generator: z.enum(["llm", "template"]),
  model: nullableString,
  prompt_ids: z.array(z.string()).default([]),
  /** 5.11 additions */
  language: z.enum(["en", "sw"]).optional(),
  contacts_verified: z.boolean().optional(),
  consumer_warning: z.object({ title: z.string(), body: z.string(), whatsapp_share_url: z.string(), ...PerBook }),
  platform_takedown: z.object({ platform: z.string(), report_url: z.string(), body: z.string(), ...PerBook }),
  safaricom_report: z.object({ channel: z.string(), to: z.string(), subject: z.string(), body: z.string(), ...PerBook }),
  kecirt_report: z.object({ to: z.string(), subject: z.string(), body: z.string(), ...PerBook }),
});
export type Playbooks = z.infer<typeof Playbooks>;

// --- 5.8 reports ----------------------------------------------------------------------------

export const ReportCreate = z
  .object({
    target_url: z.string().max(2048).nullable().optional(),
    target_handle: z.string().max(100).nullable().optional(),
    platform: z.string().nullable().optional(),
    reported_phone: z.string().max(20).nullable().optional(),
    reported_till: z.string().max(10).nullable().optional(),
    description: z.string().max(1000).nullable().optional(),
    reporter_contact: z.string().max(200).nullable().optional(),
  })
  .refine((r) => Boolean(r.target_url || r.target_handle || r.reported_phone || r.reported_till), {
    message: "At least one of url, handle, phone or till is required.",
  });
export type ReportCreate = z.infer<typeof ReportCreate>;

export const ReportCreated = z.object({ id: z.string(), status: z.string() });
export type ReportCreated = z.infer<typeof ReportCreated>;

// --- 5.9 stats ------------------------------------------------------------------------------

export const Stats = z.object({
  pages_scanned: z.number().int(),
  threats_detected: z.number().int(),
  impersonations_blocked_7d: z.number().int(),
  merchants_protected: z.number().int(),
  median_detection_ms: z.number(),
  top_platforms: z.array(z.object({ platform: z.string(), count: z.number().int() })).default([]),
  active_threats: nullableInt,
  resolved: nullableInt,
  customers_warned_estimate: nullableInt,
});
export type Stats = z.infer<typeof Stats>;

// --- 5.10 simulator -------------------------------------------------------------------------

export const HandleStyle = z.enum(["suffix", "homoglyph", "underscore"]);
export const LogoTweak = z.enum(["exact", "recolor", "crop", "jpeg"]);
export const PaymentTweak = z.enum(["phone", "pochi", "none"]);

export const SimulatorRequest = z.object({
  merchant_id: z.string(),
  tweaks: z.object({
    handle_style: HandleStyle,
    logo: LogoTweak,
    payment: PaymentTweak,
    bio_tokens: z.boolean(),
  }),
});
export type SimulatorRequest = z.infer<typeof SimulatorRequest>;
export type Tweaks = SimulatorRequest["tweaks"];

// --- 8.2 alerts -----------------------------------------------------------------------------

export const Alert = z.object({
  id: z.string(),
  threat_id: z.string(),
  kind: z.enum(["new_threat", "score_increase", "resolved"]),
  title: z.string(),
  body: z.string(),
  score: z.number(),
  created_at: z.string(),
  read_at: nullableString,
  threat: ThreatSummary,
});
export type Alert = z.infer<typeof Alert>;

export const AlertsResponse = z.object({
  alerts: z.array(Alert),
  unread_count: z.number().int(),
  server_time: z.string(),
});
export type AlertsResponse = z.infer<typeof AlertsResponse>;

export const MarkRead = z.union([z.object({ ids: z.array(z.string()) }), z.object({ all: z.literal(true) })]);
export const MarkReadResponse = z.object({ unread_count: z.number().int() });

// --- errors ---------------------------------------------------------------------------------

export const ApiErrorBody = z.object({
  error: z.object({ code: z.string(), message: z.string().optional() }),
});

export const Health = z.object({
  status: z.string(),
  version: z.string().optional(),
  demo_mode: z.boolean().optional(),
  engine: z.record(z.string(), z.string()).optional(),
  llm: z.string().optional(),
  db: z.string().optional(),
});
