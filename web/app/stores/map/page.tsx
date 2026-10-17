"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints } from "@/lib/api";

type StorePoint = {
  store_id: string;
  store_name: string;
  region_id: string;
  city: string;
  lat: number;
  lng: number;
  incident_count: number;
  high_severity_count: number;
};

export default function StoreMapPage() {
  const [stores, setStores] = useState<StorePoint[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);

  useEffect(() => {
    endpoints.mapStores()
      .then((d: any) => setStores(d.stores ?? []))
      .catch((e) => setErr(String(e)));
  }, []);

  const maxCount = Math.max(1, ...stores.map((s) => s.incident_count));

  // Bounding box for the map (India)
  const minLat = 8, maxLat = 32, minLng = 68, maxLng = 92;
  const project = (lat: number, lng: number) => ({
    x: ((lng - minLng) / (maxLng - minLng)) * 100,
    y: 100 - ((lat - minLat) / (maxLat - minLat)) * 100,
  });

  return (
    <AppShell active="/stores" title="Store impact map">
      <div className="page-head">
        <div>
          <h1>Store impact map</h1>
          <p>Each dot is a store. Size scales with incident count. Coordinates derived from region centers.</p>
        </div>
        <Link href="/stores" className="btn btn-secondary">List view</Link>
      </div>

      {err && <div className="card" style={{ color: "var(--st-critical)" }}>{err}</div>}

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <div
          style={{
            position: "relative",
            width: "100%",
            aspectRatio: "4 / 3",
            background:
              "radial-gradient(50% 60% at 50% 40%, color-mix(in oklab, var(--accent) 4%, transparent), transparent 70%), var(--bg-sunken)",
          }}
        >
          {stores.map((s) => {
            const { x, y } = project(s.lat, s.lng);
            const size = 8 + (s.incident_count / maxCount) * 26;
            const sev = s.high_severity_count > 3;
            return (
              <Link
                key={s.store_id}
                href={`/stores/${s.store_id}`}
                onMouseEnter={() => setHover(s.store_id)}
                onMouseLeave={() => setHover(null)}
                style={{
                  position: "absolute",
                  left: `${x}%`,
                  top: `${y}%`,
                  transform: "translate(-50%, -50%)",
                  width: size,
                  height: size,
                  borderRadius: "50%",
                  background: sev ? "var(--st-critical)" : "var(--accent)",
                  opacity: hover && hover !== s.store_id ? 0.4 : 0.85,
                  boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
                  transition: "opacity 200ms, transform 200ms",
                  zIndex: hover === s.store_id ? 10 : 1,
                }}
                title={`${s.store_id} — ${s.store_name} — ${s.incident_count} incidents`}
              />
            );
          })}
          {hover && (() => {
            const s = stores.find((x) => x.store_id === hover);
            if (!s) return null;
            return (
              <div
                style={{
                  position: "absolute",
                  bottom: 16,
                  left: 16,
                  padding: "10px 14px",
                  borderRadius: 10,
                  background: "var(--bg-raised)",
                  border: "1px solid var(--line)",
                  boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
                  fontSize: 12,
                }}
              >
                <div style={{ fontWeight: 600 }}>{s.store_id} · {s.store_name}</div>
                <div className="muted">{s.city} · {s.incident_count} incidents · {s.high_severity_count} high</div>
              </div>
            );
          })()}
        </div>
      </div>

      <section style={{ marginTop: 24 }}>
        <h2 className="t-heading" style={{ marginBottom: 12 }}>Stores ranked by impact</h2>
        <div className="card card-flat">
          <table className="table">
            <thead>
              <tr><th>Store</th><th>City</th><th>Incidents</th><th>High severity</th></tr>
            </thead>
            <tbody>
              {[...stores].sort((a, b) => b.incident_count - a.incident_count).slice(0, 12).map((s) => (
                <tr key={s.store_id}>
                  <td><Link href={`/stores/${s.store_id}`} style={{ color: "var(--accent)" }}>{s.store_id}</Link></td>
                  <td>{s.city}</td>
                  <td>{s.incident_count}</td>
                  <td>{s.high_severity_count > 3 ? <span className="pill pill-critical">{s.high_severity_count}</span> : s.high_severity_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </AppShell>
  );
}
