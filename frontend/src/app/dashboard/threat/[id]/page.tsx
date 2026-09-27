"use client";

import { useAlertDrawer } from "@/components/merchant/alert-context";
import { api, qk } from "@/lib/api";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { VerdictStamp } from "@/components/checker/verdict-stamp";
import { HandleDiff } from "@/components/merchant/handle-diff";
import { CompareSlider } from "@/components/merchant/compare-slider";
import { HashGrid } from "@/components/checker/hash-grid";
import { ScoreRadar } from "@/components/merchant/score-radar";
import { EvidenceBars } from "@/components/checker/evidence-bars";
import { PlaybookTabs } from "@/components/merchant/playbook-tabs";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { formatDateTime } from "@/lib/format";

export default function ThreatDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const { merchantId } = useAlertDrawer();
  const queryClient = useQueryClient();

  const { data: threat, isLoading: threatLoading } = useQuery({
    queryKey: qk.threat(id),
    queryFn: () => api.getThreat(id),
  });

  const { data: merchant } = useQuery({
    queryKey: qk.merchant(merchantId), 
    queryFn: () => api.getMerchant("nairobi-sneaker-vault"), // Mock
  });

  const updateStatus = useMutation({
    mutationFn: (status: any) => api.updateThreat(id, status),
    onSuccess: () => {
       queryClient.invalidateQueries({ queryKey: qk.threat(id) });
       queryClient.invalidateQueries({ queryKey: qk.threats(merchantId) });
    }
  });

  if (threatLoading || !threat) {
    return <div className="p-8"><div className="skeleton-ink h-32 rounded-sm" /></div>;
  }

  const isHighRisk = threat.score >= 70;
  const merchantHandles = merchant?.official_handles.map(h => h.handle) || [];

  return (
    <div className="space-y-12">
      <div className="flex flex-col gap-6">
        <Link href="/dashboard" className="flex items-center gap-2 text-fg-2 hover:text-fg type-caption w-fit transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to dashboard
        </Link>
        
        <header className="flex flex-col lg:flex-row lg:items-end justify-between gap-6 pb-6 border-b border-line">
           <div>
              <div className="flex items-center gap-4 mb-2">
                 <VerdictStamp verdict={isHighRisk ? "impersonation" : "suspicious"} size="sm" />
                 <span className={`type-data text-2xl ${isHighRisk ? 'text-[var(--color-feki)]' : 'text-[var(--color-caution)]'}`}>
                    {threat.score}%
                 </span>
              </div>
              <div className="type-display-m text-fg mt-4">
                 <HandleDiff target={threat.target.handle || ""} officials={merchantHandles} />
              </div>
              <p className="type-caption text-fg-2 mt-4">Based on 5 of 5 signals</p>
           </div>
           
           <div className="flex flex-col items-start lg:items-end gap-3">
              <div className="flex gap-2">
                 {/* Stepper MVP */}
                 {["detected", "advisory_sent", "takedown_filed", "resolved"].map(step => (
                    <button 
                       key={step}
                       onClick={() => updateStatus.mutate(step)}
                       className={`px-3 py-1 text-xs uppercase tracking-widest font-medium rounded-pill border transition-colors ${
                          threat.status === step 
                          ? 'bg-fg text-bg border-fg' 
                          : 'border-line text-fg-2 hover:border-fg-2 hover:text-fg'
                       }`}
                    >
                       {step.replace("_", " ")}
                    </button>
                 ))}
              </div>
              <button 
                 onClick={() => updateStatus.mutate("false_positive")}
                 className="text-xs text-fg-3 hover:text-fg underline decoration-line underline-offset-4 transition-colors"
              >
                 Mark false positive
              </button>
           </div>
        </header>
      </div>

      <div className="result-grid">
         <section data-area="compare" className="space-y-6">
            <h3 className="type-heading text-fg">Visual Match</h3>
            <div className="desk-panel p-6">
               <CompareSlider 
                 official={merchant?.logo_url || ""} 
                 suspect={threat.target.avatar_url || ""} 
               />
            </div>
         </section>

         <section data-area="hash" className="space-y-6">
            <h3 className="type-heading text-fg">Fingerprint</h3>
            <div className="desk-panel p-6">
               <HashGrid hex={threat.hashes?.target_phash || "0"} compareHex={threat.hashes?.reference_phash || "0"} label="Hash" />
            </div>
         </section>

         <section data-area="bars" className="space-y-6">
            <h3 className="type-heading text-fg">Sub-scores</h3>
            <div className="desk-panel p-6 flex flex-col md:flex-row gap-8 items-center justify-between">
               <div className="w-full max-w-[200px] flex-shrink-0">
                 <ScoreRadar dimensions={threat.dimensions} />
               </div>
               <div className="flex-1 w-full max-w-[320px]">
                 <EvidenceBars dimensions={threat.dimensions} color="var(--color-feki)" />
               </div>
            </div>
         </section>
         
         <section data-area="reasons" className="space-y-6">
            <h3 className="type-heading text-fg">Timeline</h3>
            <div className="desk-panel p-6 space-y-4">
               {threat.status_history.map((h, i) => (
                  <div key={i} className="flex justify-between items-center text-sm border-b border-line pb-4 last:border-0 last:pb-0">
                     <span className="text-fg-2 uppercase tracking-wider text-xs font-medium">{h.status.replace("_", " ")}</span>
                     <span className="text-fg-3 type-data">{formatDateTime(h.at)}</span>
                  </div>
               ))}
            </div>
         </section>

         <section data-area="verdict" className="space-y-6">
            <PlaybookTabs threatId={threat.id || ""} />
         </section>
      </div>
    </div>
  );
}
