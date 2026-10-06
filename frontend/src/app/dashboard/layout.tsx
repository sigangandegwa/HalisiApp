import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { ReactNode } from "react";
import { SESSION_COOKIE, verifySession } from "@/lib/session";
import { DashboardShell } from "./dashboard-shell";

/**
 * Reads the *actual* logged-in merchant from the session (src/proxy.ts already redirected
 * unauthenticated requests to /login before this ever renders). Previously this layout hardcoded
 * one demo merchant's id, so every account — including a business that had just signed up through
 * /onboarding — landed on Nairobi Sneaker Vault's dashboard instead of its own.
 */
export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const session = await verifySession((await cookies()).get(SESSION_COOKIE)?.value);
  if (!session) redirect("/login?next=/dashboard");

  return (
    <DashboardShell merchantId={session.mid} merchantSlug={session.slug}>
      {children}
    </DashboardShell>
  );
}
