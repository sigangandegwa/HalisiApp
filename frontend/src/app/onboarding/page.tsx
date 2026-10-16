"use client";

import { useState } from "react";
import { api, qk } from "@/lib/api";
import { Certificate } from "@/components/certificate/certificate";
import type { MerchantCreate, MpesaType } from "@/lib/schemas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowLeft, ArrowRight, CheckCircle2, ExternalLink, ShieldCheck, Upload } from "lucide-react";
import Link from "next/link";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useI18n } from "@/lib/i18n/provider";
import { LogoImage } from "@/components/brand/logo-image";
import { paymentParts } from "@/lib/format";

export default function OnboardingPage() {
  const { t } = useI18n();
  const [view, setView] = useState<"register" | "directory">("register");
  const [step, setStep] = useState(1);
  const [data, setData] = useState<Partial<MerchantCreate>>({
    handles: [],
    mpesa_type: "none",
    phone_numbers: [],
  });
  const [logoFile, setLogoFile] = useState<File | null>(null);

  const { data: merchantsList, isLoading: loadingMerchants, refetch: refetchMerchants } = useQuery({
    queryKey: qk.merchants(),
    queryFn: () => api.listMerchants(),
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      if (!logoFile) throw new Error("Please upload an official logo.");
      const bName = (data.business_name ?? "").trim();
      if (bName.length < 2) throw new Error("Business name must be at least 2 characters.");
      const sSlug = (data.slug ?? "").trim().toLowerCase().replace(/[^a-z0-9-]/g, "-").replace(/^-+|-+$/g, "");
      if (sSlug.length < 3) throw new Error("Slug must be at least 3 characters.");

      const cleanedHandles = (data.handles ?? [])
        .filter((h) => h.handle && h.handle.trim().length > 0)
        .map((h) => ({
          platform: h.platform,
          handle: h.handle.trim().replace(/^@/, ""),
        }));

      const mpesaNum = data.mpesa_type !== "none" && data.mpesa_number?.trim() ? data.mpesa_number.trim() : null;
      const mpesaAcc = data.mpesa_type !== "none" && data.mpesa_account_name?.trim() ? data.mpesa_account_name.trim() : null;

      const payload: MerchantCreate = {
        business_name: bName,
        slug: sSlug,
        aliases: data.aliases ?? [],
        category: data.category ?? null,
        location: data.location ?? null,
        established_on: data.established_on ?? null,
        mpesa_type: data.mpesa_type ?? "none",
        mpesa_number: mpesaNum,
        mpesa_account_name: mpesaAcc,
        phone_numbers: data.phone_numbers ?? [],
        handles: cleanedHandles,
      };

      return api.createMerchant(payload, logoFile);
    },
    onSuccess: () => {
      refetchMerchants();
    },
  });

  const next = () => setStep((s) => Math.min(4, s + 1));
  const back = () => setStep((s) => Math.max(1, s - 1));

  if (createMutation.isSuccess) {
    const merchant = createMutation.data;
    return (
      <div className="theme-night world-night min-h-dvh bg-bg text-fg">
        <div className="page-wrap py-10 sm:py-14">
          <div className="max-w-2xl mx-auto space-y-8 flex flex-col items-center animate-in fade-in">
            <div className="flex flex-col items-center text-center space-y-3">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-pill bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-sm font-medium">
                <CheckCircle2 className="w-4 h-4" />
                <span>Successfully Registered</span>
              </div>
              <h1 className="type-display-l text-fg">{merchant.business_name}</h1>
              <p className="type-lede text-fg-2 max-w-md">
                Your business is now stored in the database and protected against impersonation. Your customers can verify your official payment and handles instantly.
              </p>
            </div>

            <div className="w-full">
              <Certificate merchant={merchant} url={`https://halisi.app/v/${merchant.slug}`} t={t} />
            </div>

            <div className="flex flex-wrap items-center justify-center gap-4 mt-6">
              <Link
                href="/dashboard"
                className="bg-fg text-bg hover:bg-fg/90 px-8 py-3 rounded-pill type-caption transition-all duration-100 ease-out active:scale-[0.96]"
              >
                Go to your dashboard
              </Link>
              <Link
                href={`/v/${merchant.slug}`}
                target="_blank"
                className="border border-line-strong text-fg hover:border-fg px-8 py-3 rounded-pill type-caption transition-all duration-100 ease-out active:scale-[0.96] inline-flex items-center gap-2"
              >
                View Public Certificate <ExternalLink className="w-3.5 h-3.5" />
              </Link>
              <button
                type="button"
                onClick={() => {
                  createMutation.reset();
                  setStep(1);
                  setData({ handles: [], mpesa_type: "none", phone_numbers: [] });
                  setLogoFile(null);
                  setView("directory");
                }}
                className="border border-line text-fg-2 hover:text-fg px-6 py-3 rounded-pill type-caption transition-all duration-100 ease-out active:scale-[0.96] cursor-pointer"
              >
                View in Directory
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="theme-night world-night min-h-dvh bg-bg text-fg">
      <div className="page-wrap py-10 sm:py-14">
        {/* Navigation header */}
        <div className="max-w-2xl mx-auto mb-8 flex items-center justify-between">
          <Link
            href="/"
            className="group inline-flex items-center gap-2 px-3.5 py-1.5 rounded-pill border border-line bg-fg/[0.03] text-fg-2 hover:text-fg hover:border-line-strong hover:bg-fg/[0.06] text-xs font-medium transition-all duration-100 ease-out active:scale-[0.96]"
          >
            <ArrowLeft className="size-3.5 transition-transform duration-100 group-hover:-translate-x-0.5" />
            <span>Back to Home</span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-xs text-fg-3 hover:text-fg transition-colors"
            >
              Already registered? <span className="underline text-fg font-medium">Log in</span>
            </Link>
          </div>
        </div>

        <div className="max-w-2xl mx-auto space-y-10">
          {/* Header and View Switcher */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-line pb-6">
        <div>
          <h1 className="type-display-m text-fg">
            {view === "register" ? "Register Business" : "Registered Businesses"}
          </h1>
          <p className="type-caption text-fg-2 mt-1">
            {view === "register"
              ? "Protect your brand and payment channels against impersonation."
              : "All verified businesses currently secured in the Halisi database."}
          </p>
        </div>
        <div className="inline-flex rounded-pill border border-line bg-bg-2 p-1 text-xs self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setView("register")}
            className={`px-3 py-1.5 rounded-pill font-medium transition-colors ${
              view === "register" ? "bg-fg text-bg" : "text-fg-2 hover:text-fg"
            }`}
          >
            Register New
          </button>
          <button
            type="button"
            onClick={() => setView("directory")}
            className={`px-3 py-1.5 rounded-pill font-medium transition-colors flex items-center gap-1.5 ${
              view === "directory" ? "bg-fg text-bg" : "text-fg-2 hover:text-fg"
            }`}
          >
            <span>Directory</span>
            {merchantsList && (
              <span className="rounded-full bg-bg-3 px-1.5 py-0.5 text-[10px]">
                {merchantsList.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {view === "directory" ? (
        /* Registered Businesses Directory View */
        <div className="space-y-4 animate-in fade-in">
          {loadingMerchants ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="skeleton-ink h-24 rounded-doc" />
              ))}
            </div>
          ) : !merchantsList || merchantsList.length === 0 ? (
            <div className="desk-panel p-12 text-center text-fg-3">
              <ShieldCheck className="w-12 h-12 mx-auto mb-3 opacity-40" />
              <p className="type-heading text-fg mb-1">No businesses registered yet</p>
              <p className="text-small mb-6">Register your brand to start active protection.</p>
              <Button onClick={() => setView("register")}>Register a Business</Button>
            </div>
          ) : (
            <div className="grid gap-3">
              {merchantsList.map((m, i) => {
                const pay = paymentParts(m.payment);
                return (
                  <div
                    key={`${m.id || m.slug}-${i}`}
                    className="desk-panel p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border border-line hover:border-line-strong transition-colors"
                  >
                    <div className="flex items-center gap-4 min-w-0">
                      <LogoImage src={m.logo_url} alt={m.business_name} size={48} className="size-12 shrink-0" />
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <h2 className="font-medium text-fg truncate text-base">{m.business_name}</h2>
                          {m.is_verified && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-pill bg-halisi/15 text-halisi text-[10px] font-semibold tracking-wider uppercase shrink-0">
                              Verified
                            </span>
                          )}
                        </div>
                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-fg-2 mt-1">
                          {m.official_handles.map((h, hi) => (
                            <span key={`${h.platform}-${h.handle}-${hi}`}>
                              @{h.handle} <span className="text-fg-3 uppercase">({h.platform})</span>
                            </span>
                          ))}
                          {pay && (
                            <span className="text-fg-3">
                              · {pay.label}: <strong className="text-fg">{pay.value}</strong>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                      <Link
                        href={`/v/${m.slug}`}
                        target="_blank"
                        className="inline-flex items-center gap-1 text-xs font-medium text-fg-2 hover:text-fg border border-line hover:border-fg rounded-pill px-3 py-1.5 transition-colors"
                      >
                        <span>Certificate</span>
                        <ExternalLink className="w-3 h-3" />
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        /* Register Business Wizard View */
        <div className="space-y-8 animate-in fade-in">
          {/* Step indicators */}
          <div className="flex gap-2">
            {[1, 2, 3].map((s) => (
              <div key={s} className={`h-1 flex-1 rounded-full ${step >= s ? "bg-fg" : "bg-line"}`} />
            ))}
          </div>

          {step === 1 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
              <div>
                <label className="type-caption text-fg-2 block mb-2">Business Name</label>
                <Input
                  value={data.business_name || ""}
                  onChange={(e) => {
                    const bName = e.target.value;
                    const autoSlug = bName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
                    setData((prev) => ({
                      ...prev,
                      business_name: bName,
                      slug: !prev.slug || prev.slug === prev.business_name?.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "")
                        ? autoSlug
                        : prev.slug,
                    }));
                  }}
                  placeholder="e.g. Nairobi Sneaker Vault"
                />
              </div>
              <div>
                <label className="type-caption text-fg-2 block mb-2">Slug</label>
                <div className="flex items-center">
                  <span className="text-fg-3 px-3 py-2 bg-bg-2 border border-r-0 border-line rounded-l-doc text-sm">
                    halisi.app/v/
                  </span>
                  <Input
                    value={data.slug || ""}
                    onChange={(e) => setData({ ...data, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-") })}
                    placeholder="nairobi-sneaker-vault"
                    className="rounded-l-none"
                  />
                </div>
              </div>
              <div className="pt-6">
                <Button onClick={next} disabled={!data.business_name || !data.slug} className="w-full gap-2">
                  Next <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
              <div>
                <label className="type-caption text-fg-2 block mb-2">Official Instagram Handle</label>
                <Input
                  value={data.handles?.[0]?.handle || ""}
                  onChange={(e) =>
                    setData({
                      ...data,
                      handles: [{ platform: "instagram", handle: e.target.value }],
                    })
                  }
                  placeholder="@nairobisneakervault"
                />
              </div>
              <div>
                <label className="type-caption text-fg-2 block mb-2">M-Pesa Type</label>
                <select
                  value={data.mpesa_type}
                  onChange={(e) => setData({ ...data, mpesa_type: e.target.value as MpesaType })}
                  className="w-full bg-bg border border-line rounded-doc p-2 outline-none focus-visible:ring-2 focus-visible:ring-fg text-sm text-fg"
                >
                  <option value="none">None</option>
                  <option value="till">Buy Goods Till</option>
                  <option value="paybill">Paybill</option>
                  <option value="pochi">Pochi la Biashara</option>
                </select>
              </div>
              {data.mpesa_type !== "none" && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="type-caption text-fg-2 block mb-2">Number</label>
                    <Input
                      value={data.mpesa_number || ""}
                      onChange={(e) => setData({ ...data, mpesa_number: e.target.value })}
                      placeholder="e.g. 543210"
                    />
                  </div>
                  <div>
                    <label className="type-caption text-fg-2 block mb-2">Account Name (from SMS)</label>
                    <Input
                      value={data.mpesa_account_name || ""}
                      onChange={(e) => setData({ ...data, mpesa_account_name: e.target.value })}
                      placeholder="e.g. NAIROBI SNEAKER VAULT"
                    />
                  </div>
                </div>
              )}
              <div className="flex gap-4 pt-6">
                <Button variant="secondary" onClick={back} className="w-1/3">
                  Back
                </Button>
                <Button onClick={next} className="w-2/3 gap-2">
                  Next <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
              <div>
                <label className="type-caption text-fg-2 block mb-2">Official Logo</label>
                <label className="flex flex-col items-center justify-center p-10 border-2 border-dashed border-line rounded-doc hover:bg-bg-2 transition-colors cursor-pointer">
                  <Upload className="w-8 h-8 text-fg-3 mb-3" />
                  <p className="text-fg-2 font-medium text-sm">Click or drag image to upload logo</p>
                  <p className="text-fg-3 text-xs mt-1">PNG, JPEG or WebP (max 5 MB)</p>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => setLogoFile(e.target.files?.[0] || null)}
                  />
                </label>
              </div>

              {/* Upload confirmation replacing the confusing hash grid */}
              {logoFile && (
                <div className="desk-panel p-4 flex items-center justify-between border border-emerald-500/40 bg-emerald-950/20 rounded-doc animate-in fade-in">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="size-10 rounded-full bg-emerald-500/20 border border-emerald-500/30 grid place-items-center text-emerald-400 shrink-0">
                      <CheckCircle2 className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-fg truncate">{logoFile.name}</p>
                      <p className="text-xs text-emerald-300">
                        {(logoFile.size / 1024).toFixed(1)} KB · Logo attached successfully
                      </p>
                    </div>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setLogoFile(null)}
                    className="text-xs text-fg-3 hover:text-fg shrink-0"
                  >
                    Remove
                  </Button>
                </div>
              )}

              {createMutation.isError && (
                <div className="p-3.5 rounded-doc bg-red-950/40 border border-red-500/40 text-red-300 text-sm">
                  <p className="font-medium mb-0.5">Registration failed</p>
                  <p className="text-xs text-red-200">
                    {(createMutation.error as Error)?.message || "Please check your details and try again."}
                  </p>
                </div>
              )}

              <div className="flex gap-4 pt-6">
                <Button variant="secondary" onClick={back} className="w-1/3">
                  Back
                </Button>
                <Button
                  onClick={() => createMutation.mutate()}
                  disabled={!logoFile || createMutation.isPending}
                  className="w-2/3 gap-2"
                >
                  {createMutation.isPending ? "Registering..." : "Complete Registration"}
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
        </div>
      </div>
    </div>
  );
}
