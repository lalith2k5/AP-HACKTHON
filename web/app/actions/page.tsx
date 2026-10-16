"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints } from "@/lib/api";

export default function ActionsPage() {
  const [rows, setRows] = useState<any[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    endpoints.incidents().then((d: any) => {
      const items = (d.items ?? d.incidents ?? d) as any[];
      const sorted = [...items].sort((a, b) => (a.severity === "critical" ? -1 : 1));
      setRows(sorted.slice(0, 60));
    }).catch((e) => setErr(String(e)));
  }, []);

  return (
    <AppShell active="/actions" title="Action queue">
      {err && <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{err}</div>}
      <div className="grid gap-3 md:grid-cols-2">
        {(rows ?? []).map((r) => (
          <div key={r.incident_id} className="rounded-xl border border-border bg-card p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <Link href={`/incidents/${r.incident_id}`} className="text-sm font-semibold hover:text-[var(--primary)]">
                  {r.incident_id}
                </Link>
                <p className="mt-0.5 text-xs text-muted-foreground">{r.store_id} · {r.predicted_category}</p>
              </div>
              <span className={"shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium " +
                (r.severity === "critical" ? "bg-red-100 text-red-700"
                  : r.severity === "high" ? "bg-amber-100 text-amber-700"
                  : "bg-muted text-muted-foreground")}>{r.severity}</span>
            </div>
            <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">{r.sample_text}</p>
            <div className="mt-3 flex items-center justify-between text-xs">
              <span>Owner: <span className="font-medium">{r.owner_function}</span></span>
              <Link href={`/incidents/${r.incident_id}`} className="text-[var(--primary)] hover:underline">Open →</Link>
            </div>
          </div>
        ))}
      </div>
    </AppShell>
  );
}
