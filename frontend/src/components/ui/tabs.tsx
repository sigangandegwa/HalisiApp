"use client";

import { Tabs as TabsPrimitive } from "@base-ui/react/tabs";
import { cn } from "@/lib/utils";

/**
 * Tabs (restyled). Two looks:
 *  - "line": editorial tabs with a 2 px ink rule that slides between tabs (playbooks)
 *  - "pill": a segmented control with a sliding ink pill (checker Link | Till / Phone)
 */
export function Tabs({ className, ...props }: TabsPrimitive.Root.Props) {
  return <TabsPrimitive.Root data-slot="tabs" className={cn("flex flex-col gap-4", className)} {...props} />;
}

export function TabsList({
  className,
  variant = "line",
  children,
  ...props
}: TabsPrimitive.List.Props & { variant?: "line" | "pill" }) {
  return (
    <TabsPrimitive.List
      data-slot="tabs-list"
      data-variant={variant}
      className={cn(
        "group/tabs-list relative isolate flex items-center",
        variant === "line" && "no-scrollbar gap-6 overflow-x-auto border-b border-line",
        variant === "pill" && "inline-flex w-fit gap-0 rounded-pill border border-line-strong p-1",
        className,
      )}
      {...props}
    >
      {children}
      <TabsPrimitive.Indicator
        className={cn(
          "absolute -z-10 transition-[left,width,top,height] duration-(--dur-ui) ease-out",
          variant === "line" && "bottom-[-1px] left-(--active-tab-left) h-0.5 w-(--active-tab-width) bg-fg",
          variant === "pill" && "top-(--active-tab-top) left-(--active-tab-left) h-(--active-tab-height) w-(--active-tab-width) rounded-pill bg-fg",
        )}
      />
    </TabsPrimitive.List>
  );
}

export function TabsTrigger({ className, ...props }: TabsPrimitive.Tab.Props) {
  return (
    <TabsPrimitive.Tab
      data-slot="tabs-trigger"
      className={cn(
        "relative inline-flex cursor-pointer items-center justify-center gap-2 whitespace-nowrap select-none",
        "text-[0.9375rem] font-medium text-fg-2 transition-colors duration-(--dur-ui) ease-quart hover:text-fg",
        "group-data-[variant=line]/tabs-list:h-11 group-data-[variant=line]/tabs-list:data-active:text-fg",
        "group-data-[variant=pill]/tabs-list:h-9 group-data-[variant=pill]/tabs-list:rounded-pill group-data-[variant=pill]/tabs-list:px-4",
        "group-data-[variant=pill]/tabs-list:data-active:text-bg pointer-coarse:group-data-[variant=pill]/tabs-list:h-10",
        "disabled:pointer-events-none disabled:opacity-45",
        className,
      )}
      {...props}
    />
  );
}

export function TabsContent({ className, ...props }: TabsPrimitive.Panel.Props) {
  return <TabsPrimitive.Panel data-slot="tabs-content" className={cn("outline-none", className)} {...props} />;
}
