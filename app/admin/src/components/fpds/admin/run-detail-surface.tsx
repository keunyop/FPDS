"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import type { RunRetryResponse, RunStatusDetailResponse } from "@/lib/admin-api";
import { cn } from "@/lib/utils";

type RunDetailSurfaceProps = {
  csrfToken: string | null | undefined;
  detail: RunStatusDetailResponse;
};

export function RunDetailSurface({ csrfToken, detail }: RunDetailSurfaceProps) {
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
        setRetryError(payload.error?.message ?? "Run retry could not be queued.");
        return;
      }
      setRetryMessage("Retry queued.");
      router.push(`/admin/runs/${payload.data.retry_run_id}`);
      router.refresh();
    } catch {
      setRetryError("Run retry could not be queued. Check the admin API and try again.");
    } finally {
      setRetryPending(false);
    }
  }

  return (
    <section className="grid gap-6">
      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="max-w-4xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Run detail</p>
            <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
              {detail.run.run_id}
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
              This surface explains run-level execution outcome, source processing impact, related review workload, and
              model usage without mixing run diagnosis into review or publish actions.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <span className={cn("rounded-full px-3 py-1 text-xs font-medium", runStateBadgeClasses(detail.run.run_status))}>
              {toTitleCase(detail.run.run_status)}
            </span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              {toTitleCase(detail.run.run_type)}
            </span>
            {detail.run.partial_completion_flag ? (
              <span className="rounded-full bg-warning-soft px-3 py-1 text-xs font-medium text-warning">Partial completion</span>
            ) : null}
          </div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-4">
          <SummaryStat label="Source items" value={String(detail.run.source_item_count)} />
          <SummaryStat label="Candidates" value={String(detail.run.candidate_count)} />
          <SummaryStat label="Review queued" value={String(detail.run.review_queued_count)} />
          <SummaryStat label="Correlation" value={detail.run.correlation_id ?? "n/a"} />
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <SummaryStat label="Started" value={formatTimestamp(detail.run.started_at)} />
          <SummaryStat label="Completed" value={formatTimestamp(detail.run.completed_at)} />
          <SummaryStat label="Trigger" value={toTitleCase(detail.run.trigger_type)} />
          <SummaryStat label="Actor" value={detail.run.triggered_by ?? "n/a"} />
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/admin/runs">Back to runs</Link>
          </Button>
          {detail.run.retry_action.available ? (
            <Button disabled={retryPending} onClick={handleRetry} type="button">
              {retryPending ? "Retrying..." : "Retry run"}
            </Button>
          ) : null}
          {detail.run.retry_of_run_id ? (
            <Button asChild variant="outline">
              <Link href={`/admin/runs/${detail.run.retry_of_run_id}`}>Previous attempt</Link>
            </Button>
          ) : null}
          {detail.run.retried_by_run_id ? (
            <Button asChild variant="outline">
              <Link href={`/admin/runs/${detail.run.retried_by_run_id}`}>Next attempt</Link>
            </Button>
          ) : null}
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
              eyebrow="Stage summary"
              title="Execution stage strip"
              description="Stage status stays compact at the top of run detail so operators can quickly see whether the run failed, completed cleanly, or completed in a degraded way."
            />
            <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {detail.stage_summaries.map((item) => (
                <div className="rounded-2xl border border-border/80 bg-background p-4" key={item.stage_name}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-foreground">{item.stage_label}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{item.execution_count} execution entries</p>
                    </div>
                    <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", stageStatusBadgeClasses(item.stage_status))}>
                      {toTitleCase(item.stage_status)}
                    </span>
                  </div>
                  <dl className="mt-4 grid gap-2 text-sm">
                    <MetaRow label="Success" value={String(item.success_count)} />
                    <MetaRow label="Failure" value={String(item.failure_count)} />
                    <MetaRow label="Started" value={formatTimestamp(item.started_at)} />
                    <MetaRow label="Completed" value={formatTimestamp(item.completed_at)} />
                  </dl>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow="Source processing"
              title="Per-source summary"
              description="Run detail keeps source processing summary separate from error events so impact scope and processing state remain easy to scan."
            />

            {detail.source_items.length === 0 ? (
              <p className="mt-6 text-sm leading-6 text-muted-foreground">No source-item rows were persisted for this run.</p>
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
                            {item.warning_count} warning
                          </span>
                        ) : null}
                        {item.error_count > 0 ? (
                          <span className="rounded-full bg-destructive/10 px-2.5 py-1 text-[11px] font-medium text-destructive">
                            {item.error_count} error
                          </span>
                        ) : null}
                      </div>
                    </div>

                    <dl className="mt-4 grid gap-2 text-sm">
                      <MetaRow label="Source doc" value={item.source_document_id} />
                      <MetaRow label="Snapshot" value={item.snapshot_id ?? "n/a"} />
                      <MetaRow label="Parsed doc" value={item.parsed_document_id ?? "n/a"} />
                      <MetaRow label="Fetched" value={formatTimestamp(item.fetched_at)} />
                    </dl>

                    {item.error_summary ? (
                      <p className="mt-4 rounded-2xl border border-destructive/15 bg-destructive/5 px-3 py-3 text-sm leading-6 text-destructive">
                        {item.error_summary}
                      </p>
                    ) : null}

                    {item.parse_quality_note ? (
                      <p className="mt-4 rounded-2xl bg-muted px-3 py-3 text-sm leading-6 text-muted-foreground">
                        Parse note: {item.parse_quality_note}
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
                        <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">Safe stage metadata</p>
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
                        Open source URL
                      </a>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow="Failure summary"
              title="Run and source issues"
              description="Error and degraded-event summaries stay together here so operators can explain what went wrong and how wide the impact was."
            />

            {detail.error_events.length === 0 ? (
              <p className="mt-6 text-sm leading-6 text-muted-foreground">No run-level or source-level issues were recorded for this run.</p>
            ) : (
              <div className="mt-6 grid gap-3">
                {detail.error_events.map((item, index) => (
                  <div className="rounded-2xl border border-border/80 bg-background p-4" key={`${item.scope}-${item.source_document_id ?? index}`}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium text-foreground">{item.scope === "run" ? "Run event" : item.source_id ?? item.source_document_id ?? "Source event"}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{item.stage_status ? toTitleCase(item.stage_status) : "Run summary"}</p>
                      </div>
                      <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", issueBadgeClasses(item.severity))}>
                        {toTitleCase(item.severity)}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-muted-foreground">{item.summary}</p>
                    <div className="mt-4 flex flex-wrap gap-2">
                      <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                        {item.warning_count} warning
                      </span>
                      <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                        {item.error_count} error
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
              eyebrow="Usage summary"
              title="Model and token usage"
              description="Usage stays readable from the same run context so operators can connect execution cost to the exact diagnostic surface."
            />
            <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-1">
              <SummaryStat label="Usage records" value={String(detail.usage_summary.usage_record_count)} />
              <SummaryStat label="Model executions" value={String(detail.usage_summary.model_execution_count)} />
              <SummaryStat label="Total tokens" value={detail.usage_summary.total_tokens.toLocaleString("en-CA")} />
              <SummaryStat label="Estimated cost" value={formatCost(detail.usage_summary.estimated_cost)} />
            </div>

            {detail.usage_summary.by_stage.length === 0 ? (
              <p className="mt-6 text-sm leading-6 text-muted-foreground">No usage records were linked to this run.</p>
            ) : (
              <div className="mt-6 grid gap-3">
                {detail.usage_summary.by_stage.map((item) => (
                  <div className="rounded-2xl border border-border/80 bg-background p-4" key={item.stage_name}>
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-medium text-foreground">{item.stage_label}</p>
                      <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                        {item.usage_record_count} records
                      </span>
                    </div>
                    <dl className="mt-4 grid gap-2 text-sm">
                      <MetaRow label="Prompt tokens" value={item.prompt_tokens.toLocaleString("en-CA")} />
                      <MetaRow label="Completion tokens" value={item.completion_tokens.toLocaleString("en-CA")} />
                      <MetaRow label="Total tokens" value={item.total_tokens.toLocaleString("en-CA")} />
                      <MetaRow label="Cost" value={formatCost(item.estimated_cost)} />
                    </dl>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow="Related review tasks"
              title="Review workload produced by this run"
              description="Run detail links directly to the queue items created from this run so operators can move from execution diagnosis into task-level evidence review."
            />

            {detail.related_review_tasks.length === 0 ? (
              <p className="mt-6 text-sm leading-6 text-muted-foreground">This run did not produce any related review tasks.</p>
            ) : (
              <div className="mt-6 grid gap-3">
                {detail.related_review_tasks.map((item) => (
                  <div className="rounded-2xl border border-border/80 bg-background p-4" key={item.review_task_id}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <Link className="text-sm font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" href={`/admin/reviews/${item.review_task_id}`}>
                          {item.review_task_id}
                        </Link>
                        <p className="mt-1 text-sm leading-6 text-muted-foreground">{item.product_name}</p>
                      </div>
                      <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", reviewStateBadgeClasses(item.review_state))}>
                        {toTitleCase(item.review_state)}
                      </span>
                    </div>
                    <dl className="mt-4 grid gap-2 text-sm">
                      <MetaRow label="Candidate" value={item.candidate_id} />
                      <MetaRow label="Bank" value={item.bank_name} />
                      <MetaRow label="Validation" value={toTitleCase(item.validation_status)} />
                      <MetaRow label="Created" value={formatTimestamp(item.created_at)} />
                    </dl>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow="Run context"
              title="Retry and scope summary"
              description="Core identifiers and retry linkage stay compact on the side so the main pane remains focused on diagnosis."
            />
            <div className="mt-6 rounded-2xl border border-border/80 bg-background p-4">
              <dl className="grid gap-3 text-sm">
                <MetaRow label="Pipeline stage" value={detail.run.pipeline_stage ?? "n/a"} />
                <MetaRow label="Request ID" value={detail.run.request_id ?? "n/a"} />
                <MetaRow label="Retry of" value={detail.run.retry_of_run_id ?? "n/a"} />
                <MetaRow label="Retried by" value={detail.run.retried_by_run_id ?? "n/a"} />
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

function formatTimestamp(value: string | null) {
  if (!value) {
    return "n/a";
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
