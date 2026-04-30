import Link from "next/link";
import { ClipboardList, ListChecks, CirclePause, TriangleAlert } from "lucide-react";

import { AdminTableAutoRefresh } from "@/components/fpds/admin/admin-table-auto-refresh";
import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { Stats5 } from "@/components/stats5";
import { Button } from "@/components/ui/button";
import type { ProductTypeItem, ReviewQueueResponse } from "@/lib/admin-api";
import {
  buildAdminHref,
  formatAdminDateTime,
  translateReviewState,
  translateValidationStatus,
  type AdminLocale,
} from "@/lib/admin-i18n";
import { buildAdminProductTypeLabelMap, buildAdminProductTypeOptions, formatAdminProductType } from "@/lib/admin-product-types";
import { cn } from "@/lib/utils";

const REVIEW_STATES = ["queued", "deferred", "approved", "edited", "rejected"] as const;
const BANK_OPTIONS = ["TD", "RBC", "BMO", "SCOTIA", "CIBC"] as const;
const VALIDATION_OPTIONS = ["pass", "warning", "error"] as const;

const REVIEW_QUEUE_COPY = {
  en: {
    headerDescription: "Active review work, filters, and queue drill-in.",
    path: ["Review", "Review Queue"],
    title: "Review Queue",
    snapshotTitle: "Queue Snapshot",
    visibleTasks: "Visible tasks",
    currentFilters: "Current filters.",
    queuedNote: "Needs review.",
    deferredNote: "Parked work.",
    warningsErrors: "Warnings + Errors",
    needsAttention: "Needs attention.",
    filtersEyebrow: "Filters and sort",
    controlsTitle: "Queue Controls",
    activeQueue: "Active queue",
    allStates: "All states",
    search: "Search",
    searchPlaceholder: "task, candidate, run, bank, or product",
    bank: "Bank",
    allBanks: "All banks",
    productType: "Product type",
    allTypes: "All types",
    validation: "Validation",
    allStatuses: "All statuses",
    sortBy: "Sort by",
    order: "Order",
    priority: "Priority",
    createdTime: "Created time",
    updatedTime: "Updated time",
    confidence: "Confidence",
    productName: "Product name",
    descending: "Descending",
    ascending: "Ascending",
    reviewStates: "Review states",
    createdFrom: "Created from",
    createdTo: "Created to",
    applyFilters: "Search",
    reset: "Reset",
    results: "Results",
    tableTitle: "Reviewer intake table",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `Page ${page} of ${Math.max(totalPages, 1)} with ${totalItems} matching task${totalItems === 1 ? "" : "s"}.`,
    noMatches: "No matching tasks",
    emptyTitle: "The current queue filter returned no review work.",
    emptyBody:
      "Widen the state filter, clear the search term, or reset the form. Active queue remains the default intake view.",
    resetQueueFilters: "Reset queue filters",
    task: "Task",
    country: "Country",
    product: "Product",
    issueSummary: "Issue summary",
    created: "Created",
    status: "Status",
    action: "Action",
    candidate: "Candidate",
    run: "Run",
    sourceConfidence: "Source confidence",
    updated: "Updated",
    openDetail: "Open detail",
    detailHint: "Decision controls are available on the detail and trace surface.",
    showing: (from: number, to: number, total: number) => `Showing ${from}-${to} of ${total}`,
    previous: "Previous",
    next: "Next",
  },
  ko: {
    headerDescription: "활성 검토 작업, 필터, 대기열 drill-in.",
    path: ["검토", "검토 대기열"],
    title: "검토 대기열",
    snapshotTitle: "대기열 스냅샷",
    visibleTasks: "표시된 작업",
    currentFilters: "현재 필터.",
    queuedNote: "검토 필요.",
    deferredNote: "보류된 작업.",
    warningsErrors: "경고 + 오류",
    needsAttention: "확인 필요.",
    filtersEyebrow: "필터 및 정렬",
    controlsTitle: "대기열 제어",
    activeQueue: "활성 대기열",
    allStates: "모든 상태",
    search: "검색",
    searchPlaceholder: "작업, 후보, 실행, 은행, 상품",
    bank: "은행",
    allBanks: "모든 은행",
    productType: "상품 유형",
    allTypes: "모든 유형",
    validation: "검증",
    allStatuses: "모든 상태",
    sortBy: "정렬 기준",
    order: "순서",
    priority: "우선순위",
    createdTime: "생성 시간",
    updatedTime: "수정 시간",
    confidence: "신뢰도",
    productName: "상품명",
    descending: "내림차순",
    ascending: "오름차순",
    reviewStates: "검토 상태",
    createdFrom: "생성 시작일",
    createdTo: "생성 종료일",
    applyFilters: "Search",
    reset: "초기화",
    results: "결과",
    tableTitle: "검토 접수 테이블",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `${Math.max(totalPages, 1)}페이지 중 ${page}페이지, 일치 작업 ${totalItems}건.`,
    noMatches: "일치하는 작업 없음",
    emptyTitle: "현재 대기열 필터에 해당하는 검토 작업이 없습니다.",
    emptyBody: "상태 필터를 넓히거나 검색어를 지우거나 양식을 초기화하세요. 활성 대기열이 기본 접수 화면입니다.",
    resetQueueFilters: "대기열 필터 초기화",
    task: "작업",
    country: "국가",
    product: "상품",
    issueSummary: "이슈 요약",
    created: "생성",
    status: "상태",
    action: "작업",
    candidate: "후보",
    run: "실행",
    sourceConfidence: "Source confidence",
    updated: "수정",
    openDetail: "상세 열기",
    detailHint: "결정 제어는 상세 및 trace 화면에서 사용할 수 있습니다.",
    showing: (from: number, to: number, total: number) => `${total}건 중 ${from}-${to} 표시`,
    previous: "이전",
    next: "다음",
  },
  ja: {
    headerDescription: "アクティブな審査作業、フィルター、キュー drill-in。",
    path: ["審査", "審査キュー"],
    title: "審査キュー",
    snapshotTitle: "キュー Snapshot",
    visibleTasks: "表示中のタスク",
    currentFilters: "現在のフィルター。",
    queuedNote: "審査が必要。",
    deferredNote: "保留中の作業。",
    warningsErrors: "警告 + エラー",
    needsAttention: "確認が必要。",
    filtersEyebrow: "フィルターと並び替え",
    controlsTitle: "キュー制御",
    activeQueue: "アクティブキュー",
    allStates: "すべての状態",
    search: "検索",
    searchPlaceholder: "タスク、候補、実行、銀行、商品",
    bank: "銀行",
    allBanks: "すべての銀行",
    productType: "商品タイプ",
    allTypes: "すべてのタイプ",
    validation: "検証",
    allStatuses: "すべての状態",
    sortBy: "並び替え",
    order: "順序",
    priority: "優先度",
    createdTime: "作成日時",
    updatedTime: "更新日時",
    confidence: "信頼度",
    productName: "商品名",
    descending: "降順",
    ascending: "昇順",
    reviewStates: "審査状態",
    createdFrom: "作成開始日",
    createdTo: "作成終了日",
    applyFilters: "Search",
    reset: "リセット",
    results: "結果",
    tableTitle: "審査受付テーブル",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `${Math.max(totalPages, 1)}ページ中${page}ページ、該当タスク${totalItems}件。`,
    noMatches: "該当タスクなし",
    emptyTitle: "現在のキューフィルターに該当する審査作業はありません。",
    emptyBody: "状態フィルターを広げるか、検索語を消すか、フォームをリセットしてください。アクティブキューが既定の受付画面です。",
    resetQueueFilters: "キューフィルターをリセット",
    task: "タスク",
    country: "国",
    product: "商品",
    issueSummary: "課題要約",
    created: "作成",
    status: "状態",
    action: "操作",
    candidate: "候補",
    run: "実行",
    sourceConfidence: "Source confidence",
    updated: "更新",
    openDetail: "詳細を開く",
    detailHint: "判断操作は詳細と trace 画面で利用できます。",
    showing: (from: number, to: number, total: number) => `${total}件中${from}-${to}件を表示`,
    previous: "前へ",
    next: "次へ",
  },
} as const;

