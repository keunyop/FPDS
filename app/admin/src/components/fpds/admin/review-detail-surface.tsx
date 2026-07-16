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
  ReviewFieldItem,
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
  action: ReviewDecisionAction;
  title: string;
  tone: "success" | "warning" | "destructive";
  reasonCode: string;
  headline: string;
  affectedFields: string[];
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

const STRUCTURED_EDITABLE_FIELDS = new Set([
  "interest_payment_options",
  "target_customer_tags",
  "term_options",
  "term_rate_table",
]);

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
  const [reasonCode, setReasonCode] = useState("");
  const [reasonText, setReasonText] = useState("");
  const [editableValues, setEditableValues] = useState(() => buildInitialEditableValues(detail));
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
    const names = new Set([
      ...COMMON_EDITABLE_FIELDS,
      ...detail.review_field_items.map((item) => item.field_name),
      ...detail.field_trace_groups.map((item) => item.field_name),
    ]);
    return Array.from(names).sort();
  }, [detail.field_trace_groups, detail.review_field_items]);

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

  const orderedReviewFields = useMemo(
    () =>
      [...detail.review_field_items].sort((left, right) => {
        const leftPriority = left.missing || left.suspect ? 0 : 1;
        const rightPriority = right.missing || right.suspect ? 0 : 1;
        if (leftPriority !== rightPriority) {
          return leftPriority - rightPriority;
        }
        if (left.field_name === "product_name" || right.field_name === "product_name") {
          return left.field_name === "product_name" ? -1 : 1;
        }
        return left.label.localeCompare(right.label);
      }),
    [detail.review_field_items],
  );
  const issueReviewFields = useMemo(
    () => orderedReviewFields.filter((item) => item.missing || item.suspect),
    [orderedReviewFields],
  );
  const otherReviewFields = useMemo(
    () => orderedReviewFields.filter((item) => !item.missing && !item.suspect),
    [orderedReviewFields],
  );

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

      <ReviewProductPresentation detail={detail} editableValues={editableValues} />

      <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <DecisionRecommendationCard recommendation={recommendation} />
        <SourceDecisionCard detail={detail} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_25rem]">
        <article className="min-w-0 rounded-lg border border-border/80 bg-card/95 p-5 shadow-sm">
          <SectionHeading eyebrow="Review fields" title={issueReviewFields.length > 0 ? "Fix flagged values" : "No field issues detected"} />
          {issueReviewFields.length > 0 ? (
            <div className="mt-5 grid gap-3">
              {issueReviewFields.map((item) => (
              <FieldReviewRow
                editableValue={editableValues[item.field_name] ?? valueToEditableString(item.effective_value)}
                item={item}
                key={item.field_name}
                onValueChange={(value) => updateEditableField(item.field_name, value)}
                trace={detail.field_trace_groups.find((traceItem) => traceItem.field_name === item.field_name) ?? null}
              />
              ))}
            </div>
          ) : null}

          {otherReviewFields.length > 0 ? (
            <details className="mt-5 rounded-lg border border-border/80 bg-background">
              <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-foreground">
                Other collected fields ({otherReviewFields.length})
              </summary>
              <div className="grid gap-3 border-t border-border/70 p-4">
                {otherReviewFields.map((item) => (
                  <FieldReviewRow
                    editableValue={editableValues[item.field_name] ?? valueToEditableString(item.effective_value)}
                    item={item}
                    key={item.field_name}
                    onValueChange={(value) => updateEditableField(item.field_name, value)}
                    trace={detail.field_trace_groups.find((traceItem) => traceItem.field_name === item.field_name) ?? null}
                  />
                ))}
              </div>
            </details>
          ) : null}

          <details className="mt-5 rounded-lg border border-dashed border-border bg-background">
            <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-muted-foreground">Add another field (advanced)</summary>
            <div className="border-t border-border/70 p-4">
              <div className="grid gap-3 md:grid-cols-[minmax(0,0.7fr)_minmax(0,1fr)_auto]">
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
          </details>
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
                {productNameError ? (
                  <StatusMessage tone="destructive">{productNameError}</StatusMessage>
                ) : null}
                {message ? <StatusMessage tone="success">Submitted action: {message}</StatusMessage> : null}
                {error ? <StatusMessage tone="destructive">{error}</StatusMessage> : null}

                <div className="grid gap-2">
                  {orderDecisionActions(recommendation.action).map((action, index) => (
                    <DecisionActionButton
                      action={action}
                      disabled={
                        action === "edit_approve"
                          ? editApproveDisabled
                          : decisionDisabled || !detail.available_actions.includes(action)
                      }
                      key={action}
                      onClick={() => handleDecision(action)}
                      pending={pendingAction === action}
                      primary={index === 0}
                    />
                  ))}
                  {recommendation.action === "edit_approve" && diffPreview.length === 0 ? (
                    <p className="text-xs leading-5 text-muted-foreground">Correct a highlighted field to enable edit and approve.</p>
                  ) : null}
                </div>

                <details className="rounded-lg border border-border/80 bg-background">
                  <summary className="cursor-pointer px-3 py-2 text-sm font-medium text-muted-foreground">Decision note (optional)</summary>
                  <div className="grid gap-3 border-t border-border/70 p-3">
                    <label className="grid gap-2 text-sm">
                      <span className="font-medium text-foreground">Reason code</span>
                      <select
                        className="h-10 rounded-lg border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                        onChange={(event) => setReasonCode(event.target.value)}
                        value={reasonCode}
                      >
                        <option value="">Use suggested reason</option>
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
                        className="min-h-20 rounded-lg bg-background"
                        onChange={(event) => setReasonText(event.target.value)}
                        placeholder="Add audit context."
                        value={reasonText}
                      />
                    </label>
                  </div>
                </details>
              </div>
            )}
          </article>

          {diffPreview.length > 0 ? (
            <article className="rounded-lg border border-border/80 bg-card/95 p-5 shadow-sm">
              <SectionHeading eyebrow="Edited approval" title="Diff preview" />
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
            </article>
          ) : null}
        </aside>
      </div>

      <EvidenceTracePanel activeField={activeField} detail={detail} onSelectField={setSelectedFieldName} />
      <AuditContextPanel detail={detail} />
    </section>
  );
}

