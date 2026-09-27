import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, qk } from "@/lib/api";
import { useEffect, useState, useRef } from "react";
import { toast } from "sonner";

export function useAlerts(merchantId: string) {
  const queryClient = useQueryClient();
  const [since, setSince] = useState<string | null>(null);
  
  const query = useQuery({
    queryKey: qk.alerts(merchantId),
    queryFn: async () => {
      const data = await api.listAlerts(merchantId, { limit: 50 });
      return data;
    },
    refetchInterval: 5000,
  });

  const previousCount = useRef(0);

  useEffect(() => {
    if (query.data) {
      const unreadAlerts = query.data.alerts.filter((a) => !a.read_at);
      if (unreadAlerts.length > previousCount.current && previousCount.current !== 0) {
        // New alert arrived!
        const newest = unreadAlerts[0];
        toast(`New threat detected: ${newest.threat?.target_handle}`, {
           description: `Score: ${newest.score}. ${newest.body}`,
           className: "desk-panel border-l-4 border-l-[var(--color-feki)] text-fg relative overflow-hidden",
           action: {
              label: "Open",
              onClick: () => {
                 window.location.href = `/dashboard/threat/${newest.threat_id}`;
              }
           }
        });

        // Trigger browser notification if permitted
        if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'granted' && document.visibilityState !== 'visible') {
           navigator.serviceWorker.ready.then(registration => {
              registration.showNotification("Halisi Alert", {
                 body: `New threat detected: ${newest.threat?.target_handle}`,
                 tag: newest.threat_id,
                 data: { url: `/dashboard/threat/${newest.threat_id}` }
              });
           });
        }
      }
      previousCount.current = unreadAlerts.length;
    }
  }, [query.data]);

  const markRead = useMutation({
    mutationFn: (ids: string[]) => api.markAlertsRead(merchantId, { ids }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qk.alerts(merchantId) });
    },
  });

  const markAllRead = useMutation({
    mutationFn: () => api.markAlertsRead(merchantId, { all: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qk.alerts(merchantId) });
    },
  });

  return {
    ...query,
    markRead,
    markAllRead,
    unreadCount: query.data?.alerts.filter(a => !a.read_at).length ?? 0,
  };
}
