"use client";

import * as React from "react";
import { Dialog as SheetPrimitive } from "@base-ui/react/dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

/** Side sheet (restyled shadcn Sheet on base-ui Dialog): mobile nav, alert drawer. */
export function Sheet(props: SheetPrimitive.Root.Props) {
  return <SheetPrimitive.Root data-slot="sheet" {...props} />;
}

export function SheetTrigger(props: SheetPrimitive.Trigger.Props) {
  return <SheetPrimitive.Trigger data-slot="sheet-trigger" {...props} />;
}

export function SheetClose(props: SheetPrimitive.Close.Props) {
  return <SheetPrimitive.Close data-slot="sheet-close" {...props} />;
}

export function SheetContent({
  className,
  children,
  side = "right",
  closeLabel = "Close",
  ...props
}: SheetPrimitive.Popup.Props & { side?: "left" | "right"; closeLabel?: string }) {
  return (
    <SheetPrimitive.Portal>
      <SheetPrimitive.Backdrop
        className={cn(
          "fixed inset-0 z-50 bg-[color-mix(in_oklab,var(--color-ink)_42%,transparent)]",
          "transition-opacity duration-(--dur-ui) ease-quart data-ending-style:opacity-0 data-starting-style:opacity-0",
        )}
      />
      <SheetPrimitive.Popup
        data-side={side}
        className={cn(
          "fixed inset-y-0 z-50 flex w-[min(92vw,26rem)] flex-col bg-bg text-fg outline-none",
          "transition-transform duration-[480ms] ease-out",
          side === "right" && "right-0 border-l border-line data-ending-style:translate-x-full data-starting-style:translate-x-full",
          side === "left" && "left-0 border-r border-line data-ending-style:-translate-x-full data-starting-style:-translate-x-full",
          className,
        )}
        {...props}
      >
        {children}
        <SheetPrimitive.Close
          className="absolute top-3 right-3 grid size-11 cursor-pointer place-items-center rounded-pill text-fg-2 transition-colors duration-(--dur-ui) ease-quart hover:bg-bg-2 hover:text-fg"
          aria-label={closeLabel}
        >
          <X className="size-5" strokeWidth={1.5} />
        </SheetPrimitive.Close>
      </SheetPrimitive.Popup>
    </SheetPrimitive.Portal>
  );
}

export function SheetHeader({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("grid gap-1 border-b border-line px-6 pt-6 pb-5 pr-16", className)} {...props} />;
}

export function SheetTitle({ className, ...props }: SheetPrimitive.Title.Props) {
  return <SheetPrimitive.Title className={cn("type-heading", className)} {...props} />;
}

export function SheetDescription({ className, ...props }: SheetPrimitive.Description.Props) {
  return <SheetPrimitive.Description className={cn("text-small text-fg-2", className)} {...props} />;
}