type ReviewProductFact = {
  label: string;
  value: string;
};

function ReviewProductPresentation({
  detail,
  editableValues,
}: {
  detail: ReviewTaskDetailResponse;
  editableValues: Record<string, string>;
}) {
  const product = buildReviewProductView(detail, editableValues);

  return (
    <article className="overflow-hidden rounded-lg border border-border/80 bg-card/95 shadow-sm">
      <div className="border-b border-border/80 bg-muted/20 p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-md border border-primary/20 bg-primary/5 px-2 py-1 text-xs font-medium text-primary">Candidate product</span>
              <span className="rounded-md border border-border bg-background px-2 py-1 text-xs font-medium text-muted-foreground">
                {product.typeLabel}
              </span>
              <span className="text-xs text-muted-foreground">{detail.candidate.bank_name}</span>
            </div>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">{product.name}</h2>
            {product.description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{product.description}</p> : null}
          </div>
          {detail.source_context.source_url ? (
            <Button asChild className="shrink-0" variant="outline">
              <a href={detail.source_context.source_url} rel="noreferrer" target="_blank">
                <ExternalLink />
                Open origin source
              </a>
            </Button>
          ) : null}
        </div>

        <dl className="mt-5 grid gap-3 sm:grid-cols-3">
          {product.metrics.map((metric, index) => (
            <ReviewMetricTile highlight={index === 0} key={metric.label} label={metric.label} value={metric.value} />
          ))}
        </dl>
      </div>

      <div className="grid gap-4 p-5 lg:grid-cols-[minmax(0,1fr)_22rem] lg:items-start">
        <section>
          <SectionHeading eyebrow="Candidate details" title="Product facts" />
          <dl className="mt-4 grid gap-x-6 gap-y-4 sm:grid-cols-2">
            {product.facts.map((fact) => (
              <ReviewProductFactRow key={fact.label} {...fact} />
            ))}
          </dl>
        </section>
        <section className="rounded-lg border border-border/80 bg-muted/20 p-4">
          <SectionHeading eyebrow="Review focus" title="Key conditions" />
          <dl className="mt-4 grid gap-4">
            {product.conditions.map((fact) => (
              <ReviewProductFactRow key={fact.label} {...fact} />
            ))}
          </dl>
        </section>
      </div>
    </article>
  );
}

