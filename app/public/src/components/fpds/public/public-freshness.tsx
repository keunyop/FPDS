import { Check, CircleAlert, Clock3 } from "lucide-react";

import { getPublicDesignCopy, getPublicMessages } from "@/lib/public-locale";
import type { PublicFreshness } from "@/lib/public-api";
import { cn } from "@/lib/utils";

export function PublicFreshness({
  className = "",
  freshness,
  locale,
  compact = false,
}: {
  className?: string;
  compact?: boolean;
  freshness: PublicFreshness;
  locale: string;
}) {
  const copy = getPublicMessages(locale);
  const designCopy = getPublicDesignCopy(locale);
  const status = freshness.status;
  const Icon = status === "fresh" ? Check : status === "stale" ? Clock3 : CircleAlert;
  const statusLabel = status === "fresh" ? designCopy.fresh : status === "stale" ? designCopy.stale : designCopy.unavailable;
  const date = formatSnapshotDate(freshness.refreshed_at, copy.common.noDate);

  return (
    <div
      className={cn(
        "inline-flex min-h-11 min-w-0 max-w-full items-center gap-2.5 whitespace-nowrap rounded-full border px-3.5 py-2 text-sm",
        status === "fresh" && "border-verification/20 bg-verification-soft text-verification",
        status === "stale" && "border-warning/25 bg-warning-soft text-warning",
        status === "unavailable" && "border-destructive/20 bg-destructive/5 text-destructive",
        className
      )}
    >
      <span className="grid size-6 shrink-0 place-items-center rounded-full bg-current/10">
        <Icon className="size-3.5" aria-hidden="true" />
      </span>
      <span className="min-w-0">
        <span className="font-semibold">{statusLabel}</span>
        {!compact ? <span className="mx-1.5 text-current/45" aria-hidden="true">·</span> : null}
        {!compact ? <span className="font-mono text-xs text-current/80">{date}</span> : null}
      </span>
    </div>
  );
}

export function formatSnapshotDate(value: string | null, fallback: string) {
  if (!value) {
    return fallback;
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value.slice(0, 10) : date.toISOString().slice(0, 10);
}
