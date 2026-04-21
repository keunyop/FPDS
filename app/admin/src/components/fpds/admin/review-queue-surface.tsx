import Link from "next/link";

import { Banner1 } from "@/components/banner1";
import { Stats5 } from "@/components/stats5";
import { Button } from "@/components/ui/button";
import type { ReviewQueueResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

const REVIEW_STATES = ["queued", "deferred", "approved", "edited", "rejected"] as const;
const BANK_OPTIONS = ["TD", "RBC", "BMO", "SCOTIA", "CIBC"] as const;
const PRODUCT_TYPE_OPTIONS = ["savings", "chequing", "gic"] as const;
const VALIDATION_OPTIONS = ["pass", "warning", "error"] as const;

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
};

export function ReviewQueueSurface({ queue, filters, locale }: ReviewQueueSurfaceProps) {
  const stateCounts = queue.summary.state_counts;
  const validationCounts = queue.summary.validation_counts;
  const statItems = [
    {
      label: "Visible tasks",
      value: String(queue.summary.total_items),
      note: "The current filter set drives the table, state counts, and pagination.",
      tone: "info" as const,
    },
    {
      label: "Queued",
      value: String(stateCounts.queued ?? 0),
      note: "Ready for reviewer intake right now.",
      tone: "warning" as const,
    },
    {
      label: "Deferred",
      value: String(stateCounts.deferred ?? 0),
      note: "Parked tasks stay visible without mixing into terminal history.",
      tone: "neutral" as const,
    },
    {
      label: "Warnings + Errors",
      value: String((validationCounts.warning ?? 0) + (validationCounts.error ?? 0)),
      note: "Validation pressure stays visible even before detail and trace actions land.",
      tone: "success" as const,
    },
  ];

  return (
    <section className="grid gap-6">
      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Review queue</p>
            <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
              Active candidate review work now has its own protected queue surface.
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
              This route keeps reviewer intake table-first, searchable, and filterable inside the FPDS admin shell.
              Review decisions and evidence trace stay reserved for the next slices, but queue triage is now live on top
              of real `review_task` data.
            </p>
          </div>

          <div className="inline-flex items-center rounded-full bg-success-soft px-3 py-1 text-xs font-medium text-success">
            Live route
          </div>
        </div>

        <div className="mt-6">
          <Banner1
            defaultVisible={true}
            description="Default load stays focused on active work by showing queued and deferred tasks first. Detail, approve, reject, defer, and trace controls remain intentionally out of this slice."
            dismissible={false}
            title="Slice boundary"
            tone="info"
          />
        </div>
      </article>

      <Stats5
        className="bg-card/95"
        description="Queue metrics stay compact and operational. They summarize the filtered result set instead of pretending to replace the dedicated detail, run, and publish surfaces."
        items={statItems}
        title="Filtered queue snapshot"
      />

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <div className="flex flex-col gap-4 border-b border-border/80 pb-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Filters and sort</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Queue-first controls</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Search by task, candidate, run, bank, or product name. State defaults stay active-first unless you
              explicitly widen the queue.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button asChild size="sm" variant="outline">
              <Link href={buildAdminHref("/admin/reviews", new URLSearchParams(), locale)}>Active queue</Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href={buildQueueHref(filters, { states: [...REVIEW_STATES], page: 1 }, locale)}>All states</Link>
            </Button>
          </div>
        </div>

        <form action={buildAdminHref("/admin/reviews", new URLSearchParams(), locale)} className="mt-6 grid gap-5">
          <div className="grid gap-4 xl:grid-cols-[1.5fr_repeat(5,minmax(0,1fr))]">
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Search</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.q}
                name="q"
                placeholder="task, candidate, run, bank, or product"
                type="search"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Bank</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.bankCode}
                name="bank_code"
              >
                <option value="">All banks</option>
                {BANK_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Product type</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.productType}
                name="product_type"
              >
                <option value="">All types</option>
                {PRODUCT_TYPE_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {toTitleCase(option)}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Validation</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.validationStatus}
                name="validation_status"
              >
                <option value="">All statuses</option>
                {VALIDATION_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {toTitleCase(option)}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Sort by</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.sortBy}
                name="sort_by"
              >
                <option value="priority">Priority</option>
                <option value="created_at">Created time</option>
                <option value="updated_at">Updated time</option>
                <option value="source_confidence">Confidence</option>
                <option value="product_name">Product name</option>
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Order</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.sortOrder}
                name="sort_order"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </label>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr_1fr_auto]">
            <fieldset className="grid gap-2 text-sm">
              <legend className="font-medium text-foreground">Review states</legend>
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
                    <span>{toTitleCase(state)}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Created from</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.createdFrom}
                name="created_from"
                type="date"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Created to</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.createdTo}
                name="created_to"
                type="date"
              />
            </label>

            <div className="flex items-end gap-2">
              <Button type="submit">Apply filters</Button>
              <Button asChild variant="outline">
                <Link href={buildAdminHref("/admin/reviews", new URLSearchParams(), locale)}>Reset</Link>
              </Button>
            </div>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="flex flex-col gap-3 border-b border-border/80 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Results</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Reviewer intake table</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Page {queue.page} of {Math.max(queue.total_pages, 1)} with {queue.total_items} matching task
              {queue.total_items === 1 ? "" : "s"}.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {filters.states.map((state) => (
              <span className={cn("rounded-full px-3 py-1 text-xs font-medium", stateBadgeClasses(state))} key={state}>
                {toTitleCase(state)}
              </span>
            ))}
            {filters.bankCode ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {filters.bankCode}
              </span>
            ) : null}
            {filters.productType ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {toTitleCase(filters.productType)}
              </span>
            ) : null}
            {filters.validationStatus ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {toTitleCase(filters.validationStatus)}
              </span>
            ) : null}
          </div>
        </div>

        {queue.items.length === 0 ? (
          <div className="px-6 py-10">
            <div className="rounded-[1.5rem] border border-dashed border-border bg-background px-6 py-8">
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">No matching tasks</p>
              <h3 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
                The current queue filter returned no review work.
              </h3>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
                Widen the state filter, clear the search term, or reset the form. Active queue remains the default
                intake view, so terminal states only appear when you explicitly request them.
              </p>
              <div className="mt-6">
                <Button asChild variant="outline">
                  <Link href="/admin/reviews">Reset queue filters</Link>
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto px-6 py-5">
              <table className="min-w-[1120px] table-fixed border-separate border-spacing-0">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    <th className="border-b border-border px-3 py-3 font-medium">Task</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Bank</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Country</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Product</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Issue summary</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Confidence</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Validation</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Created</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Status</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Action</th>
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
                          <span className="text-xs text-muted-foreground">Candidate {item.candidate_id}</span>
                          <Link className="text-xs text-muted-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/runs/${item.run_id}`, new URLSearchParams(), locale)}>
                            Run {item.run_id}
                          </Link>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          <span className="font-medium text-foreground">{item.bank_name}</span>
                          <span className="text-xs text-muted-foreground">{item.bank_code}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4 text-sm text-foreground">{item.country_code}</td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <span className="font-medium text-foreground">{item.product_name}</span>
                          <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
                            {toTitleCase(item.product_type)}
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
                          <span className="text-xs text-muted-foreground">Source confidence</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <span className={cn("inline-flex rounded-full px-2.5 py-1 text-xs font-medium", validationBadgeClasses(item.validation_status))}>
                          {formatValidationStatusLabel(item.validation_status)}
                        </span>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          <span className="text-sm text-foreground">{formatTimestamp(item.created_at)}</span>
                          <span className="text-xs text-muted-foreground">Updated {formatTimestamp(item.updated_at)}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <span className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", stateBadgeClasses(item.review_state))}>
                            {toTitleCase(item.review_state)}
                          </span>
                          <span className="text-xs text-muted-foreground">Candidate {item.candidate_state}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <Button asChild size="sm" variant="outline">
                            <Link href={buildAdminHref(`/admin/reviews/${item.review_task_id}`, new URLSearchParams(), locale)}>Open detail</Link>
                          </Button>
                          <span className="text-xs leading-5 text-muted-foreground">
                            Decision controls land in `4.3` after detail and trace context are in place.
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
                Showing {(queue.page - 1) * queue.page_size + 1}-
                {Math.min(queue.page * queue.page_size, queue.total_items)} of {queue.total_items}
              </p>
              <div className="flex items-center gap-2">
                {queue.page > 1 ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildQueueHref(filters, { page: Math.max(1, queue.page - 1) }, locale)}>Previous</Link>
                  </Button>
                ) : (
                  <span className="inline-flex h-7 items-center rounded-[min(var(--radius-md),12px)] border border-border bg-muted px-2.5 text-[0.8rem] text-muted-foreground opacity-60">
                    Previous
                  </span>
                )}
                {queue.has_next_page ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildQueueHref(filters, { page: queue.page + 1 }, locale)}>Next</Link>
                  </Button>
                ) : (
                  <span className="inline-flex h-7 items-center rounded-[min(var(--radius-md),12px)] border border-border bg-muted px-2.5 text-[0.8rem] text-muted-foreground opacity-60">
                    Next
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

function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatConfidence(value: number | null) {
  if (value === null) {
    return "n/a";
  }
  return `${Math.round(value * 100)}%`;
}

function formatValidationStatusLabel(value: string) {
  if (value === "error") {
    return "Validation Error";
  }
  if (value === "warning") {
    return "Validation Warning";
  }
  return toTitleCase(value);
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