function ReviewMetricTile({ highlight, label, value }: { highlight?: boolean; label: string; value: string }) {
  return (
    <div className={cn("min-h-24 rounded-lg border p-3", highlight ? "border-primary/25 bg-primary/5" : "border-border bg-background/80")}>
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-2 break-words text-2xl font-semibold leading-tight text-foreground tabular-nums">{value}</dd>
    </div>
  );
}

function ReviewProductFactRow({ label, value }: ReviewProductFact) {
  return (
    <div>
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-1 break-words text-sm font-medium leading-6 text-foreground">{value}</dd>
    </div>
  );
}

function buildReviewProductView(detail: ReviewTaskDetailResponse, editableValues: Record<string, string>) {
  const value = (fieldName: string) => reviewProductValue(detail, editableValues, fieldName);
  const productFamily = detail.candidate.product_family;
  const productType = detail.candidate.product_type;
  const name = displayReviewValue(value("product_name")) || detail.candidate.product_name;
  const rate = value("mortgage_rate") ?? value("interest_rate") ?? value("public_display_rate") ?? value("standard_rate") ?? value("base_12_month_rate");
  const depositEntry = value("minimum_deposit") ?? value("minimum_balance");
  const commonFacts = [
    reviewFact("Product type", toTitleCase(productType)),
    reviewFact("Eligibility", value("eligibility_text")),
    reviewFact("Application method", value("application_method")),
  ];

  if (productFamily === "lending") {
    return {
      name,
      typeLabel: toTitleCase(productType),
      description: optionalReviewValue(value("description_short")),
      metrics: [
        { label: "Interest rate", value: formatReviewRate(rate) },
        { label: "Rate type", value: displayReviewValue(value("rate_type")) },
        { label: "Term", value: displayReviewValue(value("term_length_text") ?? value("term_length_days")) },
      ],
      facts: compactReviewFacts([
        reviewFact("Interest rate", rate, formatReviewRate),
        reviewFact("Rate type", value("rate_type")),
        reviewFact("Term", value("term_length_text") ?? value("term_length_days")),
        reviewFact("Amortization", value("amortization_text")),
        reviewFact("Payment frequency", value("payment_frequency")),
        reviewFact("Prepayment", value("prepayment_privileges")),
        reviewFact("Loan amount", value("loan_amount_text")),
        reviewFact("Monthly payment", value("monthly_payment_text")),
        reviewFact("Credit limit", value("credit_limit_text")),
        reviewFact("Security requirement", value("security_requirement") ?? value("collateral_text")),
        ...commonFacts,
      ]),
      conditions: reviewConditionFacts([
        reviewFact("Eligibility", value("eligibility_text")),
        reviewFact("Application method", value("application_method")),
        reviewFact("Prepayment", value("prepayment_privileges")),
        reviewFact("Security", value("security_requirement") ?? value("collateral_text")),
      ]),
    };
  }

  if (productType === "chequing") {
    return {
      name,
      typeLabel: toTitleCase(productType),
      description: optionalReviewValue(value("description_short")),
      metrics: [
        { label: "Monthly fee", value: formatReviewCurrency(value("monthly_fee") ?? value("public_display_fee"), detail.candidate.currency) },
        { label: "Minimum balance", value: formatReviewCurrency(value("minimum_balance"), detail.candidate.currency) },
        { label: "Transactions", value: displayReviewValue(value("unlimited_transactions_flag")) },
      ],
      facts: compactReviewFacts([
        reviewFact("Monthly fee", value("monthly_fee") ?? value("public_display_fee"), (item) => formatReviewCurrency(item, detail.candidate.currency)),
        reviewFact("Minimum balance", value("minimum_balance"), (item) => formatReviewCurrency(item, detail.candidate.currency)),
        reviewFact("Fee waiver", value("fee_waiver_condition")),
        reviewFact("Transactions", value("unlimited_transactions_flag")),
        ...commonFacts,
        reviewFact("Deposit insurance", value("deposit_insurance")),
      ]),
      conditions: reviewConditionFacts([
        reviewFact("Fee waiver", value("fee_waiver_condition")),
        reviewFact("Eligibility", value("eligibility_text")),
        reviewFact("Application method", value("application_method")),
      ]),
    };
  }

  return {
    name,
    typeLabel: toTitleCase(productType),
    description: optionalReviewValue(value("description_short")),
    metrics: [
      { label: "Interest rate", value: formatReviewRate(rate) },
      { label: "Term", value: displayReviewValue(value("term_length_text") ?? value("term_length_days")) },
      { label: "Entry amount", value: formatReviewCurrency(depositEntry, detail.candidate.currency) },
    ],
    facts: compactReviewFacts([
      reviewFact("Interest rate", rate, formatReviewRate),
      reviewFact("Promotional rate", value("promotional_rate"), formatReviewRate),
      reviewFact("Term", value("term_length_text") ?? value("term_length_days")),
      reviewFact("Entry amount", depositEntry, (item) => formatReviewCurrency(item, detail.candidate.currency)),
      reviewFact("Monthly fee", value("monthly_fee") ?? value("public_display_fee"), (item) => formatReviewCurrency(item, detail.candidate.currency)),
      reviewFact("Payout option", value("payout_option")),
      reviewFact("Cashability", value("cashability")),
      reviewFact("Deposit insurance", value("deposit_insurance")),
      ...commonFacts,
    ]),
    conditions: reviewConditionFacts([
      reviewFact("Eligibility", value("eligibility_text")),
      reviewFact("Application method", value("application_method")),
      reviewFact("Deposit insurance", value("deposit_insurance")),
      reviewFact("Term", value("term_length_text") ?? value("term_length_days")),
    ]),
  };
}

