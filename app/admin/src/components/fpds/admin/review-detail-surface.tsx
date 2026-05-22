"use client";

import Link from "next/link";
import { useMemo, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Bot, Check, CirclePause, ExternalLink, Loader2, PencilLine, X } from "lucide-react";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type {
  ReviewDecisionAction,
  ReviewEvidenceLink,
  ReviewFieldTraceGroup,
  ReviewModelExecution,
  ReviewTaskDetailResponse,
} from "@/lib/admin-api";
import { formatAdminDateTimeValue } from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

type ReviewDetailSurfaceProps = {
  detail: ReviewTaskDetailResponse;
  csrfToken: string | null | undefined;
};

type Recommendation = {
  action: "approve" | "reject" | "defer";
  title: string;
  tone: "success" | "warning" | "destructive";
  reasonCode: string;
  reasons: string[];
};

type ExtraOverride = {
  id: string;
  fieldName: string;
  value: string;
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

const COMMON_EDITABLE_FIELDS = [
  "product_name",
  "description_short",
  "source_subtype_label",
  "subtype_code",
  "status",
  "currency",
  "public_display_rate",
  "standard_rate",
  "base_12_month_rate",
  "promotional_rate",
  "public_display_fee",
  "monthly_fee",
  "minimum_balance",
  "minimum_deposit",
  "term_length_text",
  "term_length_days",
  "term_options",
  "cashability",
  "redeemable_flag",
  "non_redeemable_flag",
  "payout_option",
  "compounding_frequency",
  "interest_payment_options",
  "eligibility_text",
  "application_method",
  "post_maturity_interest_rate",
  "tax_benefits",
  "deposit_insurance",
  "term_rate_table",
  "fee_waiver_condition",
  "target_customer_tags",
  "registered_plan_supported",
  "unlimited_transactions_flag",
  "notes",
];

const READ_ONLY_FIELDS = new Set([
  "bank_name",
  "bank_code",
  "country_code",
  "product_family",
  "product_type",
  "source_language",
  "last_verified_at",
  "effective_date",
]);

export function ReviewDetailSurface({ detail, csrfToken }: ReviewDetailSurfaceProps) {
  const router = useRouter();
  const sourceDerivedProductName = resolveCandidateProductName(detail);
  const approvedDisplayProductName = resolveApprovedDisplayProductName(detail);
  const showingApprovedName = approvedDisplayProductName !== sourceDerivedProductName;
  const recommendation = useMemo(() => buildRecommendation(detail), [detail]);
  const [reasonCode, setReasonCode] = useState(detail.review_task.queue_reason_code || recommendation.reasonCode);
  const [reasonText, setReasonText] = useState("");
  const [editableValues, setEditableValues] = useState(() => buildInitialEditableValues(detail, sourceDerivedProductName));
  const [extraFieldName, setExtraFieldName] = useState("");
  const [extraFieldValue, setExtraFieldValue] = useState("");
  const [extraOverrides, setExtraOverrides] = useState<ExtraOverride[]>([]);
  const [pendingAction, setPendingAction] = useState<ReviewDecisionAction | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFieldName, setSelectedFieldName] = useState<string | null>(
    detail.field_trace_groups.find((item) => item.has_evidence)?.field_name ?? detail.field_trace_groups[0]?.field_name ?? null,
  );

  const fieldOptionNames = useMemo(() => {
    const names = new Set([...COMMON_EDITABLE_FIELDS, ...detail.field_trace_groups.map((item) => item.field_name)]);
    return Array.from(names).sort();
  }, [detail.field_trace_groups]);

  const productNameError = useMemo(() => {
    const reviewedProductName = editableValues.product_name ?? sourceDerivedProductName;
    return reviewedProductName.trim().length > 0 ? null : "Reviewed product name cannot be empty.";
  }, [editableValues.product_name, sourceDerivedProductName]);

  const approvalOverridePayload = useMemo(() => {
    if (productNameError) {
      return null;
    }

    const payload: Record<string, unknown> = {};
    for (const [fieldName, rawValue] of Object.entries(editableValues)) {
      if (!isReviewEditableField(fieldName)) {
        continue;
      }
      const originalValue = originalValueForField(detail, fieldName, sourceDerivedProductName);
      const parsedValue = parseReviewedValue(rawValue, originalValue);
      if (!reviewValuesEqual(parsedValue, originalValue)) {
        payload[fieldName] = parsedValue;
      }
    }

    for (const item of extraOverrides) {
      const fieldName = item.fieldName.trim();
      if (!fieldName || !isReviewEditableField(fieldName)) {
        continue;
      }
      const parsedValue = parseManualValue(item.value);
      const originalValue = originalValueForField(detail, fieldName, sourceDerivedProductName);
      if (!reviewValuesEqual(parsedValue, originalValue)) {
        payload[fieldName] = parsedValue;
      }
    }

    return payload;
  }, [detail, editableValues, extraOverrides, productNameError, sourceDerivedProductName]);

  const diffPreview = useMemo(() => {
    if (!approvalOverridePayload) {
      return [];
    }
    return Object.entries(approvalOverridePayload).map(([fieldName, nextValue]) => ({
      fieldName,
      before: originalValueForField(detail, fieldName, sourceDerivedProductName),
      after: nextValue,
    }));
  }, [approvalOverridePayload, detail, sourceDerivedProductName]);

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

  const decisionDisabled = Boolean(pendingAction);
  const editApproveDisabled =
    decisionDisabled ||
    !detail.available_actions.includes("edit_approve") ||
    Boolean(productNameError) ||
    diffPreview.length === 0;

  function updateEditableField(fieldName: string, value: string) {
    setError(null);
    setEditableValues((current) => ({ ...current, [fieldName]: value }));
  }

  function addExtraOverride() {
    const fieldName = extraFieldName.trim();
    if (!fieldName || !isReviewEditableField(fieldName)) {
      setError("Choose an editable field name before adding a correction.");
      return;
    }
    setExtraOverrides((current) => [
      ...current.filter((item) => item.fieldName !== fieldName),
      { id: `${fieldName}-${current.length}-${Date.now()}`, fieldName, value: extraFieldValue },
    ]);
    setExtraFieldName("");
    setExtraFieldValue("");
    setError(null);
  }

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
          reason_code: reasonCode || defaultReasonCodeForAction(action, recommendation, detail),
          reason_text: reasonText || null,
          override_payload: action === "edit_approve" ? approvalOverridePayload ?? {} : {},
        }),
      });

      const payload = (await response.json()) as { error?: { message?: string } };
      if (!response.ok) {
        setError(payload.error?.message ?? "Review action failed.");
        return;
      }

      setMessage(actionLabel(action));
      if (action === "defer" || action === "reject") {
        router.replace("/admin/reviews");
        return;
      }
      router.refresh();
    } catch {
      setError("The review action could not be submitted. Check the admin API and try again.");
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <section className="grid gap-6">
      <AdminPageHeader
        actions={
          <>
            <Button asChild variant="outline">
              <Link href="/admin/reviews">Back to queue</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href={`/admin/runs/${detail.review_task.run_id}`}>Open run</Link>
            </Button>
          </>
        }
        badges={
          <>
            <span className={cn("rounded-full px-3 py-1 text-xs font-medium", stateBadgeClasses(detail.review_task.review_state))}>
              {toTitleCase(detail.review_task.review_state)}
            </span>
            <span className={cn("rounded-full px-3 py-1 text-xs font-medium", validationBadgeClasses(detail.candidate.validation_status))}>
              {formatValidationStatusLabel(detail.candidate.validation_status)}
            </span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              {detail.candidate.bank_name} {toTitleCase(detail.candidate.product_type)}
            </span>
          </>
        }
        description={showingApprovedName ? `Source candidate name: ${sourceDerivedProductName}` : undefined}
        path={["Review", "Review Queue", "Review Detail"]}
        title={approvedDisplayProductName}
      />

      <div className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr_0.9fr]">
        <DecisionRecommendationCard recommendation={recommendation} />
        <SourceDecisionCard detail={detail} />
        <IssueDecisionCard detail={detail} />
      </div>

      <ReviewDataCoverageCard detail={detail} />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_25rem]">
        <article className="min-w-0 rounded-lg border border-border/80 bg-card/95 p-5 shadow-sm">
          <SectionHeading eyebrow="Review fields" title="Agent values and reviewer corrections" />
          <div className="mt-5 grid gap-3">
            {detail.field_trace_groups.map((item) => (
              <FieldReviewRow
                editableValue={editableValues[item.field_name] ?? valueToEditableString(item.value)}
                item={item}
                key={item.field_name}
                onSelectTrace={() => setSelectedFieldName(item.field_name)}
                onValueChange={(value) => updateEditableField(item.field_name, value)}
                selected={item.field_name === activeField?.field_name}
              />
            ))}
          </div>

          <div className="mt-5 rounded-lg border border-dashed border-border bg-background p-4">
            <p className="text-sm font-medium text-foreground">Add missing field</p>
            <div className="mt-3 grid gap-3 md:grid-cols-[minmax(0,0.7fr)_minmax(0,1fr)_auto]">
              <label className="grid gap-2 text-sm">
                <span className="text-muted-foreground">Field</span>
                <Input
                  className="h-10 rounded-lg bg-background"
                  list="review-editable-field-options"
                  onChange={(event) => setExtraFieldName(event.target.value)}
                  placeholder="standard_rate"
                  value={extraFieldName}
                />
              </label>
              <label className="grid gap-2 text-sm">
                <span className="text-muted-foreground">Reviewed value</span>
                <Input
                  className="h-10 rounded-lg bg-background"
                  onChange={(event) => setExtraFieldValue(event.target.value)}
                  placeholder="2.75"
                  value={extraFieldValue}
                />
              </label>
              <div className="flex items-end">
                <Button onClick={addExtraOverride} type="button" variant="outline">
                  <PencilLine />
                  Add
                </Button>
              </div>
              <datalist id="review-editable-field-options">
                {fieldOptionNames.map((fieldName) => (
                  <option key={fieldName} value={fieldName} />
                ))}
              </datalist>
            </div>
            {extraOverrides.length > 0 ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {extraOverrides.map((item) => (
                  <button
                    className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                    key={item.id}
                    onClick={() => setExtraOverrides((current) => current.filter((candidate) => candidate.id !== item.id))}
                    type="button"
                  >
                    {item.fieldName}: {item.value}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </article>

        <aside className="grid content-start gap-4">
          <article className="rounded-lg border border-border/80 bg-card/95 p-5 shadow-sm">
            <SectionHeading eyebrow="Decision" title="Submit review action" />

            {detail.available_actions.length === 0 ? (
              <p className="mt-5 text-sm leading-6 text-muted-foreground">
                This task is read-only from your current session or already closed.
              </p>
            ) : (
              <div className="mt-5 grid gap-4">
                <label className="grid gap-2 text-sm">
                  <span className="font-medium text-foreground">Reason code</span>
                  <select
                    className="h-10 rounded-lg border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
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
                  <Textarea
                    className="min-h-24 rounded-lg bg-background"
                    onChange={(event) => setReasonText(event.target.value)}
                    placeholder="Short note for audit history."
                    value={reasonText}
                  />
                </label>

                {productNameError ? (
                  <StatusMessage tone="destructive">{productNameError}</StatusMessage>
                ) : null}
                {message ? <StatusMessage tone="success">Submitted action: {message}</StatusMessage> : null}
                {error ? <StatusMessage tone="destructive">{error}</StatusMessage> : null}

                <div className="grid gap-2">
                  <Button
                    disabled={decisionDisabled || !detail.available_actions.includes("approve")}
                    onClick={() => handleDecision("approve")}
                    type="button"
                  >
                    {pendingAction === "approve" ? <Loader2 className="animate-spin" /> : <Check />}
                    {pendingAction === "approve" ? "Approving..." : "Approve"}
                  </Button>
                  <Button
                    disabled={decisionDisabled || !detail.available_actions.includes("defer")}
                    onClick={() => handleDecision("defer")}
                    type="button"
                    variant="outline"
                  >
                    {pendingAction === "defer" ? <Loader2 className="animate-spin" /> : <CirclePause />}
                    {pendingAction === "defer" ? "Deferring..." : "Defer"}
                  </Button>
                  <Button disabled={editApproveDisabled} onClick={() => handleDecision("edit_approve")} type="button" variant="outline">
                    {pendingAction === "edit_approve" ? <Loader2 className="animate-spin" /> : <PencilLine />}
                    {pendingAction === "edit_approve" ? "Submitting edit..." : "Edit & approve"}
                  </Button>
                  <Button
                    disabled={decisionDisabled || !detail.available_actions.includes("reject")}
                    onClick={() => handleDecision("reject")}
                    type="button"
                    variant="destructive"
                  >
                    {pendingAction === "reject" ? <Loader2 className="animate-spin" /> : <X />}
                    {pendingAction === "reject" ? "Rejecting..." : "Reject"}
                  </Button>
                </div>
              </div>
            )}
          </article>

          <article className="rounded-lg border border-border/80 bg-card/95 p-5 shadow-sm">
            <SectionHeading eyebrow="Edited approval" title="Diff preview" />
            {diffPreview.length === 0 ? (
              <p className="mt-5 text-sm leading-6 text-muted-foreground">No reviewed values differ from the agent values.</p>
            ) : (
              <div className="mt-5 grid gap-3">
                {diffPreview.map((item) => (
                  <div className="rounded-lg border border-border/80 bg-background p-3" key={item.fieldName}>
                    <p className="text-sm font-medium text-foreground">{toTitleCase(item.fieldName)}</p>
                    <p className="mt-2 text-xs text-muted-foreground">Agent value</p>
                    <p className="mt-1 break-words text-sm leading-6 text-muted-foreground">{formatValue(item.before)}</p>
                    <p className="mt-3 text-xs text-muted-foreground">Reviewed value</p>
                    <p className="mt-1 break-words text-sm leading-6 text-foreground">{formatValue(item.after)}</p>
                  </div>
                ))}
              </div>
            )}
          </article>
        </aside>
      </div>

      <EvidenceTracePanel activeField={activeField} detail={detail} onSelectField={setSelectedFieldName} />
      <AuditContextPanel detail={detail} />
    </section>
  );
}

function ReviewDataCoverageCard({ detail }: { detail: ReviewTaskDetailResponse }) {
  const payload = detail.candidate.candidate_payload;
  const rows = buildReviewCoverageRows(payload);

  return (
    <article className="rounded-lg border border-border/80 bg-card/95 p-5 shadow-sm">
      <SectionHeading eyebrow="Collection coverage" title="Deposit fields for review" />
      <dl className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {rows.map((row) => (
          <div className="min-w-0 rounded-lg border border-border/80 bg-background p-3" key={row.label}>
            <dt className="text-xs font-medium text-muted-foreground">{row.label}</dt>
            <dd className="mt-1 break-words text-sm font-medium leading-6 text-foreground">{row.value}</dd>
          </div>
        ))}
      </dl>
    </article>
  );
}

function buildReviewCoverageRows(payload: Record<string, unknown>) {
  const depositAmount = payload.minimum_deposit ?? payload.minimum_balance;
  return [
    { label: "Product name", value: formatValue(payload.product_name) },
    { label: "Highest rate", value: formatRateValue(payload.public_display_rate) },
    { label: "Base rate (12M)", value: formatRateValue(payload.base_12_month_rate ?? payload.standard_rate) },
    { label: "Customer tags", value: formatValue(payload.target_customer_tags) },
    { label: "Deposit amount", value: formatValue(depositAmount) },
    { label: "Eligibility", value: formatValue(payload.eligibility_text) },
    { label: "Application method", value: formatValue(payload.application_method) },
    { label: "Post-maturity rate", value: formatValue(payload.post_maturity_interest_rate) },
    { label: "Tax benefits", value: formatValue(payload.tax_benefits) },
    { label: "Deposit insurance", value: formatValue(payload.deposit_insurance) },
    { label: "Rates by term", value: formatTermRateTableSummary(payload.term_rate_table) },
  ];
}

function formatRateValue(value: unknown) {
  if (typeof value === "number") {
    return `${value.toFixed(2).replace(/\.?0+$/, "")}%`;
  }
  return formatValue(value);
}

function formatTermRateTableSummary(value: unknown) {
  if (!Array.isArray(value) || value.length === 0) {
    return "n/a";
  }
  return `${value.length} row${value.length === 1 ? "" : "s"} captured`;
}

function DecisionRecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  return (
    <article className={cn("rounded-lg border p-5 shadow-sm", recommendationCardClasses(recommendation.tone))}>
      <div className="flex items-start gap-3">
        <span className="mt-0.5 rounded-lg bg-background/80 p-2">
          <Bot className="h-4 w-4" />
        </span>
        <div className="min-w-0">
          <p className="text-sm font-medium uppercase tracking-[0.16em]">Agent recommendation</p>
          <h2 className="mt-2 text-xl font-semibold tracking-tight">{recommendation.title}</h2>
        </div>
      </div>
      <ul className="mt-4 grid gap-2 text-sm leading-6">
        {recommendation.reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
    </article>
  );
}

function SourceDecisionCard({ detail }: { detail: ReviewTaskDetailResponse }) {
  return (
    <article className="rounded-lg border border-border/80 bg-card/95 p-5 shadow-sm">
      <p className="text-sm font-medium uppercase tracking-[0.16em] text-muted-foreground">Decision facts</p>
      <dl className="mt-4 grid gap-3 text-sm">
        <MetaRow label="Product" value={detail.candidate.product_name} />
        <MetaRow label="Bank" value={`${detail.candidate.bank_name} (${detail.candidate.bank_code})`} />
        <MetaRow label="Type" value={toTitleCase(detail.candidate.product_type)} />
        <MetaRow label="Confidence" value={formatConfidence(detail.candidate.source_confidence)} />
        <MetaRow label="Evidence fields" value={`${detail.evidence_summary.field_count} fields / ${detail.evidence_summary.item_count} links`} />
      </dl>
      {detail.source_context.source_url ? (
        <Button asChild className="mt-4 w-full justify-center" variant="outline">
          <a href={detail.source_context.source_url} rel="noreferrer" target="_blank">
            <ExternalLink />
            Open origin source
          </a>
        </Button>
      ) : null}
    </article>
  );
}

function IssueDecisionCard({ detail }: { detail: ReviewTaskDetailResponse }) {
  const issues = detail.validation_issues.slice(0, 3);
  return (
    <article className="rounded-lg border border-border/80 bg-card/95 p-5 shadow-sm">
      <p className="text-sm font-medium uppercase tracking-[0.16em] text-muted-foreground">Check before deciding</p>
      <p className="mt-3 text-sm leading-6 text-foreground">{detail.review_task.issue_summary}</p>
      {issues.length > 0 ? (
        <div className="mt-4 grid gap-2">
          {issues.map((issue) => (
            <div className="flex items-center gap-2 text-sm" key={`${issue.code}-${issue.summary}`}>
              <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", issueBadgeClasses(issue.severity))}>
                {issue.code || issue.severity}
              </span>
              <span className="min-w-0 text-muted-foreground">{issue.summary}</span>
            </div>
          ))}
        </div>
      ) : null}
    </article>
  );
}

function FieldReviewRow({
  item,
  editableValue,
  selected,
  onValueChange,
  onSelectTrace,
}: {
  item: ReviewFieldTraceGroup;
  editableValue: string;
  selected: boolean;
  onValueChange: (value: string) => void;
  onSelectTrace: () => void;
}) {
  const editable = isReviewEditableField(item.field_name);
  const useTextarea = shouldUseTextarea(item.value, editableValue);
  return (
    <div className={cn("grid gap-3 rounded-lg border bg-background p-4", selected ? "border-primary/45" : "border-border/80")}>
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <p className="text-sm font-medium text-foreground">{item.label}</p>
          <p className="mt-1 break-words text-sm leading-6 text-muted-foreground">Agent value: {formatValue(item.value)}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", item.has_evidence ? "bg-success-soft text-success" : "bg-muted text-muted-foreground")}>
            {item.evidence_count} evidence
          </span>
          {editable ? (
            <span className="rounded-full bg-info-soft px-2.5 py-1 text-[11px] font-medium text-info">Editable</span>
          ) : (
            <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">Read only</span>
          )}
        </div>
      </div>

      {editable ? (
        <label className="grid gap-2 text-sm">
          <span className="text-muted-foreground">Reviewed value</span>
          {useTextarea ? (
            <Textarea className="min-h-24 rounded-lg" onChange={(event) => onValueChange(event.target.value)} value={editableValue} />
          ) : (
            <Input className="h-10 rounded-lg bg-background" onChange={(event) => onValueChange(event.target.value)} value={editableValue} />
          )}
        </label>
      ) : null}

      <div>
        <Button onClick={onSelectTrace} size="sm" type="button" variant="outline">
          Evidence
        </Button>
      </div>
    </div>
  );
}

function EvidenceTracePanel({
  detail,
  activeField,
  onSelectField,
}: {
  detail: ReviewTaskDetailResponse;
  activeField: ReviewFieldTraceGroup | null;
  onSelectField: (fieldName: string) => void;
}) {
  return (
    <details className="rounded-lg border border-border/80 bg-card/95 shadow-sm">
      <summary className="cursor-pointer px-5 py-4 text-sm font-medium text-foreground">Evidence trace and source context</summary>
      <div className="grid gap-5 border-t border-border/80 p-5 lg:grid-cols-[16rem_minmax(0,1fr)]">
        <div className="grid content-start gap-2">
          {detail.field_trace_groups.map((item) => (
            <button
              className={cn(
                "rounded-lg border px-3 py-2 text-left text-sm",
                item.field_name === activeField?.field_name ? "border-primary/45 bg-primary/5" : "border-border/80 bg-background hover:border-primary/30",
              )}
              key={item.field_name}
              onClick={() => onSelectField(item.field_name)}
              type="button"
            >
              <span className="font-medium text-foreground">{item.label}</span>
              <span className="mt-1 block text-xs text-muted-foreground">{item.evidence_count} evidence</span>
            </button>
          ))}
        </div>

        {!activeField ? (
          <p className="text-sm leading-6 text-muted-foreground">No field-level trace is available for this candidate.</p>
        ) : (
          <div className="grid gap-4">
            <div>
              <p className="text-sm font-medium text-foreground">{activeField.label}</p>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{formatValue(activeField.value)}</p>
            </div>
            <dl className="grid gap-2 text-sm md:grid-cols-2">
              <MetaRow label="Source field" value={activeField.mapping.source_field_name ?? "n/a"} />
              <MetaRow label="Normalization" value={activeField.mapping.normalization_method ?? "n/a"} />
              <MetaRow label="Extraction" value={activeField.mapping.extraction_method ?? "n/a"} />
              <MetaRow label="Confidence" value={formatConfidence(activeField.mapping.extraction_confidence)} />
            </dl>
            {activeField.evidence_links.length === 0 ? (
              <p className="text-sm leading-6 text-muted-foreground">No direct evidence link was persisted for this field.</p>
            ) : (
              <div className="grid gap-3">
                {activeField.evidence_links.map((item) => (
                  <TraceEvidenceCard item={item} key={`${item.field_name}-${item.evidence_chunk_id}`} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </details>
  );
}

function AuditContextPanel({ detail }: { detail: ReviewTaskDetailResponse }) {
  return (
    <details className="rounded-lg border border-border/80 bg-card/95 shadow-sm">
      <summary className="cursor-pointer px-5 py-4 text-sm font-medium text-foreground">History, model runs, and canonical context</summary>
      <div className="grid gap-5 border-t border-border/80 p-5 lg:grid-cols-3">
        <div>
          <p className="text-sm font-medium text-foreground">Decision history</p>
          {detail.decision_history.length === 0 ? (
            <p className="mt-3 text-sm leading-6 text-muted-foreground">No review decisions recorded.</p>
          ) : (
            <div className="mt-3 grid gap-3">
              {detail.decision_history.map((item) => (
                <div className="rounded-lg border border-border/80 bg-background p-3" key={item.review_decision_id}>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <span className={cn("rounded-full px-2.5 py-1 text-xs font-medium", stateBadgeClasses(decisionActionState(item.action_type)))}>
                      {toTitleCase(item.action_type)}
                    </span>
                    <span className="text-xs text-muted-foreground">{formatTimestamp(item.decided_at)}</span>
                  </div>
                  <p className="mt-2 text-sm text-foreground">{item.actor.display_name ?? item.actor.email ?? "Unknown reviewer"}</p>
                  {item.diff_summary ? <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.diff_summary}</p> : null}
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <p className="text-sm font-medium text-foreground">Model runs</p>
          {detail.model_executions.length === 0 ? (
            <p className="mt-3 text-sm leading-6 text-muted-foreground">No model execution references are available.</p>
          ) : (
            <div className="mt-3 grid gap-3">
              {detail.model_executions.map((item) => (
                <ModelExecutionCard item={item} key={item.model_execution_id} />
              ))}
            </div>
          )}
        </div>

        <div>
          <p className="text-sm font-medium text-foreground">Canonical context</p>
          {detail.current_product ? (
            <dl className="mt-3 grid gap-3 text-sm">
              <MetaRow label="Product" value={detail.current_product.product_name} />
              <MetaRow label="Product ID" value={detail.current_product.product_id} />
              <MetaRow label="Version" value={String(detail.current_product.current_version_no)} />
              <MetaRow label="Status" value={detail.current_product.status} />
              <MetaRow label="Last verified" value={formatTimestamp(detail.current_product.last_verified_at)} />
            </dl>
          ) : (
            <p className="mt-3 text-sm leading-6 text-muted-foreground">Approval will create the first canonical record for this product.</p>
          )}
        </div>
      </div>
    </details>
  );
}

function TraceEvidenceCard({ item }: { item: ReviewEvidenceLink }) {
  return (
    <div className="rounded-lg border border-border/80 bg-background p-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-foreground">{item.label}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {item.source_id ?? item.source_document_id ?? "Unknown source"} - {item.anchor_label}
          </p>
        </div>
        <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
          {formatConfidence(item.citation_confidence)}
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">{item.evidence_excerpt ?? "No excerpt captured."}</p>
      {item.source_url ? (
        <a
          className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-primary underline-offset-4 hover:underline"
          href={item.source_url}
          rel="noreferrer"
          target="_blank"
        >
          <ExternalLink className="h-4 w-4" />
          Origin source
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
    <div className="rounded-lg border border-border/80 bg-background p-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-foreground">{item.stage_label}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {item.agent_name} - {item.model_id}
          </p>
        </div>
        <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
          {toTitleCase(item.execution_status)}
        </span>
      </div>
      <dl className="mt-3 grid gap-2 text-sm">
        <MetaRow label="Started" value={formatTimestamp(item.started_at)} />
        <MetaRow label="Completed" value={formatTimestamp(item.completed_at)} />
        <MetaRow label="Tokens" value={tokenSummary} />
        <MetaRow label="Cost" value={formatCost(item.usage.estimated_cost)} />
      </dl>
    </div>
  );
}

function SectionHeading({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div>
      <p className="text-sm font-medium uppercase tracking-[0.16em] text-muted-foreground">{eyebrow}</p>
      <h2 className="mt-2 text-xl font-semibold tracking-tight text-foreground">{title}</h2>
    </div>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex min-w-0 items-start justify-between gap-4">
      <dt className="shrink-0 text-muted-foreground">{label}</dt>
      <dd className="min-w-0 break-words text-right text-foreground">{value}</dd>
    </div>
  );
}

function StatusMessage({ tone, children }: { tone: "success" | "destructive"; children: ReactNode }) {
  return (
    <div
      className={cn(
        "rounded-lg border px-4 py-3 text-sm",
        tone === "success" ? "border-success/20 bg-success-soft text-success" : "border-destructive/20 bg-destructive/5 text-destructive",
      )}
    >
      {children}
    </div>
  );
}

function buildRecommendation(detail: ReviewTaskDetailResponse): Recommendation {
  const issueCodes = new Set([
    ...detail.candidate.validation_issue_codes,
    ...detail.validation_issues.map((item) => item.code).filter(Boolean),
  ]);
  const confidence = detail.candidate.source_confidence;
  const hasRejectSignal = Array.from(issueCodes).some((code) =>
    ["source_mismatch", "product_mismatch", "wrong_product", "out_of_scope", "unsupported_product_type"].includes(code),
  );

  if (hasRejectSignal) {
    return {
      action: "reject",
      title: "Reject",
      tone: "destructive",
      reasonCode: "conflicting_evidence",
      reasons: ["The candidate appears mismatched with the source or approved product scope.", "Rejecting blocks canonical promotion for this artifact."],
    };
  }

  if (detail.candidate.validation_status === "error") {
    return {
      action: "defer",
      title: "Defer",
      tone: "warning",
      reasonCode: detail.review_task.queue_reason_code || "validation_error",
      reasons: ["Validation has error-level issues.", "Resolve missing or conflicting source fields before approval."],
    };
  }

  if (issueCodes.has("low_confidence") || (confidence !== null && confidence < 0.7)) {
    return {
      action: "defer",
      title: "Defer",
      tone: "warning",
      reasonCode: "low_confidence",
      reasons: ["The candidate passed validation but confidence is still a review signal.", "Check key fields and use edit approval if the source supports corrections."],
    };
  }

  return {
    action: "approve",
    title: "Approve",
    tone: "success",
    reasonCode: detail.review_task.queue_reason_code || "manual_sampling_review",
    reasons: ["Validation passed.", "Approve if the visible reviewed values match the origin source."],
  };
}

function buildInitialEditableValues(detail: ReviewTaskDetailResponse, sourceDerivedProductName: string) {
  const values: Record<string, string> = {};
  for (const item of detail.field_trace_groups) {
    if (isReviewEditableField(item.field_name)) {
      values[item.field_name] = valueToEditableString(item.value);
    }
  }
  if (!values.product_name) {
    values.product_name = sourceDerivedProductName;
  }
  return values;
}

function isReviewEditableField(fieldName: string) {
  if (READ_ONLY_FIELDS.has(fieldName)) {
    return false;
  }
  if (fieldName.endsWith("_id")) {
    return false;
  }
  return true;
}

function originalValueForField(detail: ReviewTaskDetailResponse, fieldName: string, sourceDerivedProductName: string) {
  if (fieldName === "product_name") {
    return detail.candidate.candidate_payload.product_name ?? sourceDerivedProductName;
  }
  return detail.candidate.candidate_payload[fieldName];
}

function parseReviewedValue(rawValue: string, originalValue: unknown) {
  const trimmed = rawValue.trim();
  if (trimmed.length === 0) {
    return null;
  }
  if (typeof originalValue === "number") {
    const parsed = Number(trimmed.replace(/,/g, ""));
    return Number.isFinite(parsed) ? parsed : rawValue;
  }
  if (typeof originalValue === "boolean") {
    if (/^(true|yes|1)$/i.test(trimmed)) {
      return true;
    }
    if (/^(false|no|0)$/i.test(trimmed)) {
      return false;
    }
    return rawValue;
  }
  if (Array.isArray(originalValue) || isPlainObject(originalValue)) {
    try {
      return JSON.parse(rawValue) as unknown;
    } catch {
      return rawValue;
    }
  }
  return rawValue;
}

function parseManualValue(rawValue: string) {
  const trimmed = rawValue.trim();
  if (trimmed.length === 0) {
    return null;
  }
  if (/^(true|false)$/i.test(trimmed)) {
    return trimmed.toLowerCase() === "true";
  }
  if (/^null$/i.test(trimmed)) {
    return null;
  }
  if (/^-?\d+(\.\d+)?$/.test(trimmed)) {
    return Number(trimmed);
  }
  if ((trimmed.startsWith("[") && trimmed.endsWith("]")) || (trimmed.startsWith("{") && trimmed.endsWith("}"))) {
    try {
      return JSON.parse(trimmed) as unknown;
    } catch {
      return rawValue;
    }
  }
  return rawValue;
}

function reviewValuesEqual(left: unknown, right: unknown) {
  return stableStringify(left) === stableStringify(right);
}

function stableStringify(value: unknown) {
  if (value === undefined) {
    return "__undefined__";
  }
  return JSON.stringify(sortForStableStringify(value));
}

function sortForStableStringify(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => sortForStableStringify(item));
  }
  if (!isPlainObject(value)) {
    return value;
  }
  return Object.fromEntries(
    Object.entries(value)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => [key, sortForStableStringify(item)]),
  );
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function shouldUseTextarea(value: unknown, editableValue: string) {
  return Array.isArray(value) || isPlainObject(value) || editableValue.length > 80 || editableValue.includes("\n");
}

function valueToEditableString(value: unknown) {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value, null, 2);
}

function formatTimestamp(value: string | null) {
  return formatAdminDateTimeValue(value);
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

function formatValidationStatusLabel(value: string) {
  if (value === "error") {
    return "Validation Error";
  }
  if (value === "warning") {
    return "Validation Warning";
  }
  return toTitleCase(value);
}

function resolveCandidateProductName(detail: ReviewTaskDetailResponse) {
  const payloadValue = detail.candidate.candidate_payload.product_name;
  if (typeof payloadValue === "string" && payloadValue.trim().length > 0) {
    return payloadValue.trim();
  }
  return detail.candidate.product_name;
}

function resolveApprovedDisplayProductName(detail: ReviewTaskDetailResponse) {
  for (const item of detail.decision_history) {
    const overrideValue = item.override_payload.product_name;
    if (typeof overrideValue === "string" && overrideValue.trim().length > 0) {
      return overrideValue.trim();
    }
  }
  if (detail.current_product?.product_name.trim()) {
    return detail.current_product.product_name.trim();
  }
  return resolveCandidateProductName(detail);
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

function actionLabel(action: ReviewDecisionAction) {
  switch (action) {
    case "edit_approve":
      return "Edit & approve";
    default:
      return toTitleCase(action);
  }
}

function defaultReasonCodeForAction(action: ReviewDecisionAction, recommendation: Recommendation, detail: ReviewTaskDetailResponse) {
  if (action === recommendation.action) {
    return recommendation.reasonCode;
  }
  if (action === "edit_approve") {
    return "manual_override";
  }
  if (action === "reject") {
    return "needs_domain_review";
  }
  return detail.review_task.queue_reason_code || "manual_sampling_review";
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

function recommendationCardClasses(tone: Recommendation["tone"]) {
  switch (tone) {
    case "success":
      return "border-success/30 bg-success-soft text-success";
    case "destructive":
      return "border-destructive/30 bg-destructive/5 text-destructive";
    default:
      return "border-warning/30 bg-warning-soft text-warning";
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
