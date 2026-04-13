"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import type {
  ReviewDecisionAction,
  ReviewEvidenceLink,
  ReviewModelExecution,
  ReviewTaskDetailResponse,
} from "@/lib/admin-api";
import { cn } from "@/lib/utils";

type ReviewDetailSurfaceProps = {
  detail: ReviewTaskDetailResponse;
  csrfToken: string | null | undefined;
};

const REASON_CODE_OPTIONS = [
  "low_confidence",
  "required_field_missing",
  "conflicting_evidence",
  "ambiguous_mapping",
  "validation_error",
  "manual_sampling_review",
  "partial_source_failure",
  "insufficient_context",
  "needs_domain_review",
  "policy_hold",
  "manual_override",
] as const;

export function ReviewDetailSurface({ detail, csrfToken }: ReviewDetailSurfaceProps) {
  const router = useRouter();
  const [reasonCode, setReasonCode] = useState(detail.review_task.queue_reason_code ?? "");
  const [reasonText, setReasonText] = useState("");
  const [overrideJson, setOverrideJson] = useState("{}");
  const [pendingAction, setPendingAction] = useState<ReviewDecisionAction | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFieldName, setSelectedFieldName] = useState<string | null>(
    detail.field_trace_groups.find((item) => item.has_evidence)?.field_name ?? detail.field_trace_groups[0]?.field_name ?? null,
  );

  const parsedOverride = useMemo(() => {
    try {
      const parsed = JSON.parse(overrideJson || "{}") as unknown;
      if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
        return { value: null, error: "Override JSON must be an object." };
      }
      return { value: parsed as Record<string, unknown>, error: null };
    } catch {
      return { value: null, error: "Override JSON is not valid." };
    }
  }, [overrideJson]);

  const diffPreview = useMemo(() => {
    if (!parsedOverride.value) {
      return [];
    }
    return Object.entries(parsedOverride.value)
      .filter(([fieldName, nextValue]) => detail.candidate.candidate_payload[fieldName] !== nextValue)
      .map(([fieldName, nextValue]) => ({
        fieldName,
        before: detail.candidate.candidate_payload[fieldName],
        after: nextValue,
      }));
  }, [detail.candidate.candidate_payload, parsedOverride.value]);

  const activeField = useMemo(() => {
    if (detail.field_trace_groups.length === 0) {
      return null;
    }
    return (
      detail.field_trace_groups.find((item) => item.field_name === selectedFieldName) ??
      detail.field_trace_groups.find((item) => item.has_evidence) ??
      detail.field_trace_groups[0]
    );
  }, [detail.field_trace_groups, selectedFieldName]);

  async function handleDecision(action: ReviewDecisionAction) {
    if (!detail.available_actions.includes(action)) {
      return;
    }

    setPendingAction(action);
    setError(null);
    setMessage(null);

    try {
      const response = await fetch(`/admin/reviews/${detail.review_task.review_task_id}/decision`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify({
          action_type: action,
          reason_code: reasonCode || null,
          reason_text: reasonText || null,
          override_payload: action === "edit_approve" ? parsedOverride.value ?? {} : {},
        }),
      });

      const payload = (await response.json()) as { error?: { message?: string } };
      if (!response.ok) {
        setError(payload.error?.message ?? "Review action failed.");
        return;
      }

      setMessage(actionLabel(action));
      router.refresh();
    } catch {
      setError("The review action could not be submitted. Check the admin API and try again.");
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <section className="grid gap-6">
      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="max-w-4xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Review detail</p>
            <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
              {detail.candidate.product_name}
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
              This surface now keeps field selection, trace drilldown, and review actions together so operators can
              verify evidence before making a decision.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <span className={cn("rounded-full px-3 py-1 text-xs font-medium", stateBadgeClasses(detail.review_task.review_state))}>
              {toTitleCase(detail.review_task.review_state)}
            </span>
            <span className={cn("rounded-full px-3 py-1 text-xs font-medium", validationBadgeClasses(detail.candidate.validation_status))}>
              {toTitleCase(detail.candidate.validation_status)}
            </span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              {detail.candidate.bank_name} {toTitleCase(detail.candidate.product_type)}
            </span>
          </div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-4">
          <SummaryStat label="Review task" value={detail.review_task.review_task_id} />
          <SummaryStat label="Run" value={detail.review_task.run_id} />
          <SummaryStat label="Confidence" value={formatConfidence(detail.candidate.source_confidence)} />
          <SummaryStat label="Evidence fields" value={String(detail.evidence_summary.field_count)} />
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <SummaryStat label="Created" value={formatTimestamp(detail.review_task.created_at)} />
          <SummaryStat label="Updated" value={formatTimestamp(detail.review_task.updated_at)} />
          <SummaryStat label="Fetched" value={formatTimestamp(detail.source_context.fetched_at)} />
          <SummaryStat label="Focused field" value={activeField?.label ?? "n/a"} />
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/admin/reviews">Back to queue</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href={`/admin/runs/${detail.review_task.run_id}`}>Open producing run</Link>
          </Button>
          {detail.current_product ? (
            <span className="inline-flex items-center rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              Canonical {detail.current_product.product_id} v{detail.current_product.current_version_no}
            </span>
          ) : (
            <span className="inline-flex items-center rounded-full bg-info-soft px-3 py-1 text-xs font-medium text-info">
              New canonical product on approval
            </span>
          )}
        </div>
      </article>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.18fr)_minmax(20rem,0.82fr)]">
        <div className="grid gap-6">
          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow="Candidate summary"
              title="Normalized fields with trace focus"
              description="Select a field to move the trace pane to the most relevant evidence links, mapping metadata, and model-run references."
            />
            <div className="mt-6 grid gap-3 md:grid-cols-2">
              {detail.field_trace_groups.map((item) => (
                <button
                  className={cn(
                    "rounded-2xl border px-4 py-3 text-left transition-colors",
                    item.field_name === activeField?.field_name
                      ? "border-primary/40 bg-primary/5 shadow-sm"
                      : "border-border/80 bg-background hover:border-primary/25 hover:bg-accent/35",
                  )}
                  key={item.field_name}
                  onClick={() => setSelectedFieldName(item.field_name)}
                  type="button"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">{item.label}</p>
                      <p className="mt-2 text-sm leading-6 text-foreground">{formatValue(item.value)}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <span
                        className={cn(
                          "rounded-full px-2.5 py-1 text-[11px] font-medium",
                          item.has_evidence ? "bg-success-soft text-success" : "bg-muted text-muted-foreground",
                        )}
                      >
                        {item.evidence_count} evidence
                      </span>
                      {item.mapping.normalization_method ? (
                        <span className="rounded-full bg-info-soft px-2.5 py-1 text-[11px] font-medium text-info">
                          {shortMethodLabel(item.mapping.normalization_method)}
                        </span>
                      ) : null}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow="Validation"
              title="Issue summary and source context"
              description="Current validation findings stay visible in the main pane while the trace pane concentrates on the selected field."
            />
            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              <div className="rounded-2xl border border-border/80 bg-background p-4">
                <p className="text-sm font-medium text-foreground">Issue summary</p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{detail.review_task.issue_summary}</p>
                <div className="mt-4 grid gap-2">
                  {detail.validation_issues.map((issue) => (
                    <div className="flex items-start gap-3 rounded-2xl border border-border/70 px-3 py-3" key={`${issue.code}-${issue.summary}`}>
                      <span className={cn("mt-0.5 rounded-full px-2.5 py-1 text-[11px] font-medium", issueBadgeClasses(issue.severity))}>
                        {toTitleCase(issue.severity)}
                      </span>
                      <div>
                        <p className="text-sm font-medium text-foreground">{issue.code ? toTitleCase(issue.code) : "Validation issue"}</p>
                        <p className="mt-1 text-sm leading-6 text-muted-foreground">{issue.summary}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border border-border/80 bg-background p-4">
                <p className="text-sm font-medium text-foreground">Source context</p>
                <dl className="mt-4 grid gap-3 text-sm">
                  <MetaRow label="Source ID" value={detail.source_context.source_id ?? "n/a"} />
                  <MetaRow label="Source type" value={detail.source_context.source_type ?? "n/a"} />
                  <MetaRow label="Snapshot" value={detail.source_context.snapshot_id ?? "n/a"} />
                  <MetaRow label="Parsed doc" value={detail.source_context.parsed_document_id ?? "n/a"} />
                  <MetaRow label="Fetched" value={formatTimestamp(detail.source_context.fetched_at)} />
                  <MetaRow label="Stage status" value={detail.source_context.stage_status ?? "n/a"} />
                </dl>
                {detail.source_context.parse_quality_note ? (
                  <p className="mt-4 rounded-2xl bg-muted px-3 py-3 text-sm leading-6 text-muted-foreground">
                    Parse note: {detail.source_context.parse_quality_note}
                  </p>
                ) : null}
                {detail.source_context.runtime_notes.length > 0 ? (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {detail.source_context.runtime_notes.map((note) => (
                      <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground" key={note}>
                        {note}
                      </span>
                    ))}
                  </div>
                ) : null}
                {detail.source_context.source_url ? (
                  <a
                    className="mt-4 inline-flex text-sm font-medium text-primary underline-offset-4 hover:underline"
                    href={detail.source_context.source_url}
                    rel="noreferrer"
                    target="_blank"
                  >
                    Open source URL
                  </a>
                ) : null}
              </div>
            </div>
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow="History"
              title="Decision history"
              description="Current queue state and append-only decision history stay separate so operators can see what changed without losing the present task status."
            />
            {detail.decision_history.length === 0 ? (
              <p className="mt-6 text-sm leading-6 text-muted-foreground">No review decisions have been recorded on this task yet.</p>
            ) : (
              <div className="mt-6 grid gap-3">
                {detail.decision_history.map((item) => (
                  <div className="rounded-2xl border border-border/80 bg-background p-4" key={item.review_decision_id}>
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <span className={cn("rounded-full px-2.5 py-1 text-xs font-medium", stateBadgeClasses(decisionActionState(item.action_type)))}>
                        {toTitleCase(item.action_type)}
                      </span>
                      <span className="text-xs text-muted-foreground">{formatTimestamp(item.decided_at)}</span>
                    </div>
                    <p className="mt-3 text-sm text-foreground">
                      {item.actor.display_name ?? item.actor.email ?? "Unknown reviewer"}
                    </p>
                    {item.diff_summary ? <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.diff_summary}</p> : null}
                    {item.reason_text ? <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.reason_text}</p> : null}
                  </div>
                ))}
              </div>
            )}
          </article>
        </div>

        <div className="grid gap-6">
          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow="Trace viewer"
              title={activeField ? `${activeField.label} trace` : "Field trace"}
              description="The trace pane prioritizes the selected normalized field and keeps evidence, mapping, and model context together without exposing private object paths."
            />

            {!activeField ? (
              <p className="mt-6 text-sm leading-6 text-muted-foreground">No field-level trace is available for this candidate yet.</p>
            ) : (
              <div className="mt-6 grid gap-4">
                <div className="rounded-2xl border border-border/80 bg-background p-4">
                  <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Selected field</p>
                  <p className="mt-2 text-sm font-medium text-foreground">{activeField.label}</p>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{formatValue(activeField.value)}</p>
                </div>

                <div className="rounded-2xl border border-border/80 bg-background p-4">
                  <p className="text-sm font-medium text-foreground">Parsed field mapping</p>
                  <dl className="mt-4 grid gap-3 text-sm">
                    <MetaRow label="Source field" value={activeField.mapping.source_field_name ?? "n/a"} />
                    <MetaRow label="Normalization" value={activeField.mapping.normalization_method ?? "n/a"} />
                    <MetaRow label="Extraction method" value={activeField.mapping.extraction_method ?? "n/a"} />
                    <MetaRow label="Value type" value={activeField.mapping.value_type ?? "n/a"} />
                    <MetaRow label="Extraction confidence" value={formatConfidence(activeField.mapping.extraction_confidence)} />
                    <MetaRow label="Mapped chunk" value={activeField.mapping.evidence_chunk_id ?? "n/a"} />
                  </dl>
                </div>

                <div className="rounded-2xl border border-border/80 bg-background p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm font-medium text-foreground">Evidence links</p>
                    <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                      {activeField.evidence_count} linked
                    </span>
                  </div>
                  {activeField.evidence_links.length === 0 ? (
                    <p className="mt-4 text-sm leading-6 text-muted-foreground">
                      No direct field evidence link was persisted for this field. Review can still continue with the wider task context.
                    </p>
                  ) : (
                    <div className="mt-4 grid gap-3">
                      {activeField.evidence_links.map((item) => (
                        <TraceEvidenceCard item={item} key={`${item.field_name}-${item.evidence_chunk_id}`} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow="Model runs"
              title="Relevant execution references"
              description="Extraction, normalization, and validation references stay visible here so the selected field trace can be tied back to the producing run stages."
            />
            {detail.model_executions.length === 0 ? (
              <p className="mt-6 text-sm leading-6 text-muted-foreground">No model execution references were available for this task.</p>
            ) : (
              <div className="mt-6 grid gap-3">
                {detail.model_executions.map((item) => (
                  <ModelExecutionCard item={item} key={item.model_execution_id} />
                ))}
              </div>
            )}
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow="Decision form"
              title="Approve, reject, defer, or edit"
              description="The action area stays beside the trace pane so operators can decide with the selected field evidence still in view."
            />

            {detail.available_actions.length === 0 ? (
              <p className="mt-6 text-sm leading-6 text-muted-foreground">
                This task is read-only from your current session or already closed.
              </p>
            ) : (
              <div className="mt-6 grid gap-4">
                <label className="grid gap-2 text-sm">
                  <span className="font-medium text-foreground">Reason code</span>
                  <select
                    className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                    onChange={(event) => setReasonCode(event.target.value)}
                    value={reasonCode}
                  >
                    <option value="">Optional</option>
                    {REASON_CODE_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {toTitleCase(option)}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="grid gap-2 text-sm">
                  <span className="font-medium text-foreground">Reviewer note</span>
                  <textarea
                    className="min-h-28 rounded-2xl border border-border bg-background px-3 py-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                    onChange={(event) => setReasonText(event.target.value)}
                    placeholder="Add a short decision note when context or operator judgment should be preserved."
                    value={reasonText}
                  />
                </label>

                <label className="grid gap-2 text-sm">
                  <span className="font-medium text-foreground">Edit approval override JSON</span>
                  <textarea
                    className="min-h-40 rounded-2xl border border-border bg-background px-3 py-3 font-mono text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                    onChange={(event) => setOverrideJson(event.target.value)}
                    placeholder='{"monthly_fee": 0, "notes": "Reviewer confirmed no monthly fee."}'
                    value={overrideJson}
                  />
                </label>

                {parsedOverride.error ? (
                  <div className="rounded-2xl border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">
                    {parsedOverride.error}
                  </div>
                ) : null}

                {message ? (
                  <div className="rounded-2xl border border-success/20 bg-success-soft px-4 py-3 text-sm text-success">
                    Submitted action: {message}
                  </div>
                ) : null}

                {error ? (
                  <div className="rounded-2xl border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">
                    {error}
                  </div>
                ) : null}

                <div className="grid gap-3 sm:grid-cols-2">
                  <Button disabled={Boolean(pendingAction)} onClick={() => handleDecision("approve")} type="button">
                    {pendingAction === "approve" ? "Approving..." : "Approve"}
                  </Button>
                  <Button disabled={Boolean(pendingAction)} onClick={() => handleDecision("reject")} type="button" variant="outline">
                    {pendingAction === "reject" ? "Rejecting..." : "Reject"}
                  </Button>
                  <Button
                    disabled={Boolean(pendingAction) || Boolean(parsedOverride.error) || diffPreview.length === 0}
                    onClick={() => handleDecision("edit_approve")}
                    type="button"
                    variant="outline"
                  >
                    {pendingAction === "edit_approve" ? "Submitting edit..." : "Edit & approve"}
                  </Button>
                  <Button disabled={Boolean(pendingAction)} onClick={() => handleDecision("defer")} type="button" variant="outline">
                    {pendingAction === "defer" ? "Deferring..." : "Defer"}
                  </Button>
                </div>
              </div>
            )}
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow="Override preview"
              title="Candidate-to-approved diff"
              description="Previewed changes are computed against the current normalized candidate payload before edit approval is submitted."
            />
            {diffPreview.length === 0 ? (
              <p className="mt-6 text-sm leading-6 text-muted-foreground">
                Add one or more changed fields in the override JSON object to preview an edited approval.
              </p>
            ) : (
              <div className="mt-6 grid gap-3">
                {diffPreview.map((item) => (
                  <div className="rounded-2xl border border-border/80 bg-background p-4" key={item.fieldName}>
                    <p className="text-sm font-medium text-foreground">{toTitleCase(item.fieldName)}</p>
                    <p className="mt-2 text-xs uppercase tracking-[0.14em] text-muted-foreground">Current</p>
                    <p className="mt-1 text-sm leading-6 text-muted-foreground">{formatValue(item.before)}</p>
                    <p className="mt-3 text-xs uppercase tracking-[0.14em] text-muted-foreground">Approved</p>
                    <p className="mt-1 text-sm leading-6 text-foreground">{formatValue(item.after)}</p>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <SectionHeading
              eyebrow="Canonical continuity"
              title="Current approved product snapshot"
              description="Approval reuses the existing canonical continuity record when a product match already exists, otherwise it creates a new one."
            />
            {detail.current_product ? (
              <div className="mt-6 rounded-2xl border border-border/80 bg-background p-4">
                <p className="text-sm font-medium text-foreground">{detail.current_product.product_name}</p>
                <dl className="mt-4 grid gap-3 text-sm">
                  <MetaRow label="Product ID" value={detail.current_product.product_id} />
                  <MetaRow label="Version" value={String(detail.current_product.current_version_no)} />
                  <MetaRow label="Status" value={detail.current_product.status} />
                  <MetaRow label="Last verified" value={formatTimestamp(detail.current_product.last_verified_at)} />
                </dl>
              </div>
            ) : (
              <p className="mt-6 text-sm leading-6 text-muted-foreground">
                No canonical product match is linked yet. A successful approval will create the first canonical record
                for this continuity in the current prototype baseline.
              </p>
            )}
          </article>
        </div>
      </div>
    </section>
  );
}

function TraceEvidenceCard({ item }: { item: ReviewEvidenceLink }) {
  return (
    <div className="rounded-2xl border border-border/70 px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-foreground">{item.label}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {item.source_id ?? item.source_document_id ?? "Unknown source"} · {item.anchor_label}
          </p>
        </div>
        <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
          {formatConfidence(item.citation_confidence)}
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">{item.evidence_excerpt ?? "No excerpt captured."}</p>
      <dl className="mt-4 grid gap-2 text-sm">
        <MetaRow label="Chunk" value={item.evidence_chunk_id} />
        <MetaRow label="Snapshot" value={item.source_snapshot_id ?? "n/a"} />
        <MetaRow label="Parsed doc" value={item.parsed_document_id ?? "n/a"} />
        <MetaRow label="Source type" value={item.source_type ?? "n/a"} />
        <MetaRow label="Model run" value={item.model_execution_id ?? "n/a"} />
      </dl>
      {item.source_url ? (
        <a
          className="mt-4 inline-flex text-sm font-medium text-primary underline-offset-4 hover:underline"
          href={item.source_url}
          rel="noreferrer"
          target="_blank"
        >
          Open source URL
        </a>
      ) : null}
    </div>
  );
}

function ModelExecutionCard({ item }: { item: ReviewModelExecution }) {
  const tokenSummary =
    item.usage.prompt_tokens !== null || item.usage.completion_tokens !== null
      ? `${item.usage.prompt_tokens ?? 0} / ${item.usage.completion_tokens ?? 0} tokens`
      : "n/a";

  return (
    <div className="rounded-2xl border border-border/80 bg-background p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-foreground">{item.stage_label}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {item.agent_name} · {item.model_id}
          </p>
        </div>
        <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
          {toTitleCase(item.execution_status)}
        </span>
      </div>
      <dl className="mt-4 grid gap-2 text-sm">
        <MetaRow label="Execution" value={item.model_execution_id} />
        <MetaRow label="Started" value={formatTimestamp(item.started_at)} />
        <MetaRow label="Completed" value={formatTimestamp(item.completed_at)} />
        <MetaRow label="Usage mode" value={item.usage.usage_mode ?? "n/a"} />
        <MetaRow label="Tokens" value={tokenSummary} />
        <MetaRow label="Cost" value={formatCost(item.usage.estimated_cost)} />
      </dl>
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

function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div>
      <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{eyebrow}</p>
      <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{description}</p>
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

function formatConfidence(value: number | null) {
  if (value === null) {
    return "n/a";
  }
  return `${Math.round(value * 100)}%`;
}

function formatCost(value: number | null) {
  if (value === null) {
    return "n/a";
  }
  return `$${value.toFixed(6)}`;
}

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

function toTitleCase(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function shortMethodLabel(value: string) {
  return value
    .replace(/^heuristic_/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function actionLabel(action: ReviewDecisionAction) {
  switch (action) {
    case "edit_approve":
      return "Edit & approve";
    default:
      return toTitleCase(action);
  }
}

function decisionActionState(actionType: string) {
  switch (actionType) {
    case "approve":
      return "approved";
    case "reject":
      return "rejected";
    case "edit_approve":
      return "edited";
    case "defer":
      return "deferred";
    default:
      return "queued";
  }
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
