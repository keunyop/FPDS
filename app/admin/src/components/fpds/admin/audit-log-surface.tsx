"use client";

import Link from "next/link";

import { Banner1 } from "@/components/banner1";
import { Stats5 } from "@/components/stats5";
import { Button } from "@/components/ui/button";
import type { AuditLogListResponse } from "@/lib/admin-api";
import { cn } from "@/lib/utils";

const CATEGORY_OPTIONS = ["review", "run", "publish", "auth", "config", "usage"] as const;
const ACTOR_TYPE_OPTIONS = ["user", "system", "service", "scheduler"] as const;

export type AuditLogPageFilters = {
  q: string;
  eventCategory: string;
  eventType: string;
  actorType: string;
  targetType: string;
  occurredFrom: string;
  occurredTo: string;
  sortBy: string;
  sortOrder: "asc" | "desc";
  page: number;
};

type AuditLogSurfaceProps = {
  auditLog: AuditLogListResponse;
  filters: AuditLogPageFilters;
};

export function AuditLogSurface({ auditLog, filters }: AuditLogSurfaceProps) {
  const categoryCounts = auditLog.summary.category_counts;
  const statItems = [
    {
      label: "Visible events",
      value: String(auditLog.summary.total_items),
      note: "The filtered audit set stays append-only and page oriented.",
      tone: "info" as const,
    },
    {
      label: "Review events",
      value: String(categoryCounts.review ?? 0),
      note: "Decision, defer, and trace-access history stay queryable in one route.",
      tone: "success" as const,
    },
    {
      label: "Auth events",
      value: String(categoryCounts.auth ?? 0),
      note: "Login success, failure, and logout activity stay visible beside workflow history.",
      tone: "warning" as const,
    },
    {
      label: "User actors",
      value: String(auditLog.summary.user_actor_items),
      note: "Human operator activity remains distinct from system and scheduler events.",
      tone: "neutral" as const,
    },
  ];

  return (
    <section className="grid gap-6">
      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Audit log</p>
            <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
              Append-only audit history now has its own protected route inside the FPDS admin shell.
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
              This surface keeps review, auth, run, publish, config, and usage audit events queryable without
              overloading change history. It is built for chronology, actor visibility, and drilldown back into the
              run or review routes that already own the underlying work.
            </p>
          </div>

          <div className="inline-flex items-center rounded-full bg-success-soft px-3 py-1 text-xs font-medium text-success">
            Live route
          </div>
        </div>

        <div className="mt-6">
          <Banner1
            defaultVisible={true}
            description="This baseline focuses on audit chronology, actor and target context, request metadata, and review or run drilldowns. Publish actions, usage analytics, and privilege-management screens remain separate follow-on surfaces."
            dismissible={false}
            title="Slice boundary"
            tone="info"
          />
        </div>
      </article>

      <Stats5
        className="bg-card/95"
        description="Audit metrics stay compact and operational. They summarize the current filtered event set instead of replacing the dedicated log."
        items={statItems}
        title="Filtered audit snapshot"
      />

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <div className="flex flex-col gap-4 border-b border-border/80 pb-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Filters and sort</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Chronology-first controls</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Search by audit id, event type, request id, actor, product, run, or review task. Exact event type and
              target type filters keep this route useful even before publish and usage flows widen.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button asChild size="sm" variant="outline">
              <Link href="/admin/audit">Latest events</Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href={buildAuditHref(filters, { eventCategory: "auth", page: 1 })}>Auth events</Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href={buildAuditHref(filters, { eventType: "evidence_trace_viewed", page: 1 })}>Trace views</Link>
            </Button>
          </div>
        </div>

        <form action="/admin/audit" className="mt-6 grid gap-5">
          <div className="grid gap-4 xl:grid-cols-[1.4fr_repeat(5,minmax(0,1fr))]">
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Search</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.q}
                name="q"
                placeholder="audit id, request id, actor, run, review task"
                type="search"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Category</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.eventCategory}
                name="event_category"
              >
                <option value="">All categories</option>
                {CATEGORY_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {toTitleCase(option)}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Event type</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.eventType}
                name="event_type"
                placeholder="review_task_edited"
                type="text"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Actor type</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.actorType}
                name="actor_type"
              >
                <option value="">All actors</option>
                {ACTOR_TYPE_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {toTitleCase(option)}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Target type</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.targetType}
                name="target_type"
                placeholder="review_task"
                type="text"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Sort by</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.sortBy}
                name="sort_by"
              >
                <option value="occurred_at">Occurred time</option>
                <option value="event_category">Category</option>
                <option value="event_type">Event type</option>
                <option value="target_type">Target type</option>
              </select>
            </label>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1fr_1fr_1fr_auto]">
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Occurred from</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.occurredFrom}
                name="occurred_from"
                type="date"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Occurred to</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.occurredTo}
                name="occurred_to"
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
                <Link href="/admin/audit">Reset</Link>
              </Button>
            </div>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="flex flex-col gap-3 border-b border-border/80 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Results</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Audit table</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Page {auditLog.page} of {Math.max(auditLog.total_pages, 1)} with {auditLog.total_items} matching audit
              {auditLog.total_items === 1 ? " event" : " events"}.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {filters.eventCategory ? (
              <span className={cn("rounded-full px-3 py-1 text-xs font-medium", categoryBadgeClasses(filters.eventCategory))}>
                {toTitleCase(filters.eventCategory)}
              </span>
            ) : null}
            {filters.actorType ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {toTitleCase(filters.actorType)}
              </span>
            ) : null}
            {filters.eventType ? (
              <span className="rounded-full bg-info-soft px-3 py-1 text-xs font-medium text-info">{filters.eventType}</span>
            ) : null}
            {filters.occurredFrom || filters.occurredTo ? (
              <span className="rounded-full bg-warning-soft px-3 py-1 text-xs font-medium text-warning">
                {filters.occurredFrom || "Start"} to {filters.occurredTo || "Now"}
              </span>
            ) : null}
          </div>
        </div>

        {auditLog.items.length === 0 ? (
          <div className="px-6 py-10">
            <div className="rounded-[1.5rem] border border-dashed border-border bg-background px-6 py-8">
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">No matching audit events</p>
              <h3 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
                The current filter set returned no append-only audit history.
              </h3>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
                Widen the time range, remove the category filter, or search more broadly. This route only shows
                persisted audit events, so future publish and usage history will appear here as those writer paths land.
              </p>
              <div className="mt-6">
                <Button asChild variant="outline">
                  <Link href="/admin/audit">Reset audit filters</Link>
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto px-6 py-5">
              <table className="min-w-[1640px] table-fixed border-separate border-spacing-0">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    <th className="border-b border-border px-3 py-3 font-medium">Event</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Actor</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Target</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Reason and diff</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Linked context</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Request</th>
                    <th className="border-b border-border px-3 py-3 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLog.items.map((item) => (
                    <tr className="align-top" key={item.audit_event_id}>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className={cn("inline-flex rounded-full px-2.5 py-1 text-xs font-medium", categoryBadgeClasses(item.event_category))}>
                              {toTitleCase(item.event_category)}
                            </span>
                            <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
                              {formatEventType(item.event_type)}
                            </span>
                          </div>
                          <p className="text-sm font-medium leading-6 text-foreground">{formatTimestamp(item.occurred_at)}</p>
                          <span className="text-xs text-muted-foreground">{item.audit_event_id}</span>
                        </div>
                      </td>

                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2 text-sm">
                          <span className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", actorTypeBadgeClasses(item.actor_type))}>
                            {toTitleCase(item.actor_type)}
                          </span>
                          <span className="font-medium text-foreground">
                            {item.actor.display_name ?? item.actor.email ?? item.actor.actor_id ?? "System actor"}
                          </span>
                          <span className="text-muted-foreground">
                            {item.actor.role_snapshot
                              ? `Role snapshot: ${item.actor.role_snapshot}`
                              : "No role snapshot stored."}
                          </span>
                        </div>
                      </td>

                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2 text-sm">
                          <span className="font-medium text-foreground">{item.target.display_name ?? item.target.target_id}</span>
                          <span className="text-muted-foreground">
                            {toTitleCase(item.target.target_type)} / {item.target.target_id}
                          </span>
                          {item.state_transition.previous_state || item.state_transition.new_state ? (
                            <span className="text-muted-foreground">
                              {item.state_transition.previous_state ?? "unknown"}
                              {" -> "}
                              {item.state_transition.new_state ?? "unknown"}
                            </span>
                          ) : (
                            <span className="text-muted-foreground">No state transition was stored for this event.</span>
                          )}
                        </div>
                      </td>

                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2 text-sm">
                          <span className="font-medium text-foreground">
                            {item.reason.reason_text ?? item.reason.reason_code ?? "No explicit reason was stored."}
                          </span>
                          <span className="text-muted-foreground">
                            {item.diff_summary ?? "No diff summary was stored for this event."}
                          </span>
                          {item.source_ref ? <span className="text-muted-foreground">Source ref: {item.source_ref}</span> : null}
                        </div>
                      </td>

                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2 text-sm">
                          <span className="font-medium text-foreground">
                            {item.related_context.product_name ?? item.related_context.bank_name ?? "No product context stored."}
                          </span>
                          <span className="text-muted-foreground">
                            {item.related_context.bank_name
                              ? `${item.related_context.bank_name}${item.related_context.bank_code ? ` (${item.related_context.bank_code})` : ""}`
                              : "No bank context stored."}
                          </span>
                          <span className="text-muted-foreground">
                            {item.related_context.review_task_id
                              ? `Review ${item.related_context.review_task_id}`
                              : item.related_context.run_id
                                ? `Run ${item.related_context.run_id}`
                                : "No linked run or review task."}
                          </span>
                        </div>
                      </td>

                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2 text-sm">
                          <span className="font-medium text-foreground">{item.request_context.request_id ?? "No request id stored."}</span>
                          <span className="text-muted-foreground">
                            {item.request_context.ip_address ?? "No IP stored."}
                          </span>
                          <span className="text-muted-foreground">
                            Retention {item.retention_class}
                          </span>
                        </div>
                      </td>

                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="flex flex-col gap-2">
                          {item.related_context.review_task_id ? (
                            <Button asChild size="sm" variant="outline">
                              <Link href={`/admin/reviews/${item.related_context.review_task_id}`}>Review detail</Link>
                            </Button>
                          ) : null}
                          {item.related_context.run_id ? (
                            <Button asChild size="sm" variant="outline">
                              <Link href={`/admin/runs/${item.related_context.run_id}`}>Run detail</Link>
                            </Button>
                          ) : null}
                          {!item.related_context.review_task_id && !item.related_context.run_id ? (
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
                Showing {(auditLog.page - 1) * auditLog.page_size + 1}-{Math.min(auditLog.page * auditLog.page_size, auditLog.total_items)} of{" "}
                {auditLog.total_items}
              </p>
              <div className="flex items-center gap-2">
                {auditLog.page > 1 ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildAuditHref(filters, { page: Math.max(1, auditLog.page - 1) })}>Previous</Link>
                  </Button>
                ) : (
                  <span className="inline-flex h-7 items-center rounded-[min(var(--radius-md),12px)] border border-border bg-muted px-2.5 text-[0.8rem] text-muted-foreground opacity-60">
                    Previous
                  </span>
                )}
                {auditLog.has_next_page ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildAuditHref(filters, { page: auditLog.page + 1 })}>Next</Link>
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

function buildAuditHref(filters: AuditLogPageFilters, overrides: Partial<AuditLogPageFilters>) {
  const next = {
    ...filters,
    ...overrides,
  };
  const params = new URLSearchParams();
  if (next.q) {
    params.set("q", next.q);
  }
  if (next.eventCategory) {
    params.set("event_category", next.eventCategory);
  }
  if (next.eventType) {
    params.set("event_type", next.eventType);
  }
  if (next.actorType) {
    params.set("actor_type", next.actorType);
  }
  if (next.targetType) {
    params.set("target_type", next.targetType);
  }
  if (next.occurredFrom) {
    params.set("occurred_from", next.occurredFrom);
  }
  if (next.occurredTo) {
    params.set("occurred_to", next.occurredTo);
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
  return query ? `/admin/audit?${query}` : "/admin/audit";
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

function formatEventType(value: string) {
  return toTitleCase(value);
}

function toTitleCase(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function categoryBadgeClasses(category: string) {
  switch (category) {
    case "review":
      return "bg-info-soft text-info";
    case "auth":
      return "bg-warning-soft text-warning";
    case "publish":
      return "bg-success-soft text-success";
    case "run":
      return "bg-muted text-foreground";
    case "config":
      return "bg-muted text-muted-foreground";
    case "usage":
      return "bg-primary/10 text-primary";
    default:
      return "bg-muted text-muted-foreground";
  }
}

function actorTypeBadgeClasses(actorType: string) {
  switch (actorType) {
    case "user":
      return "bg-info-soft text-info";
    case "system":
      return "bg-muted text-muted-foreground";
    case "service":
      return "bg-success-soft text-success";
    case "scheduler":
      return "bg-warning-soft text-warning";
    default:
      return "bg-muted text-muted-foreground";
  }
}
