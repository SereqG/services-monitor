"use client";

import { useMemo } from "react";
import { type MetricStatus, statusColor } from "@/lib/utils/scoring";

export function ScoreRing({ score, status }: { score: number; status: MetricStatus }) {
  const radius = 52;
  const circ = 2 * Math.PI * radius;
  const offset = useMemo(() => circ - (score / 100) * circ, [circ, score]);
  const stroke =
    status === "good"
      ? "var(--accent)"
      : status === "warn"
        ? "var(--warning)"
        : "var(--destructive)";

  return (
    <div className="relative size-32">
      <svg viewBox="0 0 120 120" className="size-full -rotate-90">
        <circle cx="60" cy="60" r={radius} fill="none" stroke="var(--border)" strokeWidth="8" />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke={stroke}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 700ms ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className={`font-mono text-4xl font-bold ${statusColor(status)}`}>{score}</span>
      </div>
    </div>
  );
}
