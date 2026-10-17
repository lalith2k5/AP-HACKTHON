"use client";

import { useState } from "react";
import { endpoints } from "@/lib/api";

export function MergeSplitDialog({
  incidentId,
  onDone,
}: {
  incidentId: string;
  onDone: () => void;
}) {
  const [mode, setMode] = useState<"merge" | "split" | null>(null);
  const [target, setTarget] = useState("");
  const [sourcesText, setSourcesText] = useState("");
  const [recordIds, setRecordIds] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  async function doMerge() {
    setErr(null); setBusy(true);
    try {
      const sources = sourcesText.split(/[\s,]+/).filter(Boolean);
      await endpoints.mergeIncidents({
        target_id: target || incidentId,
        source_ids: sources,
        reason,
        actor: "operator",
      });
      setOk(`Merged ${sources.length} into ${target || incidentId}`);
      onDone();
    } catch (e: any) { setErr(String(e?.message ?? e)); }
    finally { setBusy(false); }
  }

  async function doSplit() {
    setErr(null); setBusy(true);
    try {
      const ids = recordIds.split(/[\s,]+/).filter(Boolean);
      const r: any = await endpoints.splitIncident(incidentId, {
        record_ids: ids,
        reason,
        actor: "operator",
      });
      setOk(`Split into ${r.new_incident_id} (${ids.length} records)`);
      onDone();
    } catch (e: any) { setErr(String(e?.message ?? e)); }
    finally { setBusy(false); }
  }

  return (
    <div className="card" style={{ padding: 20 }}>
      <div className="t-heading">Merge / split</div>
      <div className="t-caption" style={{ marginTop: 4 }}>
        Originals are always preserved. Reason is required.
      </div>

      <div className="row" style={{ marginTop: 16, gap: 8 }}>
        <button className="btn btn-secondary btn-sm" onClick={() => setMode(mode === "merge" ? null : "merge")}>
          Merge into this
        </button>
        <button className="btn btn-secondary btn-sm" onClick={() => setMode(mode === "split" ? null : "split")}>
          Split records out
        </button>
      </div>

      {mode === "merge" && (
        <div className="stack-sm" style={{ marginTop: 16 }}>
          <label className="t-caption">Source incident IDs (comma or space separated)</label>
          <input className="input" value={sourcesText} onChange={(e) => setSourcesText(e.target.value)} placeholder="INC-... INC-..." />
          <label className="t-caption">Target incident (blank = this incident)</label>
          <input className="input" value={target} onChange={(e) => setTarget(e.target.value)} placeholder={incidentId} />
          <label className="t-caption">Reason (required)</label>
          <input className="input" value={reason} onChange={(e) => setReason(e.target.value)} />
          <div className="row" style={{ justifyContent: "flex-end" }}>
            <button className="btn btn-primary btn-sm" onClick={doMerge} disabled={busy || reason.length < 4}>
              {busy ? "Merging…" : "Confirm merge"}
            </button>
          </div>
        </div>
      )}

      {mode === "split" && (
        <div className="stack-sm" style={{ marginTop: 16 }}>
          <label className="t-caption">Record IDs to split off (comma or space separated)</label>
          <textarea className="input" rows={3} value={recordIds} onChange={(e) => setRecordIds(e.target.value)} placeholder="FB-001 FB-002" />
          <label className="t-caption">Reason (required)</label>
          <input className="input" value={reason} onChange={(e) => setReason(e.target.value)} />
          <div className="row" style={{ justifyContent: "flex-end" }}>
            <button className="btn btn-primary btn-sm" onClick={doSplit} disabled={busy || reason.length < 4}>
              {busy ? "Splitting…" : "Confirm split"}
            </button>
          </div>
        </div>
      )}

      {err && <div className="t-caption" style={{ color: "var(--st-critical)", marginTop: 10 }}>{err}</div>}
      {ok && <div className="t-caption" style={{ color: "var(--st-ok)", marginTop: 10 }}>{ok}</div>}
    </div>
  );
}
