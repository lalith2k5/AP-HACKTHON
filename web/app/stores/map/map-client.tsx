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

function sevColor(high: number) {
  if (high >= 20) return "#d70015";
  if (high >= 10) return "#c93400";
  if (high >= 3) return "#b25000";
  return "#00875a";
}

export default function MapClient() {
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
      // Fix default marker icons
      delete (leaflet.Icon.Default.prototype as any)._getIconUrl;
      leaflet.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });
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

  if (!ready || !L || !RL) {
    return (
      <AppShell active="/stores" title="Store impact map">
        <div className="card" style={{ padding: 60, textAlign: "center" }}>
          <div className="t-caption">Loading map…</div>
        </div>
      </AppShell>
    );
  }

  const { MapContainer, TileLayer, CircleMarker, Tooltip, LayersControl, ScaleControl } = RL;

  return (
    <AppShell active="/stores" title="Store impact map">
      {/* Leaflet CSS */}
      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      />

      <div className="page-head">
        <div>
          <p>
            {stores.length} stores · {new Set(stores.map((s) => s.region_id)).size} regions ·
            click a dot to open the store · toggle layers top-right
          </p>
        </div>
        <Link href="/stores" className="btn btn-secondary btn-sm">List view</Link>
      </div>

      {err && <div className="card" style={{ color: "var(--st-critical)" }}>{err}</div>}

      <div
        className="card"
        style={{ padding: 0, overflow: "hidden", position: "relative" }}
      >
        <div style={{ height: "68vh", minHeight: 480, position: "relative" }}>
          <MapContainer
            center={[22.9734, 78.6569]}
            zoom={5}
            style={{ height: "100%", width: "100%" }}
            scrollWheelZoom={true}
            worldCopyJump={false}
          >
            <LayersControl position="topright">
              <LayersControl.BaseLayer checked name="Satellite">
                <TileLayer
                  attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                  url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                  maxZoom={19}
                />
              </LayersControl.BaseLayer>
              <LayersControl.BaseLayer name="Streets">
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  maxZoom={19}
                />
              </LayersControl.BaseLayer>
              <LayersControl.BaseLayer name="Topographic">
                <TileLayer
                  attribution='Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ'
                  url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
                  maxZoom={19}
                />
              </LayersControl.BaseLayer>
              <LayersControl.BaseLayer name="Light (Positron)">
                <TileLayer
                  attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
                  url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                  maxZoom={19}
                />
              </LayersControl.BaseLayer>
            </LayersControl>

            <ScaleControl position="bottomleft" imperial={false} />

            {stores.map((s) => {
              const size = 6 + (s.incident_count / maxCount) * 14;
              const color = sevColor(s.high_severity_count);
              return (
                <CircleMarker
                  key={s.store_id}
                  center={[s.lat, s.lng]}
                  radius={size}
                  pathOptions={{
                    color: "#ffffff",
                    weight: 1.5,
                    fillColor: color,
                    fillOpacity: 0.9,
                  }}
                >
                  <Tooltip direction="top" offset={[0, -6]} opacity={1}>
                    <div style={{ fontSize: 12, lineHeight: 1.4 }}>
                      <div style={{ fontWeight: 700 }}>{s.store_id}</div>
                      <div style={{ color: "#64748b" }}>
                        {s.store_name} · {s.city}
                      </div>
                      <div style={{ marginTop: 4 }}>
                        <strong>{s.incident_count}</strong> incidents ·{" "}
                        <span style={{ color }}>
                          <strong>{s.high_severity_count}</strong> high
                        </span>
                      </div>
                      <div style={{ marginTop: 4, color: "#0ea5e9" }}>
                        Click to open →
                      </div>
                    </div>
                  </Tooltip>
                </CircleMarker>
              );
            })}
          </MapContainer>

          {/* Click-to-open on marker — leaflet needs an event handler */}
          <MarkerClickBridge stores={stores} />
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
            { color: "#00875a", label: "0-2" },
            { color: "#b25000", label: "3-9" },
            { color: "#c93400", label: "10-19" },
            { color: "#d70015", label: "20+" },
          ].map((l) => (
            <span
              key={l.label}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                color: "var(--fg-2)",
              }}
            >
              <span
                style={{
                  display: "inline-block",
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  background: l.color,
                  border: "1.5px solid rgba(255,255,255,0.9)",
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

/* Small bridge so clicking a leaflet marker navigates.
   react-leaflet markers do not accept onClick={navigate} as a prop,
   so we add a document-level listener that reads the marker's data. */
function MarkerClickBridge({ stores }: { stores: StorePoint[] }) {
  useEffect(() => {
    function onClick(e: MouseEvent) {
      const el = (e.target as HTMLElement).closest(".leaflet-marker-icon, .leaflet-interactive");
      if (!el) return;
      const label = el.getAttribute("data-store-id");
      if (label) window.location.href = `/stores/${label}`;
    }
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, [stores]);
  return null;
}
