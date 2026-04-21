"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Banner1 } from "@/components/banner1";
import { Button } from "@/components/ui/button";
import type {
  DashboardHealthDomain,
  DashboardHealthResponse,
  DashboardHealthRetryResponse,
} from "@/lib/admin-api";
import { cn } from "@/lib/utils";

type HealthDashboardSurfaceProps = {
  csrfToken: string | null | undefined;
  health: DashboardHealthResponse;
};

export function HealthDashboardSurface({ csrfToken, health }: HealthDashboardSurfaceProps) {
  const router = useRouter();
  const [retryPending, setRetryPending] = useState(false);
  const [retryMessage, setRetryMessage] = useState<string | null>(null);
  const [retryError, setRetryError] = useState<string | null>(null);

  const domain = health.domains[0] ?? null;
  if (!domain) {
    return (
      <section className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Dashboard health</h1>
        <p className="mt-3 text-sm leading-7 text-muted-foreground">
          No aggregate health domains are configured for this admin environment yet.
        </p>
      </section>
    );
  }

  async function handleRetry() {
    setRetryPending(true);
    setRetryMessage(null);
    setRetryError(null);
    try {
      const response = await fetch("/admin/health/dashboard/retry", {
        method: "POST",
        headers: {
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
      });
      const payload = (await response.json()) as { data?: DashboardHealthRetryResponse; error?: { message?: string } };
      if (!response.ok || !payload.data?.aggregate_refresh_request_id) {
        setRetryError(payload.error?.message ?? "Aggregate refresh retry could not be queued.");
        return;
      }
      setRetryMessage(payload.data.already_pending ? "An aggregate refresh is already queued." : "Aggregate refresh queued.");
      router.refresh();
    } catch {
      setRetryError("Aggregate refresh retry could not be queued. Check the admin API and try again.");
    } finally {
      setRetryPending(false);
    }
  }

  return (
    <section className="grid gap-6">
      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-4xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Dashboard health</p>
            <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
              Public aggregate freshness, serving fallback, and operator retry now live in one health surface.
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
              Approve and edit-approve now queue aggregate refresh work automatically. This route shows whether the
              public site is serving the latest successful snapshot, waiting on queued work, or holding a stale or
              failed refresh boundary.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className={cn("rounded-full px-3 py-1 text-xs font-medium", healthStatusClasses(domain.status))}>
              {toTitleCase(domain.status)}
            </span>
            <Button asChild variant="outline">
              <Link href="/admin/runs">Open runs</Link>
            </Button>
            <Button disabled={retryPending || !domain.retry_action.available} onClick={handleRetry} type="button">
              {retryPending ? "Retrying..." : "Retry refresh"}
            </Button>
          </div>
        </div>

        <div className="mt-6">
          <Banner1
            defaultVisible={true}
            description="Public responses keep serving the latest successful aggregate snapshot. Failures and pending refresh requests should be visible here instead of silently flattening the public grid to zero products."
            dismissible={false}
            title="Serving contract"
            tone={bannerTone(domain.status)}
          />
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <SummaryStat label="Serving snapshot" value={domain.serving_snapshot_id ?? "none"} />
          <SummaryStat label="Canonical active" value={formatCount(domain.active_product_count)} />
          <SummaryStat label="Projected active" value={formatCount(domain.projected_active_product_count)} />
          <SummaryStat label="Pending requests" value={formatCount(domain.queued_request_count + domain.in_progress_request_count)} />
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <SummaryStat label="Latest success" value={formatTimestamp(domain.latest_success_at)} />
          <SummaryStat label="Latest failure" value={formatTimestamp(domain.latest_failure_at)} />
          <SummaryStat label="Latest canonical change" value={formatTimestamp(domain.latest_canonical_change_at)} />
          <SummaryStat label="Missing data ratio" value={formatPercent(domain.missing_data_ratio)} />
        </div>

        {retryMessage ? (
          <p className="mt-4 rounded-2xl border border-success/20 bg-success-soft px-3 py-3 text-sm leading-6 text-success">
            {retryMessage}
          </p>
        ) : null}
        {retryError ? (
          <p className="mt-4 rounded-2xl border border-destructive/20 bg-destructive/5 px-3 py-3 text-sm leading-6 text-destructive">
            {retryError}
          </p>
        ) : null}
        {!domain.retry_action.available && domain.retry_action.reason ? (
          <p className="mt-4 text-sm leading-6 text-muted-foreground">{domain.retry_action.reason}</p>
        ) : null}
      </article>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.08fr)_minmax(20rem,0.92fr)]">
        <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
          <SectionHeading
            eyebrow="Serving state"
            title="What the public site is serving"
            description="The public product grid and insights keep reading the latest successful aggregate snapshot even when a newer refresh is still pending or has failed."
          />
          <div className="mt-6 grid gap-4">
            <SignalRow label="Serving note" value={domain.serving_note} />
            <SignalRow label="Serving snapshot id" value={domain.serving_snapshot_id ?? "No successful snapshot"} />
            <SignalRow label="Serving refreshed at" value={formatTimestamp(domain.serving_snapshot_refreshed_at)} />
            <SignalRow
              label="Freshness gap"
              value={domain.stale_reason ?? "No canonical freshness gap is currently detected."}
              tone={domain.stale_flag ? "warning" : "neutral"}
            />
          </div>
        </article>

        <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
          <SectionHeading
            eyebrow="Queue"
            title="Refresh queue visibility"
            description="Pending and in-progress refresh work stays visible here so approvals can be separated from public serving without becoming invisible."
          />
          <div className="mt-6 grid gap-4">
            <SignalRow label="Queued requests" value={formatCount(domain.queued_request_count)} />
            <SignalRow label="In-progress requests" value={formatCount(domain.in_progress_request_count)} />
            <SignalRow label="Latest request id" value={domain.latest_request_id ?? "n/a"} />
            <SignalRow
              label="Latest request"
              value={`${toTitleCase(domain.latest_request_status ?? "unknown")} / ${toTitleCase(domain.latest_request_reason ?? "unknown")}`}
            />
            <SignalRow label="Latest requested at" value={formatTimestamp(domain.latest_requested_at)} />
          </div>
        </article>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
          <SectionHeading
            eyebrow="Latest attempt"
            title="Newest aggregate execution"
            description="The latest refresh attempt may be newer than the serving snapshot. This is where failed or incomplete attempts are surfaced."
          />
          <div className="mt-6 grid gap-4">
            <SignalRow label="Attempt status" value={toTitleCase(domain.latest_attempt_status ?? "unknown")} />
            <SignalRow label="Attempt snapshot id" value={domain.latest_attempt_snapshot_id ?? "n/a"} />
            <SignalRow label="Attempted at" value={formatTimestamp(domain.latest_attempt_at)} />
            <SignalRow
              label="Attempt error"
              value={domain.latest_attempt_error_summary ?? "No aggregate attempt error is currently recorded."}
              tone={domain.latest_attempt_error_summary ? "danger" : "neutral"}
            />
          </div>
        </article>

        <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
          <SectionHeading
            eyebrow="Methodology"
            title="How to interpret health"
            description="Status distinguishes between pending work, stale serving, failed execution, and healthy serving so operators can decide whether to wait, retry, or inspect upstream changes."
          />
          <div className="mt-6 grid gap-3 text-sm leading-6 text-muted-foreground">
            <p>
              <strong className="font-medium text-foreground">Pending</strong> means at least one refresh request is queued
              or currently running.
            </p>
            <p>
              <strong className="font-medium text-foreground">Stale</strong> means canonical products are newer than the latest
              successful public snapshot.
            </p>
            <p>
              <strong className="font-medium text-foreground">Failed</strong> means the latest completed refresh request failed,
              but the public site may still be serving the previous successful snapshot.
            </p>
            <p>
              <strong className="font-medium text-foreground">Healthy</strong> means no pending work, no freshness gap, and a
              successful serving snapshot exists.
            </p>
          </div>
        </article>
      </div>
    </section>
  );
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/80 bg-background p-4">
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-sm font-semibold text-foreground">{value}</p>
    </div>
  );
}

