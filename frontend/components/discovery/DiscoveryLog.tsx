"use client";

import { useEffect, useRef } from "react";
import { useI18n } from "@/lib/i18n";

interface DiscoveryLogProps {
  messages: string[];
  elapsedSeconds: number | null;
  maxDurationSeconds: number | null;
}

export function DiscoveryLog({ messages, elapsedSeconds, maxDurationSeconds }: DiscoveryLogProps) {
  const { dict } = useI18n();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const progressPercent =
    elapsedSeconds != null && maxDurationSeconds != null && maxDurationSeconds > 0
      ? Math.min((elapsedSeconds / maxDurationSeconds) * 100, 100)
      : null;

  const formatTime = (seconds: number) =>
    seconds >= 60
      ? `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`
      : `${seconds.toFixed(1)}s`;

  return (
    <section className="mt-16 space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div className="h-1 flex-1 overflow-hidden rounded-full bg-secondary">
          {progressPercent != null ? (
            <div
              className="h-full rounded-full bg-accent transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          ) : (
            <div className="h-full w-1/3 animate-pulse rounded-full bg-accent" />
          )}
        </div>
        {elapsedSeconds != null && maxDurationSeconds != null && (
          <span className="shrink-0 font-mono text-xs text-muted-foreground tabular-nums">
            {formatTime(elapsedSeconds)}&nbsp;/&nbsp;{formatTime(maxDurationSeconds)}&nbsp;{dict.progress.maxSuffix}
          </span>
        )}
      </div>
      <div className="h-64 overflow-y-auto rounded-xl border border-border bg-card/50 p-5 space-y-1.5">
        {messages.map((msg, i) => (
          <div key={i} className="discovery-log-line font-mono text-sm text-foreground/80">
            <span className="text-accent mr-2">›</span>
            {msg}
          </div>
        ))}
        <div ref={bottomRef} className="font-mono text-accent animate-pulse">
          _
        </div>
      </div>
    </section>
  );
}
