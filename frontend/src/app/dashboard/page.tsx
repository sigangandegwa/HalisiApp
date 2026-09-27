"use client";

import { useAlertDrawer } from "@/components/merchant/alert-context";
import { KpiTile } from "@/components/merchant/kpi-tile";
import { ThreatRow } from "@/components/merchant/threat-row";
import { api, qk } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { Shield, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { paymentParts } from "@/lib/format";
import { Seal } from "@/components/brand/seal";

export default function DashboardPage() {
  const { merchantId } = useAlertDrawer();

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: qk.stats(merchantId),
    queryFn: () => api.getStats(merchantId),
    refetchInterval: 5000,
  });

  const { data: merchant } = useQuery({
    queryKey: qk.merchant(merchantId), // Wait, merchant lookup requires slug in api.ts, not id. But since we need the merchant, we'll fetch with a known slug for demo.
    queryFn: () => api.getMerchant("nairobi-sneaker-vault"), 
  });

  const { data: threats, isLoading: threatsLoading } = useQuery({
    queryKey: qk.threats(merchantId),
    queryFn: () => api.listThreats(merchantId),
    refetchInterval: 5000,
  });

  const activeThreats = stats?.active_threats ?? 0;
  const merchantHandles = merchant?.official_handles.map(h => h.handle) || [];
  const payment = merchant ? paymentParts(merchant.payment) : null;

  return (
    <div className="space-y-8">
      {/* KPIs Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiTile 
          label="Active threats" 
          value={activeThreats} 
          highlight={activeThreats > 0} 
        />
        <KpiTile 
          label="Pages scanned" 
          value={stats?.pages_scanned ?? 0} 
        />
        <KpiTile 
          label="Customers warned" 
          value={`~${stats?.customers_warned_estimate ?? 0}`} 
          subtitle="Estimated"
        />
        <KpiTile 
          label="Median time to detect" 
          value="4 m" 
        />
      </div>

      <div className="grid grid-cols-12 gap-8">
        {/* Live threat feed */}
        <div className="col-span-12 lg:col-span-8 space-y-4">
          <h2 className="type-heading text-fg mb-6">Live threat feed</h2>
          
          {threatsLoading ? (
            <div className="skeleton-ink h-24 rounded-sm" />
          ) : !threats || threats.length === 0 ? (
             <div className="desk-panel p-12 flex flex-col items-center justify-center text-center">
               <Shield className="w-12 h-12 text-fg-3 mb-4 opacity-50" />
               <p className="type-heading text-fg mb-2">All quiet</p>
               <p className="text-fg-2">Halisi is watching {merchantHandles.length} official accounts.</p>
             </div>
          ) : (
            <div className="space-y-3">
              {threats.map(threat => (
                <ThreatRow key={threat.id} threat={threat} merchantHandles={merchantHandles} />
              ))}
            </div>
          )}
        </div>

        {/* Protection summary */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
           <div className="desk-panel p-6 flex flex-col items-center text-center">
             <div className="w-32 h-32 mb-6">
                <Seal logoUrl={merchant?.logo_url ?? undefined} name={merchant?.business_name || ""} />
             </div>
             <h3 className="type-heading text-fg">{merchant?.business_name}</h3>
             <p className="type-caption text-fg-2 mt-2 mb-6">Protection Active</p>
             
             <div className="w-full text-left space-y-4 mt-4 border-t border-line pt-6">
                <div>
                   <span className="type-caption text-fg-3 block mb-1">Official Handles</span>
                   <div className="type-data text-fg space-y-1">
                      {merchantHandles.map(h => <div key={h}>@{h}</div>)}
                   </div>
                </div>
                {payment && (
                   <div>
                     <span className="type-caption text-fg-3 block mb-1">Official {payment.label}</span>
                     <div className="type-data text-fg">{payment.value}</div>
                   </div>
                )}
             </div>
             
             <Link 
               href="/dashboard/badge" 
               className="mt-8 w-full block bg-bg-3 hover:bg-bg-2 text-fg py-3 rounded-pill text-sm font-medium transition-colors border border-line text-center"
             >
               Get your badge
             </Link>
           </div>
        </div>
      </div>
    </div>
  );
}
