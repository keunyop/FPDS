"use client";

import Link from "next/link";
import { Activity, CircleX, LoaderCircle, Split } from "lucide-react";

import { AdminTableAutoRefresh } from "@/components/fpds/admin/admin-table-auto-refresh";
import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { Stats5 } from "@/components/stats5";
import { Button } from "@/components/ui/button";
import type { RunStatusListResponse } from "@/lib/admin-api";
import { buildAdminHref, formatAdminDateTime, translateRunState, type AdminLocale } from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

const RUN_STATES = ["started", "completed", "failed", "retried"] as const;
const COMMON_RUN_TYPES = ["snapshot_capture", "parse_chunk", "extraction", "normalization", "validation_routing"] as const;

const RUN_STATUS_COPY = {
  en: {
    headerDescription: "Run state, partial completion, and execution diagnostics.",
    path: ["Operations", "Runs"],
    title: "Runs",
    snapshotTitle: "Run Snapshot",
    visibleRuns: "Visible runs",
    currentFilters: "Current filters.",
    failed: "Failed",
    failedNote: "Failed runs.",
    partial: "Partial",
    partialNote: "Degraded runs.",
    inProgress: "In progress",
    inProgressNote: "Still running.",
    filtersEyebrow: "Filters and sort",
    controlsTitle: "Run Controls",
    defaultRuns: "Default runs",
    allStates: "All states",
    search: "Search",
    searchPlaceholder: "run, trigger, actor, or correlation",
    runType: "Run type",
    allTypes: "All types",
    sortBy: "Sort by",
    order: "Order",
    startedTime: "Started time",
    completedTime: "Completed time",
    candidateCount: "Candidate count",
    reviewQueued: "Review queued",
    descending: "Descending",
    ascending: "Ascending",
    scope: "Scope",
    partialOnly: "Partial only",
    runStates: "Run states",
    startedFrom: "Started from",
    startedTo: "Started to",
    applyFilters: "Search",
    reset: "Reset",
    results: "Results",
    tableTitle: "Run table",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `Page ${page} of ${Math.max(totalPages, 1)} with ${totalItems} matching run${totalItems === 1 ? "" : "s"}.`,
    noMatches: "No matching runs",
    emptyTitle: "The current run filter returned no execution history.",
    emptyBody:
      "Widen the state filter, clear the search term, or turn off the partial-only filter. Retries and started runs remain queryable.",
    resetRunFilters: "Reset run filters",
    run: "Run",
    type: "Type",
    status: "Status",
    window: "Window",
    sourceSummary: "Source summary",
    candidateSummary: "Candidate summary",
    errorSummary: "Error summary",
    retryChain: "Retry chain",
    action: "Action",
    trigger: "Trigger",
    correlation: "Correlation",
    partialCompletion: "Partial completion",
    completed: "Completed",
    sourceItems: "source items",
    success: "success",
    failure: "failure",
    candidates: "candidates",
    queuedForReview: "queued for review",
    noRunError: "No run-level error summary persisted.",
    originalRun: "Original run",
    next: "Next",
    openDetail: "Open detail",
    showing: (from: number, to: number, total: number) => `Showing ${from}-${to} of ${total}`,
    previous: "Previous",
  },
  ko: {
    headerDescription: "실행 상태, 부분 완료, 실행 진단.",
    path: ["운영", "실행"],
    title: "실행",
    snapshotTitle: "실행 스냅샷",
    visibleRuns: "표시된 실행",
    currentFilters: "현재 필터.",
    failed: "실패",
    failedNote: "실패한 실행.",
    partial: "부분 완료",
    partialNote: "저하된 실행.",
    inProgress: "진행 중",
    inProgressNote: "아직 실행 중.",
    filtersEyebrow: "필터 및 정렬",
    controlsTitle: "실행 제어",
    defaultRuns: "기본 실행",
    allStates: "모든 상태",
    search: "검색",
    searchPlaceholder: "실행, 트리거, 작업자, correlation",
    runType: "실행 유형",
    allTypes: "모든 유형",
    sortBy: "정렬 기준",
    order: "순서",
    startedTime: "시작 시간",
    completedTime: "완료 시간",
    candidateCount: "후보 수",
    reviewQueued: "검토 대기",
    descending: "내림차순",
    ascending: "오름차순",
    scope: "범위",
    partialOnly: "부분 완료만",
    runStates: "실행 상태",
    startedFrom: "시작일",
    startedTo: "종료일",
    applyFilters: "Search",
    reset: "초기화",
    results: "결과",
    tableTitle: "실행 테이블",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `${Math.max(totalPages, 1)}페이지 중 ${page}페이지, 일치 실행 ${totalItems}건.`,
    noMatches: "일치하는 실행 없음",
    emptyTitle: "현재 실행 필터에 해당하는 실행 이력이 없습니다.",
    emptyBody: "상태 필터를 넓히거나 검색어를 지우거나 부분 완료 필터를 끄세요. 재시도와 시작된 실행은 계속 조회할 수 있습니다.",
    resetRunFilters: "실행 필터 초기화",
    run: "실행",
    type: "유형",
    status: "상태",
    window: "구간",
    sourceSummary: "소스 요약",
    candidateSummary: "후보 요약",
    errorSummary: "오류 요약",
    retryChain: "재시도 연결",
    action: "작업",
    trigger: "트리거",
    correlation: "Correlation",
    partialCompletion: "부분 완료",
    completed: "완료",
    sourceItems: "소스 항목",
    success: "성공",
    failure: "실패",
    candidates: "후보",
    queuedForReview: "검토 대기",
    noRunError: "실행 수준 오류 요약이 저장되지 않았습니다.",
    originalRun: "원본 실행",
    next: "다음",
    openDetail: "상세 열기",
    showing: (from: number, to: number, total: number) => `${total}건 중 ${from}-${to} 표시`,
    previous: "이전",
  },
  ja: {
    headerDescription: "実行状態、部分完了、実行診断。",
    path: ["運用", "実行"],
    title: "実行",
    snapshotTitle: "実行 Snapshot",
    visibleRuns: "表示中の実行",
    currentFilters: "現在のフィルター。",
    failed: "失敗",
    failedNote: "失敗した実行。",
    partial: "部分完了",
    partialNote: "低下した実行。",
    inProgress: "進行中",
    inProgressNote: "まだ実行中。",
    filtersEyebrow: "フィルターと並び替え",
    controlsTitle: "実行制御",
    defaultRuns: "既定の実行",
    allStates: "すべての状態",
    search: "検索",
    searchPlaceholder: "実行、トリガー、作業者、correlation",
    runType: "実行タイプ",
    allTypes: "すべてのタイプ",
    sortBy: "並び替え",
    order: "順序",
    startedTime: "開始日時",
    completedTime: "完了日時",
    candidateCount: "候補数",
    reviewQueued: "審査待ち",
    descending: "降順",
    ascending: "昇順",
    scope: "範囲",
    partialOnly: "部分完了のみ",
    runStates: "実行状態",
    startedFrom: "開始日",
    startedTo: "終了日",
    applyFilters: "Search",
    reset: "リセット",
    results: "結果",
    tableTitle: "実行テーブル",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `${Math.max(totalPages, 1)}ページ中${page}ページ、該当実行${totalItems}件。`,
    noMatches: "該当する実行なし",
    emptyTitle: "現在の実行フィルターに該当する実行履歴はありません。",
    emptyBody: "状態フィルターを広げるか、検索語を消すか、部分完了フィルターをオフにしてください。再試行と開始済み実行は引き続き検索できます。",
    resetRunFilters: "実行フィルターをリセット",
    run: "実行",
    type: "タイプ",
    status: "状態",
    window: "期間",
    sourceSummary: "ソース要約",
    candidateSummary: "候補要約",
    errorSummary: "エラー要約",
    retryChain: "再試行チェーン",
    action: "操作",
    trigger: "トリガー",
    correlation: "Correlation",
    partialCompletion: "部分完了",
    completed: "完了",
    sourceItems: "ソース項目",
    success: "成功",
    failure: "失敗",
    candidates: "候補",
    queuedForReview: "審査待ち",
    noRunError: "実行レベルのエラー要約は保存されていません。",
    originalRun: "元の実行",
    next: "次",
    openDetail: "詳細を開く",
    showing: (from: number, to: number, total: number) => `${total}件中${from}-${to}件を表示`,
    previous: "前へ",
  },
} as const;

