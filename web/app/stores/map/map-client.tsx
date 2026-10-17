"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
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

const LAYERS = {
  Light:
    "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
  Streets:
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
  Satellite:
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  Topographic:
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
} as const;

type LayerName = keyof typeof LAYERS;

export default function MapClient() {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const layerRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const [stores, setStores] = useState<StorePoint[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [layer, setLayer] = useState<LayerName>("Light");

  // Load stores
  useEffect(() => {
    endpoints.mapStores()
      .then((d: any) => setStores(d.stores ?? []))
      .catch((e) => setErr(String(e)));
  }, []);

  // Init Leaflet directly (no react-leaflet). Leaflet gets the fully
  // laid-out DOM node, so no invalidateSize race.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!containerRef.current || mapRef.current) return;
      const L = (await import("leaflet")).default;
      if (cancelled || !containerRef.current) return;

      // Hard reset: wipe container in case of double-init in StrictMode
      containerRef.current.innerHTML = "";

      const map = L.map(containerRef.current, {
        center: [22.9734, 78.6569],
        zoom: 5,
        minZoom: 4,
        maxZoom: 16,
        scrollWheelZoom: true,
        zoomControl: true,
        attributionControl: true,
      });

      const tileLayer = L.tileLayer(LAYERS.Light, {
        attribution:
          "Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors",
        maxZoom: 16,
      }).addTo(map);

      L.control.scale({ imperial: false, position: "bottomright" }).addTo(map);

      // Base-layer switcher (top-right)
      const layersControl = L.control.layers(
        Object.fromEntries(
          Object.entries(LAYERS).map(([name, url]) => [
            name,
            L.tileLayer(url, { maxZoom: 16 }),
          ]),
        ),
        {},
        { position: "topright", collapsed: false },
      );
      layersControl.addTo(map);

      mapRef.current = map;
      layerRef.current = tileLayer;
    })();

    return () => {
      cancelled = true;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
      markersRef.current = [];
    };
  }, []);

  // Update markers whenever stores change
  useEffect(() => {
    (async () => {
      if (!mapRef.current) return;
      const L = (await import("leaflet")).default;

      // Clear existing markers
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];

      const maxCount = Math.max(1, ...stores.map((s) => s.incident_count));

      stores.forEach((s) => {
        const size = 8 + (s.incident_count / maxCount) * 12;
        const color = sevColor(s.high_severity_count);
        const marker = L.circleMarker([s.lat, s.lng], {
          radius: size,
          color: "#ffffff",
          weight: 2.5,
          fillColor: color,
          fillOpacity: 1,
        })
          .bindTooltip(
            `<div style="font-size:12px;line-height:1.45;color:#1d1d1f">
               <div style="font-weight:700">${s.store_id}</div>
               <div style="color:#6e6e73">${s.store_name} · ${s.city}</div>
               <div style="margin-top:4px">
                 <strong>${s.incident_count}</strong> incidents ·
                 <span style="color:${color}"><strong>${s.high_severity_count}</strong> high</span>
               </div>
             </div>`,
            { direction: "top", offset: [0, -8], opacity: 1 },
          )
          .on("click", () => router.push(`/stores/${s.store_id}`))
          .addTo(mapRef.current);
        markersRef.current.push(marker);
      });
    })();
  }, [stores, router]);

  // Swap base layer when user picks one
  useEffect(() => {
    (async () => {
      if (!mapRef.current || !layerRef.current) return;
      const L = (await import("leaflet")).default;
      layerRef.current.setUrl(LAYERS[layer]);
    })();
  }, [layer]);

  return (
    <AppShell active="/stores" title="Stores">
      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      />

      <div className="tabs" style={{ marginBottom: 24 }}>
        <Link href="/stores" className="tab">List</Link>
        <Link href="/stores/map" className="tab is-active">Map</Link>
      </div>

      <div className="page-head">
        <div>
          <p>
            {stores.length} stores · {new Set(stores.map((s) => s.region_id)).size} regions ·
            click a dot to open the store
          </p>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {(["Light", "Streets", "Satellite", "Topographic"] as LayerName[]).map((name) => (
            <button
              key={name}
              onClick={() => setLayer(name)}
              className={"btn btn-sm " + (layer === name ? "btn-primary" : "btn-secondary")}
            >
              {name}
            </button>
          ))}
        </div>
      </div>

      {err && <div className="card" style={{ color: "var(--st-critical)" }}>{err}</div>}

      <div className="card" style={{ padding: 0, overflow: "hidden", position: "relative" }}>
        <div
          ref={containerRef}
          id="storesignal-map"
          style={{
            width: "100%",
            height: "620px",
            background: "#eef2f6",
          }}
        />

        {/* Legend */}
        <div
          style={{
            position: "absolute",
            bottom: 16,
            left: 16,
            padding: "10px 14px",
            borderRadius: 12,
            background: "rgba(255,255,255,0.9)",
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
                    display: "inline-block",
                    width: 9, height: 9, borderRadius: "50%",
                    background: l.color,
                    border: "1.5px solid rgba(255,255,255,0.9)",
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
