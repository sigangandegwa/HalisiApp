"use client";

import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Check, Copy, ExternalLink, RefreshCw } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function PlaybookTabs({ threatId }: { threatId: string }) {
  const [lang, setLang] = useState<"en" | "sw">("en");
  const [copied, setCopied] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["playbooks", threatId, lang],
    queryFn: () => api.generatePlaybooks(threatId, lang),
  });

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback handled nicely in modern browsers mostly
    }
  };

  const actions = {
    customers: (text: string) => (
      <a href={`https://wa.me/?text=${encodeURIComponent(text)}`} target="_blank" rel="noreferrer" className="flex items-center gap-2 type-caption text-fg hover:opacity-80 transition-opacity">
        <ExternalLink className="w-4 h-4" /> Share to WhatsApp
      </a>
    ),
    platform: () => (
      <a href="https://help.instagram.com/contact/584460464982589" target="_blank" rel="noreferrer" className="flex items-center gap-2 type-caption text-fg hover:opacity-80 transition-opacity">
        <ExternalLink className="w-4 h-4" /> Open report form
      </a>
    ),
    safaricom: (text: string) => (
      <a href={`mailto:fraud@safaricom.co.ke?subject=Fraudulent M-Pesa Account Report&body=${encodeURIComponent(text)}`} className="flex items-center gap-2 type-caption text-fg hover:opacity-80 transition-opacity">
        <ExternalLink className="w-4 h-4" /> Open email draft
      </a>
    ),
    kecirt: (text: string) => (
      <a href={`mailto:incidents@ke-cirt.go.ke?subject=Impersonation Report&body=${encodeURIComponent(text)}`} className="flex items-center gap-2 type-caption text-fg hover:opacity-80 transition-opacity">
        <ExternalLink className="w-4 h-4" /> Open email draft
      </a>
    ),
  };

  const renderContent = (content: string | undefined, actionNode: React.ReactNode) => {
    if (isLoading) {
      return (
        <div className="space-y-4">
           <div className="skeleton-ink h-4 w-3/4 rounded-sm" />
           <div className="skeleton-ink h-4 w-full rounded-sm" />
           <div className="skeleton-ink h-4 w-5/6 rounded-sm" />
           <div className="skeleton-ink h-4 w-1/2 rounded-sm" />
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        <div className="bg-bg-2 p-6 rounded-doc border border-line whitespace-pre-wrap font-sans text-fg">
          {content}
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex gap-4 items-center">
            <button 
              onClick={() => handleCopy(content || "")}
              className="flex items-center gap-2 type-caption text-fg-2 hover:text-fg transition-colors"
            >
              {copied ? <Check className="w-4 h-4 text-[var(--color-halisi-glow)]" /> : <Copy className="w-4 h-4" />}
              {copied ? "Copied" : "Copy"}
            </button>
            {actionNode}
          </div>
          <p className="text-xs text-fg-3">Drafted by Llama 3.1 via NVIDIA NIM · review before sending</p>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
         <h3 className="type-heading text-fg">Remediation Playbooks</h3>
         <div className="flex items-center gap-4">
            <div className="flex bg-bg-2 border border-line rounded-pill p-1">
               <button 
                 onClick={() => setLang("en")} 
                 className={`px-3 py-1 text-sm rounded-pill transition-colors ${lang === "en" ? "bg-bg text-fg" : "text-fg-2 hover:text-fg"}`}
               >
                 EN
               </button>
               <button 
                 onClick={() => setLang("sw")} 
                 className={`px-3 py-1 text-sm rounded-pill transition-colors ${lang === "sw" ? "bg-bg text-fg" : "text-fg-2 hover:text-fg"}`}
               >
                 SW
               </button>
            </div>
            <button onClick={() => refetch()} className="p-2 text-fg-2 hover:text-fg" title="Regenerate">
               <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>
         </div>
      </div>

      <Tabs defaultValue="customers">
        <TabsList variant="line" className="mb-6">
          <TabsTrigger value="customers">Customers</TabsTrigger>
          <TabsTrigger value="platform">Instagram / Facebook</TabsTrigger>
          <TabsTrigger value="safaricom">Safaricom</TabsTrigger>
          <TabsTrigger value="kecirt">KE-CIRT/CC</TabsTrigger>
        </TabsList>

        <TabsContent value="customers">
          {renderContent(data?.consumer_warning?.body, actions.customers(data?.consumer_warning?.body || ""))}
        </TabsContent>
        <TabsContent value="platform">
          {renderContent(data?.platform_takedown?.body, actions.platform())}
        </TabsContent>
        <TabsContent value="safaricom">
          {renderContent(data?.safaricom_report?.body, actions.safaricom(data?.safaricom_report?.body || ""))}
        </TabsContent>
        <TabsContent value="kecirt">
          {renderContent(data?.kecirt_report?.body, actions.kecirt(data?.kecirt_report?.body || ""))}
        </TabsContent>
      </Tabs>
    </div>
  );
}
