"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";

import { AdminTableAutoRefresh } from "@/components/fpds/admin/admin-table-auto-refresh";
import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { ReviewQueueResults } from "@/components/fpds/admin/review-queue-results";
import { Button } from "@/components/ui/button";
import type { BankItem, ProductTypeItem, ReviewQueueResponse } from "@/lib/admin-api";
import { buildAdminHref, translateReviewState, translateValidationStatus, type AdminLocale } from "@/lib/admin-i18n";
import { buildAdminProductTypeOptions } from "@/lib/admin-product-types";
import {
  REVIEW_QUEUE_PAGE_SIZES,
  buildReviewQueueBrowserSearchParams,
  defaultReviewQueueFilters,
  parseReviewQueueFilters,
  type ReviewQueuePageFilters,
} from "@/lib/review-queue-query";

const REVIEW_STATES = ["queued", "deferred", "approved", "edited", "rejected"] as const;
const VALIDATION_OPTIONS = ["pass", "warning", "error"] as const;

const REVIEW_QUEUE_COPY = {
  en: {
    headerDescription: "Review items that need a decision.",
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
    pageSize: "Rows per page",
    loading: "Updating review results…",
    loadError: "Review results could not be refreshed. The current results are still shown.",
    advancedFilters: "Advanced filters",
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
    headerDescription: "결정이 필요한 항목을 검토합니다.",
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
    applyFilters: "검색",
    reset: "초기화",
    pageSize: "조회 건수",
    loading: "검토 결과를 갱신하는 중입니다…",
    loadError: "검토 결과를 갱신하지 못했습니다. 현재 결과는 그대로 표시됩니다.",
    advancedFilters: "고급 필터",
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
    headerDescription: "判断が必要な項目を審査します。",
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
    applyFilters: "検索",
    reset: "リセット",
    pageSize: "表示件数",
    loading: "審査結果を更新しています…",
    loadError: "審査結果を更新できませんでした。現在の結果を引き続き表示します。",
    advancedFilters: "詳細フィルター",
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

type ReviewQueueSurfaceProps = {
  queue: ReviewQueueResponse;
  filters: ReviewQueuePageFilters;
  locale: AdminLocale;
  banks: BankItem[];
  productTypes: ProductTypeItem[];
  csrfToken: string | null | undefined;
};

export function ReviewQueueSurface({ queue, filters, locale, banks, productTypes, csrfToken }: ReviewQueueSurfaceProps) {
  const copy = REVIEW_QUEUE_COPY[locale];
  const productTypeOptions = buildAdminProductTypeOptions(productTypes);
  const [activeQueue, setActiveQueue] = useState(queue);
  const [activeFilters, setActiveFilters] = useState(filters);
  const [draftFilters, setDraftFilters] = useState(filters);
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const requestSequence = useRef(0);

  useEffect(() => {
    setActiveQueue(queue);
    setActiveFilters(filters);
    setDraftFilters(filters);
  }, [filters, queue]);

  const loadQueue = useCallback(async (requestedFilters: ReviewQueuePageFilters, updateUrl = true) => {
    const normalizedFilters = parseReviewQueueFilters(buildReviewQueueBrowserSearchParams(requestedFilters));
    const requestId = requestSequence.current + 1;
    requestSequence.current = requestId;
    setIsLoading(true);
    setLoadError(null);

    try {
      const search = buildReviewQueueBrowserSearchParams(normalizedFilters);
      const response = await fetch(buildAdminHref("/admin/reviews/data", search, locale), {
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) {
        throw new Error(`Review queue request failed with ${response.status}.`);
      }
      const payload = (await response.json()) as { data?: ReviewQueueResponse };
      if (!payload.data) {
        throw new Error("Review queue response did not include data.");
      }
      if (requestSequence.current !== requestId) {
        return;
      }

      setActiveQueue(payload.data);
      if (updateUrl) {
        setActiveFilters(normalizedFilters);
        setDraftFilters(normalizedFilters);
        window.history.replaceState(
          window.history.state,
          "",
          buildAdminHref("/admin/reviews", buildReviewQueueBrowserSearchParams(normalizedFilters), locale),
        );
      }
    } catch {
      if (requestSequence.current === requestId) {
        setLoadError(copy.loadError);
      }
    } finally {
      if (requestSequence.current === requestId) {
        setIsLoading(false);
      }
    }
  }, [copy.loadError, locale]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void loadQueue({ ...draftFilters, page: 1 });
  }

  function handleReset() {
    const nextFilters = defaultReviewQueueFilters();
    setDraftFilters(nextFilters);
    void loadQueue(nextFilters);
  }

  function handlePageSizeChange(value: string) {
    const nextFilters = { ...draftFilters, page: 1, pageSize: Number(value) };
    setDraftFilters(nextFilters);
    void loadQueue(nextFilters);
  }

  const handleAutoRefresh = useCallback(
    () => loadQueue(activeFilters, false),
    [activeFilters, loadQueue],
  );

  const advancedFiltersActive =
    Boolean(draftFilters.validationStatus || draftFilters.createdFrom || draftFilters.createdTo) ||
    draftFilters.sortBy !== "priority" ||
    draftFilters.sortOrder !== "desc" ||
    draftFilters.states.length !== 2 ||
    !draftFilters.states.includes("queued") ||
    !draftFilters.states.includes("deferred");

  return (
    <section className="grid min-w-0 gap-4">
      <AdminTableAutoRefresh locale={locale} onRefresh={handleAutoRefresh} />

      <AdminPageHeader
        description={copy.headerDescription}
        path={copy.path}
        title={copy.title}
      />

      <article className="min-w-0 rounded-lg border border-border bg-card p-4">
        <form className="grid min-w-0 gap-4" onSubmit={handleSubmit}>
          <div className="grid min-w-0 gap-3 md:grid-cols-2 xl:grid-cols-[minmax(16rem,1.7fr)_minmax(10rem,1fr)_minmax(10rem,1fr)_minmax(7rem,auto)_auto]">
            <label className="grid min-w-0 gap-1.5 text-sm">
              <span className="font-medium text-foreground">{copy.search}</span>
              <input
                className="h-10 w-full min-w-0 rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/30"
                onChange={(event) => setDraftFilters((current) => ({ ...current, q: event.target.value }))}
                name="q"
                placeholder={copy.searchPlaceholder}
                type="search"
                value={draftFilters.q}
              />
            </label>

            <label className="grid min-w-0 gap-1.5 text-sm">
              <span className="font-medium text-foreground">{copy.bank}</span>
              <select
                className="h-10 w-full min-w-0 max-w-full rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/30"
                onChange={(event) => setDraftFilters((current) => ({ ...current, bankCode: event.target.value }))}
                name="bank_code"
                value={draftFilters.bankCode}
              >
                <option value="">{copy.allBanks}</option>
                {banks.map((bank) => (
                  <option key={bank.bank_code} value={bank.bank_code}>
                    {bank.bank_name} ({bank.bank_code})
                  </option>
                ))}
              </select>
            </label>

            <label className="grid min-w-0 gap-1.5 text-sm">
              <span className="font-medium text-foreground">{copy.productType}</span>
              <select
                className="h-10 w-full min-w-0 max-w-full rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/30"
                onChange={(event) => setDraftFilters((current) => ({ ...current, productType: event.target.value }))}
                name="product_type"
                value={draftFilters.productType}
              >
                <option value="">{copy.allTypes}</option>
                {productTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid min-w-0 gap-1.5 text-sm">
              <span className="font-medium text-foreground">{copy.pageSize}</span>
              <select
                aria-label={copy.pageSize}
                className="h-10 rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/30"
                disabled={isLoading}
                onChange={(event) => handlePageSizeChange(event.target.value)}
                value={draftFilters.pageSize}
              >
                {REVIEW_QUEUE_PAGE_SIZES.map((pageSize) => (
                  <option key={pageSize} value={pageSize}>{pageSize}</option>
                ))}
              </select>
            </label>

            <div className="flex items-end gap-2">
              <Button disabled={isLoading} type="submit">{copy.applyFilters}</Button>
              <Button disabled={isLoading} onClick={handleReset} type="button" variant="outline">{copy.reset}</Button>
            </div>
          </div>

          <details className="border-t border-border pt-3" open={advancedFiltersActive}>
            <summary className="cursor-pointer text-sm font-semibold text-foreground">{copy.advancedFilters}</summary>
            <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <label className="grid gap-1.5 text-sm">
                <span className="font-medium text-foreground">{copy.validation}</span>
                <select
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/30"
                  onChange={(event) => setDraftFilters((current) => ({ ...current, validationStatus: event.target.value }))}
                  name="validation_status"
                  value={draftFilters.validationStatus}
                >
                  <option value="">{copy.allStatuses}</option>
                  {VALIDATION_OPTIONS.map((option) => (
                    <option key={option} value={option}>
                      {translateValidationStatus(locale, option)}
                    </option>
                  ))}
                </select>
              </label>

              <label className="grid gap-1.5 text-sm">
                <span className="font-medium text-foreground">{copy.sortBy}</span>
                <select
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/30"
                  onChange={(event) => setDraftFilters((current) => ({ ...current, sortBy: event.target.value }))}
                  name="sort_by"
                  value={draftFilters.sortBy}
                >
                  <option value="priority">{copy.priority}</option>
                  <option value="created_at">{copy.createdTime}</option>
                  <option value="updated_at">{copy.updatedTime}</option>
                  <option value="source_confidence">{copy.confidence}</option>
                  <option value="product_name">{copy.productName}</option>
                </select>
              </label>

              <label className="grid gap-1.5 text-sm">
                <span className="font-medium text-foreground">{copy.order}</span>
                <select
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/30"
                  onChange={(event) => setDraftFilters((current) => ({ ...current, sortOrder: event.target.value === "asc" ? "asc" : "desc" }))}
                  name="sort_order"
                  value={draftFilters.sortOrder}
                >
                  <option value="desc">{copy.descending}</option>
                  <option value="asc">{copy.ascending}</option>
                </select>
              </label>

              <fieldset className="grid gap-1.5 text-sm md:col-span-2 xl:col-span-4">
                <legend className="font-medium text-foreground">{copy.reviewStates}</legend>
                <div className="flex flex-wrap gap-2">
                  {REVIEW_STATES.map((state) => (
                    <label
                      className="inline-flex min-h-10 items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/30"
                      key={state}
                    >
                      <input
                        className="h-4 w-4 rounded border-border text-primary accent-[var(--primary)]"
                        checked={draftFilters.states.includes(state)}
                        name="state"
                        onChange={(event) => setDraftFilters((current) => ({
                          ...current,
                          states: event.target.checked
                            ? [...current.states, state]
                            : current.states.filter((value) => value !== state),
                        }))}
                        type="checkbox"
                        value={state}
                      />
                      <span>{translateReviewState(locale, state)}</span>
                    </label>
                  ))}
                </div>
              </fieldset>

              <label className="grid gap-1.5 text-sm">
                <span className="font-medium text-foreground">{copy.createdFrom}</span>
                <input
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/30"
                  onChange={(event) => setDraftFilters((current) => ({ ...current, createdFrom: event.target.value }))}
                  name="created_from"
                  type="date"
                  value={draftFilters.createdFrom}
                />
              </label>

              <label className="grid gap-1.5 text-sm">
                <span className="font-medium text-foreground">{copy.createdTo}</span>
                <input
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/30"
                  onChange={(event) => setDraftFilters((current) => ({ ...current, createdTo: event.target.value }))}
                  name="created_to"
                  type="date"
                  value={draftFilters.createdTo}
                />
              </label>
            </div>
          </details>
        </form>
      </article>

      <ReviewQueueResults
        csrfToken={csrfToken}
        filters={activeFilters}
        isLoading={isLoading}
        loadError={loadError}
        loadingLabel={copy.loading}
        locale={locale}
        onPageChange={(page) => loadQueue({ ...activeFilters, page })}
        onRefresh={() => loadQueue(activeFilters, false)}
        onReset={handleReset}
        productTypes={productTypes}
        queue={activeQueue}
      />
    </section>
  );
}