export type ReviewQueuePageFilters = {
  q: string;
  states: string[];
  bankCode: string;
  productType: string;
  validationStatus: string;
  createdFrom: string;
  createdTo: string;
  sortBy: string;
  sortOrder: "asc" | "desc";
  page: number;
};

type ReviewQueueSurfaceProps = {
  queue: ReviewQueueResponse;
  filters: ReviewQueuePageFilters;
  locale: AdminLocale;
  productTypes: ProductTypeItem[];
};

export function ReviewQueueSurface({ queue, filters, locale, productTypes }: ReviewQueueSurfaceProps) {
  const copy = REVIEW_QUEUE_COPY[locale];
  const productTypeOptions = buildAdminProductTypeOptions(productTypes);
  const productTypeLabelMap = buildAdminProductTypeLabelMap(productTypes);
  const stateCounts = queue.summary.state_counts;
  const validationCounts = queue.summary.validation_counts;
  const statItems = [
    {
      label: copy.visibleTasks,
      value: String(queue.summary.total_items),
      note: copy.currentFilters,
      tone: "info" as const,
      icon: ListChecks,
    },
    {
      label: translateReviewState(locale, "queued"),
      value: String(stateCounts.queued ?? 0),
      note: copy.queuedNote,
      tone: "warning" as const,
      icon: ClipboardList,
    },
    {
      label: translateReviewState(locale, "deferred"),
      value: String(stateCounts.deferred ?? 0),
      note: copy.deferredNote,
      tone: "neutral" as const,
      icon: CirclePause,
    },
    {
      label: copy.warningsErrors,
      value: String((validationCounts.warning ?? 0) + (validationCounts.error ?? 0)),
      note: copy.needsAttention,
      tone: "success" as const,
      icon: TriangleAlert,
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
        framed={false}
        items={statItems}
      />

      <article className="min-w-0 rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <div className="flex flex-col gap-4 border-b border-border/80 pb-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.filtersEyebrow}</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{copy.controlsTitle}</h2>
          </div>

        </div>

        <form action={buildAdminHref("/admin/reviews", new URLSearchParams(), locale)} className="mt-6 grid min-w-0 gap-5">
          <div className="grid min-w-0 gap-4 xl:grid-cols-[1.5fr_repeat(5,minmax(0,1fr))]">
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

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.bank}</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.bankCode}
                name="bank_code"
              >
                <option value="">{copy.allBanks}</option>
                {BANK_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.productType}</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.productType}
                name="product_type"
              >
                <option value="">{copy.allTypes}</option>
                {productTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.validation}</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.validationStatus}
                name="validation_status"
              >
                <option value="">{copy.allStatuses}</option>
                {VALIDATION_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {translateValidationStatus(locale, option)}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.sortBy}</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.sortBy}
                name="sort_by"
              >
                <option value="priority">{copy.priority}</option>
                <option value="created_at">{copy.createdTime}</option>
                <option value="updated_at">{copy.updatedTime}</option>
                <option value="source_confidence">{copy.confidence}</option>
                <option value="product_name">{copy.productName}</option>
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.order}</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.sortOrder}
                name="sort_order"
              >
                <option value="desc">{copy.descending}</option>
                <option value="asc">{copy.ascending}</option>
              </select>
            </label>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr_1fr_auto]">
            <fieldset className="grid gap-2 text-sm">
              <legend className="font-medium text-foreground">{copy.reviewStates}</legend>
              <div className="flex flex-wrap gap-2">
                {REVIEW_STATES.map((state) => (
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
                    <span>{translateReviewState(locale, state)}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.createdFrom}</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.createdFrom}
                name="created_from"
                type="date"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.createdTo}</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.createdTo}
                name="created_to"
                type="date"
              />
            </label>

            <div className="flex items-end gap-2">
              <Button type="submit">{copy.applyFilters}</Button>
              <Button asChild variant="outline">
                <Link href={buildAdminHref("/admin/reviews", new URLSearchParams(), locale)}>{copy.reset}</Link>
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
              {copy.pageSummary(queue.page, queue.total_pages, queue.total_items)}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {filters.states.map((state) => (
              <span className={cn("rounded-full px-3 py-1 text-xs font-medium", stateBadgeClasses(state))} key={state}>
                {translateReviewState(locale, state)}
              </span>
            ))}
            {filters.bankCode ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {filters.bankCode}
              </span>
            ) : null}
            {filters.productType ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {formatAdminProductType(filters.productType, productTypeLabelMap)}
              </span>
            ) : null}
            {filters.validationStatus ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {translateValidationStatus(locale, filters.validationStatus)}
              </span>
            ) : null}
          </div>
        </div>

        {queue.items.length === 0 ? (
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
                  <Link href={buildAdminHref("/admin/reviews", new URLSearchParams(), locale)}>{copy.resetQueueFilters}</Link>
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="max-w-full overflow-x-auto px-6 py-5">
              <table className="min-w-[940px] table-fixed border-separate border-spacing-0">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.task}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.bank}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.product}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.issueSummary}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.confidence}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.validation}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.created}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.status}</th>
                  </tr>
                </thead>
                <tbody>
                  {queue.items.map((item) => (
                    <tr className="align-top" key={item.review_task_id}>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          <Link
                            className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline"
                            href={buildAdminHref(`/admin/reviews/${item.review_task_id}`, new URLSearchParams(), locale)}
                          >
                            {item.review_task_id}
                          </Link>
                          <span className="text-xs text-muted-foreground">{copy.candidate} {item.candidate_id}</span>
                          <Link className="text-xs text-muted-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/runs/${item.run_id}`, new URLSearchParams(), locale)}>
                            {copy.run} {item.run_id}
                          </Link>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          <span className="font-medium text-foreground">{item.bank_name}</span>
                          <span className="text-xs text-muted-foreground">{item.bank_code}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <span className="font-medium text-foreground">{item.product_name}</span>
                          <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
                            {formatAdminProductType(item.product_type, productTypeLabelMap)}
                          </span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <p className="text-sm leading-6 text-foreground">{item.issue_summary}</p>
                          <div className="flex flex-wrap gap-2">
                            {item.issue_summary_items.slice(0, 2).map((issue) => (
                              <span
                                className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", issueBadgeClasses(issue.severity))}
                                key={`${item.review_task_id}-${issue.code}`}
                              >
                                {issue.code}
                              </span>
                            ))}
                          </div>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          <span className="text-sm font-medium text-foreground">{formatConfidence(item.source_confidence)}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <span className={cn("inline-flex rounded-full px-2.5 py-1 text-xs font-medium", validationBadgeClasses(item.validation_status))}>
                          {formatValidationStatusLabel(locale, item.validation_status)}
                        </span>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          <span className="text-sm text-foreground">{formatAdminDateTime(locale, item.created_at)}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <span className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", stateBadgeClasses(item.review_state))}>
                            {translateReviewState(locale, item.review_state)}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-col gap-3 border-t border-border/80 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-muted-foreground">
                {copy.showing((queue.page - 1) * queue.page_size + 1, Math.min(queue.page * queue.page_size, queue.total_items), queue.total_items)}
              </p>
              <div className="flex items-center gap-2">
                {queue.page > 1 ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildQueueHref(filters, { page: Math.max(1, queue.page - 1) }, locale)}>{copy.previous}</Link>
                  </Button>
                ) : (
                  <span className="inline-flex h-7 items-center rounded-[min(var(--radius-md),12px)] border border-border bg-muted px-2.5 text-[0.8rem] text-muted-foreground opacity-60">
                    {copy.previous}
                  </span>
                )}
                {queue.has_next_page ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildQueueHref(filters, { page: queue.page + 1 }, locale)}>{copy.next}</Link>
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

function buildQueueHref(
  filters: ReviewQueuePageFilters,
  overrides: Partial<ReviewQueuePageFilters>,
  locale: AdminLocale,
) {
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
  if (next.bankCode) {
    params.set("bank_code", next.bankCode);
  }
  if (next.productType) {
    params.set("product_type", next.productType);
  }
  if (next.validationStatus) {
    params.set("validation_status", next.validationStatus);
  }
  if (next.createdFrom) {
    params.set("created_from", next.createdFrom);
  }
  if (next.createdTo) {
    params.set("created_to", next.createdTo);
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

  return buildAdminHref("/admin/reviews", params, locale);
}

function formatConfidence(value: number | null) {
  if (value === null) {
    return "n/a";
  }
  return `${Math.round(value * 100)}%`;
}

function formatValidationStatusLabel(locale: AdminLocale, value: string) {
  if (value === "error") {
    return locale === "ko" ? "검증 오류" : locale === "ja" ? "検証エラー" : "Validation Error";
  }
  if (value === "warning") {
    return locale === "ko" ? "검증 경고" : locale === "ja" ? "検証警告" : "Validation Warning";
  }
  return translateValidationStatus(locale, value);
}

function toTitleCase(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function stateBadgeClasses(state: string) {
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

function validationBadgeClasses(status: string) {
  switch (status) {
    case "error":
      return "bg-destructive/10 text-destructive";
    case "warning":
      return "bg-warning-soft text-warning";
    case "pass":
      return "bg-success-soft text-success";
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