function reviewProductValue(detail: ReviewTaskDetailResponse, editableValues: Record<string, string>, fieldName: string): unknown {
  if (Object.prototype.hasOwnProperty.call(editableValues, fieldName)) {
    return editableValues[fieldName];
  }
  return detail.review_field_items.find((item) => item.field_name === fieldName)?.effective_value ?? detail.candidate.candidate_payload[fieldName];
}

function reviewFact(label: string, value: unknown, formatter: (item: unknown) => string = displayReviewValue): ReviewProductFact | null {
  const formatted = formatter(value);
  return formatted === "Not disclosed" ? null : { label, value: formatted };
}

function compactReviewFacts(facts: Array<ReviewProductFact | null>) {
  return facts.filter((fact): fact is ReviewProductFact => Boolean(fact));
}

function reviewConditionFacts(facts: Array<ReviewProductFact | null>) {
  const visible = compactReviewFacts(facts);
  return visible.length > 0 ? visible : [{ label: "Status", value: "No additional conditions collected" }];
}

function displayReviewValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "Not disclosed";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (Array.isArray(value)) {
    return value.map((item) => displayReviewValue(item)).join(", ");
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function optionalReviewValue(value: unknown) {
  const formatted = displayReviewValue(value);
  return formatted === "Not disclosed" ? null : formatted;
}

function formatReviewRate(value: unknown) {
  if (typeof value === "number" && Number.isFinite(value)) {
    return `${value.toFixed(2).replace(/\.?0+$/, "")}%`;
  }
  const text = displayReviewValue(value);
  if (text === "Not disclosed" || text.includes("%")) {
    return text;
  }
  const numeric = Number(text.replace(/,/g, ""));
  return Number.isFinite(numeric) ? `${numeric.toFixed(2).replace(/\.?0+$/, "")}%` : text;
}

function formatReviewCurrency(value: unknown, currency: string) {
  if (typeof value === "number" && Number.isFinite(value)) {
    return new Intl.NumberFormat("en-CA", { style: "currency", currency: normalizeReviewCurrency(currency), maximumFractionDigits: Number.isInteger(value) ? 0 : 2 }).format(value);
  }
  const text = displayReviewValue(value);
  if (text === "Not disclosed") {
    return text;
  }
  const numeric = Number(text.replace(/[$,]/g, ""));
  return Number.isFinite(numeric)
    ? new Intl.NumberFormat("en-CA", { style: "currency", currency: normalizeReviewCurrency(currency), maximumFractionDigits: Number.isInteger(numeric) ? 0 : 2 }).format(numeric)
    : text;
}

function normalizeReviewCurrency(currency: string) {
  const normalized = currency.trim().toUpperCase();
  return /^[A-Z]{3}$/.test(normalized) ? normalized : "CAD";
}

function DecisionRecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  return (
    <article className={cn("rounded-lg border p-5 shadow-sm", recommendationCardClasses(recommendation.tone))}>
      <div className="flex items-start gap-3">
        <span className="mt-0.5 rounded-lg bg-background/80 p-2">
          <Bot className="h-4 w-4" />
        </span>
        <div className="min-w-0">
          <p className="text-sm font-medium uppercase tracking-[0.16em]">Recommended</p>
          <h2 className="mt-2 text-xl font-semibold tracking-tight">{recommendation.title}</h2>
        </div>
      </div>
      <p className="mt-4 text-sm leading-6">{recommendation.headline}</p>
      {recommendation.affectedFields.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {recommendation.affectedFields.map((field) => (
            <span className="rounded-full bg-background/80 px-2.5 py-1 text-xs font-medium" key={field}>
              {field}
            </span>
          ))}
        </div>
      ) : null}
    </article>
  );
}

