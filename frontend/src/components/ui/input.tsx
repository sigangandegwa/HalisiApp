import * as React from "react";
import { cn } from "@/lib/utils";

const fieldBase = [
  "w-full min-w-0 border border-line-strong bg-bg-2 text-fg",
  "transition-[border-color,background-color] duration-(--dur-ui) ease-quart",
  "hover:border-[color-mix(in_oklab,var(--fg)_45%,transparent)]",
  "focus-visible:border-fg focus-visible:bg-bg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-fg focus-visible:ring-offset-0",
  "aria-invalid:border-fake aria-invalid:ring-fake",
  "disabled:cursor-not-allowed disabled:opacity-50",
].join(" ");

/** Document-style input: sharp corners, paper-2 well, ink hairline (FRONTEND.md 4.3). */
export function Input({ className, mono, ...props }: React.ComponentProps<"input"> & { mono?: boolean }) {
  return (
    <input
      data-slot="input"
      className={cn(fieldBase, "h-12 rounded-doc px-4 text-body", mono && "type-data tracking-[0.02em]", className)}
      {...props}
    />
  );
}

export function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return <textarea data-slot="textarea" className={cn(fieldBase, "min-h-28 rounded-doc px-4 py-3 text-body leading-relaxed", className)} {...props} />;
}

/** Label + control + hint + inline error. Placeholder text is never the label. */
export function Field({
  label,
  hint,
  error,
  htmlFor,
  children,
  className,
}: {
  label: string;
  hint?: string;
  error?: string | null;
  htmlFor: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("grid gap-2", className)}>
      <label htmlFor={htmlFor} className="type-caption text-fg-2">
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${htmlFor}-error`} role="alert" className="text-small text-fake">
          {error}
        </p>
      ) : hint ? (
        <p id={`${htmlFor}-hint`} className="text-small text-fg-3">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
