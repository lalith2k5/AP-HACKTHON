"use client";

import { useState } from "react";
import { endpoints } from "@/lib/api";

const CATEGORIES = [
  "food_safety_or_hygiene","allergen_or_labeling","product_quality_or_freshness",
  "out_of_stock","equipment_or_refrigeration","pricing_or_price_tag_error",
  "checkout_experience","delivery_or_receiving","app_crash_or_bug",
  "staff_misconduct","staff_conduct","queue_or_wait_time",
  "store_cleanliness","product_assortment","other_unclear",
];

export function FlagLabel({ recordId }: { recordId: string }) {
  const [open, setOpen] = useState(false);
  const [action, setAction] = useState<"flag" | "accept" | "remove">("flag");
  const [suggested, setSuggested] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit() {
    setBusy(true); setErr(null);
    try {
      await endpoints.flagLabel(recordId, {
        action,
        suggested_category: suggested,
        reason,
        actor: "reviewer",
      });
      setDone(true);
    } catch (e: any) { setErr(String(e?.message ?? e)); }
    finally { setBusy(false); }
  }

  if (done) return <span className="pill pill-ok">Flagged</span>;

  return (
    <div>
      <button
        className="btn btn-ghost btn-sm"
        onClick={() => setOpen(!open)}
        style={{ padding: "2px 8px", fontSize: 11 }}
      >
        Flag
      </button>
      {open && (
        <div
          style={{
            position: "absolute", zIndex: 50, marginTop: 6,
            background: "var(--bg-raised)", border: "1px solid var(--line)",
            borderRadius: 12, padding: 14, boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
            minWidth: 260,
          }}
        >
          <div className="t-caption" style={{ marginBottom: 8 }}>{recordId}</div>
          <div className="row" style={{ gap: 4, marginBottom: 8 }}>
            {(["flag", "accept", "remove"] as const).map((a) => (
              <button
                key={a}
                onClick={() => setAction(a)}
                className={"btn btn-sm " + (action === a ? "btn-primary" : "btn-secondary")}
                style={{ fontSize: 11, padding: "3px 8px" }}
              >
                {a}
              </button>
            ))}
          </div>
          {action !== "remove" && (
            <select className="select" value={suggested} onChange={(e) => setSuggested(e.target.value)} style={{ width: "100%", marginBottom: 8 }}>
              <option value="">Select category…</option>
              {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          )}
          <input className="input" placeholder="Reason (optional)" value={reason} onChange={(e) => setReason(e.target.value)} />
          <div className="row" style={{ justifyContent: "flex-end", marginTop: 10 }}>
            <button className="btn btn-primary btn-sm" onClick={submit} disabled={busy || (action !== "remove" && !suggested)}>
              {busy ? "…" : "Submit"}
            </button>
          </div>
          {err && <div className="t-caption" style={{ color: "var(--st-critical)", marginTop: 6 }}>{err}</div>}
        </div>
      )}
    </div>
  );
}
