"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints } from "@/lib/api";

type Store = { store_id:string; store_name:string; region_id:string; city:string; store_format:string;
  weekly_footfall:number|null; has_denominator:boolean; incident_count:number; alert_count:number; };

export default function StoresPage() {
  const [rows, setRows] = useState<Store[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { endpoints.stores().then((d: any) => setRows(d.stores)).catch((e) => setErr(String(e))); }, []);

  return (
    <AppShell active="/stores" title="Stores">
      {err && <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{err}</div>}
      {!rows && !err && <p className="text-sm text-muted-foreground">Loading...</p>}
      {rows && (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/40 text-left text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-2.5">Store</th>
                <th>Region</th>
                <th>Format</th>
                <th>Footfall</th>
                <th className="text-right">Incidents</th>
                <th className="text-right pr-4">Alerts</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((s) => (
                <tr key={s.store_id} className="border-t border-border hover:bg-muted/30">
                  <td className="px-4 py-2">
                    <Link href={`/stores/${s.store_id}`} className="font-medium hover:text-[var(--primary)]">{s.store_id}</Link>
                    <div className="text-xs text-muted-foreground">{s.store_name}</div>
                  </td>
                  <td>{s.region_id}</td>
                  <td className="text-xs text-muted-foreground">{s.store_format}</td>
                  <td className="text-xs">{s.weekly_footfall ?? "n/a"}</td>
                  <td className="text-right">{s.incident_count}</td>
                  <td className="text-right pr-4">{s.alert_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  );
}
