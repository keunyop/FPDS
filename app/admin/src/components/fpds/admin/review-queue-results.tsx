"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { CirclePause, Loader2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import type { ProductTypeItem, ReviewQueueResponse, ReviewTaskListItem } from "@/lib/admin-api";
import {
  buildAdminHref,
  formatAdminDateTime,
  translateReviewAction,
  translateReviewState,
  translateValidationStatus,
  type AdminLocale,
} from "@/lib/admin-i18n";
import { buildAdminProductTypeLabelMap, formatAdminProductType } from "@/lib/admin-product-types";
import { cn } from "@/lib/utils";

type ReviewQueueResultsFilters = {
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

type ReviewQueueResultsProps = {
  queue: ReviewQueueResponse;
  filters: ReviewQueueResultsFilters;
  locale: AdminLocale;
  productTypes: ProductTypeItem[];
  csrfToken: string | null | undefined;
};

type BulkAction = "defer";

const ACTIVE_REVIEW_STATES = new Set(["queued", "deferred"]);

const RESULTS_COPY = {
  en: {
    results: "Results",
    tableTitle: "Review work",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `Page ${page} of ${Math.max(totalPages, 1)} · ${totalItems} matching task${totalItems === 1 ? "" : "s"}`,
    noMatches: "No matching tasks",
    emptyTitle: "No review work matches these filters.",
    emptyBody: "Widen the state filter, clear the search term, or reset the queue controls.",
    resetQueueFilters: "Reset queue filters",
    select: "Select",
    selected: (count: number) => `${count} selected`,
    selectPage: "Select active rows on this page",
    selectTask: (product: string) => `Select ${product}`,
    bulkUnavailable: "Bulk defer only. Approval and rejection require task-level evidence review.",
    bulkSucceeded: (action: string, count: number) => `${action} completed for ${count} task${count === 1 ? "" : "s"}.`,
    bulkPartial: (action: string, succeeded: number, failed: number) => `${action} completed for ${succeeded}; ${failed} failed.`,
    bulkFailed: (action: string, failed: number) => `${action} failed for ${failed} task${failed === 1 ? "" : "s"}.`,
    bank: "Bank",
    product: "Product",
    issueSummary: "Issue & next step",
    severity: "Severity & confidence",
    status: "Status & created",
    references: "References",
    recommendation: "Next",
    confidence: "confidence",
    candidate: "Candidate",
    task: "Task",
    run: "Run",
    defer: "Defer",
    deferring: "Deferring…",
    previous: "Previous",
    next: "Next",
    showing: (from: number, to: number, total: number) => `Showing ${from}-${to} of ${total}`,
  },
  ko: {
    results: "결과",
    tableTitle: "검토 작업",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `${Math.max(totalPages, 1)}페이지 중 ${page}페이지 · 일치 작업 ${totalItems}건`,
    noMatches: "일치하는 작업 없음",
    emptyTitle: "현재 필터에 맞는 검토 작업이 없습니다.",
    emptyBody: "상태 범위를 넓히거나 검색어를 지우고 대기열 필터를 초기화해 보세요.",
    resetQueueFilters: "대기열 필터 초기화",
    select: "선택",
    selected: (count: number) => `${count}건 선택`,
    selectPage: "이 페이지의 처리 가능한 행 선택",
    selectTask: (product: string) => `${product} 선택`,
    bulkUnavailable: "일괄 보류만 가능합니다. 승인과 거절은 작업별 근거 확인이 필요합니다.",
    bulkSucceeded: (action: string, count: number) => `${count}건 ${action} 완료.`,
    bulkPartial: (action: string, succeeded: number, failed: number) => `${action} ${succeeded}건 완료, ${failed}건 실패.`,
    bulkFailed: (action: string, failed: number) => `${action} ${failed}건 실패.`,
    bank: "은행",
    product: "상품",
    issueSummary: "문제 및 다음 단계",
    severity: "심각도 및 신뢰도",
    status: "상태 및 생성 시각",
    references: "참조",
    recommendation: "다음 단계",
    confidence: "신뢰도",
    candidate: "후보",
    task: "작업",
    run: "실행",
    defer: "보류",
    deferring: "보류 중…",
    previous: "이전",
    next: "다음",
    showing: (from: number, to: number, total: number) => `${total}건 중 ${from}-${to} 표시`,
  },
  ja: {
    results: "結果",
    tableTitle: "審査作業",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `${Math.max(totalPages, 1)}ページ中${page}ページ · 該当${totalItems}件`,
    noMatches: "該当する作業なし",
    emptyTitle: "現在のフィルターに一致する審査作業はありません。",
    emptyBody: "状態の範囲を広げるか、検索語を消去してキューフィルターをリセットしてください。",
    resetQueueFilters: "キューフィルターをリセット",
    select: "選択",
    selected: (count: number) => `${count}件選択`,
    selectPage: "このページの処理可能な行を選択",
    selectTask: (product: string) => `${product}を選択`,
    bulkUnavailable: "一括保留のみ利用できます。承認と却下には作業ごとの根拠確認が必要です。",
    bulkSucceeded: (action: string, count: number) => `${count}件の${action}が完了しました。`,
    bulkPartial: (action: string, succeeded: number, failed: number) => `${action}：${succeeded}件完了、${failed}件失敗。`,
    bulkFailed: (action: string, failed: number) => `${action}：${failed}件失敗。`,
    bank: "銀行",
    product: "商品",
    issueSummary: "問題と次の手順",
    severity: "重大度と信頼度",
    status: "状態と作成日時",
    references: "参照",
    recommendation: "次の手順",
    confidence: "信頼度",
    candidate: "候補",
    task: "作業",
    run: "実行",
    defer: "保留",
    deferring: "保留中…",
    previous: "前へ",
    next: "次へ",
    showing: (from: number, to: number, total: number) => `${total}件中${from}-${to}件を表示`,
  },
} as const;

export function ReviewQueueResults({ queue, filters, locale, productTypes, csrfToken }: ReviewQueueResultsProps) {
  const router = useRouter();
  const copy = RESULTS_COPY[locale];
  const productTypeLabelMap = buildAdminProductTypeLabelMap(productTypes);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [pendingAction, setPendingAction] = useState<BulkAction | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);
  const selectableItems = queue.items.filter(isBulkSelectable);
  const selectableIds = selectableItems.map((item) => item.review_task_id);
  const visibleIdsKey = queue.items.map((item) => item.review_task_id).join("|");
  const allSelectableSelected = selectableIds.length > 0 && selectableIds.every((id) => selectedSet.has(id));

  useEffect(() => {
    const visibleIds = new Set(queue.items.map((item) => item.review_task_id));
    setSelectedIds((current) => current.filter((id) => visibleIds.has(id)));
  }, [visibleIdsKey, queue.items]);

  function toggleItem(reviewTaskId: string, checked: boolean) {
    setStatusMessage(null);
    setSelectedIds((current) => {
      if (checked) {
        return current.includes(reviewTaskId) ? current : [...current, reviewTaskId];
      }
      return current.filter((id) => id !== reviewTaskId);
    });
  }

  function togglePage(checked: boolean) {
    setStatusMessage(null);
    setSelectedIds((current) => {
      const next = new Set(current);
      for (const id of selectableIds) {
        if (checked) {
          next.add(id);
        } else {
          next.delete(id);
        }
      }
      return Array.from(next);
    });
  }

  async function handleBulkAction(action: BulkAction) {
    const selectedItems = queue.items.filter((item) => selectedSet.has(item.review_task_id) && isBulkSelectable(item));
    if (selectedItems.length === 0) {
      setStatusMessage(copy.bulkUnavailable);
      return;
    }

    setPendingAction(action);
    setStatusMessage(null);

    const failures: string[] = [];
    for (const item of selectedItems) {
      const response = await fetch(`/admin/reviews/${encodeURIComponent(item.review_task_id)}/decision`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify({
          action_type: action,
          reason_code: item.queue_reason_code || "bulk_review_action",
          reason_text: "Bulk defer from Review Queue.",
          override_payload: {},
        }),
      });

      if (!response.ok) {
        failures.push(`${item.review_task_id}: ${await responseErrorMessage(response)}`);
      }
    }

    const succeeded = selectedItems.length - failures.length;
    setSelectedIds((current) => current.filter((id) => failures.some((failure) => failure.startsWith(`${id}:`))));
    setPendingAction(null);
    if (failures.length === 0) {
      setStatusMessage(copy.bulkSucceeded(actionLabel(locale, action), succeeded));
    } else if (succeeded > 0) {
      setStatusMessage(`${copy.bulkPartial(actionLabel(locale, action), succeeded, failures.length)} ${failures.slice(0, 2).join(" ")}`);
    } else {
      setStatusMessage(`${copy.bulkFailed(actionLabel(locale, action), failures.length)} ${failures.slice(0, 2).join(" ")}`);
    }
    router.refresh();
  }

  return (
    <article className="min-w-0 overflow-hidden rounded-lg border border-border bg-card">
      <div className="flex flex-col gap-2 border-b border-border px-4 py-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <h2 className="text-base font-semibold text-foreground">{copy.tableTitle}</h2>
            <p className="text-sm text-muted-foreground">
              {copy.pageSummary(queue.page, queue.total_pages, queue.total_items)}
            </p>
          </div>
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
        <div className="px-4 py-8">
          <div className="rounded-md border border-dashed border-border bg-background px-5 py-6">
            <p className="text-sm font-medium text-muted-foreground">{copy.noMatches}</p>
            <h3 className="mt-2 text-lg font-semibold text-foreground">
              {copy.emptyTitle}
            </h3>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              {copy.emptyBody}
            </p>
            <div className="mt-4">
              <Button asChild variant="outline">
                <Link href={buildAdminHref("/admin/reviews", new URLSearchParams(), locale)}>{copy.resetQueueFilters}</Link>
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="flex flex-col gap-2 border-b border-border bg-background/45 px-4 py-2.5 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-wrap items-center gap-3">
              <label className="inline-flex min-h-10 items-center gap-2 text-sm font-medium text-foreground">
                <input
                  aria-label={copy.selectPage}
                  checked={allSelectableSelected}
                  className="h-4 w-4 rounded border-border text-primary accent-[var(--primary)]"
                  disabled={selectableIds.length === 0 || pendingAction !== null}
                  onChange={(event) => togglePage(event.currentTarget.checked)}
                  type="checkbox"
                />
                <span>{copy.selected(selectedIds.length)}</span>
              </label>
              <span className="text-xs text-muted-foreground">{copy.bulkUnavailable}</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button className="min-h-10" disabled={selectedIds.length === 0 || pendingAction !== null} onClick={() => handleBulkAction("defer")} size="sm" type="button" variant="outline">
                {pendingAction === "defer" ? <Loader2 className="animate-spin" /> : <CirclePause />}
                {pendingAction === "defer" ? copy.deferring : translateReviewAction(locale, "defer")}
              </Button>
            </div>
          </div>

          {statusMessage ? (
            <div className="border-b border-border px-4 py-3">
              <p aria-live="polite" className="text-sm text-muted-foreground" role="status">{statusMessage}</p>
            </div>
          ) : null}

          <ul className="divide-y divide-border md:hidden">
            {queue.items.map((item) => {
              const selectable = isBulkSelectable(item);
              return (
                <li className="grid gap-3 px-4 py-4" key={item.review_task_id}>
                  <div className="flex min-w-0 items-start gap-2">
                    <label className="-ml-2 inline-flex h-10 w-10 shrink-0 items-center justify-center">
                      <span className="sr-only">{copy.selectTask(item.product_name)}</span>
                      <input
                        checked={selectedSet.has(item.review_task_id)}
                        className="h-4 w-4 rounded border-border text-primary accent-[var(--primary)] disabled:opacity-40"
                        disabled={!selectable || pendingAction !== null}
                        onChange={(event) => toggleItem(item.review_task_id, event.currentTarget.checked)}
                        type="checkbox"
                      />
                    </label>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium text-muted-foreground">
                        {item.bank_name} <span aria-hidden="true">·</span> <span className="font-mono">{item.bank_code}</span>
                      </p>
                      <Link
                        className="mt-0.5 block text-base font-semibold leading-6 text-foreground underline-offset-4 hover:text-primary hover:underline"
                        href={buildAdminHref(`/admin/reviews/${item.review_task_id}`, new URLSearchParams(), locale)}
                      >
                        {item.product_name}
                      </Link>
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        {formatAdminProductType(item.product_type, productTypeLabelMap)}
                      </p>
                    </div>
                    <span className={cn("inline-flex shrink-0 rounded-full px-2.5 py-1 text-xs font-medium", stateBadgeClasses(item.review_state))}>
                      {translateReviewState(locale, item.review_state)}
                    </span>
                  </div>

                  <div className="grid gap-2 pl-10">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", diagnosisBadgeClasses(item.review_diagnosis.category))}>
                        {diagnosisCategoryLabel(locale, item.review_diagnosis.category)}
                      </span>
                      <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", validationBadgeClasses(item.validation_status))}>
                        {formatValidationStatusLabel(locale, item.validation_status)}
                      </span>
                      <span className="text-xs font-medium text-foreground">
                        {formatConfidence(item.source_confidence)} {copy.confidence}
                      </span>
                    </div>
                    <p className="text-sm font-medium leading-6 text-foreground">{item.review_diagnosis.headline}</p>
                    <p className="border-l-2 border-primary/35 pl-3 text-xs leading-5 text-muted-foreground">
                      <span className="font-medium text-foreground">{copy.recommendation}:</span>{" "}
                      {recommendedActionLabel(locale, item.review_diagnosis.recommended_action)}
                    </p>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                      <time dateTime={item.created_at}>{formatAdminDateTime(locale, item.created_at)}</time>
                    </div>
                    <details className="text-xs text-muted-foreground">
                      <summary className="inline-flex min-h-10 cursor-pointer items-center font-medium text-foreground">
                        {copy.references}
                      </summary>
                      <div className="grid gap-1 pb-1 font-mono leading-5">
                        <span>{copy.task} {item.review_task_id}</span>
                        <span>{copy.candidate} {item.candidate_id}</span>
                        <Link
                          className="underline-offset-4 hover:text-primary hover:underline"
                          href={buildAdminHref(`/admin/runs/${item.run_id}`, new URLSearchParams(), locale)}
                        >
                          {copy.run} {item.run_id}
                        </Link>
                      </div>
                    </details>
                  </div>
                </li>
              );
            })}
          </ul>

          <div className="hidden max-w-full overflow-x-auto md:block">
            <table className="min-w-[1080px] table-fixed border-separate border-spacing-0">
              <caption className="sr-only">{copy.tableTitle}</caption>
              <thead>
                <tr className="text-left text-xs text-muted-foreground">
                  <th className="w-12 border-b border-border px-2 py-2.5 text-center font-medium">{copy.select}</th>
                  <th className="w-[13%] border-b border-border px-3 py-2.5 font-medium">{copy.bank}</th>
                  <th className="w-[18%] border-b border-border px-3 py-2.5 font-medium">{copy.product}</th>
                  <th className="w-[31%] border-b border-border px-3 py-2.5 font-medium">{copy.issueSummary}</th>
                  <th className="w-[15%] border-b border-border px-3 py-2.5 font-medium">{copy.severity}</th>
                  <th className="w-[12%] border-b border-border px-3 py-2.5 font-medium">{copy.status}</th>
                  <th className="w-[11%] border-b border-border px-3 py-2.5 font-medium">{copy.references}</th>
                </tr>
              </thead>
              <tbody>
                {queue.items.map((item) => {
                  const selectable = isBulkSelectable(item);
                  return (
                    <tr className="align-top" key={item.review_task_id}>
                      <td className="border-b border-border/70 px-1 py-2">
                        <label className="inline-flex h-10 w-10 items-center justify-center">
                          <span className="sr-only">{copy.selectTask(item.product_name)}</span>
                          <input
                            checked={selectedSet.has(item.review_task_id)}
                            className="h-4 w-4 rounded border-border text-primary accent-[var(--primary)] disabled:opacity-40"
                            disabled={!selectable || pendingAction !== null}
                            onChange={(event) => toggleItem(item.review_task_id, event.currentTarget.checked)}
                            type="checkbox"
                          />
                        </label>
                      </td>
                      <td className="border-b border-border/70 px-3 py-3">
                        <div className="grid gap-1">
                          <span className="font-medium text-foreground">{item.bank_name}</span>
                          <span className="font-mono text-[11px] text-muted-foreground">{item.bank_code}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-3">
                        <div className="grid gap-1">
                          <Link
                            className="font-medium leading-5 text-foreground underline-offset-4 hover:text-primary hover:underline"
                            href={buildAdminHref(`/admin/reviews/${item.review_task_id}`, new URLSearchParams(), locale)}
                          >
                            {item.product_name}
                          </Link>
                          <span className="w-fit rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                            {formatAdminProductType(item.product_type, productTypeLabelMap)}
                          </span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-3">
                        <div className="grid gap-1.5">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", diagnosisBadgeClasses(item.review_diagnosis.category))}>
                                {diagnosisCategoryLabel(locale, item.review_diagnosis.category)}
                              </span>
                              <span className="text-xs text-muted-foreground">{toTitleCase(item.source_role)}</span>
                            </div>
                            <p className="text-sm font-medium leading-5 text-foreground">{item.review_diagnosis.headline}</p>
                            {item.review_diagnosis.affected_fields.length > 0 ? (
                              <div className="flex flex-wrap gap-1.5">
                                {item.review_diagnosis.affected_fields.slice(0, 4).map((field) => (
                                  <span
                                    className="rounded-full border border-warning/25 bg-warning-soft px-2 py-0.5 text-[11px] font-medium text-warning"
                                    key={`${item.review_task_id}-${field.field_name}`}
                                  >
                                    {field.label}
                                  </span>
                                ))}
                                {item.review_diagnosis.affected_fields.length > 4 ? (
                                  <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                                    +{item.review_diagnosis.affected_fields.length - 4}
                                  </span>
                                ) : null}
                              </div>
                            ) : null}
                            <p className="border-l-2 border-primary/35 pl-2.5 text-xs leading-5 text-muted-foreground">
                              <span className="font-medium text-foreground">{copy.recommendation}:</span>{" "}
                              {recommendedActionLabel(locale, item.review_diagnosis.recommended_action)}
                            </p>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-3">
                        <div className="grid gap-2">
                          <span className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", validationBadgeClasses(item.validation_status))}>
                            {formatValidationStatusLabel(locale, item.validation_status)}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            <strong className="font-semibold text-foreground">{formatConfidence(item.source_confidence)}</strong>{" "}
                            {copy.confidence}
                          </span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-3">
                        <div className="grid gap-2">
                          <span className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", stateBadgeClasses(item.review_state))}>
                            {translateReviewState(locale, item.review_state)}
                          </span>
                          <time className="text-xs leading-5 text-muted-foreground" dateTime={item.created_at}>
                            {formatAdminDateTime(locale, item.created_at)}
                          </time>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-3">
                        <div className="grid gap-1 font-mono text-[11px] leading-5 text-muted-foreground">
                          <Link
                            className="underline-offset-4 hover:text-primary hover:underline"
                            href={buildAdminHref(`/admin/reviews/${item.review_task_id}`, new URLSearchParams(), locale)}
                          >
                            {copy.task} {item.review_task_id}
                          </Link>
                          <span>{copy.candidate} {item.candidate_id}</span>
                          <Link
                            className="underline-offset-4 hover:text-primary hover:underline"
                            href={buildAdminHref(`/admin/runs/${item.run_id}`, new URLSearchParams(), locale)}
                          >
                            {copy.run} {item.run_id}
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="flex flex-col gap-3 border-t border-border px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              {copy.showing((queue.page - 1) * queue.page_size + 1, Math.min(queue.page * queue.page_size, queue.total_items), queue.total_items)}
            </p>
            <div className="flex items-center gap-2">
              {queue.page > 1 ? (
                <Button asChild className="min-h-10" size="sm" variant="outline">
                  <Link href={buildQueueHref(filters, { page: Math.max(1, queue.page - 1) }, locale)}>{copy.previous}</Link>
                </Button>
              ) : (
                <span className="inline-flex h-10 items-center rounded-md border border-border bg-muted px-3 text-sm text-muted-foreground opacity-60">
                  {copy.previous}
                </span>
              )}
              {queue.has_next_page ? (
                <Button asChild className="min-h-10" size="sm" variant="outline">
                  <Link href={buildQueueHref(filters, { page: queue.page + 1 }, locale)}>{copy.next}</Link>
                </Button>
              ) : (
                <span className="inline-flex h-10 items-center rounded-md border border-border bg-muted px-3 text-sm text-muted-foreground opacity-60">
                  {copy.next}
                </span>
              )}
            </div>
          </div>
        </>
      )}
    </article>
  );
}

function buildQueueHref(
  filters: ReviewQueueResultsFilters,
  overrides: Partial<ReviewQueueResultsFilters>,
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

function isBulkSelectable(item: ReviewTaskListItem) {
  return ACTIVE_REVIEW_STATES.has(item.review_state);
}

function actionLabel(locale: AdminLocale, _action: BulkAction) {
  return RESULTS_COPY[locale].defer;
}

async function responseErrorMessage(response: Response) {
  try {
    const payload = (await response.json()) as { error?: { message?: string } };
    return payload.error?.message ?? response.statusText;
  } catch {
    return response.statusText;
  }
}

function formatConfidence(value: number | null) {
  if (value === null) {
    return "n/a";
  }
  return `${Math.round(value * 100)}%`;
}

function formatValidationStatusLabel(locale: AdminLocale, value: string) {
  if (value === "error") {
    return locale === "en" ? "Validation Error" : translateValidationStatus(locale, value);
  }
  if (value === "warning") {
    return locale === "en" ? "Validation Warning" : translateValidationStatus(locale, value);
  }
  return translateValidationStatus(locale, value);
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

function recommendedActionLabel(locale: AdminLocale, action: ReviewTaskListItem["recommended_action"]) {
  switch (action) {
    case "edit_approve":
      return locale === "ko" ? "필드를 수정한 뒤 승인" : locale === "ja" ? "項目を修正して承認" : "Correct fields and approve";
    case "reject":
      return locale === "ko" ? "거절" : locale === "ja" ? "却下" : "Reject";
    case "defer":
      return locale === "ko" ? "보류 후 추가 조사" : locale === "ja" ? "保留して追加調査" : "Defer and investigate";
    default:
      return locale === "ko" ? "확인 후 승인" : locale === "ja" ? "確認後に承認" : "Approve after verification";
  }
}

function diagnosisCategoryLabel(locale: AdminLocale, category: string) {
  switch (category) {
    case "non_product_source":
      return locale === "ko" ? "상품 아님" : locale === "ja" ? "商品ではない" : "Not a product";
    case "suspect_fields":
      return locale === "ko" ? "의심 값" : locale === "ja" ? "疑わしい値" : "Wrong values";
    case "missing_fields":
      return locale === "ko" ? "누락 값" : locale === "ja" ? "欠損値" : "Missing values";
    case "validation_error":
      return locale === "ko" ? "검증 오류" : locale === "ja" ? "検証エラー" : "Validation error";
    default:
      return locale === "ko" ? "근거 확인" : locale === "ja" ? "根拠確認" : "Evidence check";
  }
}

function diagnosisBadgeClasses(category: string) {
  if (category === "non_product_source") {
    return "bg-destructive/10 text-destructive";
  }
  if (category === "evidence_review") {
    return "bg-info-soft text-info";
  }
  return "bg-warning-soft text-warning";
}

function toTitleCase(value: string) {
  return value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}
