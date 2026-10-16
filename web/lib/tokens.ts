// StoreSignal — JS-side design tokens.
// Mirrors the CSS tokens in app/globals.css. Keep in sync.
// HANDOFF 5a: SF Pro stack, 8pt grid, Apple-like spring feel.

export const motion = {
  // Apple-ish spring physics
  spring: { type: "spring", stiffness: 260, damping: 30, mass: 1 } as const,
  springSnappy: { type: "spring", stiffness: 380, damping: 28 } as const,
  springSoft: { type: "spring", stiffness: 180, damping: 26 } as const,
} as const;

export const duration = {
  fast: 0.15,
  base: 0.25,
  slow: 0.4,
} as const;

export const spacing = {
  // 8pt grid
  xs: 4, sm: 8, md: 16, lg: 24, xl: 32, xxl: 48,
} as const;

export const radius = {
  sm: "6px", md: "10px", lg: "12px", xl: "16px", card: "12px",
} as const;

export const status = {
  critical: { css: "var(--status-critical)", label: "Critical" },
  high:     { css: "var(--status-high)",     label: "High" },
  medium:   { css: "var(--status-medium)",   label: "Medium" },
  low:      { css: "var(--status-low)",      label: "Low" },
  info:     { css: "var(--status-info)",     label: "Info" },
  ok:       { css: "var(--status-ok)",       label: "Resolved" },
} as const;

export type StatusKey = keyof typeof status;
