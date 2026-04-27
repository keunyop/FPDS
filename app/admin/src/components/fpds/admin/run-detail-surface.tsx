"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { Button } from "@/components/ui/button";
import type { RunRetryResponse, RunStatusDetailResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

type RunDetailSurfaceProps = {
  csrfToken: string | null | undefined;
  detail: RunStatusDetailResponse;
  locale: AdminLocale;
};

const RUN_DETAIL_COPY = {
  en: {
    retryFailed: "Run retry could not be queued.",
    retryApiFailed: "Run retry could not be queued. Check the admin API and try again.",
    retryQueued: "Retry queued.",
    back: "Back to runs",
    retrying: "Retrying...",
    retryRun: "Retry run",
    previousAttempt: "Previous attempt",
    nextAttempt: "Next attempt",
    partialCompletion: "Partial completion",
    description: "Execution outcome, source impact, related reviews, and usage.",
    path: ["Operations", "Runs", "Run Detail"],
    sourceItems: "Source items",
    candidates: "Candidates",
    reviewQueued: "Review queued",
    correlation: "Correlation",
    started: "Started",
    completed: "Completed",
    trigger: "Trigger",
    actor: "Actor",
    stageSummary: "Stage summary",
    executionStageStrip: "Execution stage strip",
    stageSummaryDescription:
      "Stage status stays compact at the top of run detail so operators can quickly see whether the run failed, completed cleanly, or completed in a degraded way.",
    executionEntries: (count: number) => `${count} execution entries`,
    success: "Success",
    failure: "Failure",
    sourceProcessing: "Source processing",
    perSourceSummary: "Per-source summary",
    sourceProcessingDescription:
      "Run detail keeps source processing summary separate from error events so impact scope and processing state remain easy to scan.",
    noSourceItems: "No source-item rows were persisted for this run.",
    warning: (count: number) => `${count} warning`,
    error: (count: number) => `${count} error`,
    sourceDoc: "Source doc",
    snapshot: "Snapshot",
    parsedDoc: "Parsed doc",
    fetched: "Fetched",
    parseNote: "Parse note",
    safeMetadata: "Safe stage metadata",
    openSourceUrl: "Open source URL",
    failureSummary: "Failure summary",
    runSourceIssues: "Run and source issues",
    failureDescription:
      "Error and degraded-event summaries stay together here so operators can explain what went wrong and how wide the impact was.",
    noIssues: "No run-level or source-level issues were recorded for this run.",
    runEvent: "Run event",
    sourceEvent: "Source event",
    runSummary: "Run summary",
    usageSummary: "Usage summary",
    modelTokenUsage: "Model and token usage",
    usageDescription:
      "Usage stays readable from the same run context so operators can connect execution cost to the exact diagnostic surface.",
    usageRecords: "Usage records",
    modelExecutions: "Model executions",
    totalTokens: "Total tokens",
    estimatedCost: "Estimated cost",
    noUsage: "No usage records were linked to this run.",
    records: (count: number) => `${count} records`,
    promptTokens: "Prompt tokens",
    completionTokens: "Completion tokens",
    cost: "Cost",
    relatedReviews: "Related review tasks",
    reviewWorkload: "Review workload produced by this run",
    reviewDescription:
      "Run detail links directly to the queue items created from this run so operators can move from execution diagnosis into task-level evidence review.",
    noReviews: "This run did not produce any related review tasks.",
    candidate: "Candidate",
    bank: "Bank",
    validation: "Validation",
    created: "Created",
    runContext: "Run context",
    retryScope: "Retry and scope summary",
    contextDescription: "Core identifiers and retry linkage stay compact on the side so the main pane remains focused on diagnosis.",
    pipelineStage: "Pipeline stage",
    requestId: "Request ID",
    retryOf: "Retry of",
    retriedBy: "Retried by",
    missing: "n/a",
  },
  ko: {
    retryFailed: "Run retry를 대기열에 넣을 수 없습니다.",
    retryApiFailed: "Run retry를 대기열에 넣을 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    retryQueued: "Retry가 대기열에 등록되었습니다.",
    back: "Runs로 돌아가기",
    retrying: "재시도 중...",
    retryRun: "Run 재시도",
    previousAttempt: "이전 attempt",
    nextAttempt: "다음 attempt",
    partialCompletion: "부분 완료",
    description: "Execution 결과, source 영향, 관련 review, usage입니다.",
    path: ["운영", "Runs", "Run 상세"],
    sourceItems: "Source 항목",
    candidates: "Candidates",
    reviewQueued: "Review queued",
    correlation: "Correlation",
    started: "시작",
    completed: "완료",
    trigger: "Trigger",
    actor: "Actor",
    stageSummary: "Stage 요약",
    executionStageStrip: "Execution stage strip",
    stageSummaryDescription: "운영자가 run 실패/정상 완료/저하 완료 여부를 빠르게 볼 수 있도록 stage 상태를 상단에 압축해 표시합니다.",
    executionEntries: (count: number) => `execution entry ${count}개`,
    success: "성공",
    failure: "실패",
    sourceProcessing: "Source 처리",
    perSourceSummary: "Source별 요약",
    sourceProcessingDescription: "영향 범위와 처리 상태를 쉽게 훑을 수 있도록 source 처리 요약을 error event와 분리합니다.",
    noSourceItems: "이 run에 저장된 source-item row가 없습니다.",
    warning: (count: number) => `warning ${count}개`,
    error: (count: number) => `error ${count}개`,
    sourceDoc: "Source doc",
    snapshot: "Snapshot",
    parsedDoc: "Parsed doc",
    fetched: "Fetched",
    parseNote: "Parse note",
    safeMetadata: "Safe stage metadata",
    openSourceUrl: "소스 URL 열기",
    failureSummary: "실패 요약",
    runSourceIssues: "Run 및 source 이슈",
    failureDescription: "무엇이 잘못되었고 영향 범위가 어느 정도인지 설명할 수 있도록 오류와 degraded event 요약을 함께 표시합니다.",
    noIssues: "이 run에 기록된 run-level 또는 source-level 이슈가 없습니다.",
    runEvent: "Run event",
    sourceEvent: "Source event",
    runSummary: "Run 요약",
    usageSummary: "Usage 요약",
    modelTokenUsage: "Model 및 token usage",
    usageDescription: "운영자가 실행 비용을 정확한 진단 화면과 연결할 수 있도록 같은 run context에서 usage를 표시합니다.",
    usageRecords: "Usage records",
    modelExecutions: "Model executions",
    totalTokens: "Total tokens",
    estimatedCost: "Estimated cost",
    noUsage: "이 run에 연결된 usage record가 없습니다.",
    records: (count: number) => `record ${count}개`,
    promptTokens: "Prompt tokens",
    completionTokens: "Completion tokens",
    cost: "Cost",
    relatedReviews: "관련 review task",
    reviewWorkload: "이 run에서 생성된 review workload",
    reviewDescription: "운영자가 실행 진단에서 task-level evidence review로 이동할 수 있도록 이 run에서 생성된 queue 항목을 연결합니다.",
    noReviews: "이 run은 관련 review task를 생성하지 않았습니다.",
    candidate: "Candidate",
    bank: "은행",
    validation: "Validation",
    created: "생성",
    runContext: "Run context",
    retryScope: "Retry 및 scope 요약",
    contextDescription: "핵심 식별자와 retry 연결을 사이드에 압축해 메인 영역이 진단에 집중되도록 합니다.",
    pipelineStage: "Pipeline stage",
    requestId: "Request ID",
    retryOf: "Retry of",
    retriedBy: "Retried by",
    missing: "없음",
  },
  ja: {
    retryFailed: "Run retry をキューに追加できません。",
    retryApiFailed: "Run retry をキューに追加できません。Admin APIを確認してから再試行してください。",
    retryQueued: "Retry をキューに追加しました。",
    back: "Runs に戻る",
    retrying: "再試行中...",
    retryRun: "Run を再試行",
    previousAttempt: "前の attempt",
    nextAttempt: "次の attempt",
    partialCompletion: "部分完了",
    description: "Execution 結果、source 影響、関連 review、usage です。",
    path: ["運用", "Runs", "Run 詳細"],
    sourceItems: "Source 項目",
    candidates: "Candidates",
    reviewQueued: "Review queued",
    correlation: "Correlation",
    started: "開始",
    completed: "完了",
    trigger: "Trigger",
    actor: "Actor",
    stageSummary: "Stage サマリー",
    executionStageStrip: "Execution stage strip",
    stageSummaryDescription: "オペレーターが run の失敗、正常完了、劣化完了を素早く確認できるよう stage 状態を上部に集約します。",
    executionEntries: (count: number) => `execution entry ${count} 件`,
    success: "成功",
    failure: "失敗",
    sourceProcessing: "Source 処理",
    perSourceSummary: "Source 別サマリー",
    sourceProcessingDescription: "影響範囲と処理状態を見やすくするため、source 処理サマリーを error event と分けて表示します。",
    noSourceItems: "この run に保存された source-item row はありません。",
    warning: (count: number) => `warning ${count} 件`,
    error: (count: number) => `error ${count} 件`,
    sourceDoc: "Source doc",
    snapshot: "Snapshot",
    parsedDoc: "Parsed doc",
    fetched: "Fetched",
    parseNote: "Parse note",
    safeMetadata: "Safe stage metadata",
    openSourceUrl: "ソースURLを開く",
    failureSummary: "失敗サマリー",
    runSourceIssues: "Run と source の問題",
    failureDescription: "何が問題で影響範囲がどの程度か説明できるよう、エラーと degraded event サマリーをまとめて表示します。",
    noIssues: "この run に記録された run-level または source-level の問題はありません。",
    runEvent: "Run event",
    sourceEvent: "Source event",
    runSummary: "Run サマリー",
    usageSummary: "Usage サマリー",
    modelTokenUsage: "Model と token usage",
    usageDescription: "実行コストを正確な診断画面と結びつけられるよう、同じ run context で usage を表示します。",
    usageRecords: "Usage records",
    modelExecutions: "Model executions",
    totalTokens: "Total tokens",
    estimatedCost: "Estimated cost",
    noUsage: "この run に紐づく usage record はありません。",
    records: (count: number) => `record ${count} 件`,
    promptTokens: "Prompt tokens",
    completionTokens: "Completion tokens",
    cost: "Cost",
    relatedReviews: "関連 review task",
    reviewWorkload: "この run が生成した review workload",
    reviewDescription: "実行診断から task-level evidence review へ移動できるよう、この run で作成された queue 項目へリンクします。",
    noReviews: "この run は関連 review task を生成していません。",
    candidate: "Candidate",
    bank: "銀行",
    validation: "Validation",
    created: "作成",
    runContext: "Run context",
    retryScope: "Retry と scope サマリー",
    contextDescription: "主要識別子と retry の関連をサイドに集約し、メイン領域を診断に集中させます。",
    pipelineStage: "Pipeline stage",
    requestId: "Request ID",
    retryOf: "Retry of",
    retriedBy: "Retried by",
    missing: "なし",
  },
} as const;

export function RunDetailSurface({ csrfToken, detail, locale }: RunDetailSurfaceProps) {
  const copy = RUN_DETAIL_COPY[locale];
  const router = useRouter();
  const [retryPending, setRetryPending] = useState(false);
  const [retryMessage, setRetryMessage] = useState<string | null>(null);
  const [retryError, setRetryError] = useState<string | null>(null);

  async function handleRetry() {
    setRetryPending(true);
    setRetryMessage(null);
    setRetryError(null);
    try {
      const response = await fetch(`/admin/runs/${detail.run.run_id}/retry`, {
        method: "POST",
        headers: {
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
      });
      const payload = (await response.json()) as { data?: RunRetryResponse; error?: { message?: string } };
      if (!response.ok || !payload.data?.retry_run_id) {
        setRetryError(payload.error?.message ?? copy.retryFailed);
        return;
      }
      setRetryMessage(copy.retryQueued);
      router.push(buildAdminHref(`/admin/runs/${payload.data.retry_run_id}`, new URLSearchParams(), locale));
      router.refresh();
    } catch {
      setRetryError(copy.retryApiFailed);
    } finally {
      setRetryPending(false);
    }
  }

  return (
    <section className="grid gap-6">
      <AdminPageHeader
        actions={
          <>
            <Button asChild variant="outline">
              <Link href={buildAdminHref("/admin/runs", new URLSearchParams(), locale)}>{copy.back}</Link>
            </Button>
            {detail.run.retry_action.available ? (
              <Button disabled={retryPending} onClick={handleRetry} type="button">
                {retryPending ? copy.retrying : copy.retryRun}
              </Button>
            ) : null}
            {detail.run.retry_of_run_id ? (
              <Button asChild variant="outline">
                <Link href={buildAdminHref(`/admin/runs/${detail.run.retry_of_run_id}`, new URLSearchParams(), locale)}>{copy.previousAttempt}</Link>
              </Button>
            ) : null}
            {detail.run.retried_by_run_id ? (
              <Button asChild variant="outline">
                <Link href={buildAdminHref(`/admin/runs/${detail.run.retried_by_run_id}`, new URLSearchParams(), locale)}>{copy.nextAttempt}</Link>
              </Button>
            ) : null}
          </>
        }
        badges={
          <>
            <span className={cn("rounded-full px-3 py-1 text-xs font-medium", runStateBadgeClasses(detail.run.run_status))}>
              {toTitleCase(detail.run.run_status)}
            </span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              {toTitleCase(detail.run.run_type)}
            </span>
            {detail.run.partial_completion_flag ? (
              <span className="rounded-full bg-warning-soft px-3 py-1 text-xs font-medium text-warning">{copy.partialCompletion}</span>
            ) : null}
          </>
        }
        description={copy.description}
        path={copy.path}
        title={detail.run.run_id}
      />

      <article className="rounded-lg border border-border/80 bg-background p-4">
        <div className="grid gap-3 lg:grid-cols-4">
          <SummaryStat label={copy.sourceItems} value={String(detail.run.source_item_count)} />
          <SummaryStat label={copy.candidates} value={String(detail.run.candidate_count)} />
          <SummaryStat label={copy.reviewQueued} value={String(detail.run.review_queued_count)} />
          <SummaryStat label={copy.correlation} value={detail.run.correlation_id ?? copy.missing} />
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <SummaryStat label={copy.started} value={formatTimestamp(detail.run.started_at, copy.missing)} />
          <SummaryStat label={copy.completed} value={formatTimestamp(detail.run.completed_at, copy.missing)} />
          <SummaryStat label={copy.trigger} value={toTitleCase(detail.run.trigger_type)} />
          <SummaryStat label={copy.actor} value={detail.run.triggered_by ?? copy.missing} />
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
        {!detail.run.retry_action.available && detail.run.run_status === "failed" && !detail.run.retried_by_run_id && detail.run.retry_action.reason ? (
          <p className="mt-4 text-sm leading-6 text-muted-foreground">{detail.run.retry_action.reason}</p>
        ) : null}
      </article>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.16fr)_minmax(20rem,0.84fr)]">
        <div className="grid gap-6">
          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow={copy.stageSummary}
              title={copy.executionStageStrip}
              description={copy.stageSummaryDescription}
            />
            <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {detail.stage_summaries.map((item) => (
                <div className="rounded-2xl border border-border/80 bg-background p-4" key={item.stage_name}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-foreground">{item.stage_label}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{copy.executionEntries(item.execution_count)}</p>
                    </div>
                    <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", stageStatusBadgeClasses(item.stage_status))}>
                      {toTitleCase(item.stage_status)}
                    </span>
                  </div>
                  <dl className="mt-4 grid gap-2 text-sm">
                    <MetaRow label={copy.success} value={String(item.success_count)} />
                    <MetaRow label={copy.failure} value={String(item.failure_count)} />
                    <MetaRow label={copy.started} value={formatTimestamp(item.started_at, copy.missing)} />
                    <MetaRow label={copy.completed} value={formatTimestamp(item.completed_at, copy.missing)} />
                  </dl>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow={copy.sourceProcessing}
              title={copy.perSourceSummary}
              description={copy.sourceProcessingDescription}
            />

            {detail.source_items.length === 0 ? (
              <p className="mt-6 text-sm leading-6 text-muted-foreground">{copy.noSourceItems}</p>
            ) : (
              <div className="mt-6 grid gap-3">
                {detail.source_items.map((item) => (
                  <div className="rounded-2xl border border-border/80 bg-background p-4" key={item.source_document_id}>
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div>
                        <p className="text-sm font-medium text-foreground">{item.source_id}</p>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {item.bank_name} {item.country_code} {toTitleCase(item.source_type)}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", stageStatusBadgeClasses(item.stage_status))}>
                          {toTitleCase(item.stage_status)}
                        </span>
                        {item.warning_count > 0 ? (
                          <span className="rounded-full bg-warning-soft px-2.5 py-1 text-[11px] font-medium text-warning">
                            {copy.warning(item.warning_count)}
                          </span>
                        ) : null}
                        {item.error_count > 0 ? (
                          <span className="rounded-full bg-destructive/10 px-2.5 py-1 text-[11px] font-medium text-destructive">
                            {copy.error(item.error_count)}
                          </span>
                        ) : null}
                      </div>
                    </div>

                    <dl className="mt-4 grid gap-2 text-sm">
                      <MetaRow label={copy.sourceDoc} value={item.source_document_id} />
                      <MetaRow label={copy.snapshot} value={item.snapshot_id ?? copy.missing} />
                      <MetaRow label={copy.parsedDoc} value={item.parsed_document_id ?? copy.missing} />
                      <MetaRow label={copy.fetched} value={formatTimestamp(item.fetched_at, copy.missing)} />
                    </dl>

                    {item.error_summary ? (
                      <p className="mt-4 rounded-2xl border border-destructive/15 bg-destructive/5 px-3 py-3 text-sm leading-6 text-destructive">
                        {item.error_summary}
                      </p>
                    ) : null}

                    {item.parse_quality_note ? (
                      <p className="mt-4 rounded-2xl bg-muted px-3 py-3 text-sm leading-6 text-muted-foreground">
                        {copy.parseNote}: {item.parse_quality_note}
                      </p>
                    ) : null}

                    {item.runtime_notes.length > 0 ? (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {item.runtime_notes.map((note) => (
                          <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground" key={note}>
                            {note}
                          </span>
                        ))}
                      </div>
                    ) : null}

                    {Object.keys(item.safe_metadata).length > 0 ? (
                      <div className="mt-4 rounded-2xl border border-border/70 px-3 py-3">
                        <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">{copy.safeMetadata}</p>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {Object.entries(item.safe_metadata).map(([key, value]) => (
                            <span className="rounded-full bg-info-soft px-2.5 py-1 text-[11px] font-medium text-info" key={`${item.source_document_id}-${key}`}>
                              {toTitleCase(key)}: {formatValue(value)}
                            </span>
                          ))}
                        </div>
                      </div>
                    ) : null}

                    {item.source_url ? (
                      <a className="mt-4 inline-flex text-sm font-medium text-primary underline-offset-4 hover:underline" href={item.source_url} rel="noreferrer" target="_blank">
                        {copy.openSourceUrl}
                      </a>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow={copy.failureSummary}
              title={copy.runSourceIssues}
              description={copy.failureDescription}
            />

            {detail.error_events.length === 0 ? (
              <p className="mt-6 text-sm leading-6 text-muted-foreground">{copy.noIssues}</p>
            ) : (
              <div className="mt-6 grid gap-3">
                {detail.error_events.map((item, index) => (
                  <div className="rounded-2xl border border-border/80 bg-background p-4" key={`${item.scope}-${item.source_document_id ?? index}`}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium text-foreground">{item.scope === "run" ? copy.runEvent : item.source_id ?? item.source_document_id ?? copy.sourceEvent}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{item.stage_status ? toTitleCase(item.stage_status) : copy.runSummary}</p>
                      </div>
                      <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", issueBadgeClasses(item.severity))}>
                        {toTitleCase(item.severity)}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-muted-foreground">{item.summary}</p>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                        {copy.warning(item.warning_count)}
                      </span>
                      <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                        {copy.error(item.error_count)}
                      </span>
                    </div>
                    {item.runtime_notes.length > 0 ? (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {item.runtime_notes.map((note) => (
                          <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground" key={note}>
                            {note}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </article>
        </div>

        <div className="grid gap-6">
          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow={copy.usageSummary}
              title={copy.modelTokenUsage}
              description={copy.usageDescription}
            />
            <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-1">
              <SummaryStat label={copy.usageRecords} value={String(detail.usage_summary.usage_record_count)} />
              <SummaryStat label={copy.modelExecutions} value={String(detail.usage_summary.model_execution_count)} />
              <SummaryStat label={copy.totalTokens} value={detail.usage_summary.total_tokens.toLocaleString("en-CA")} />
              <SummaryStat label={copy.estimatedCost} value={formatCost(detail.usage_summary.estimated_cost)} />
            </div>

            {detail.usage_summary.by_stage.length === 0 ? (
              <p className="mt-6 text-sm leading-6 text-muted-foreground">{copy.noUsage}</p>
            ) : (
              <div className="mt-6 grid gap-3">
                {detail.usage_summary.by_stage.map((item) => (
                  <div className="rounded-2xl border border-border/80 bg-background p-4" key={item.stage_name}>
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-medium text-foreground">{item.stage_label}</p>
                      <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                        {copy.records(item.usage_record_count)}
                      </span>
                    </div>
                    <dl className="mt-4 grid gap-2 text-sm">
                      <MetaRow label={copy.promptTokens} value={item.prompt_tokens.toLocaleString("en-CA")} />
                      <MetaRow label={copy.completionTokens} value={item.completion_tokens.toLocaleString("en-CA")} />
                      <MetaRow label={copy.totalTokens} value={item.total_tokens.toLocaleString("en-CA")} />
                      <MetaRow label={copy.cost} value={formatCost(item.estimated_cost)} />
                    </dl>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow={copy.relatedReviews}
              title={copy.reviewWorkload}
              description={copy.reviewDescription}
            />

            {detail.related_review_tasks.length === 0 ? (
              <p className="mt-6 text-sm leading-6 text-muted-foreground">{copy.noReviews}</p>
            ) : (
              <div className="mt-6 grid gap-3">
                {detail.related_review_tasks.map((item) => (
                  <div className="rounded-2xl border border-border/80 bg-background p-4" key={item.review_task_id}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <Link className="text-sm font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/reviews/${item.review_task_id}`, new URLSearchParams(), locale)}>
                          {item.review_task_id}
                        </Link>
                        <p className="mt-1 text-sm leading-6 text-muted-foreground">{item.product_name}</p>
                      </div>
                      <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", reviewStateBadgeClasses(item.review_state))}>
                        {toTitleCase(item.review_state)}
                      </span>
                    </div>
                    <dl className="mt-4 grid gap-2 text-sm">
                      <MetaRow label={copy.candidate} value={item.candidate_id} />
                      <MetaRow label={copy.bank} value={item.bank_name} />
                      <MetaRow label={copy.validation} value={toTitleCase(item.validation_status)} />
                      <MetaRow label={copy.created} value={formatTimestamp(item.created_at, copy.missing)} />
                    </dl>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow={copy.runContext}
              title={copy.retryScope}
              description={copy.contextDescription}
            />
            <div className="mt-6 rounded-2xl border border-border/80 bg-background p-4">
              <dl className="grid gap-3 text-sm">
                <MetaRow label={copy.pipelineStage} value={detail.run.pipeline_stage ?? copy.missing} />
                <MetaRow label={copy.requestId} value={detail.run.request_id ?? copy.missing} />
                <MetaRow label={copy.retryOf} value={detail.run.retry_of_run_id ?? copy.missing} />
                <MetaRow label={copy.retriedBy} value={detail.run.retried_by_run_id ?? copy.missing} />
              </dl>

              {detail.run.error_summary ? (
                <p className="mt-4 rounded-2xl border border-destructive/15 bg-destructive/5 px-3 py-3 text-sm leading-6 text-destructive">
                  {detail.run.error_summary}
                </p>
              ) : null}

              {detail.run.source_ids.length > 0 ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  {detail.run.source_ids.map((item) => (
                    <span className="rounded-full bg-info-soft px-2.5 py-1 text-[11px] font-medium text-info" key={item}>
                      {item}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}

function SectionHeading({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return (
    <div>
      <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{eyebrow}</p>
      <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{description}</p>
    </div>
  );
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/80 bg-background px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="text-right text-foreground">{value}</dd>
    </div>
  );
}

function formatTimestamp(value: string | null, missing = "n/a") {
  if (!value) {
    return missing;
  }
  return new Intl.DateTimeFormat("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatCost(value: number) {
  return `$${value.toFixed(6)}`;
}

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  return JSON.stringify(value);
}

function toTitleCase(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function runStateBadgeClasses(state: string) {
  switch (state) {
    case "started":
      return "bg-info-soft text-info";
    case "completed":
      return "bg-success-soft text-success";
    case "failed":
      return "bg-destructive/10 text-destructive";
    case "retried":
      return "bg-warning-soft text-warning";
    default:
      return "bg-muted text-muted-foreground";
  }
}

function reviewStateBadgeClasses(state: string) {
  switch (state) {
    case "queued":
      return "bg-info-soft text-info";
    case "deferred":
      return "bg-warning-soft text-warning";
    case "approved":
    case "edited":
      return "bg-success-soft text-success";
    case "rejected":
      return "bg-destructive/10 text-destructive";
    default:
      return "bg-muted text-muted-foreground";
  }
}

function stageStatusBadgeClasses(status: string) {
  switch (status) {
    case "completed":
      return "bg-success-soft text-success";
    case "degraded":
      return "bg-warning-soft text-warning";
    case "failed":
      return "bg-destructive/10 text-destructive";
    case "started":
      return "bg-info-soft text-info";
    case "retried":
      return "bg-muted text-muted-foreground";
    default:
      return "bg-muted text-muted-foreground";
  }
}

function issueBadgeClasses(severity: string) {
  if (severity === "error") {
    return "bg-destructive/10 text-destructive";
  }
  return "bg-warning-soft text-warning";
}
