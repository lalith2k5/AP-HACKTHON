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

const INDIA_BOUNDS = { minLat: 6, maxLat: 37, minLng: 67, maxLng: 98 };
const REGION_LABEL: Record<string, string> = {
  DEL: "Delhi NCR", MUM: "Mumbai", BLR: "Bangalore",
  HYD: "Hyderabad", CHN: "Chennai",
};

function sevColor(high: number) {
  if (high >= 20) return "var(--st-critical)";
  if (high >= 10) return "var(--st-high)";
  if (high >= 3) return "var(--st-medium)";
  return "var(--st-ok)";
}

export default function StoreMapPage() {
  const [stores, setStores] = useState<StorePoint[]>([]);
  const [hover, setHover] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    endpoints.mapStores()
      .then((d: any) => setStores(d.stores ?? []))
      .catch((e) => setErr(String(e)));
  }, []);

  const maxCount = Math.max(1, ...stores.map((s) => s.incident_count));
  const project = (lat: number, lng: number) => ({
    x: ((lng - INDIA_BOUNDS.minLng) / (INDIA_BOUNDS.maxLng - INDIA_BOUNDS.minLng)) * 100,
    y: 100 - ((lat - INDIA_BOUNDS.minLat) / (INDIA_BOUNDS.maxLat - INDIA_BOUNDS.minLat)) * 100,
  });

  const total = stores.length;
  const byRegion = stores.reduce<Record<string, number>>((acc, s) => {
    acc[s.region_id] = (acc[s.region_id] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <AppShell active="/stores" title="Store impact map">
      <div className="page-head">
        <div>
          <p>
            {total} stores across {Object.keys(byRegion).length} regions.
            Dot color reflects high-severity incident count. Size reflects total incidents.
          </p>
        </div>
        <Link href="/stores" className="btn btn-secondary btn-sm">List view</Link>
      </div>

      {err && <div className="card" style={{ color: "var(--st-critical)" }}>{err}</div>}

      <div className="card" style={{ padding: 0, overflow: "hidden", position: "relative" }}>
        {/* Map canvas */}
        <div
          style={{
            position: "relative",
            width: "100%",
            aspectRatio: "5 / 4",
            background:
              "linear-gradient(180deg, color-mix(in oklab, var(--accent) 5%, transparent) 0%, transparent 60%), var(--bg-sunken)",
            overflow: "hidden",
          }}
        >
          {/* Subtle grid */}
          <svg
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            style={{ position: "absolute", inset: 0, width: "100%", height: "100%", opacity: 0.35 }}
          >
            <defs>
              <pattern id="grid" width="5" height="5" patternUnits="userSpaceOnUse">
                <path d="M 5 0 L 0 0 0 5" fill="none" stroke="var(--line-soft)" strokeWidth="0.15" />
              </pattern>
            </defs>
            <rect width="100" height="100" fill="url(#grid)" />
          </svg>

          {/* Region labels */}
          {Object.entries({
            DEL: { lat: 28.61, lng: 77.21 },
            MUM: { lat: 19.08, lng: 72.88 },
            BLR: { lat: 12.97, lng: 77.59 },
            HYD: { lat: 17.38, lng: 78.49 },
            CHN: { lat: 13.08, lng: 80.27 },
          }).map(([code, c]) => {
            const { x, y } = project(c.lat, c.lng);
            return (
              <div
                key={code}
                style={{
                  position: "absolute",
                  left: `${x}%`,
                  top: `${y + 6}%`,
                  transform: "translate(-50%, 0)",
                  fontSize: 11,
                  fontWeight: 600,
                  color: "var(--fg-3)",
                  letterSpacing: "0.06em",
                  textTransform: "uppercase",
                  pointerEvents: "none",
                  whiteSpace: "nowrap",
                }}
              >
                {REGION_LABEL[code] ?? code}
              </div>
            );
          })}

          {/* Store dots */}
          {stores.map((s) => {
            const { x, y } = project(s.lat, s.lng);
            const size = 8 + (s.incident_count / maxCount) * 18;
            const active = hover === s.store_id;
            const dim = hover && !active;
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
                  transform: `translate(-50%, -50%) scale(${active ? 1.35 : 1})`,
                  width: size,
                  height: size,
                  borderRadius: "50%",
                  background: sevColor(s.high_severity_count),
                  border: "2px solid var(--bg)",
                  opacity: dim ? 0.25 : 1,
                  boxShadow: active
                    ? "0 4px 16px rgba(0,0,0,0.18)"
                    : "0 1px 3px rgba(0,0,0,0.10)",
                  transition: "transform 200ms var(--ease), opacity 200ms var(--ease)",
                  zIndex: active ? 20 : 1,
                }}
                title={`${s.store_id} · ${s.store_name}`}
              />
            );
          })}

          {/* Hover tooltip */}
          {hover && (() => {
            const s = stores.find((x) => x.store_id === hover);
            if (!s) return null;
            const { x, y } = project(s.lat, s.lng);
            return (
              <div
                style={{
                  position: "absolute",
                  left: `${x}%`,
                  top: `${y}%`,
                  transform: "translate(-50%, calc(-100% - 12px))",
                  padding: "10px 14px",
                  borderRadius: 12,
                  background: "var(--bg-raised)",
                  border: "1px solid var(--line)",
                  boxShadow: "0 8px 24px rgba(0,0,0,0.10)",
                  fontSize: 12,
                  pointerEvents: "none",
                  zIndex: 30,
                  whiteSpace: "nowrap",
                }}
              >
                <div style={{ fontWeight: 600 }}>{s.store_id}</div>
                <div className="muted" style={{ marginTop: 2 }}>
                  {s.store_name} · {s.city}
                </div>
                <div style={{ marginTop: 6, display: "flex", gap: 10 }}>
                  <span><strong>{s.incident_count}</strong> incidents</span>
                  <span style={{ color: sevColor(s.high_severity_count) }}>
                    <strong>{s.high_severity_count}</strong> high
                  </span>
                </div>
              </div>
            );
          })()}
        </div>

        {/* Legend */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 20,
            padding: "14px 20px",
            borderTop: "1px solid var(--line-soft)",
            fontSize: 11,
            flexWrap: "wrap",
          }}
        >
          <span className="t-micro" style={{ margin: 0 }}>High severity count</span>
          {[
            { color: "var(--st-ok)", label: "0-2" },
            { color: "var(--st-medium)", label: "3-9" },
            { color: "var(--st-high)", label: "10-19" },
            { color: "var(--st-critical)", label: "20+" },
          ].map((l) => (
            <span key={l.label} style={{ display: "inline-flex", alignItems: "center", gap: 6, color: "var(--fg-2)" }}>
              <span
                style={{
                  display: "inline-block",
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  background: l.color,
                  border: "1.5px solid var(--bg)",
                }}
              />
              {l.label}
            </span>
          ))}
          <span style={{ marginLeft: "auto", color: "var(--fg-3)" }}>
            Dot size ∝ total incidents
          </span>
        </div>
      </div>

      <section style={{ marginTop: 24 }}>
        <h2 className="t-heading" style={{ marginBottom: 12 }}>Top 12 stores by incident volume</h2>
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
                  <td>
                    <span
                      className="pill"
                      style={{
                        background: `color-mix(in oklab, ${sevColor(s.high_severity_count)} 14%, transparent)`,
                        color: sevColor(s.high_severity_count),
                      }}
                    >
                      {s.high_severity_count}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </AppShell>
  );
}
