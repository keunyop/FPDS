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
  results: "Results",
  tableTitle: "Reviewer intake table",
  pageSummary: (page: number, totalPages: number, totalItems: number) =>
    `Page ${page} of ${Math.max(totalPages, 1)} with ${totalItems} matching task${totalItems === 1 ? "" : "s"}.`,
  noMatches: "No matching tasks",
  emptyTitle: "The current queue filter returned no review work.",
  emptyBody: "Widen the state filter, clear the search term, or reset the form. Active queue remains the default intake view.",
  resetQueueFilters: "Reset queue filters",
  select: "Select",
  selected: (count: number) => `${count} selected`,
  selectPage: "Select active rows on this page",
  bulkUnavailable: "Only bulk defer is available. Approval and rejection require opening each task.",
  bulkSucceeded: (action: string, count: number) => `${action} completed for ${count} task${count === 1 ? "" : "s"}.`,
  bulkPartial: (action: string, succeeded: number, failed: number) => `${action} completed for ${succeeded}; ${failed} failed.`,
  bulkFailed: (action: string, failed: number) => `${action} failed for ${failed} task${failed === 1 ? "" : "s"}.`,
  task: "Task",
  bank: "Bank",
  product: "Product",
  issueSummary: "Issue summary",
  confidence: "Confidence",
  validation: "Validation",
  created: "Created",
  status: "Status",
  candidate: "Candidate",
  run: "Run",
  previous: "Previous",
  next: "Next",
  showing: (from: number, to: number, total: number) => `Showing ${from}-${to} of ${total}`,
};

