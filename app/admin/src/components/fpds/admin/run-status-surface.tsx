"use client";

import Link from "next/link";

import { Banner1 } from "@/components/banner1";
import { Stats5 } from "@/components/stats5";
import { Button } from "@/components/ui/button";
import type { RunStatusListResponse } from "@/lib/admin-api";
import { cn } from "@/lib/utils";

const RUN_STATES = ["started", "completed", "failed", "retried"] as const;
const COMMON_RUN_TYPES = ["snapshot_capture", "parse_chunk", "extraction", "normalization", "validation_routing"] as const;

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
};

export function RunStatusSurface({ filters, runs }: RunStatusSurfaceProps) {
  const stateCounts = runs.summary.state_counts;
  const runTypeOptions = Array.from(new Set([...COMMON_RUN_TYPES, ...Object.keys(runs.summary.run_type_counts)])).sort();
  const statItems = [
    {
      label: "Visible runs",
      value: String(runs.summary.total_items),
      note: "The current filter set drives the table, counts, and paging.",
      tone: "info" as const,
    },
    {
      label: "Failed",
      value: String(stateCounts.failed ?? 0),
      note: "Fatal run-level failures stay separate from completed partial runs.",
      tone: "warning" as const,
    },
    {
      label: "Partial",
      value: String(runs.summary.partial_items),
      note: "Completed runs with degraded source or stage outcomes stay explicit.",
      tone: "neutral" as const,
    },
    {
      label: "In progress",
      value: String(stateCounts.started ?? 0),
      note: "Started runs remain visible until they reach a terminal state.",
      tone: "success" as const,
    },
  ];

  return (
    <section className="grid gap-6">
      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Run diagnostics</p>
            <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
              Ingestion runs now have a dedicated diagnostic surface inside the FPDS admin shell.
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
              This route keeps run status table-first, surfaces partial completion separately from fatal failure, and
              gives operators a stable path into run-level diagnosis when review trace points to broader execution
              issues.
            </p>
          </div>

          <div className="inline-flex items-center rounded-full bg-success-soft px-3 py-1 text-xs font-medium text-success">
            Live route
          </div>
        </div>

        <div className="mt-6">
          <Banner1
            defaultVisible={true}
            description="The current slice focuses on run list, run detail, source processing summary, error summary, related review tasks, and usage summary. Retry controls, audit history, and publish drilldown remain separate follow-on surfaces."
            dismissible={false}
            title="Slice boundary"
            tone="info"
          />
        </div>
      </article>

      <Stats5
        className="bg-card/95"
        description="Run metrics stay compact and operational. They summarize the filtered run set instead of replacing the dedicated detail surface."
        items={statItems}
        title="Filtered run snapshot"
      />

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <div className="flex flex-col gap-4 border-b border-border/80 pb-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Filters and sort</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Triage-first controls</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Search by run id, trigger, or correlation id. Partial completion and retried history stay queryable
              without taking over the default view.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button asChild size="sm" variant="outline">
              <Link href="/admin/runs">Default runs</Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href={buildRunHref(filters, { states: [...RUN_STATES], page: 1 })}>All states</Link>
            </Button>
          </div>
        </div>

        <form action="/admin/runs" className="mt-6 grid gap-5">
          <div className="grid gap-4 xl:grid-cols-[1.45fr_repeat(4,minmax(0,1fr))]">
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Search</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.q}
                name="q"
                placeholder="run, trigger, actor, or correlation"
                type="search"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Run type</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.runType}
                name="run_type"
              >
                <option value="">All types</option>
                {runTypeOptions.map((option) => (
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
                <option value="started_at">Started time</option>
                <option value="completed_at">Completed time</option>
                <option value="candidate_count">Candidate count</option>
                <option value="review_queued_count">Review queued</option>
                <option value="run_type">Run type</option>
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

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Scope</span>
              <span className="flex h-10 items-center rounded-xl border border-border bg-background px-3 text-sm text-foreground">
                <input
                  className="mr-2 h-4 w-4 rounded border-border text-primary accent-[var(--primary)]"
                  defaultChecked={filters.partialOnly}
                  name="partial_only"
                  type="checkbox"
                  value="true"
                />
                Partial only
              </span>
            </label>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.3fr_1fr_1fr_auto]">
            <fieldset className="grid gap-2 text-sm">
              <legend className="font-medium text-foreground">Run states</legend>
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
                    <span>{toTitleCase(state)}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Started from</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.startedFrom}
                name="started_from"
                type="date"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Started to</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.startedTo}
                name="started_to"
                type="date"
              />
            </label>

            <div className="flex items-end gap-2">
              <Button type="submit">Apply filters</Button>
              <Button asChild variant="outline">
                <Link href="/admin/runs">Reset</Link>
              </Button>
            </div>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="flex flex-col gap-3 border-b border-border/80 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Results</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Run table</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Page {runs.page} of {Math.max(runs.total_pages, 1)} with {runs.total_items} matching run
              {runs.total_items === 1 ? "" : "s"}.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {filters.states.map((state) => (
              <span className={cn("rounded-full px-3 py-1 text-xs font-medium", runStateBadgeClasses(state))} key={state}>
                {toTitleCase(state)}
              </span>
            ))}
            {filters.runType ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {toTitleCase(filters.runType)}
              </span>
            ) : null}
            {filters.partialOnly ? (
              <span className="rounded-full bg-warning-soft px-3 py-1 text-xs font-medium text-warning">Partial only</span>
            ) : null}
          </div>
        </div>

        {runs.items.length === 0 ? (
          <div className="px-6 py-10">
            <div className="rounded-[1.5rem] border border-dashed border-border bg-background px-6 py-8">
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">No matching runs</p>
              <h3 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
                The current run filter returned no execution history.
              </h3>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
                Widen the state filter, clear the search term, or turn off the partial-only filter. Retries and started
                runs remain queryable, but the default view stays focused on active and meaningful terminal states.
              </p>
              <div className="mt-6">
                <Button asChild variant="outline">
                  <Link href="/admin/runs">Reset run filters</Link>
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto px-6 py-5">
              <table className="min-w-[1220px] table-fixed border-separate border-spacing-0">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    <th className="border-b border-border px-3 py-3 font-medium">Run</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Type</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Status</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Window</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Source summary</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Candidate summary</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Error summary</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Retry chain</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.items.map((item) => (
                    <tr className="align-top" key={item.run_id}>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          <Link className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" href={`/admin/runs/${item.run_id}`}>
                            {item.run_id}
                          </Link>
                          <span className="text-xs text-muted-foreground">Trigger {toTitleCase(item.trigger_type)}</span>
                          {item.correlation_id ? (
                            <span className="text-xs text-muted-foreground">Correlation {item.correlation_id}</span>
                          ) : null}
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
                            {toTitleCase(item.run_type)}
                          </span>
                          {item.triggered_by ? <span className="text-xs text-muted-foreground">{item.triggered_by}</span> : null}
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <span className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", runStateBadgeClasses(item.run_status))}>
                            {toTitleCase(item.run_status)}
                          </span>
                          {item.partial_completion_flag ? (
                            <span className="inline-flex w-fit rounded-full bg-warning-soft px-2.5 py-1 text-xs font-medium text-warning">
                              Partial completion
                            </span>
                          ) : null}
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          <span className="text-sm text-foreground">{formatTimestamp(item.started_at)}</span>
                          <span className="text-xs text-muted-foreground">Completed {formatTimestamp(item.completed_at)}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1 text-sm">
                          <span className="font-medium text-foreground">{item.source_item_count} source items</span>
                          <span className="text-muted-foreground">
                            {item.success_count} success / {item.failure_count} failure
                          </span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1 text-sm">
                          <span className="font-medium text-foreground">{item.candidate_count} candidates</span>
                          <span className="text-muted-foreground">{item.review_queued_count} queued for review</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <p className="text-sm leading-6 text-muted-foreground">{item.error_summary ?? "No run-level error summary persisted."}</p>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1 text-sm">
                          <span className="text-foreground">{item.retry_of_run_id ?? "Original run"}</span>
                          <span className="text-muted-foreground">Next {item.retried_by_run_id ?? "n/a"}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <Button asChild size="sm" variant="outline">
                          <Link href={`/admin/runs/${item.run_id}`}>Open detail</Link>
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-col gap-3 border-t border-border/80 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {(runs.page - 1) * runs.page_size + 1}-{Math.min(runs.page * runs.page_size, runs.total_items)} of {runs.total_items}
              </p>
              <div className="flex items-center gap-2">
                {runs.page > 1 ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildRunHref(filters, { page: Math.max(1, runs.page - 1) })}>Previous</Link>
                  </Button>
                ) : (
                  <span className="inline-flex h-7 items-center rounded-[min(var(--radius-md),12px)] border border-border bg-muted px-2.5 text-[0.8rem] text-muted-foreground opacity-60">
                    Previous
                  </span>
                )}
                {runs.has_next_page ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildRunHref(filters, { page: runs.page + 1 })}>Next</Link>
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

function buildRunHref(filters: RunStatusPageFilters, overrides: Partial<RunStatusPageFilters>) {
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

  const query = params.toString();
  return query ? `/admin/runs?${query}` : "/admin/runs";
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
