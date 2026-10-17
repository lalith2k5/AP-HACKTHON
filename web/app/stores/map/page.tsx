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

const REGION_CENTROIDS: Record<string, { lat: number; lng: number }> = {
  DEL: { lat: 28.61, lng: 77.21 },
  MUM: { lat: 19.08, lng: 72.88 },
  BLR: { lat: 12.97, lng: 77.59 },
  HYD: { lat: 17.38, lng: 78.49 },
  CHN: { lat: 13.08, lng: 80.27 },
};

const INDIA_PATH =
  "M 35,7 L 42,9 L 48,11 L 55,12 L 63,12 L 70,14 L 74,16 L 79,17 L 83,19 L 86,20 L 88,22 L 92,25 L 96,28 L 97,31 L 94,34 L 92,37 L 90,40 L 88,44 L 88,48 L 84,50 L 82,54 L 80,60 L 78,66 L 77,72 L 78,78 L 78,84 L 76,90 L 73,93 L 68,93 L 60,93 L 50,93 L 44,93 L 40,91 L 36,87 L 33,82 L 30,77 L 27,72 L 24,67 L 21,62 L 18,57 L 15,53 L 12,50 L 8,48 L 4,46 L 3,43 L 5,40 L 9,38 L 13,36 L 17,32 L 20,28 L 22,23 L 25,17 L 28,12 L 32,9 Z";

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

  return (
    <AppShell active="/stores" title="Store impact map">
      <div className="page-head">
        <div>
          <p>
            {stores.length} stores · {new Set(stores.map((s) => s.region_id)).size} regions ·
            color = high-severity count · size = total incidents
          </p>
        </div>
        <Link href="/stores" className="btn btn-secondary btn-sm">List view</Link>
      </div>

      {err && <div className="card" style={{ color: "var(--st-critical)" }}>{err}</div>}

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <div
          style={{
            position: "relative",
            width: "100%",
            aspectRatio: "5 / 4",
            background:
              "linear-gradient(180deg, #dbeafe 0%, #e0e7ff 55%, #ede9fe 100%)",
            overflow: "hidden",
          }}
        >
          {/* Base SVG map */}
          <svg
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
          >
            <defs>
              <linearGradient id="land" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f1f5f9" />
                <stop offset="100%" stopColor="#e2e8f0" />
              </linearGradient>
              <filter id="landShadow" x="-10%" y="-10%" width="120%" height="120%">
                <feDropShadow dx="0" dy="0.8" stdDeviation="0.6" floodColor="#0f172a" floodOpacity="0.12" />
              </filter>
              <pattern id="oceanDots" width="3" height="3" patternUnits="userSpaceOnUse">
                <circle cx="1.5" cy="1.5" r="0.15" fill="#94a3b8" opacity="0.3" />
              </pattern>
            </defs>

            {/* Ocean texture */}
            <rect width="100" height="100" fill="url(#oceanDots)" />

            {/* India landmass */}
            <path
              d={INDIA_PATH}
              fill="url(#land)"
              stroke="#64748b"
              strokeWidth="0.3"
              strokeLinejoin="round"
              filter="url(#landShadow)"
            />

            {/* Region cluster outlines */}
            {Object.entries(REGION_CENTROIDS).map(([code, c]) => {
              const { x, y } = project(c.lat, c.lng);
              return (
                <circle
                  key={code}
                  cx={x}
                  cy={y}
                  r="1.3"
                  fill="none"
                  stroke="#94a3b8"
                  strokeWidth="0.15"
                  strokeDasharray="0.6 0.6"
                  opacity="0.5"
                />
              );
            })}
          </svg>

          {/* Region labels */}
          {Object.entries(REGION_CENTROIDS).map(([code, c]) => {
            const { x, y } = project(c.lat, c.lng);
            return (
              <div
                key={code}
                style={{
                  position: "absolute",
                  left: `${x}%`,
                  top: `${y + 3.2}%`,
                  transform: "translate(-50%, 0)",
                  fontSize: 10,
                  fontWeight: 700,
                  color: "#475569",
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  pointerEvents: "none",
                  whiteSpace: "nowrap",
                  textShadow: "0 1px 2px rgba(255,255,255,0.9)",
                }}
              >
                {REGION_LABEL[code] ?? code}
              </div>
            );
          })}

          {/* Store dots */}
          {stores.map((s) => {
            const { x, y } = project(s.lat, s.lng);
            const size = 7 + (s.incident_count / maxCount) * 16;
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
                  transform: `translate(-50%, -50%) scale(${active ? 1.5 : 1})`,
                  width: size,
                  height: size,
                  borderRadius: "50%",
                  background: sevColor(s.high_severity_count),
                  border: "1.5px solid rgba(255,255,255,0.95)",
                  opacity: dim ? 0.25 : 1,
                  boxShadow: active
                    ? "0 6px 18px rgba(15,23,42,0.30)"
                    : "0 1px 3px rgba(15,23,42,0.20)",
                  transition: "transform 200ms var(--ease), opacity 200ms var(--ease)",
                  zIndex: active ? 20 : 1,
                }}
                title={`${s.store_id} · ${s.store_name}`}
              />
            );
          })}

          {/* Tooltip */}
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
                  transform: "translate(-50%, calc(-100% - 14px))",
                  padding: "10px 14px",
                  borderRadius: 12,
                  background: "rgba(255,255,255,0.96)",
                  backdropFilter: "blur(20px)",
                  border: "1px solid rgba(15,23,42,0.08)",
                  boxShadow: "0 12px 32px rgba(15,23,42,0.18)",
                  fontSize: 12,
                  pointerEvents: "none",
                  zIndex: 30,
                  whiteSpace: "nowrap",
                }}
              >
                <div style={{ fontWeight: 700, color: "#0f172a" }}>{s.store_id}</div>
                <div style={{ color: "#64748b", marginTop: 2 }}>
                  {s.store_name} · {s.city}
                </div>
                <div style={{ marginTop: 6, display: "flex", gap: 12 }}>
                  <span style={{ color: "#0f172a" }}>
                    <strong>{s.incident_count}</strong> incidents
                  </span>
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
              <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", background: l.color, border: "1.5px solid rgba(255,255,255,0.9)" }} />
              {l.label}
            </span>
          ))}
          <span style={{ marginLeft: "auto", color: "var(--fg-3)" }}>Dot size ∝ total incidents</span>
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
                    <span className="pill" style={{
                      background: `color-mix(in oklab, ${sevColor(s.high_severity_count)} 14%, transparent)`,
                      color: sevColor(s.high_severity_count),
                    }}>
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
