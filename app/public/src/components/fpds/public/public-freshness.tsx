import { CircleAlert, Clock3 } from "lucide-react";
import type { PublicFreshness } from "@/lib/public-api";
import { getVerificationCopy, verificationDate } from "@/lib/public-verification";
import { cn } from "@/lib/utils";

export function PublicFreshness({ className = "", freshness, locale, compact = false }: {
  className?: string; compact?: boolean; freshness: PublicFreshness; locale: string;
}) {
  const copy = getVerificationCopy(locale);
  const status = freshness.snapshot_status ?? (freshness.status === "unavailable" ? "unavailable" : freshness.status === "stale" ? "stale" : "completed");
  const Icon = status === "unavailable" ? CircleAlert : Clock3;
  const counts = freshness.verification?.counts;
  const attention = counts ? counts.review_due + counts.expired + counts.unknown : null;
  return (
    <div className={cn("min-w-0 max-w-full text-xs leading-5 text-muted-foreground", className)}>
      <div className={cn("inline-flex max-w-full items-center gap-2 rounded-lg border px-3 py-2", status === "unavailable" && "text-destructive", status === "stale" && "text-warning")}>
        <Icon className="size-4 shrink-0" aria-hidden="true" />
        <span className="min-w-0 [overflow-wrap:anywhere]">
          <span className="font-semibold">{copy[status]}</span>
          {!compact ? <span className="block">{copy.snapshot}: {formatSnapshotDate(freshness.refreshed_at, copy.unknownDate)} (UTC)</span> : null}
        </span>
      </div>
      {!compact ? <>
        {attention !== null && freshness.verification?.total_products ? <p className="mt-2">{copy.summary}: {attention} / {freshness.verification.total_products}</p> : null}
        <p className="mt-1 max-w-xl">{copy.notice}</p>
      </> : null}
    </div>
  );
}

export function formatSnapshotDate(value: string | null, fallback: string) {
  return verificationDate(value, fallback);
}
