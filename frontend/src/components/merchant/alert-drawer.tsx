"use client";

import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { useAlertDrawer } from "./alert-context";
import { useAlerts } from "./use-alerts";
import Link from "next/link";
import { timeAgo } from "@/lib/format";
import { Check, ShieldAlert } from "lucide-react";

export function AlertDrawer() {
  const { isOpen, setOpen, merchantId } = useAlertDrawer();
  const { data, markRead, markAllRead, unreadCount } = useAlerts(merchantId);
  const alerts = data?.alerts || [];

  return (
    <Sheet open={isOpen} onOpenChange={setOpen}>
      <SheetContent className="theme-night w-full sm:max-w-md border-l border-line p-0 flex flex-col">
        <SheetHeader className="p-6 border-b border-line text-left">
          <div className="flex items-center justify-between">
            <SheetTitle className="type-heading text-fg">Alerts</SheetTitle>
            {unreadCount > 0 && (
              <button 
                onClick={() => markAllRead.mutate()}
                className="text-fg-2 hover:text-fg text-sm flex items-center gap-1 transition-colors"
              >
                <Check className="w-4 h-4" /> Mark all read
              </button>
            )}
          </div>
          <SheetDescription className="sr-only">
            Live threat alerts for your business.
          </SheetDescription>
        </SheetHeader>
        <div className="flex-1 overflow-y-auto">
          {alerts.length === 0 ? (
            <div className="p-6 text-center text-fg-3 flex flex-col items-center gap-3">
              <ShieldAlert className="w-8 h-8 opacity-50" />
              <p>No alerts. Halisi is watching.</p>
            </div>
          ) : (
            <div className="divide-y divide-line">
              {alerts.map((alert) => (
                <Link
                  key={alert.id}
                  href={`/dashboard/threat/${alert.threat_id}`}
                  onClick={() => {
                    if (!alert.read_at) markRead.mutate([alert.id]);
                    setOpen(false);
                  }}
                  className={`block p-4 hover:bg-bg-2 transition-colors relative ${!alert.read_at ? "bg-bg-2/50" : ""}`}
                >
                  {!alert.read_at && (
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-[var(--color-feki)]" />
                  )}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="type-data text-fg truncate">@{alert.threat?.target_handle}</p>
                      <p className="type-caption text-fg-2 mt-1">{alert.body}</p>
                    </div>
                    <div className="text-right whitespace-nowrap">
                      <div className={`type-data ${alert.score >= 70 ? 'text-[var(--color-feki)]' : 'text-[var(--color-caution)]'}`}>
                        {alert.score}%
                      </div>
                      <p className="text-xs text-fg-3 mt-1">
                        {timeAgo(alert.created_at)}
                      </p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
