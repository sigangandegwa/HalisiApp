"use client";

import { useMutation } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { useId, useState } from "react";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Field, Input, Textarea } from "@/components/ui/input";
import { api, demoData } from "@/lib/api";
import { canonicalPhone, canonicalTill, formatAsYouType, parseTarget, shortId } from "@/lib/format";
import { useI18n } from "@/lib/i18n/provider";

/** Community scam report (TSK-034, BACKEND.md section 5.8). */
export function ReportForm() {
  const { t } = useI18n();
  const id = useId();
  const params = useSearchParams();
  const initialTarget = params.get("url") ?? (params.get("handle") ? `@${params.get("handle")}` : "");
  const [target, setTarget] = useState(initialTarget);
  const [phone, setPhone] = useState(params.get("phone") ? formatAsYouType(params.get("phone")!).text : "");
  const [till, setTill] = useState(params.get("till") ?? "");
  const [description, setDescription] = useState("");
  const [contact, setContact] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<{ id: string; offline: boolean } | null>(null);

  const mutation = useMutation({ mutationFn: api.createReport });

  if (done) {
    return (
      <section role="status" className="rounded-doc border border-line bg-bg p-6 sm:p-8" style={{ animation: "halisi-fade-up 600ms var(--ease-out) both" }}>
        <span className="grid size-12 place-items-center rounded-full bg-fg text-bg">
          <Check className="size-6" strokeWidth={1.75} aria-hidden="true" />
        </span>
        <h2 className="type-heading mt-5">{t("report.success")}</h2>
        <p className="mt-2 text-fg-2">{t("report.successBody", { id: shortId(done.id) })}</p>
        {done.offline ? <p className="mt-3 text-small text-warn">{t("report.offline")}</p> : null}
        <Button
          variant="secondary"
          className="mt-6"
          onClick={() => {
            setDone(null);
            setTarget("");
            setPhone("");
            setTill("");
            setDescription("");
            setContact("");
          }}
        >
          {t("report.another")}
        </Button>
      </section>
    );
  }

  return (
    <form
      noValidate
      className="grid gap-6"
      onSubmit={async (e) => {
        e.preventDefault();
        setError(null);
        const parsed = target.trim() ? parseTarget(target.trim()) : null;
        const isUrl = /^(https?:\/\/|www\.)/i.test(target.trim()) || target.includes(".com");
        const body = {
          target_url: parsed && isUrl ? target.trim() : null,
          target_handle: parsed && !isUrl ? parsed.handle : null,
          platform: parsed?.platform ?? null,
          reported_phone: phone.trim() ? canonicalPhone(phone) : null,
          reported_till: till.trim() ? canonicalTill(till) : null,
          description: description.trim() || null,
          reporter_contact: contact.trim() || null,
        };
        if (!body.target_url && !body.target_handle && !body.reported_phone && !body.reported_till) {
          setError(t("report.need"));
          return;
        }
        try {
          const res = await mutation.mutateAsync(body);
          setDone({ id: res.id, offline: demoData.get() });
        } catch {
          setError(t("report.error"));
        }
      }}
    >
      <Field label={t("report.target")} htmlFor={`${id}-target`}>
        <Input id={`${id}-target`} value={target} onChange={(e) => setTarget(e.target.value)} placeholder="instagram.com/…" autoComplete="off" autoCapitalize="off" maxLength={2048} />
      </Field>
      <div className="grid gap-6 sm:grid-cols-2">
        <Field label={t("report.phone")} htmlFor={`${id}-phone`}>
          <Input id={`${id}-phone`} mono inputMode="tel" value={phone} onChange={(e) => setPhone(formatAsYouType(e.target.value).text)} placeholder="0712 345 678" autoComplete="off" />
        </Field>
        <Field label={t("report.till")} htmlFor={`${id}-till`}>
          <Input id={`${id}-till`} mono inputMode="numeric" value={till} onChange={(e) => setTill(e.target.value.replace(/\D/g, "").slice(0, 7))} placeholder="543210" autoComplete="off" />
        </Field>
      </div>
      <Field label={t("report.description")} hint={t("report.descriptionHint")} htmlFor={`${id}-desc`}>
        <Textarea id={`${id}-desc`} value={description} onChange={(e) => setDescription(e.target.value)} maxLength={1000} rows={4} />
      </Field>
      <Field label={t("report.contact")} hint={t("report.contactHint")} htmlFor={`${id}-contact`}>
        <Input id={`${id}-contact`} value={contact} onChange={(e) => setContact(e.target.value)} maxLength={200} autoComplete="email" />
      </Field>
      {error ? (
        <p role="alert" className="text-small text-fake">
          {error}
        </p>
      ) : null}
      <div>
        <Button type="submit" size="lg" disabled={mutation.isPending}>
          {mutation.isPending ? t("report.sending") : t("report.submit")}
        </Button>
      </div>
    </form>
  );
}
