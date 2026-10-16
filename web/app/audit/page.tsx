"use client";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints } from "@/lib/api";

export default function AuditPage() {
  const [rows, setRows] = useState<any[]>([]);
  const [etype, setEtype] = useState("");
  const [actor, setActor] = useState("");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const params: Record<string,string> = {};
    if (etype) params.event_type = etype;
    if (actor) params.actor = actor;
    endpoints.audit(params)
      .then((d: any) => setRows(d.events ?? []))
      .catch((e) => setErr(String(e)));
  }, [etype, actor]);

  return (
    <AppShell active="/audit" title="Audit log">
      <div className="space-y-4">
        <div className="flex flex-wrap gap-3">
          <input placeholder="event_type (optional)" value={etype} onChange={(e) => setEtype(e.target.value)}
            className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm" />
          <input placeholder="actor (optional)" value={actor} onChange={(e) => setActor(e.target.value)}
            className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm" />
        </div>
        {err && <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{err}</div>}
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/40 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr><th className="px-4 py-2.5">When</th><th>Event</th><th>Actor</th><th>Object</th><th>Detail</th></tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-t border-border">
                  <td className="px-4 py-2 whitespace-nowrap text-xs">{r.timestamp ?? r.occurred_at ?? ""}</td>
                  <td className="text-xs">{r.event_type}</td>
                  <td className="text-xs">{r.actor ?? r.actor_id}</td>
                  <td className="text-xs font-mono">{r.object_id ?? ""}</td>
                  <td className="text-xs text-muted-foreground">{r.detail ?? r.reason ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && <p className="p-4 text-sm text-muted-foreground">No events yet.</p>}
        </div>
      </div>
    </AppShell>
  );
}
