"use client";

import Link from "next/link";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { Stats5 } from "@/components/stats5";
import { Button } from "@/components/ui/button";
import type { ChangeHistoryListResponse } from "@/lib/admin-api";
import { cn } from "@/lib/utils";

const BANK_OPTIONS = ["TD", "RBC", "BMO", "SCOTIA", "CIBC"] as const;
const PRODUCT_TYPE_OPTIONS = ["savings", "chequing", "gic"] as const;
const CHANGE_TYPE_OPTIONS = ["New", "Updated", "Discontinued", "Reclassified", "ManualOverride"] as const;

export type ChangeHistoryPageFilters = {
  q: string;
  bankCode: string;
  productType: string;
  changeType: string;
  changedFrom: string;
  changedTo: string;
  sortBy: string;
  sortOrder: "asc" | "desc";
  page: number;
};

type ChangeHistorySurfaceProps = {
  filters: ChangeHistoryPageFilters;
  changes: ChangeHistoryListResponse;
};

export function ChangeHistorySurface({ filters, changes }: ChangeHistorySurfaceProps) {
  const changeTypeCounts = changes.summary.change_type_counts;
  const statItems = [
    {
      label: "Visible changes",
      value: String(changes.summary.total_items),
      note: "Current filters.",
      tone: "info" as const,
    },
    {
      label: "Affected products",
      value: String(changes.summary.affected_product_count),
      note: "In this view.",
      tone: "success" as const,
    },
    {
      label: "Manual overrides",
      value: String(changes.summary.manual_override_items),
      note: "Operator edits.",
      tone: "warning" as const,
    },
    {
      label: "Reclassified",
      value: String(changeTypeCounts.Reclassified ?? 0),
      note: "Taxonomy changes.",
      tone: "neutral" as const,
    },
  ];

  return (
    <section className="grid gap-6">
      <AdminPageHeader
        description="Canonical changes with review, run, and audit context."
        path={["Operations", "Change History"]}
        title="Change History"
      />

      <Stats5
        items={statItems}
        title="Change Snapshot"
      />

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <div className="flex flex-col gap-4 border-b border-border/80 pb-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Filters and sort</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Change Controls</h2>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button asChild size="sm" variant="outline">
              <Link href="/admin/changes">Latest changes</Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href={buildChangeHref(filters, { changeType: "ManualOverride", page: 1 })}>Manual overrides</Link>
            </Button>
          </div>
        </div>

        <form action="/admin/changes" className="mt-6 grid gap-5">
          <div className="grid gap-4 xl:grid-cols-[1.6fr_repeat(4,minmax(0,1fr))]">
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Search</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.q}
                name="q"
                placeholder="product, change id, run, or review task"
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
              <span className="font-medium text-foreground">Change type</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.changeType}
                name="change_type"
              >
                <option value="">All changes</option>
                {CHANGE_TYPE_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option === "ManualOverride" ? "Manual override" : option}
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
                <option value="detected_at">Detected time</option>
                <option value="change_type">Change type</option>
                <option value="product_name">Product name</option>
                <option value="bank_code">Bank code</option>
              </select>
            </label>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1fr_1fr_1fr_auto]">
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Changed from</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.changedFrom}
                name="changed_from"
                type="date"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Changed to</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.changedTo}
                name="changed_to"
                type="date"
              />
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

            <div className="flex items-end gap-2">
              <Button type="submit">Apply filters</Button>
              <Button asChild variant="outline">
                <Link href="/admin/changes">Reset</Link>
              </Button>
            </div>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="flex flex-col gap-3 border-b border-border/80 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Results</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Change table</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Page {changes.page} of {Math.max(changes.total_pages, 1)} with {changes.total_items} matching change
              {changes.total_items === 1 ? "" : "s"}.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
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
            {filters.changeType ? (
              <span className={cn("rounded-full px-3 py-1 text-xs font-medium", changeTypeBadgeClasses(filters.changeType))}>
                {formatChangeType(filters.changeType)}
              </span>
            ) : null}
            {filters.changedFrom || filters.changedTo ? (
              <span className="rounded-full bg-info-soft px-3 py-1 text-xs font-medium text-info">
                {filters.changedFrom || "Start"} to {filters.changedTo || "Now"}
              </span>
            ) : null}
          </div>
        </div>

        {changes.items.length === 0 ? (
          <div className="px-6 py-10">
            <div className="rounded-[1.5rem] border border-dashed border-border bg-background px-6 py-8">
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">No matching changes</p>
              <h3 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
                The current filter set returned no canonical change events.
              </h3>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
                Widen the date range, remove the change-type filter, or clear the search term. Change history stays
                separate from current product state, so this route only shows persisted canonical events.
              </p>
              <div className="mt-6">
                <Button asChild variant="outline">
                  <Link href="/admin/changes">Reset change filters</Link>
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto px-6 py-5">
              <table className="min-w-[1560px] table-fixed border-separate border-spacing-0">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    <th className="border-b border-border px-3 py-3 font-medium">Change</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Product</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Detected</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Changed fields</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Review context</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Run context</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Audit context</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {changes.items.map((item) => (
                    <tr className="align-top" key={item.change_event_id}>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <span className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", changeTypeBadgeClasses(item.change_type))}>
                            {formatChangeType(item.change_type)}
                          </span>
                          <p className="text-sm font-medium leading-6 text-foreground">{item.change_summary}</p>
                          <span className="text-xs text-muted-foreground">{item.change_event_id}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          <p className="font-medium text-foreground">{item.product_name}</p>
                          <p className="text-sm text-muted-foreground">
                            {item.bank_name} · {toTitleCase(item.product_type)}
                            {item.subtype_code ? ` · ${item.subtype_code}` : ""}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Product {item.canonical_product_id}
                            {item.version_info.current_version_no ? ` · v${item.version_info.current_version_no}` : ""}
                          </p>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1 text-sm">
                          <span className="font-medium text-foreground">{formatTimestamp(item.detected_at)}</span>
                          <span className="text-muted-foreground">
                            Previous version {item.version_info.previous_version_no ?? "n/a"}
                          </span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        {item.changed_fields.length === 0 ? (
                          <p className="text-sm leading-6 text-muted-foreground">No field-level diff was stored for this event.</p>
                        ) : (
                          <div className="flex flex-wrap gap-2">
                            {item.changed_fields.map((field) => (
                              <span
                                className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground"
                                key={`${item.change_event_id}-${field}`}
                              >
                                {field}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        {item.review_context.review_task_id ? (
                          <div className="grid gap-2 text-sm">
                            <Link
                              className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline"
                              href={`/admin/reviews/${item.review_context.review_task_id}`}
                            >
                              {item.review_context.review_task_id}
                            </Link>
                            <span className="text-muted-foreground">
                              {toTitleCase(item.review_context.review_state ?? "unknown")}
                              {item.review_context.action_type ? ` · ${toTitleCase(item.review_context.action_type)}` : ""}
                            </span>
                            <span className="text-muted-foreground">
                              {item.review_context.diff_summary ?? item.review_context.reason_text ?? "No reviewer note stored."}
                            </span>
                          </div>
                        ) : (
                          <p className="text-sm leading-6 text-muted-foreground">No linked review task is stored for this event.</p>
                        )}
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        {item.run_context.run_id ? (
                          <div className="grid gap-2 text-sm">
                            <Link
                              className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline"
                              href={`/admin/runs/${item.run_context.run_id}`}
                            >
                              {item.run_context.run_id}
                            </Link>
                            <span className="text-muted-foreground">
                              {toTitleCase(item.run_context.run_type ?? "unknown")} · {toTitleCase(item.run_context.run_status ?? "unknown")}
                            </span>
                            <span className="text-muted-foreground">
                              {item.run_context.correlation_id ? `Correlation ${item.run_context.correlation_id}` : "No correlation id stored."}
                            </span>
                          </div>
                        ) : (
                          <p className="text-sm leading-6 text-muted-foreground">No producing run is linked to this event.</p>
                        )}
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        {item.audit_context ? (
                          <div className="grid gap-2 text-sm">
                            <span className="inline-flex w-fit rounded-full bg-warning-soft px-2.5 py-1 text-xs font-medium text-warning">
                              Manual override audit
                            </span>
                            <span className="font-medium text-foreground">
                              {item.audit_context.actor.display_name ?? item.actor.display_name ?? "Operator"}
                            </span>
                            <span className="text-muted-foreground">
                              {item.audit_context.diff_summary ?? "Audit diff summary not stored."}
                            </span>
                            <span className="text-muted-foreground">{formatTimestamp(item.audit_context.occurred_at)}</span>
                          </div>
                        ) : (
                          <div className="grid gap-1 text-sm">
                            <span className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", actorTypeBadgeClasses(item.actor_type))}>
                              {item.actor_type === "user" ? "User-linked" : "System-linked"}
                            </span>
                            <span className="text-muted-foreground">
                              {item.actor.display_name ?? item.actor.email ?? "No explicit actor snapshot stored."}
                            </span>
                          </div>
                        )}
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="flex flex-col gap-2">
                          {item.review_context.review_task_id ? (
                            <Button asChild size="sm" variant="outline">
                              <Link href={`/admin/reviews/${item.review_context.review_task_id}`}>Review detail</Link>
                            </Button>
                          ) : null}
                          {item.run_context.run_id ? (
                            <Button asChild size="sm" variant="outline">
                              <Link href={`/admin/runs/${item.run_context.run_id}`}>Run detail</Link>
                            </Button>
                          ) : null}
                          {!item.review_context.review_task_id && !item.run_context.run_id ? (
                            <span className="text-xs text-muted-foreground">No related drilldown is available.</span>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-col gap-3 border-t border-border/80 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {(changes.page - 1) * changes.page_size + 1}-{Math.min(changes.page * changes.page_size, changes.total_items)} of{" "}
                {changes.total_items}
              </p>
              <div className="flex items-center gap-2">
                {changes.page > 1 ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildChangeHref(filters, { page: Math.max(1, changes.page - 1) })}>Previous</Link>
                  </Button>
                ) : (
                  <span className="inline-flex h-7 items-center rounded-[min(var(--radius-md),12px)] border border-border bg-muted px-2.5 text-[0.8rem] text-muted-foreground opacity-60">
                    Previous
                  </span>
                )}
                {changes.has_next_page ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildChangeHref(filters, { page: changes.page + 1 })}>Next</Link>
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

function buildChangeHref(filters: ChangeHistoryPageFilters, overrides: Partial<ChangeHistoryPageFilters>) {
  const next = {
    ...filters,
    ...overrides,
  };
  const params = new URLSearchParams();
  if (next.q) {
    params.set("q", next.q);
  }
  if (next.bankCode) {
    params.set("bank_code", next.bankCode);
  }
  if (next.productType) {
    params.set("product_type", next.productType);
  }
  if (next.changeType) {
    params.set("change_type", next.changeType);
  }
  if (next.changedFrom) {
    params.set("changed_from", next.changedFrom);
  }
  if (next.changedTo) {
    params.set("changed_to", next.changedTo);
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

  const query = params.toString();
  return query ? `/admin/changes?${query}` : "/admin/changes";
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return "n/a";
  }
  return new Intl.DateTimeFormat("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function toTitleCase(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatChangeType(value: string) {
  return value === "ManualOverride" ? "Manual override" : value;
}

function changeTypeBadgeClasses(changeType: string) {
  switch (changeType) {
    case "New":
      return "bg-success-soft text-success";
    case "Updated":
      return "bg-info-soft text-info";
    case "Discontinued":
      return "bg-destructive/10 text-destructive";
    case "Reclassified":
      return "bg-warning-soft text-warning";
    case "ManualOverride":
      return "bg-warning-soft text-warning";
    default:
      return "bg-muted text-muted-foreground";
  }
}

function actorTypeBadgeClasses(actorType: string) {
  return actorType === "user" ? "bg-info-soft text-info" : "bg-muted text-muted-foreground";
}
