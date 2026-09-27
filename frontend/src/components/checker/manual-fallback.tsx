"use client";

import { useId, useRef, useState } from "react";
import { ImageUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Field, Input, Textarea } from "@/components/ui/input";
import { useI18n } from "@/lib/i18n/provider";

const MAX_BYTES = 5 * 1024 * 1024;

/** Downscale to <= 512 px JPEG so the manual payload stays small on mobile data. */
async function toBase64(file: File): Promise<string> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, 512 / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("canvas");
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  return canvas.toDataURL("image/jpeg", 0.9).split(",")[1] ?? "";
}

/**
 * Shown on 502 TARGET_UNREACHABLE (FRONTEND.md section 7): the user pastes the bio and uploads the
 * profile picture, and the backend scores those instead. A real product feature, not a hack.
 */
export function ManualFallback({
  onSubmit,
  onCancel,
  pending,
  error,
  message,
}: {
  onSubmit: (manual: { display_name: string | null; bio: string | null; avatar_base64: string | null }) => void;
  onCancel: () => void;
  pending: boolean;
  error?: string | null;
  message?: string | null;
}) {
  const { t } = useI18n();
  const id = useId();
  const fileRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState("");
  const [bio, setBio] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  return (
    <section aria-labelledby={`${id}-title`} className="rounded-doc border border-line bg-bg p-5 sm:p-8" style={{ animation: "halisi-fade-up 600ms var(--ease-out) both" }}>
      <h2 id={`${id}-title`} className="type-heading">{t("manual.title")}</h2>
      <p className="mt-2 max-w-[56ch] text-fg-2">{message ?? t("manual.body")}</p>
      <form
        className="mt-6 grid gap-5 md:grid-cols-[minmax(0,1fr)_14rem]"
        onSubmit={async (e) => {
          e.preventDefault();
          setLocalError(null);
          if (!bio.trim() && !file) return setLocalError(t("manual.empty"));
          const avatar = file ? await toBase64(file).catch(() => null) : null;
          onSubmit({ display_name: name.trim() || null, bio: bio.trim() || null, avatar_base64: avatar });
        }}
      >
        <div className="grid gap-5">
          <Field label={t("manual.name")} htmlFor={`${id}-name`}>
            <Input id={`${id}-name`} value={name} onChange={(e) => setName(e.target.value)} maxLength={200} autoComplete="off" />
          </Field>
          <Field label={t("manual.bio")} hint={t("manual.bioHint")} htmlFor={`${id}-bio`}>
            <Textarea id={`${id}-bio`} value={bio} onChange={(e) => setBio(e.target.value)} maxLength={2200} rows={5} aria-describedby={`${id}-bio-hint`} />
          </Field>
        </div>
        <Field label={t("manual.avatar")} hint={t("manual.avatarHint")} htmlFor={`${id}-file`}>
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="grid aspect-square cursor-pointer place-items-center overflow-hidden rounded-doc border border-dashed border-line-strong bg-bg-2 text-fg-2 transition-colors duration-(--dur-ui) ease-quart hover:border-fg hover:text-fg"
          >
            {preview ? (
              // eslint-disable-next-line @next/next/no-img-element -- local object URL preview
              <img src={preview} alt="" className="size-full object-cover" />
            ) : (
              <span className="grid justify-items-center gap-2 text-small">
                <ImageUp className="size-6" strokeWidth={1.5} aria-hidden="true" />
                {t("manual.choose")}
              </span>
            )}
          </button>
          <input
            ref={fileRef}
            id={`${id}-file`}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="sr-only"
            onChange={(e) => {
              const f = e.target.files?.[0] ?? null;
              if (f && f.size > MAX_BYTES) {
                setLocalError(t("manual.tooBig"));
                return;
              }
              setFile(f);
              setPreview((old) => {
                if (old) URL.revokeObjectURL(old);
                return f ? URL.createObjectURL(f) : null;
              });
            }}
          />
        </Field>
        {localError || error ? (
          <p role="alert" className="text-small text-fake md:col-span-2">
            {localError ?? error}
          </p>
        ) : null}
        <div className="flex flex-wrap gap-3 md:col-span-2">
          <Button type="submit" size="lg" disabled={pending}>
            {pending ? t("checker.checking") : t("manual.submit")}
          </Button>
          <Button type="button" variant="ghost" size="lg" onClick={onCancel}>
            {t("manual.cancel")}
          </Button>
        </div>
      </form>
    </section>
  );
}