function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="max-w-3xl">
      <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{eyebrow}</p>
      <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{description}</p>
    </div>
  );
}

function SignalRow({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "neutral" | "warning" | "danger";
}) {
  return (
    <div className="rounded-2xl border border-border/80 bg-background p-4">
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p
        className={cn("mt-2 text-sm leading-6", {
          "text-foreground": tone === "neutral",
          "text-warning": tone === "warning",
          "text-destructive": tone === "danger",
        })}
      >
        {value}
      </p>
    </div>
  );
}

function healthStatusClasses(status: DashboardHealthDomain["status"]) {
  if (status === "healthy") {
    return "bg-success-soft text-success";
  }
  if (status === "pending") {
    return "bg-warning-soft text-warning";
  }
  if (status === "failed") {
    return "bg-destructive/10 text-destructive";
  }
  if (status === "stale") {
    return "bg-amber-100 text-amber-700";
  }
  return "bg-muted text-muted-foreground";
}

function bannerTone(status: DashboardHealthDomain["status"]): "info" | "warning" | "success" {
  if (status === "healthy") {
    return "success";
  }
  if (status === "empty") {
    return "info";
  }
  return "warning";
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return "n/a";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(date);
}

function formatCount(value: number) {
  return value.toLocaleString("en-CA");
}

function formatPercent(value: number) {
  return `${(value * 100).toFixed(value === 0 ? 0 : 1)}%`;
}

function toTitleCase(value: string) {
  return value
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