function SourceDecisionCard({ detail }: { detail: ReviewTaskDetailResponse }) {
  return (
    <article className="rounded-lg border border-border/80 bg-card/95 p-5 shadow-sm">
      <p className="text-sm font-medium uppercase tracking-[0.16em] text-muted-foreground">Source check</p>
      <dl className="mt-4 grid gap-3 text-sm">
        <MetaRow label="Confidence" value={formatConfidence(detail.candidate.source_confidence)} />
        <MetaRow label="Evidence fields" value={`${detail.evidence_summary.field_count} fields / ${detail.evidence_summary.item_count} links`} />
        {detail.source_context.discovery_role ? <MetaRow label="Source role" value={toTitleCase(detail.source_context.discovery_role)} /> : null}
      </dl>
      {detail.source_context.source_url ? (
        <Button asChild className="mt-4 w-full" variant="outline">
          <a href={detail.source_context.source_url} rel="noreferrer" target="_blank">
            Open source <ExternalLink />
          </a>
        </Button>
      ) : null}
    </article>
  );
}

function FieldReviewRow({
  item,
  editableValue,
  onValueChange,
  trace,
}: {
  item: ReviewFieldItem;
  editableValue: string;
  onValueChange: (value: string) => void;
  trace: ReviewFieldTraceGroup | null;
}) {
  const editable = item.editable && isReviewEditableField(item.field_name);
  const useTextarea = shouldUseTextarea(item.effective_value, editableValue) || STRUCTURED_EDITABLE_FIELDS.has(item.field_name);
  const hasIssue = item.missing || item.suspect;
  const effectiveDiffers = !reviewValuesEqual(item.agent_value, item.effective_value);
  return (
    <div
      className={cn(
        "grid gap-3 rounded-lg border bg-background p-4",
        hasIssue ? "border-warning/45 bg-warning-soft/30" : "border-border/80",
      )}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium text-foreground">{item.label}</p>
            {hasIssue ? (
              <span className="rounded-full bg-warning-soft px-2.5 py-1 text-[11px] font-medium text-warning">
                {fieldIssueLabel(item)}
              </span>
            ) : null}
          </div>
          <p className="mt-1 break-words text-sm leading-6 text-muted-foreground">Agent value: {formatValue(item.agent_value)}</p>
          {effectiveDiffers ? (
            <p className="mt-1 break-words text-sm leading-6 text-foreground">Current approved value: {formatValue(item.effective_value)}</p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", item.evidence_count > 0 ? "bg-success-soft text-success" : "bg-muted text-muted-foreground")}>
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
            <Textarea className="min-h-24 rounded-lg bg-background" onChange={(event) => onValueChange(event.target.value)} value={editableValue} />
          ) : typeof item.effective_value === "boolean" ? (
            <select
              className="h-10 rounded-lg border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
              onChange={(event) => onValueChange(event.target.value)}
              value={editableValue}
            >
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          ) : (
            <Input
              className="h-10 rounded-lg bg-background"
              inputMode={typeof item.effective_value === "number" ? "decimal" : undefined}
              onChange={(event) => onValueChange(event.target.value)}
              type={typeof item.effective_value === "number" ? "number" : "text"}
              value={editableValue}
            />
          )}
        </label>
      ) : null}

      {trace && trace.evidence_links.length > 0 ? (
        <details className="rounded-lg border border-border/70 bg-background">
          <summary className="cursor-pointer px-3 py-2 text-sm font-medium text-foreground">
            Evidence ({trace.evidence_links.length})
          </summary>
          <div className="grid gap-3 border-t border-border/70 p-3">
            {trace.evidence_links.map((evidence) => (
              <TraceEvidenceCard item={evidence} key={`${evidence.field_name}-${evidence.evidence_chunk_id}`} />
            ))}
          </div>
        </details>
      ) : null}
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

