"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { api, endpoints } from "@/lib/api";

export default function SettingsPage() {
  const [health, setHealth] = useState<any>(null);
  const [me, setMe] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    endpoints.health().then(setHealth).catch((e) => setErr(String(e)));
    api("/api/v1/me").then(setMe).catch(() => {});
  }, []);
  return (
    <AppShell active="/settings" title="Settings">
      <div className="max-w-3xl space-y-6">
        {err && <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{err}</div>}
        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-semibold">Backend health</h2>
          <pre className="mt-3 overflow-auto rounded-lg bg-muted/40 p-3 text-[11px]">
            {health ? JSON.stringify(health, null, 2) : "Loading..."}
          </pre>
        </section>
        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-semibold">Current session</h2>
          <pre className="mt-3 overflow-auto rounded-lg bg-muted/40 p-3 text-[11px]">
            {me ? JSON.stringify(me, null, 2) : "Not signed in / no role"}
          </pre>
        </section>
        <section className="rounded-xl border border-border bg-card p-5">
          <h2 className="text-sm font-semibold">Config files</h2>
          <ul className="mt-3 space-y-1 text-sm">
            <li>config/taxonomy.yaml</li>
            <li>config/risk_policy.yaml</li>
            <li>config/routing.yaml</li>
            <li>config/thresholds.yaml</li>
            <li>config/demo.yaml</li>
          </ul>
          <p className="mt-3 text-xs text-muted-foreground">
            In-place editing is intentionally disabled in this local build. Edit YAML on disk and reload the backend.
          </p>
          <Link href="/data-health" className="mt-3 inline-block text-sm text-[var(--primary)] hover:underline">Go to Data health →</Link>
        </section>
      </div>
    </AppShell>
  );
}
