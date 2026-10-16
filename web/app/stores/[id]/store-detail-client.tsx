"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { endpoints } from "@/lib/api";

export default function StoreDetailClient() {
  const params = useParams();
  const id = String(params?.id ?? "");
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { if (id) endpoints.store(id).then(setData).catch((e) => setErr(String(e))); }, [id]);

  return (
    <AppShell active="/stores" title={`Store ${id}`}>
      {err && <div className="rounded-2xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{err}</div>}
      {data && (
        <div className="space-y-10">
          <div className="card-soft p-6">
            <h2 className="text-lg font-semibold">{data.store.store_name ?? id}</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {data.store.city} · Region {data.store.region_id} · {data.store.store_format ?? "n/a"}
            </p>
            <p className="mt-2 text-sm">
              Footfall: {data.store.weekly_footfall ?? "n/a"} · Incidents: {data.incident_count}
            </p>
          </div>
          <div className="card-soft overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-[color-mix(in_oklch,var(--foreground),transparent_96%)] text-left text-xs uppercase tracking-wide text-[var(--muted-foreground)]">
                <tr><th className="px-4 py-2.5">Incident</th><th>Category</th><th>Severity</th><th>Owner</th><th>Records</th></tr>
              </thead>
              <tbody>
                {(data.incidents ?? []).map((r: any) => (
                  <tr key={r.incident_id} className="border-t border-[var(--border)]">
                    <td className="px-4 py-2">
                      <Link href={`/incidents/${r.incident_id}`} className="hover:text-[var(--primary)]">{r.incident_id}</Link>
                    </td>
                    <td>{r.predicted_category}</td>
                    <td>{r.severity}</td>
                    <td>{r.owner_function}</td>
                    <td>{r.record_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </AppShell>
  );
}