function DecisionActionButton({
  action,
  disabled,
  onClick,
  pending,
  primary,
}: {
  action: ReviewDecisionAction;
  disabled: boolean;
  onClick: () => void;
  pending: boolean;
  primary: boolean;
}) {
  return (
    <Button
      disabled={disabled}
      onClick={onClick}
      type="button"
      variant={primary ? (action === "reject" ? "destructive" : "default") : "outline"}
    >
      {pending ? <Loader2 className="animate-spin" /> : decisionActionIcon(action)}
      {pending ? pendingDecisionLabel(action) : actionLabel(action)}
    </Button>
  );
}

function buildRecommendation(detail: ReviewTaskDetailResponse): Recommendation {
  const action = detail.review_diagnosis.recommended_action;
  return {
    action,
    title: actionLabel(action),
    tone: action === "approve" ? "success" : action === "reject" ? "destructive" : "warning",
    reasonCode: defaultReasonCodeForAction(action, null, detail),
    headline: detail.review_diagnosis.headline,
    affectedFields: detail.review_diagnosis.affected_fields.map((field) => field.label),
  };
}

function buildInitialEditableValues(detail: ReviewTaskDetailResponse) {
  const values: Record<string, string> = {};
  for (const item of detail.review_field_items) {
    if (item.editable && isReviewEditableField(item.field_name)) {
      values[item.field_name] = valueToEditableString(item.effective_value);
    }
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
  const reviewField = detail.review_field_items.find((item) => item.field_name === fieldName);
  if (reviewField) {
    return reviewField.effective_value;
  }
  if (fieldName === "product_name") {
    return detail.current_product?.product_name ?? detail.candidate.candidate_payload.product_name ?? sourceDerivedProductName;
  }
  return detail.candidate.candidate_payload[fieldName];
}

function parseReviewedValue(rawValue: string, originalValue: unknown) {
  const trimmed = rawValue.trim();
  if (trimmed.length === 0) {
    return null;
  }
  if (originalValue === null || originalValue === undefined) {
    return parseManualValue(rawValue);
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

function orderDecisionActions(recommendedAction: ReviewDecisionAction): ReviewDecisionAction[] {
  return [recommendedAction, ...(["approve", "edit_approve", "defer", "reject"] as const)].filter(
    (action, index, actions) => actions.indexOf(action) === index,
  );
}

function decisionActionIcon(action: ReviewDecisionAction) {
  switch (action) {
    case "approve":
      return <Check />;
    case "edit_approve":
      return <PencilLine />;
    case "defer":
      return <CirclePause />;
    case "reject":
      return <X />;
  }
}

function pendingDecisionLabel(action: ReviewDecisionAction) {
  switch (action) {
    case "approve":
      return "Approving...";
    case "edit_approve":
      return "Submitting edit...";
    case "defer":
      return "Deferring...";
    case "reject":
      return "Rejecting...";
  }
}

function fieldIssueLabel(item: ReviewFieldItem) {
  if (item.missing) {
    return "Missing";
  }
  if (item.issue_type === "navigation_copy") {
    return "Navigation copy";
  }
  if (item.issue_type === "non_value_copy") {
    return "Not a value";
  }
  if (item.issue_type === "invalid_type") {
    return "Wrong type";
  }
  if (item.issue_type === "unresolved_placeholder") {
    return "Broken template";
  }
  if (item.issue_type === "cross_field_conflict") {
    return "Conflicts with term";
  }
  if (item.issue_type === "source_identity_mismatch") {
    return "Wrong product";
  }
  if (item.issue_type === "page_copy") {
    return "Page copy";
  }
  if (item.issue_type === "duplicated_page_copy") {
    return "Duplicated copy";
  }
  return "Check value";
}

function defaultReasonCodeForAction(
  action: ReviewDecisionAction,
  recommendation: Recommendation | null,
  detail: ReviewTaskDetailResponse,
) {
  if (recommendation && action === recommendation.action) {
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
