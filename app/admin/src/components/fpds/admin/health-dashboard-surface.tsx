"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AdminTableAutoRefresh } from "@/components/fpds/admin/admin-table-auto-refresh";
import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { Button } from "@/components/ui/button";
import type {
  DashboardHealthDomain,
  DashboardHealthResponse,
  DashboardHealthRetryResponse,
} from "@/lib/admin-api";
import { buildAdminHref, formatAdminDateTimeValue, type AdminLocale } from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

type HealthDashboardSurfaceProps = {
  csrfToken: string | null | undefined;
  health: DashboardHealthResponse;
  locale: AdminLocale;
};

const HEALTH_COPY = {
  en: {
    title: "Dashboard Health",
    emptyTitle: "Dashboard health",
    emptyDescription: "No aggregate health domains are configured for this admin environment yet.",
    openRuns: "Open runs",
    retrying: "Retrying...",
    retry: "Retry refresh",
    description: "Public aggregate freshness, fallback status, and retry state.",
    path: ["Observability", "Dashboard Health"],
    servingSnapshot: "Serving snapshot",
    canonicalActive: "Canonical active",
    projectedActive: "Projected active",
    pendingRequests: "Pending requests",
    latestSuccess: "Latest success",
    latestFailure: "Latest failure",
    latestCanonicalChange: "Latest canonical change",
    missingDataRatio: "Missing data ratio",
    retryFailed: "Aggregate refresh retry could not be queued.",
    retryApiFailed: "Aggregate refresh retry could not be queued. Check the admin API and try again.",
    alreadyPending: "An aggregate refresh is already queued.",
    retryQueued: "Aggregate refresh queued.",
    servingState: "Serving state",
    publicServing: "What the public site is serving",
    servingNote: "Serving note",
    servingSnapshotId: "Serving snapshot id",
    noSuccessfulSnapshot: "No successful snapshot",
    servingRefreshedAt: "Serving refreshed at",
    freshnessGap: "Freshness gap",
    noFreshnessGap: "No canonical freshness gap is currently detected.",
    queue: "Queue",
    queueTitle: "Refresh queue visibility",
    queuedRequests: "Queued requests",
    inProgressRequests: "In-progress requests",
    latestRequestId: "Latest request id",
    latestRequest: "Latest request",
    latestRequestedAt: "Latest requested at",
    latestAttempt: "Latest attempt",
    newestExecution: "Newest aggregate execution",
    attemptStatus: "Attempt status",
    attemptSnapshotId: "Attempt snapshot id",
    attemptedAt: "Attempted at",
    attemptError: "Attempt error",
    noAttemptError: "No aggregate attempt error is currently recorded.",
    status: "Status",
    interpretation: "Health interpretation",
    pendingDef: "means at least one refresh request is queued or currently running.",
    staleDef: "means canonical products are newer than the latest successful public snapshot.",
    failedDef: "means the latest completed refresh request failed, but the public site may still be serving the previous successful snapshot.",
    healthyDef: "means no pending work, no freshness gap, and a successful serving snapshot exists.",
    pending: "Pending",
    stale: "Stale",
    failed: "Failed",
    healthy: "Healthy",
    missing: "n/a",
    none: "none",
    unknown: "unknown",
  },
  ko: {
    title: "Dashboard 상태",
    emptyTitle: "Dashboard 상태",
    emptyDescription: "이 Admin 환경에는 아직 aggregate health domain이 설정되어 있지 않습니다.",
    openRuns: "Runs 열기",
    retrying: "재시도 중...",
    retry: "Refresh 재시도",
    description: "공개 aggregate freshness, fallback 상태, retry 상태입니다.",
    path: ["관측", "Dashboard 상태"],
    servingSnapshot: "Serving snapshot",
    canonicalActive: "Canonical 활성",
    projectedActive: "Projected 활성",
    pendingRequests: "대기 요청",
    latestSuccess: "최근 성공",
    latestFailure: "최근 실패",
    latestCanonicalChange: "최근 canonical 변경",
    missingDataRatio: "Missing data 비율",
    retryFailed: "Aggregate refresh retry를 대기열에 넣을 수 없습니다.",
    retryApiFailed: "Aggregate refresh retry를 대기열에 넣을 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    alreadyPending: "Aggregate refresh가 이미 대기열에 있습니다.",
    retryQueued: "Aggregate refresh가 대기열에 등록되었습니다.",
    servingState: "Serving 상태",
    publicServing: "Public site가 제공 중인 상태",
    servingNote: "Serving note",
    servingSnapshotId: "Serving snapshot id",
    noSuccessfulSnapshot: "성공한 snapshot 없음",
    servingRefreshedAt: "Serving 갱신 시각",
    freshnessGap: "Freshness gap",
    noFreshnessGap: "현재 canonical freshness gap이 감지되지 않았습니다.",
    queue: "Queue",
    queueTitle: "Refresh queue 상태",
    queuedRequests: "대기 요청",
    inProgressRequests: "진행 중 요청",
    latestRequestId: "최근 request id",
    latestRequest: "최근 request",
    latestRequestedAt: "최근 요청 시각",
    latestAttempt: "최근 attempt",
    newestExecution: "최신 aggregate 실행",
    attemptStatus: "Attempt 상태",
    attemptSnapshotId: "Attempt snapshot id",
    attemptedAt: "Attempt 시각",
    attemptError: "Attempt 오류",
    noAttemptError: "현재 기록된 aggregate attempt 오류가 없습니다.",
    status: "상태",
    interpretation: "Health 해석",
    pendingDef: "하나 이상의 refresh request가 대기 중이거나 실행 중이라는 뜻입니다.",
    staleDef: "canonical product가 최근 성공한 public snapshot보다 최신이라는 뜻입니다.",
    failedDef: "최근 완료된 refresh request가 실패했지만 public site는 이전 성공 snapshot을 제공 중일 수 있다는 뜻입니다.",
    healthyDef: "대기 작업과 freshness gap이 없고 성공한 serving snapshot이 있다는 뜻입니다.",
    pending: "Pending",
    stale: "Stale",
    failed: "Failed",
    healthy: "Healthy",
    missing: "없음",
    none: "없음",
    unknown: "unknown",
  },
  ja: {
    title: "Dashboard 健全性",
    emptyTitle: "Dashboard 健全性",
    emptyDescription: "この Admin 環境にはまだ aggregate health domain が設定されていません。",
    openRuns: "Runs を開く",
    retrying: "再試行中...",
    retry: "Refresh を再試行",
    description: "公開 aggregate freshness、fallback 状態、retry 状態です。",
    path: ["監視", "Dashboard 健全性"],
    servingSnapshot: "Serving snapshot",
    canonicalActive: "Canonical 有効",
    projectedActive: "Projected 有効",
    pendingRequests: "保留リクエスト",
    latestSuccess: "最新成功",
    latestFailure: "最新失敗",
    latestCanonicalChange: "最新 canonical 変更",
    missingDataRatio: "Missing data 比率",
    retryFailed: "Aggregate refresh retry をキューに追加できません。",
    retryApiFailed: "Aggregate refresh retry をキューに追加できません。Admin APIを確認してから再試行してください。",
    alreadyPending: "Aggregate refresh はすでにキューにあります。",
    retryQueued: "Aggregate refresh をキューに追加しました。",
    servingState: "Serving 状態",
    publicServing: "Public site が提供中の状態",
    servingNote: "Serving note",
    servingSnapshotId: "Serving snapshot id",
    noSuccessfulSnapshot: "成功した snapshot なし",
    servingRefreshedAt: "Serving 更新時刻",
    freshnessGap: "Freshness gap",
    noFreshnessGap: "現在 canonical freshness gap は検出されていません。",
    queue: "Queue",
    queueTitle: "Refresh queue 状態",
    queuedRequests: "保留リクエスト",
    inProgressRequests: "進行中リクエスト",
    latestRequestId: "最新 request id",
    latestRequest: "最新 request",
    latestRequestedAt: "最新リクエスト時刻",
    latestAttempt: "最新 attempt",
    newestExecution: "最新 aggregate 実行",
    attemptStatus: "Attempt 状態",
    attemptSnapshotId: "Attempt snapshot id",
    attemptedAt: "Attempt 時刻",
    attemptError: "Attempt エラー",
    noAttemptError: "現在記録されている aggregate attempt エラーはありません。",
    status: "状態",
    interpretation: "Health の解釈",
    pendingDef: "1件以上の refresh request がキューにある、または実行中であることを示します。",
    staleDef: "canonical product が最新の成功 public snapshot より新しいことを示します。",
    failedDef: "最新の完了 refresh request は失敗しましたが、public site は以前の成功 snapshot を提供している可能性があります。",
    healthyDef: "保留作業と freshness gap がなく、成功した serving snapshot が存在することを示します。",
    pending: "Pending",
    stale: "Stale",
    failed: "Failed",
    healthy: "Healthy",
    missing: "なし",
    none: "なし",
    unknown: "unknown",
  },
} as const;

