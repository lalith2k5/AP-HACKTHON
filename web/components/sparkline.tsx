"use client";

import { useId } from "react";

export function Sparkline({
  data,
  width = 160,
  height = 44,
  color = "var(--accent)",
  fill = true,
  strokeWidth = 2,
}: {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  fill?: boolean;
  strokeWidth?: number;
}) {
  const id = useId();
  if (!data.length) return null;
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min || 1;
  const step = width / Math.max(1, data.length - 1);

  const points = data.map((v, i) => {
    const x = i * step;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return [x, y] as [number, number];
  });

  // Smooth curve via Catmull-Rom → Bezier
  const path = points
    .map((p, i, arr) => {
      if (i === 0) return `M ${p[0]},${p[1]}`;
      const prev = arr[i - 1];
      const cp1x = prev[0] + (p[0] - prev[0]) / 2;
      const cp2x = cp1x;
      return `C ${cp1x},${prev[1]} ${cp2x},${p[1]} ${p[0]},${p[1]}`;
    })
    .join(" ");

  const areaPath = `${path} L ${width},${height} L 0,${height} Z`;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      style={{ overflow: "visible" }}
    >
      <defs>
        <linearGradient id={`grad-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.35" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      {fill && <path d={areaPath} fill={`url(#grad-${id})`} />}
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Endpoint dot */}
      <circle
        cx={points[points.length - 1][0]}
        cy={points[points.length - 1][1]}
        r="3.5"
        fill={color}
        stroke="#fff"
        strokeWidth="2"
      />
    </svg>
  );
}
