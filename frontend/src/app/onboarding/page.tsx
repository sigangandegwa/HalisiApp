"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { HashGrid } from "@/components/checker/hash-grid";
import { Certificate } from "@/components/certificate/certificate";
import type { MerchantCreate } from "@/lib/schemas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowRight, Upload } from "lucide-react";
import Link from "next/link";
import { useMutation } from "@tanstack/react-query";

export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const [data, setData] = useState<Partial<MerchantCreate>>({
    handles: [],
    mpesa_type: "none",
    phone_numbers: []
  });
  const [logoFile, setLogoFile] = useState<File | null>(null);
  
  const createMutation = useMutation({
    mutationFn: () => api.createMerchant(data as MerchantCreate, logoFile!),
  });

  const next = () => setStep(s => Math.min(4, s + 1));
  const back = () => setStep(s => Math.max(1, s - 1));

  if (createMutation.isSuccess) {
    const merchant = createMutation.data;
    return (
      <div className="max-w-2xl mx-auto space-y-12 py-12 flex flex-col items-center">
         <h1 className="type-display-l text-fg text-center">Verification Complete</h1>
         <p className="type-lede text-fg-2 text-center max-w-md">Your business is now protected. Your customers can verify you instantly.</p>
         
         <div className="w-full">
            <Certificate merchant={merchant} url={`https://halisi.app/v/${merchant.slug}`} t={(k: any) => k} />
         </div>
         
         <Link href="/dashboard/badge" className="mt-8 bg-fg text-bg hover:bg-fg/90 px-8 py-3 rounded-pill type-caption transition-colors">
            Get your badge
         </Link>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto space-y-12">
       <div>
         <h1 className="type-display-m text-fg mb-4">Register Business</h1>
         <div className="flex gap-2 mb-8">
            {[1,2,3].map(s => (
               <div key={s} className={`h-1 flex-1 rounded-full ${step >= s ? "bg-fg" : "bg-line"}`} />
            ))}
         </div>
       </div>

       {step === 1 && (
         <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
           <div>
             <label className="type-caption text-fg-2 block mb-2">Business Name</label>
             <Input 
               value={data.business_name || ""} 
               onChange={e => setData({...data, business_name: e.target.value})} 
               placeholder="e.g. Nairobi Sneaker Vault"
             />
           </div>
           <div>
             <label className="type-caption text-fg-2 block mb-2">Slug</label>
             <div className="flex items-center">
               <span className="text-fg-3 px-3 py-2 bg-bg-2 border border-r-0 border-line rounded-l-doc">halisi.app/v/</span>
               <Input 
                 value={data.slug || ""} 
                 onChange={e => setData({...data, slug: e.target.value})} 
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
               onChange={e => setData({...data, handles: [{ platform: "instagram", handle: e.target.value }]})} 
               placeholder="@nairobisneakervault"
             />
           </div>
           <div>
             <label className="type-caption text-fg-2 block mb-2">M-Pesa Type</label>
             <select 
               value={data.mpesa_type} 
               onChange={e => setData({...data, mpesa_type: e.target.value as any})}
               className="w-full bg-bg border border-line rounded-doc p-2 outline-none focus-visible:ring-2 focus-visible:ring-fg"
             >
               <option value="none">None</option>
               <option value="till">Buy Goods Till</option>
               <option value="paybill">Paybill</option>
               <option value="pochi">Pochi la Biashara</option>
             </select>
           </div>
           {data.mpesa_type !== "none" && (
             <div className="grid grid-cols-2 gap-4">
               <div>
                 <label className="type-caption text-fg-2 block mb-2">Number</label>
                 <Input 
                   value={data.mpesa_number || ""} 
                   onChange={e => setData({...data, mpesa_number: e.target.value})} 
                   placeholder="e.g. 543210"
                 />
               </div>
               <div>
                 <label className="type-caption text-fg-2 block mb-2">Account Name (from SMS)</label>
                 <Input 
                   value={data.mpesa_account_name || ""} 
                   onChange={e => setData({...data, mpesa_account_name: e.target.value})} 
                   placeholder="e.g. NAIROBI SNEAKER VAULT"
                 />
               </div>
             </div>
           )}
           <div className="flex gap-4 pt-6">
             <Button variant="secondary" onClick={back} className="w-1/3">Back</Button>
             <Button onClick={next} className="w-2/3 gap-2">Next <ArrowRight className="w-4 h-4" /></Button>
           </div>
         </div>
       )}

       {step === 3 && (
         <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
           <div>
             <label className="type-caption text-fg-2 block mb-2">Official Logo</label>
             <label className="flex flex-col items-center justify-center p-12 border-2 border-dashed border-line rounded-doc hover:bg-bg-2 transition-colors cursor-pointer">
               <Upload className="w-8 h-8 text-fg-3 mb-4" />
               <p className="text-fg-2">Click or drag image to upload</p>
               <input 
                 type="file" 
                 accept="image/*" 
                 className="hidden" 
                 onChange={e => setLogoFile(e.target.files?.[0] || null)}
               />
             </label>
           </div>

           {logoFile && (
             <div className="desk-panel p-6 flex flex-col items-center justify-center space-y-4">
               <p className="text-fg-3 text-sm">This is your logo&apos;s fingerprint</p>
               {/* We just show a dummy hash grid to simulate the fingerprint extraction */}
               <HashGrid hex="A55AA55AA55AA55A" label="Hash" />
             </div>
           )}

           <div className="flex gap-4 pt-6">
             <Button variant="secondary" onClick={back} className="w-1/3">Back</Button>
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
  );
}