export function HealthDashboardSurface({ csrfToken, health, locale }: HealthDashboardSurfaceProps) {
  const copy = HEALTH_COPY[locale];
  const router = useRouter();
  const [retryPending, setRetryPending] = useState(false);
  const [retryMessage, setRetryMessage] = useState<string | null>(null);
  const [retryError, setRetryError] = useState<string | null>(null);

  const domain = health.domains[0] ?? null;
  if (!domain) {
    return (
      <section className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">{copy.emptyTitle}</h1>
        <p className="mt-3 text-sm leading-7 text-muted-foreground">
          {copy.emptyDescription}
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
        setRetryError(payload.error?.message ?? copy.retryFailed);
        return;
      }
      setRetryMessage(payload.data.already_pending ? copy.alreadyPending : copy.retryQueued);
      router.refresh();
    } catch {
      setRetryError(copy.retryApiFailed);
    } finally {
      setRetryPending(false);
    }
  }

  return (
    <section className="grid min-w-0 gap-6">
      <AdminTableAutoRefresh />

      <AdminPageHeader
        actions={
          <>
            <Button asChild variant="outline">
              <Link href={buildAdminHref("/admin/runs", new URLSearchParams(), locale)}>{copy.openRuns}</Link>
            </Button>
            <Button disabled={retryPending || !domain.retry_action.available} onClick={handleRetry} type="button">
              {retryPending ? copy.retrying : copy.retry}
            </Button>
          </>
        }
        badges={
          <span className={cn("rounded-full px-3 py-1 text-xs font-medium", healthStatusClasses(domain.status))}>
            {toTitleCase(domain.status)}
          </span>
        }
        description={copy.description}
        path={copy.path}
        title={copy.title}
      />

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <SummaryStat label={copy.canonicalActive} value={formatCount(domain.active_product_count)} />
        <SummaryStat label={copy.projectedActive} value={formatCount(domain.projected_active_product_count)} />
        <SummaryStat label={copy.pendingRequests} value={formatCount(domain.queued_request_count + domain.in_progress_request_count)} />
        <SummaryStat label={copy.latestSuccess} value={formatTimestamp(domain.latest_success_at, copy.missing)} />
        <SummaryStat label={copy.latestFailure} value={formatTimestamp(domain.latest_failure_at, copy.missing)} />
        <SummaryStat label={copy.missingDataRatio} value={formatPercent(domain.missing_data_ratio)} />
      </div>

      {retryMessage ? (
        <p className="rounded-lg border border-success/20 bg-success-soft px-3 py-3 text-sm leading-6 text-success">
          {retryMessage}
        </p>
      ) : null}
      {retryError ? (
        <p className="rounded-lg border border-destructive/20 bg-destructive/5 px-3 py-3 text-sm leading-6 text-destructive">
          {retryError}
        </p>
      ) : null}
      {!domain.retry_action.available && domain.retry_action.reason ? (
        <p className="text-sm leading-6 text-muted-foreground">{domain.retry_action.reason}</p>
      ) : null}

      <div className="grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1.08fr)_minmax(20rem,0.92fr)]">
        <article className="min-w-0 rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
          <SectionHeading
            eyebrow={copy.servingState}
            title={copy.publicServing}
          />
          <div className="mt-6 grid gap-4">
            <SignalRow label={copy.servingNote} value={domain.serving_note} />
            <SignalRow label={copy.servingRefreshedAt} value={formatTimestamp(domain.serving_snapshot_refreshed_at, copy.missing)} />
            <SignalRow
              label={copy.freshnessGap}
              value={domain.stale_reason ?? copy.noFreshnessGap}
              tone={domain.stale_flag ? "warning" : "neutral"}
            />
          </div>
        </article>

        <article className="min-w-0 rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
          <SectionHeading
            eyebrow={copy.queue}
            title={copy.queueTitle}
          />
          <div className="mt-6 grid gap-4">
            <SignalRow label={copy.queuedRequests} value={formatCount(domain.queued_request_count)} />
            <SignalRow label={copy.inProgressRequests} value={formatCount(domain.in_progress_request_count)} />
            <SignalRow
              label={copy.latestRequest}
              value={`${toTitleCase(domain.latest_request_status ?? copy.unknown)} / ${toTitleCase(domain.latest_request_reason ?? copy.unknown)}`}
            />
            <SignalRow label={copy.latestRequestedAt} value={formatTimestamp(domain.latest_requested_at, copy.missing)} />
          </div>
        </article>
      </div>

      <div className="grid min-w-0 gap-6">
        <article className="min-w-0 rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
          <SectionHeading
            eyebrow={copy.latestAttempt}
            title={copy.newestExecution}
          />
          <div className="mt-6 grid gap-4">
            <SignalRow label={copy.attemptStatus} value={toTitleCase(domain.latest_attempt_status ?? copy.unknown)} />
            <SignalRow label={copy.attemptedAt} value={formatTimestamp(domain.latest_attempt_at, copy.missing)} />
            <SignalRow
              label={copy.attemptError}
              value={domain.latest_attempt_error_summary ?? copy.noAttemptError}
              tone={domain.latest_attempt_error_summary ? "danger" : "neutral"}
            />
          </div>
        </article>
      </div>
    </section>
  );
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border/80 bg-background p-4">
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
  description?: string;
}) {
  return (
    <div className="max-w-3xl">
      <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{eyebrow}</p>
      <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{title}</h2>
      {description ? <p className="mt-2 text-sm leading-6 text-muted-foreground">{description}</p> : null}
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

function formatTimestamp(value: string | null, missing = "n/a") {
  return formatAdminDateTimeValue(value, missing);
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
