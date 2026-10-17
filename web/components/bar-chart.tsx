"use client";

export function BarChart({
  items,
  max,
}: {
  items: { label: string; value: number; color?: string }[];
  max?: number;
}) {
  const top = max ?? Math.max(...items.map((i) => i.value), 1);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {items.map((it) => {
        const pct = (it.value / top) * 100;
        return (
          <div key={it.label}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: 6,
                fontSize: 13,
              }}
            >
              <span style={{ fontWeight: 500, textTransform: "capitalize" }}>
                {it.label.replace(/_/g, " ")}
              </span>
              <span style={{ color: "var(--fg-2)", fontVariantNumeric: "tabular-nums" }}>
                {it.value.toLocaleString()}
              </span>
            </div>
            <div
              style={{
                height: 8,
                borderRadius: 4,
                background: "var(--bg-inset)",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${pct}%`,
                  borderRadius: 4,
                  background: it.color || "var(--accent)",
                  transition: "width 900ms cubic-bezier(0.22, 0.61, 0.36, 1)",
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