export function ReviewQueueResults({ queue, filters, locale, productTypes, csrfToken }: ReviewQueueResultsProps) {
  const router = useRouter();
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
      setStatusMessage(RESULTS_COPY.bulkUnavailable);
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
          reason_text: `Bulk ${actionLabel(action).toLowerCase()} from Review Queue.`,
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
      setStatusMessage(RESULTS_COPY.bulkSucceeded(actionLabel(action), succeeded));
    } else if (succeeded > 0) {
      setStatusMessage(`${RESULTS_COPY.bulkPartial(actionLabel(action), succeeded, failures.length)} ${failures.slice(0, 2).join(" ")}`);
    } else {
      setStatusMessage(`${RESULTS_COPY.bulkFailed(actionLabel(action), failures.length)} ${failures.slice(0, 2).join(" ")}`);
    }
    router.refresh();
  }

  return (
    <article className="min-w-0 overflow-hidden rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
      <div className="flex flex-col gap-3 border-b border-border/80 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{RESULTS_COPY.results}</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{RESULTS_COPY.tableTitle}</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            {RESULTS_COPY.pageSummary(queue.page, queue.total_pages, queue.total_items)}
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
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{RESULTS_COPY.noMatches}</p>
            <h3 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
              {RESULTS_COPY.emptyTitle}
            </h3>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
              {RESULTS_COPY.emptyBody}
            </p>
            <div className="mt-6">
              <Button asChild variant="outline">
                <Link href={buildAdminHref("/admin/reviews", new URLSearchParams(), locale)}>{RESULTS_COPY.resetQueueFilters}</Link>
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="flex flex-col gap-3 border-b border-border/80 bg-background/45 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-wrap items-center gap-3">
              <label className="inline-flex items-center gap-2 text-sm font-medium text-foreground">
                <input
                  aria-label={RESULTS_COPY.selectPage}
                  checked={allSelectableSelected}
                  className="h-4 w-4 rounded border-border text-primary accent-[var(--primary)]"
                  disabled={selectableIds.length === 0 || pendingAction !== null}
                  onChange={(event) => togglePage(event.currentTarget.checked)}
                  type="checkbox"
                />
                <span>{RESULTS_COPY.selected(selectedIds.length)}</span>
              </label>
              <span className="text-xs text-muted-foreground">{RESULTS_COPY.bulkUnavailable}</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button disabled={selectedIds.length === 0 || pendingAction !== null} onClick={() => handleBulkAction("defer")} size="sm" type="button" variant="outline">
                {pendingAction === "defer" ? <Loader2 className="animate-spin" /> : <CirclePause />}
                {pendingAction === "defer" ? "Deferring..." : translateReviewAction(locale, "defer")}
              </Button>
            </div>
          </div>

          {statusMessage ? (
            <div className="border-b border-border/80 px-6 py-3">
              <p className="text-sm text-muted-foreground" role="status">{statusMessage}</p>
            </div>
          ) : null}

          <div className="max-w-full overflow-x-auto px-6 py-5">
            <table className="min-w-[1010px] table-fixed border-separate border-spacing-0">
              <thead>
                <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                  <th className="w-12 border-b border-border px-3 py-3 font-medium">{RESULTS_COPY.select}</th>
                  <th className="border-b border-border px-3 py-3 font-medium">{RESULTS_COPY.task}</th>
                  <th className="border-b border-border px-3 py-3 font-medium">{RESULTS_COPY.bank}</th>
                  <th className="border-b border-border px-3 py-3 font-medium">{RESULTS_COPY.product}</th>
                  <th className="border-b border-border px-3 py-3 font-medium">{RESULTS_COPY.issueSummary}</th>
                  <th className="border-b border-border px-3 py-3 font-medium">{RESULTS_COPY.confidence}</th>
                  <th className="border-b border-border px-3 py-3 font-medium">{RESULTS_COPY.validation}</th>
                  <th className="border-b border-border px-3 py-3 font-medium">{RESULTS_COPY.created}</th>
                  <th className="border-b border-border px-3 py-3 font-medium">{RESULTS_COPY.status}</th>
                </tr>
              </thead>
              <tbody>
                {queue.items.map((item) => {
                  const selectable = isBulkSelectable(item);
                  return (
                    <tr className="align-top" key={item.review_task_id}>
                      <td className="border-b border-border/70 px-3 py-4">
                        <input
                          aria-label={`Select ${item.review_task_id}`}
                          checked={selectedSet.has(item.review_task_id)}
                          className="h-4 w-4 rounded border-border text-primary accent-[var(--primary)] disabled:opacity-40"
                          disabled={!selectable || pendingAction !== null}
                          onChange={(event) => toggleItem(item.review_task_id, event.currentTarget.checked)}
                          type="checkbox"
                        />
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          <Link
                            className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline"
                            href={buildAdminHref(`/admin/reviews/${item.review_task_id}`, new URLSearchParams(), locale)}
                          >
                            {item.review_task_id}
                          </Link>
                          <span className="text-xs text-muted-foreground">{RESULTS_COPY.candidate} {item.candidate_id}</span>
                          <Link className="text-xs text-muted-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/runs/${item.run_id}`, new URLSearchParams(), locale)}>
                            {RESULTS_COPY.run} {item.run_id}
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
                        <span className="text-sm font-medium text-foreground">{formatConfidence(item.source_confidence)}</span>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <span className={cn("inline-flex rounded-full px-2.5 py-1 text-xs font-medium", validationBadgeClasses(item.validation_status))}>
                          {formatValidationStatusLabel(locale, item.validation_status)}
                        </span>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <span className="text-sm text-foreground">{formatAdminDateTime(locale, item.created_at)}</span>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <span className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", stateBadgeClasses(item.review_state))}>
                          {translateReviewState(locale, item.review_state)}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="flex flex-col gap-3 border-t border-border/80 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              {RESULTS_COPY.showing((queue.page - 1) * queue.page_size + 1, Math.min(queue.page * queue.page_size, queue.total_items), queue.total_items)}
            </p>
            <div className="flex items-center gap-2">
              {queue.page > 1 ? (
                <Button asChild size="sm" variant="outline">
                  <Link href={buildQueueHref(filters, { page: Math.max(1, queue.page - 1) }, locale)}>{RESULTS_COPY.previous}</Link>
                </Button>
              ) : (
                <span className="inline-flex h-7 items-center rounded-[min(var(--radius-md),12px)] border border-border bg-muted px-2.5 text-[0.8rem] text-muted-foreground opacity-60">
                  {RESULTS_COPY.previous}
                </span>
              )}
              {queue.has_next_page ? (
                <Button asChild size="sm" variant="outline">
                  <Link href={buildQueueHref(filters, { page: queue.page + 1 }, locale)}>{RESULTS_COPY.next}</Link>
                </Button>
              ) : (
                <span className="inline-flex h-7 items-center rounded-[min(var(--radius-md),12px)] border border-border bg-muted px-2.5 text-[0.8rem] text-muted-foreground opacity-60">
                  {RESULTS_COPY.next}
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

function actionLabel(_action: BulkAction) {
  return "Defer";
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

function issueBadgeClasses(severity: string) {
  if (severity === "error") {
    return "bg-destructive/10 text-destructive";
  }
  return "bg-warning-soft text-warning";
}
