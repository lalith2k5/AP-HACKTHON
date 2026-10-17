"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { endpoints } from "@/lib/api";
import { AnimatedNumber } from "@/components/animated-number";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    endpoints.alerts()
      .then((d: any) => setAlerts(d.items ?? d.alerts ?? d))
      .catch((e) => setErr(String(e)));
  }, []);

  const open = alerts?.filter((a) => a.status === "open").length ?? 0;
  const mandatory = alerts?.filter((a) => a.trigger_type === "mandatory_policy").length ?? 0;

  return (
    <AppShell active="/alerts" title="Alerts">
      <div className="fade-up" style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 32, fontWeight: 700, letterSpacing: "-0.03em", margin: 0 }}>
          Alerts
        </h1>
        <p style={{ marginTop: 8, fontSize: 15, color: "var(--fg-2)" }}>
          Time-sensitive escalations. Safety signals bypass trend volume.
        </p>
      </div>

      {err && <div className="card" style={{ color: "var(--st-critical)" }}>{err}</div>}

      {/* Summary strip */}
      <div className="fade-up" style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 28, animationDelay: "80ms" }}>
        <div className="kpi-tile">
          <div className="kpi-label">Total alerts</div>
          <div className="kpi-number-sm">
            <AnimatedNumber value={alerts?.length ?? 0} />
          </div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-label">Open</div>
          <div className="kpi-number-sm" style={{ color: "#ff9500" }}>
            <AnimatedNumber value={open} />
          </div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-label">Mandatory</div>
          <div className="kpi-number-sm" style={{ color: "#ff3b30" }}>
            <AnimatedNumber value={mandatory} />
          </div>
        </div>
      </div>

      {/* Alert list */}
      {alerts && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {alerts.slice(0, 50).map((a, i) => (
            <div
              key={a.alert_id || i}
              className="kpi-tile fade-up"
              style={{
                padding: "18px 24px",
                animationDelay: `${Math.min(i * 30, 300)}ms`,
                borderLeft: `4px solid ${a.trigger_type === "mandatory_policy" ? "#ff3b30" : "#ff9500"}`,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: "var(--fg)", letterSpacing: "-0.01em" }}>
                    {a.reason || "Alert"}
                  </div>
                  <div style={{ fontSize: 13, color: "var(--fg-2)", marginTop: 4 }}>
                    {a.alert_id} · {a.trigger_type} · {a.store_id}
                  </div>
                </div>
                <span
                  style={{
                    padding: "4px 10px",
                    borderRadius: 999,
                    fontSize: 11,
                    fontWeight: 700,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    background: a.trigger_type === "mandatory_policy" ? "rgba(255,59,48,0.15)" : "rgba(255,149,0,0.15)",
                    color: a.trigger_type === "mandatory_policy" ? "#ff3b30" : "#ff9500",
                  }}
                >
                  {a.trigger_type === "mandatory_policy" ? "MANDATORY" : a.severity}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </AppShell>
  );
}
