"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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

function sevColor(high: number) {
  if (high >= 20) return "#ff3b30";
  if (high >= 10) return "#ff9500";
  if (high >= 3) return "#ffcc00";
  return "#34c759";
}

export default function MapClient() {
  const router = useRouter();
  const [stores, setStores] = useState<StorePoint[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [L, setL] = useState<any>(null);
  const [RL, setRL] = useState<any>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const leaflet = await import("leaflet");
      const reactLeaflet = await import("react-leaflet");
      if (cancelled) return;
      setL(leaflet);
      setRL(reactLeaflet);
      setReady(true);
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    endpoints.mapStores()
      .then((d: any) => setStores(d.stores ?? []))
      .catch((e) => setErr(String(e)));
  }, []);

  const maxCount = Math.max(1, ...stores.map((s) => s.incident_count));

  return (
    <AppShell active="/stores" title="Stores">
      <div className="page-head">
        <div>
          <p>
            {stores.length} stores · {new Set(stores.map((s) => s.region_id)).size} regions ·
            click a dot to open the store
          </p>
        </div>
        <Link href="/stores" className="btn btn-secondary btn-sm">List view</Link>
      </div>

      {err && <div className="card" style={{ color: "var(--st-critical)" }}>{err}</div>}

      <div
        className="card"
        style={{
          padding: 0,
          overflow: "hidden",
          position: "relative",
          borderRadius: 16,
        }}
      >
        <div style={{ height: "70vh", minHeight: 520, position: "relative", background: "#eef2f6" }}>
          {ready && L && RL && (
            <MapInner
              L={L}
              RL={RL}
              stores={stores}
              maxCount={maxCount}
              onMarkerClick={(id: string) => router.push(`/stores/${id}`)}
            />
          )}
          {!ready && (
            <div
              style={{
                position: "absolute", inset: 0,
                display: "flex", alignItems: "center", justifyContent: "center",
                color: "var(--fg-3)", fontSize: 13,
              }}
            >
              Loading map…
            </div>
          )}
        </div>

        {/* Legend — Apple-style floating chip */}
        <div
          style={{
            position: "absolute",
            bottom: 16,
            left: 16,
            padding: "10px 14px",
            borderRadius: 12,
            background: "rgba(255,255,255,0.86)",
            backdropFilter: "blur(24px) saturate(180%)",
            WebkitBackdropFilter: "blur(24px) saturate(180%)",
            border: "1px solid rgba(0,0,0,0.06)",
            boxShadow: "0 6px 24px rgba(0,0,0,0.10)",
            fontSize: 11,
            zIndex: 500,
            pointerEvents: "none",
            color: "#1d1d1f",
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: 6, letterSpacing: "-0.01em" }}>
            High severity
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {[
              { color: "#34c759", label: "0-2" },
              { color: "#ffcc00", label: "3-9" },
              { color: "#ff9500", label: "10-19" },
              { color: "#ff3b30", label: "20+" },
            ].map((l) => (
              <div key={l.label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span
                  style={{
                    display: "inline-block", width: 9, height: 9, borderRadius: "50%",
                    background: l.color, border: "1.5px solid rgba(255,255,255,0.9)",
                    boxShadow: "0 1px 2px rgba(0,0,0,0.15)",
                  }}
                />
                <span>{l.label}</span>
              </div>
            ))}
          </div>
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

function MapInner({
  L, RL, stores, maxCount, onMarkerClick,
}: {
  L: any; RL: any; stores: StorePoint[]; maxCount: number;
  onMarkerClick: (id: string) => void;
}) {
  const { MapContainer, TileLayer, CircleMarker, Tooltip, LayersControl, ScaleControl, useMap } = RL;

  return (
    <MapContainer
      center={[22.9734, 78.6569]}
      zoom={5}
      minZoom={4}
      maxZoom={18}
      scrollWheelZoom={true}
      zoomControl={true}
      style={{ height: "100%", width: "100%", background: "#eef2f6" }}
      attributionControl={true}
    >
      <LayersControl position="topright">
        {/* Apple-Maps-like default */}
        <LayersControl.BaseLayer checked name="Voyager (default)">
          <TileLayer
            attribution='&copy; <a href="https://carto.com/attributions">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            subdomains="abcd"
            maxZoom={19}
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Satellite">
          <TileLayer
            attribution="Tiles &copy; Esri"
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            maxZoom={19}
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Streets">
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Minimal (Positron)">
          <TileLayer
            attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            subdomains="abcd"
            maxZoom={19}
          />
        </LayersControl.BaseLayer>
      </LayersControl>

      <ScaleControl position="bottomright" imperial={false} />

      {stores.map((s) => {
        const size = 8 + (s.incident_count / maxCount) * 12;
        const color = sevColor(s.high_severity_count);
        return (
          <CircleMarker
            key={s.store_id}
            center={[s.lat, s.lng]}
            radius={size}
            pathOptions={{
              color: "#ffffff",
              weight: 2.5,
              fillColor: color,
              fillOpacity: 1,
            }}
            eventHandlers={{
              click: () => onMarkerClick(s.store_id),
            }}
          >
            <Tooltip direction="top" offset={[0, -8]} opacity={1}>
              <div style={{ fontSize: 12, lineHeight: 1.45, color: "#1d1d1f" }}>
                <div style={{ fontWeight: 700 }}>{s.store_id}</div>
                <div style={{ color: "#6e6e73" }}>
                  {s.store_name} · {s.city}
                </div>
                <div style={{ marginTop: 4 }}>
                  <strong>{s.incident_count}</strong> incidents ·{" "}
                  <span style={{ color }}>
                    <strong>{s.high_severity_count}</strong> high
                  </span>
                </div>
              </div>
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