export type RunStatusPageFilters = {
  q: string;
  states: string[];
  runType: string;
  partialOnly: boolean;
  startedFrom: string;
  startedTo: string;
  sortBy: string;
  sortOrder: "asc" | "desc";
  page: number;
};

type RunStatusSurfaceProps = {
  filters: RunStatusPageFilters;
  runs: RunStatusListResponse;
  locale: AdminLocale;
};

export function RunStatusSurface({ filters, runs, locale }: RunStatusSurfaceProps) {
  const copy = RUN_STATUS_COPY[locale];
  const stateCounts = runs.summary.state_counts;
  const runTypeOptions = Array.from(new Set([...COMMON_RUN_TYPES, ...Object.keys(runs.summary.run_type_counts)])).sort();
  const statItems = [
    {
      label: copy.visibleRuns,
      value: String(runs.summary.total_items),
      note: copy.currentFilters,
      tone: "info" as const,
      icon: Activity,
    },
    {
      label: copy.failed,
      value: String(stateCounts.failed ?? 0),
      note: copy.failedNote,
      tone: "warning" as const,
      icon: CircleX,
    },
    {
      label: copy.partial,
      value: String(runs.summary.partial_items),
      note: copy.partialNote,
      tone: "neutral" as const,
      icon: Split,
    },
    {
      label: copy.inProgress,
      value: String(stateCounts.started ?? 0),
      note: copy.inProgressNote,
      tone: "success" as const,
      icon: LoaderCircle,
    },
  ];

  return (
    <section className="grid min-w-0 gap-6">
      <AdminTableAutoRefresh />

      <AdminPageHeader
        description={copy.headerDescription}
        path={copy.path}
        title={copy.title}
      />

      <Stats5
        className="[&>div]:md:grid-cols-2 [&>div]:xl:grid-cols-4"
        framed={false}
        items={statItems}
      />

      <article className="min-w-0 rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <div className="flex flex-col gap-4 border-b border-border/80 pb-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.filtersEyebrow}</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{copy.controlsTitle}</h2>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button asChild size="sm" variant="outline">
              <Link href={buildAdminHref("/admin/runs", new URLSearchParams(), locale)}>{copy.defaultRuns}</Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href={buildRunHref(filters, { states: [...RUN_STATES], page: 1 }, locale)}>{copy.allStates}</Link>
            </Button>
          </div>
        </div>

        <form action={buildAdminHref("/admin/runs", new URLSearchParams(), locale)} className="mt-6 grid gap-5">
          <div className="grid min-w-0 gap-4 xl:grid-cols-[1.45fr_repeat(4,minmax(0,1fr))]">
            <label className="grid min-w-0 gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.search}</span>
              <input
                className="h-10 min-w-0 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.q}
                name="q"
                placeholder={copy.searchPlaceholder}
                type="search"
              />
            </label>

            <label className="grid min-w-0 gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.runType}</span>
              <select
                className="h-10 min-w-0 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.runType}
                name="run_type"
              >
                <option value="">{copy.allTypes}</option>
                {runTypeOptions.map((option) => (
                  <option key={option} value={option}>
                    {toTitleCase(option)}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid min-w-0 gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.sortBy}</span>
              <select
                className="h-10 min-w-0 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.sortBy}
                name="sort_by"
              >
                <option value="started_at">{copy.startedTime}</option>
                <option value="completed_at">{copy.completedTime}</option>
                <option value="candidate_count">{copy.candidateCount}</option>
                <option value="review_queued_count">{copy.reviewQueued}</option>
                <option value="run_type">{copy.runType}</option>
              </select>
            </label>

            <label className="grid min-w-0 gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.order}</span>
              <select
                className="h-10 min-w-0 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.sortOrder}
                name="sort_order"
              >
                <option value="desc">{copy.descending}</option>
                <option value="asc">{copy.ascending}</option>
              </select>
            </label>

            <label className="grid min-w-0 gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.scope}</span>
              <span className="flex h-10 min-w-0 items-center rounded-xl border border-border bg-background px-3 text-sm text-foreground">
                <input
                  className="mr-2 h-4 w-4 rounded border-border text-primary accent-[var(--primary)]"
                  defaultChecked={filters.partialOnly}
                  name="partial_only"
                  type="checkbox"
                  value="true"
                />
                {copy.partialOnly}
              </span>
            </label>
          </div>

          <div className="grid min-w-0 gap-4 lg:grid-cols-[1.3fr_1fr_1fr_auto]">
            <fieldset className="grid min-w-0 gap-2 text-sm">
              <legend className="font-medium text-foreground">{copy.runStates}</legend>
              <div className="flex flex-wrap gap-2">
                {RUN_STATES.map((state) => (
                  <label
                    className="inline-flex items-center gap-2 rounded-full border border-border bg-background px-3 py-2 text-sm text-foreground"
                    key={state}
                  >
                    <input
                      className="h-4 w-4 rounded border-border text-primary accent-[var(--primary)]"
                      defaultChecked={filters.states.includes(state)}
                      name="state"
                      type="checkbox"
                      value={state}
                    />
                    <span>{translateRunState(locale, state)}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <label className="grid min-w-0 gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.startedFrom}</span>
              <input
                className="h-10 min-w-0 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.startedFrom}
                name="started_from"
                type="date"
              />
            </label>

            <label className="grid min-w-0 gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.startedTo}</span>
              <input
                className="h-10 min-w-0 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.startedTo}
                name="started_to"
                type="date"
              />
            </label>

            <div className="flex items-end gap-2">
              <Button type="submit">{copy.applyFilters}</Button>
              <Button asChild variant="outline">
                <Link href={buildAdminHref("/admin/runs", new URLSearchParams(), locale)}>{copy.reset}</Link>
              </Button>
            </div>
          </div>
        </form>
      </article>

      <article className="min-w-0 overflow-hidden rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="flex flex-col gap-3 border-b border-border/80 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.results}</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{copy.tableTitle}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {copy.pageSummary(runs.page, runs.total_pages, runs.total_items)}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {filters.states.map((state) => (
              <span className={cn("rounded-full px-3 py-1 text-xs font-medium", runStateBadgeClasses(state))} key={state}>
                {translateRunState(locale, state)}
              </span>
            ))}
            {filters.runType ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {toTitleCase(filters.runType)}
              </span>
            ) : null}
            {filters.partialOnly ? (
              <span className="rounded-full bg-warning-soft px-3 py-1 text-xs font-medium text-warning">{copy.partialOnly}</span>
            ) : null}
          </div>
        </div>

        {runs.items.length === 0 ? (
          <div className="px-6 py-10">
            <div className="rounded-[1.5rem] border border-dashed border-border bg-background px-6 py-8">
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.noMatches}</p>
              <h3 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
                {copy.emptyTitle}
              </h3>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
                {copy.emptyBody}
              </p>
              <div className="mt-6">
                <Button asChild variant="outline">
                  <Link href={buildAdminHref("/admin/runs", new URLSearchParams(), locale)}>{copy.resetRunFilters}</Link>
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="max-w-full overflow-x-auto px-6 py-5">
              <table className="min-w-[1080px] table-fixed border-separate border-spacing-0">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.run}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.type}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.status}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.window}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.sourceSummary}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.candidateSummary}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.errorSummary}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.action}</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.items.map((item) => (
                    <tr className="align-top" key={item.run_id}>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          <Link className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/runs/${item.run_id}`, new URLSearchParams(), locale)}>
                            {item.run_id}
                          </Link>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
                            {toTitleCase(item.run_type)}
                          </span>
                          <span className="text-xs text-muted-foreground">{copy.trigger} {toTitleCase(item.trigger_type)}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <span className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", runStateBadgeClasses(item.run_status))}>
                            {translateRunState(locale, item.run_status)}
                          </span>
                          {item.partial_completion_flag ? (
                            <span className="inline-flex w-fit rounded-full bg-warning-soft px-2.5 py-1 text-xs font-medium text-warning">
                              {copy.partialCompletion}
                            </span>
                          ) : null}
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          <span className="text-sm text-foreground">{formatAdminDateTime(locale, item.started_at)}</span>
                          <span className="text-xs text-muted-foreground">{copy.completed} {formatAdminDateTime(locale, item.completed_at)}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1 text-sm">
                          <span className="font-medium text-foreground">{item.source_item_count} {copy.sourceItems}</span>
                          <span className="text-muted-foreground">
                            {item.success_count} {copy.success} / {item.failure_count} {copy.failure}
                          </span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1 text-sm">
                          <span className="font-medium text-foreground">{item.candidate_count} {copy.candidates}</span>
                          <span className="text-muted-foreground">{item.review_queued_count} {copy.queuedForReview}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <p className="text-sm leading-6 text-muted-foreground">{item.error_summary ?? copy.noRunError}</p>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <Button asChild size="sm" variant="outline">
                          <Link href={buildAdminHref(`/admin/runs/${item.run_id}`, new URLSearchParams(), locale)}>{copy.openDetail}</Link>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-col gap-3 border-t border-border/80 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-muted-foreground">
                {copy.showing((runs.page - 1) * runs.page_size + 1, Math.min(runs.page * runs.page_size, runs.total_items), runs.total_items)}
              </p>
              <div className="flex items-center gap-2">
                {runs.page > 1 ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildRunHref(filters, { page: Math.max(1, runs.page - 1) }, locale)}>{copy.previous}</Link>
                  </Button>
                ) : (
                  <span className="inline-flex h-7 items-center rounded-[min(var(--radius-md),12px)] border border-border bg-muted px-2.5 text-[0.8rem] text-muted-foreground opacity-60">
                    {copy.previous}
                  </span>
                )}
                {runs.has_next_page ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildRunHref(filters, { page: runs.page + 1 }, locale)}>{copy.next}</Link>
                  </Button>
                ) : (
                  <span className="inline-flex h-7 items-center rounded-[min(var(--radius-md),12px)] border border-border bg-muted px-2.5 text-[0.8rem] text-muted-foreground opacity-60">
                    {copy.next}
                  </span>
                )}
              </div>
            </div>
          </>
        )}
      </article>
    </section>
  );
}

function buildRunHref(filters: RunStatusPageFilters, overrides: Partial<RunStatusPageFilters>, locale: AdminLocale) {
  const next = {
    ...filters,
    ...overrides,
  };
  const params = new URLSearchParams();
  if (next.q) {
    params.set("q", next.q);
  }
  for (const state of next.states) {
    params.append("state", state);
  }
  if (next.runType) {
    params.set("run_type", next.runType);
  }
  if (next.partialOnly) {
    params.set("partial_only", "true");
  }
  if (next.startedFrom) {
    params.set("started_from", next.startedFrom);
  }
  if (next.startedTo) {
    params.set("started_to", next.startedTo);
  }
  if (next.sortBy) {
    params.set("sort_by", next.sortBy);
  }
  if (next.sortOrder) {
    params.set("sort_order", next.sortOrder);
  }
  if (next.page > 1) {
    params.set("page", String(next.page));
  }

  return buildAdminHref("/admin/runs", params, locale);
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
