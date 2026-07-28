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
import {
  buildAdminHref,
  getAdminIntlLocale,
  localizedMissing,
  translateProductType,
  translateReviewAction,
  translateReviewState,
  translateValidationStatus,
  type AdminLocale,
} from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

type ReviewDetailSurfaceProps = {
  detail: ReviewTaskDetailResponse;
  csrfToken: string | null | undefined;
  locale: AdminLocale;
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

const REVIEW_DETAIL_COPY = {
  en: {
    backToQueue: "Back to queue",
    openRun: "Open run",
    sourceCandidateName: "Source candidate name",
    path: ["Review", "Review Queue", "Review Detail"],
    reviewFields: "Review fields",
    fixFlaggedValues: "Fix flagged values",
    noFieldIssues: "No field issues detected",
    otherCollectedFields: "Other collected fields",
    addAnotherField: "Add another field (advanced)",
    field: "Field",
    reviewedValue: "Reviewed value",
    add: "Add",
    removeOverride: "Remove correction",
    decision: "Decision",
    submitReviewAction: "Submit review action",
    readOnlyTask: "This task is read-only for your current session or is already closed.",
    submittedAction: "Submitted action",
    correctToEnable: "Correct a highlighted field to enable edit and approve.",
    decisionNote: "Decision note (optional)",
    reasonCode: "Reason code",
    useSuggestedReason: "Use suggested reason",
    reviewerNote: "Reviewer note",
    auditContextPlaceholder: "Add audit context.",
    editedApproval: "Edited approval",
    diffPreview: "Diff preview",
    agentValue: "Agent value",
    currentApprovedValue: "Current approved value",
    candidateProduct: "Candidate product",
    openOriginSource: "Open origin source",
    candidateDetails: "Candidate details",
    productFacts: "Product facts",
    reviewFocus: "Review focus",
    keyConditions: "Key conditions",
    recommended: "Recommended action",
    sourceCheck: "Source check",
    confidence: "Confidence",
    evidenceFields: "Evidence coverage",
    sourceRole: "Source role",
    openSource: "Open source",
    evidence: "evidence",
    editable: "Editable",
    readOnly: "Read only",
    yes: "Yes",
    no: "No",
    evidenceTrace: "Evidence trace and source context",
    noFieldTrace: "No field-level trace is available for this candidate.",
    sourceField: "Source field",
    normalization: "Normalization",
    extraction: "Extraction",
    noDirectEvidence: "No direct evidence link was persisted for this field.",
    auditContext: "History, model runs, and canonical context",
    decisionHistory: "Decision history",
    noDecisions: "No review decisions recorded.",
    unknownReviewer: "Unknown reviewer",
    modelRuns: "Model runs",
    noModelRuns: "No model execution references are available.",
    canonicalContext: "Canonical context",
    product: "Product",
    productId: "Product ID",
    version: "Version",
    status: "Status",
    lastVerified: "Last verified",
    firstCanonical: "Approval will create the first canonical record for this product.",
    unknownSource: "Unknown source",
    noExcerpt: "No excerpt captured.",
    originSource: "Origin source",
    started: "Started",
    completed: "Completed",
    tokens: "Tokens",
    cost: "Cost",
    fields: "fields",
    links: "links",
    chooseEditableField: "Choose an editable field name before adding a correction.",
    productNameRequired: "Reviewed product name cannot be empty.",
    actionFailed: "Review action failed.",
    actionUnavailable: "The review action could not be submitted. Check the admin API and try again.",
    submitting: "Submitting review decision",
    notDisclosed: "Not disclosed",
    noAdditionalConditions: "No additional conditions collected",
    productType: "Product type",
    eligibility: "Eligibility",
    applicationMethod: "Application method",
    interestRate: "Interest rate",
    rateType: "Rate type",
    term: "Term",
    amortization: "Amortization",
    paymentFrequency: "Payment frequency",
    prepayment: "Prepayment",
    loanAmount: "Loan amount",
    monthlyPayment: "Monthly payment",
    creditLimit: "Credit limit",
    securityRequirement: "Security requirement",
    security: "Security",
    monthlyFee: "Monthly fee",
    minimumBalance: "Minimum balance",
    transactions: "Transactions",
    feeWaiver: "Fee waiver",
    depositInsurance: "Deposit insurance",
    entryAmount: "Entry amount",
    promotionalRate: "Promotional rate",
    payoutOption: "Payout option",
    cashability: "Cashability",
  },
  ko: {
    backToQueue: "검토 대기열로",
    openRun: "실행 보기",
    sourceCandidateName: "원본 후보 이름",
    path: ["검토", "검토 대기열", "검토 상세"],
    reviewFields: "검토 필드",
    fixFlaggedValues: "표시된 값 수정",
    noFieldIssues: "감지된 필드 이슈 없음",
    otherCollectedFields: "기타 수집 필드",
    addAnotherField: "다른 필드 추가(고급)",
    field: "필드",
    reviewedValue: "검토 값",
    add: "추가",
    removeOverride: "수정값 제거",
    decision: "결정",
    submitReviewAction: "검토 결정 제출",
    readOnlyTask: "현재 세션에서 읽기 전용이거나 이미 종료된 작업입니다.",
    submittedAction: "제출한 결정",
    correctToEnable: "표시된 필드를 수정하면 수정 후 승인을 사용할 수 있습니다.",
    decisionNote: "결정 메모(선택)",
    reasonCode: "사유 코드",
    useSuggestedReason: "추천 사유 사용",
    reviewerNote: "검토자 메모",
    auditContextPlaceholder: "감사 맥락을 입력하세요.",
    editedApproval: "수정 승인",
    diffPreview: "변경 미리보기",
    agentValue: "에이전트 값",
    currentApprovedValue: "현재 승인 값",
    candidateProduct: "후보 상품",
    openOriginSource: "원본 출처 열기",
    candidateDetails: "후보 상세",
    productFacts: "상품 정보",
    reviewFocus: "검토 초점",
    keyConditions: "핵심 조건",
    recommended: "추천 결정",
    sourceCheck: "출처 점검",
    confidence: "신뢰도",
    evidenceFields: "근거 범위",
    sourceRole: "출처 역할",
    openSource: "출처 열기",
    evidence: "개 근거",
    editable: "수정 가능",
    readOnly: "읽기 전용",
    yes: "예",
    no: "아니요",
    evidenceTrace: "근거 추적 및 출처 맥락",
    noFieldTrace: "이 후보에 대한 필드 단위 추적 정보가 없습니다.",
    sourceField: "출처 필드",
    normalization: "정규화",
    extraction: "추출",
    noDirectEvidence: "이 필드에 저장된 직접 근거 링크가 없습니다.",
    auditContext: "이력, 모델 실행 및 정규 데이터 맥락",
    decisionHistory: "결정 이력",
    noDecisions: "기록된 검토 결정이 없습니다.",
    unknownReviewer: "알 수 없는 검토자",
    modelRuns: "모델 실행",
    noModelRuns: "사용 가능한 모델 실행 참조가 없습니다.",
    canonicalContext: "정규 데이터 맥락",
    product: "상품",
    productId: "상품 ID",
    version: "버전",
    status: "상태",
    lastVerified: "마지막 검증",
    firstCanonical: "승인하면 이 상품의 첫 정규 레코드가 생성됩니다.",
    unknownSource: "알 수 없는 출처",
    noExcerpt: "저장된 인용문이 없습니다.",
    originSource: "원본 출처",
    started: "시작",
    completed: "완료",
    tokens: "토큰",
    cost: "비용",
    fields: "개 필드",
    links: "개 링크",
    chooseEditableField: "수정할 수 있는 필드명을 선택한 뒤 추가하세요.",
    productNameRequired: "검토한 상품명은 비워둘 수 없습니다.",
    actionFailed: "검토 결정에 실패했습니다.",
    actionUnavailable: "검토 결정을 제출하지 못했습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    submitting: "검토 결정을 제출하는 중",
    notDisclosed: "공개되지 않음",
    noAdditionalConditions: "수집된 추가 조건 없음",
    productType: "상품 유형",
    eligibility: "자격 조건",
    applicationMethod: "신청 방법",
    interestRate: "금리",
    rateType: "금리 유형",
    term: "기간",
    amortization: "상환 기간",
    paymentFrequency: "납부 주기",
    prepayment: "중도 상환",
    loanAmount: "대출 금액",
    monthlyPayment: "월 납부액",
    creditLimit: "신용 한도",
    securityRequirement: "담보 요건",
    security: "담보",
    monthlyFee: "월 수수료",
    minimumBalance: "최소 잔액",
    transactions: "거래",
    feeWaiver: "수수료 면제",
    depositInsurance: "예금자 보호",
    entryAmount: "최소 가입 금액",
    promotionalRate: "프로모션 금리",
    payoutOption: "이자 지급 방식",
    cashability: "중도 인출",
  },
  ja: {
    backToQueue: "レビューキューへ",
    openRun: "実行を表示",
    sourceCandidateName: "ソース候補名",
    path: ["レビュー", "レビューキュー", "レビュー詳細"],
    reviewFields: "レビューフィールド",
    fixFlaggedValues: "指摘された値を修正",
    noFieldIssues: "フィールドの問題は検出されませんでした",
    otherCollectedFields: "その他の収集フィールド",
    addAnotherField: "別のフィールドを追加（詳細）",
    field: "フィールド",
    reviewedValue: "レビュー値",
    add: "追加",
    removeOverride: "修正値を削除",
    decision: "決定",
    submitReviewAction: "レビュー決定を送信",
    readOnlyTask: "現在のセッションでは読み取り専用、またはすでに終了したタスクです。",
    submittedAction: "送信した決定",
    correctToEnable: "指摘されたフィールドを修正すると、修正して承認を実行できます。",
    decisionNote: "決定メモ（任意）",
    reasonCode: "理由コード",
    useSuggestedReason: "推奨理由を使用",
    reviewerNote: "レビュアーメモ",
    auditContextPlaceholder: "監査コンテキストを追加してください。",
    editedApproval: "修正承認",
    diffPreview: "変更プレビュー",
    agentValue: "エージェント値",
    currentApprovedValue: "現在の承認値",
    candidateProduct: "候補商品",
    openOriginSource: "元のソースを開く",
    candidateDetails: "候補詳細",
    productFacts: "商品情報",
    reviewFocus: "レビューの焦点",
    keyConditions: "主要条件",
    recommended: "推奨決定",
    sourceCheck: "ソース確認",
    confidence: "信頼度",
    evidenceFields: "根拠範囲",
    sourceRole: "ソースの役割",
    openSource: "ソースを開く",
    evidence: "件の根拠",
    editable: "編集可能",
    readOnly: "読み取り専用",
    yes: "はい",
    no: "いいえ",
    evidenceTrace: "根拠トレースとソースコンテキスト",
    noFieldTrace: "この候補にはフィールド単位のトレースがありません。",
    sourceField: "ソースフィールド",
    normalization: "正規化",
    extraction: "抽出",
    noDirectEvidence: "このフィールドには直接の根拠リンクが保存されていません。",
    auditContext: "履歴、モデル実行、正規データのコンテキスト",
    decisionHistory: "決定履歴",
    noDecisions: "レビュー決定は記録されていません。",
    unknownReviewer: "不明なレビュアー",
    modelRuns: "モデル実行",
    noModelRuns: "参照できるモデル実行はありません。",
    canonicalContext: "正規データのコンテキスト",
    product: "商品",
    productId: "商品 ID",
    version: "バージョン",
    status: "状態",
    lastVerified: "最終検証",
    firstCanonical: "承認すると、この商品の最初の正規レコードが作成されます。",
    unknownSource: "不明なソース",
    noExcerpt: "保存された引用はありません。",
    originSource: "元のソース",
    started: "開始",
    completed: "完了",
    tokens: "トークン",
    cost: "コスト",
    fields: "フィールド",
    links: "リンク",
    chooseEditableField: "編集可能なフィールド名を選択してから追加してください。",
    productNameRequired: "レビューした商品名は空にできません。",
    actionFailed: "レビュー決定に失敗しました。",
    actionUnavailable: "レビュー決定を送信できませんでした。Admin API を確認して再試行してください。",
    submitting: "レビュー決定を送信中",
    notDisclosed: "非公開",
    noAdditionalConditions: "収集された追加条件はありません",
    productType: "商品タイプ",
    eligibility: "利用条件",
    applicationMethod: "申込方法",
    interestRate: "金利",
    rateType: "金利タイプ",
    term: "期間",
    amortization: "返済期間",
    paymentFrequency: "支払頻度",
    prepayment: "繰上返済",
    loanAmount: "融資額",
    monthlyPayment: "月額支払",
    creditLimit: "利用限度額",
    securityRequirement: "担保要件",
    security: "担保",
    monthlyFee: "月額手数料",
    minimumBalance: "最低残高",
    transactions: "取引",
    feeWaiver: "手数料免除",
    depositInsurance: "預金保険",
    entryAmount: "最低申込額",
    promotionalRate: "キャンペーン金利",
    payoutOption: "利息支払方法",
    cashability: "中途換金",
  },
} as const;

type ReviewDetailCopy = (typeof REVIEW_DETAIL_COPY)[AdminLocale];

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

export function ReviewDetailSurface({ detail, csrfToken, locale }: ReviewDetailSurfaceProps) {
  const router = useRouter();
  const copy = REVIEW_DETAIL_COPY[locale];
  const localeHref = (pathname: string) => buildAdminHref(pathname, new URLSearchParams(), locale);
  const sourceDerivedProductName = resolveCandidateProductName(detail);
  const approvedDisplayProductName = resolveApprovedDisplayProductName(detail);
  const showingApprovedName = approvedDisplayProductName !== sourceDerivedProductName;
  const recommendation = useMemo(() => buildRecommendation(detail, locale), [detail, locale]);
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
    return reviewedProductName.trim().length > 0 ? null : copy.productNameRequired;
  }, [copy.productNameRequired, editableValues.product_name, sourceDerivedProductName]);

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
  const hasUnsavedChanges =
    diffPreview.length > 0 ||
    extraFieldName.trim().length > 0 ||
    extraFieldValue.trim().length > 0 ||
    reasonCode.length > 0 ||
    reasonText.trim().length > 0;

  function updateEditableField(fieldName: string, value: string) {
    setError(null);
    setEditableValues((current) => ({ ...current, [fieldName]: value }));
  }

  function addExtraOverride() {
    const fieldName = extraFieldName.trim();
    if (!fieldName || !isReviewEditableField(fieldName)) {
      setError(copy.chooseEditableField);
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
        setError(payload.error?.message ?? copy.actionFailed);
        return;
      }

      setMessage(actionLabel(action, locale));
      if (action === "defer" || action === "reject") {
        router.replace(localeHref("/admin/reviews"));
        return;
      }
      router.refresh();
    } catch {
      setError(copy.actionUnavailable);
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <section
      aria-busy={pendingAction ? true : undefined}
      className="grid gap-5"
      data-admin-dirty={hasUnsavedChanges ? "true" : undefined}
      data-admin-mutation-pending={pendingAction ? "true" : undefined}
    >
      <p aria-live="polite" className="sr-only" role="status">
        {pendingAction ? copy.submitting : message ? `${copy.submittedAction}: ${message}` : ""}
      </p>
      <AdminPageHeader
        actions={
          <>
            <Button asChild variant="outline">
              <Link href={localeHref("/admin/reviews")}>{copy.backToQueue}</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href={localeHref(`/admin/runs/${detail.review_task.run_id}`)}>{copy.openRun}</Link>
            </Button>
          </>
        }
        badges={
          <>
            <span className={cn("rounded-full px-3 py-1 text-xs font-medium", stateBadgeClasses(detail.review_task.review_state))}>
              {translateReviewState(locale, detail.review_task.review_state)}
            </span>
            <span className={cn("rounded-full px-3 py-1 text-xs font-medium", validationBadgeClasses(detail.candidate.validation_status))}>
              {translateValidationStatus(locale, detail.candidate.validation_status)}
            </span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              {detail.candidate.bank_name} {translateProductType(locale, detail.candidate.product_type)}
            </span>
          </>
        }
        description={showingApprovedName ? `${copy.sourceCandidateName}: ${sourceDerivedProductName}` : undefined}
        path={[...copy.path]}
        title={approvedDisplayProductName}
      />

      <ReviewProductPresentation copy={copy} detail={detail} editableValues={editableValues} locale={locale} />

      <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <DecisionRecommendationCard copy={copy} recommendation={recommendation} />
        <SourceDecisionCard copy={copy} detail={detail} locale={locale} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_25rem] xl:items-start">
        <article className="min-w-0 border-y border-border/80 bg-card/95 px-5 py-5">
          <SectionHeading eyebrow={copy.reviewFields} title={issueReviewFields.length > 0 ? copy.fixFlaggedValues : copy.noFieldIssues} />
          {issueReviewFields.length > 0 ? (
            <div className="mt-4 divide-y divide-border/80">
              {issueReviewFields.map((item) => (
              <FieldReviewRow
                copy={copy}
                editableValue={editableValues[item.field_name] ?? valueToEditableString(item.effective_value)}
                item={item}
                key={item.field_name}
                locale={locale}
                onValueChange={(value) => updateEditableField(item.field_name, value)}
                trace={detail.field_trace_groups.find((traceItem) => traceItem.field_name === item.field_name) ?? null}
              />
              ))}
            </div>
          ) : null}

          {otherReviewFields.length > 0 ? (
            <details className="mt-5 rounded-lg border border-border/80 bg-background">
              <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-foreground">
                {copy.otherCollectedFields} ({formatCount(locale, otherReviewFields.length)})
              </summary>
              <div className="divide-y divide-border/70 border-t border-border/70 px-4">
                {otherReviewFields.map((item) => (
                  <FieldReviewRow
                    copy={copy}
                    editableValue={editableValues[item.field_name] ?? valueToEditableString(item.effective_value)}
                    item={item}
                    key={item.field_name}
                    locale={locale}
                    onValueChange={(value) => updateEditableField(item.field_name, value)}
                    trace={detail.field_trace_groups.find((traceItem) => traceItem.field_name === item.field_name) ?? null}
                  />
                ))}
              </div>
            </details>
          ) : null}

          <details className="mt-5 rounded-lg border border-dashed border-border bg-background">
            <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-muted-foreground">{copy.addAnotherField}</summary>
            <div className="border-t border-border/70 p-4">
              <div className="grid gap-3 md:grid-cols-[minmax(0,0.7fr)_minmax(0,1fr)_auto]">
                <label className="grid gap-2 text-sm">
                  <span className="text-muted-foreground">{copy.field}</span>
                  <Input
                    className="h-10 rounded-lg bg-background"
                    list="review-editable-field-options"
                    onChange={(event) => setExtraFieldName(event.target.value)}
                    placeholder="standard_rate"
                    value={extraFieldName}
                  />
                </label>
                <label className="grid gap-2 text-sm">
                  <span className="text-muted-foreground">{copy.reviewedValue}</span>
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
                    {copy.add}
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
                      className="min-h-10 rounded-full bg-muted px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                      aria-label={`${copy.removeOverride}: ${item.fieldName}`}
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

        <aside className="grid content-start gap-4 xl:sticky xl:top-24 xl:max-h-[calc(100vh-7rem)] xl:overflow-y-auto xl:overscroll-contain">
          <article
            aria-busy={pendingAction ? true : undefined}
            className="border-y border-border/80 bg-card/95 px-5 py-5"
            data-admin-dirty={hasUnsavedChanges ? "true" : undefined}
            data-admin-mutation-pending={pendingAction ? "true" : undefined}
          >
            <SectionHeading eyebrow={copy.decision} title={copy.submitReviewAction} />

            {detail.available_actions.length === 0 ? (
              <p className="mt-5 text-sm leading-6 text-muted-foreground">
                {copy.readOnlyTask}
              </p>
            ) : (
              <div className="mt-5 grid gap-4">
                {productNameError ? (
                  <StatusMessage tone="destructive">{productNameError}</StatusMessage>
                ) : null}
                {message ? <StatusMessage tone="success">{copy.submittedAction}: {message}</StatusMessage> : null}
                {error ? <StatusMessage tone="destructive">{error}</StatusMessage> : null}

                <div className="grid gap-2">
                  {orderDecisionActions(recommendation.action).map((action, index) => (
                    <DecisionActionButton
                      action={action}
                      locale={locale}
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
                    <p className="text-xs leading-5 text-muted-foreground">{copy.correctToEnable}</p>
                  ) : null}
                </div>

                <details className="rounded-lg border border-border/80 bg-background">
                  <summary className="cursor-pointer px-3 py-2 text-sm font-medium text-muted-foreground">{copy.decisionNote}</summary>
                  <div className="grid gap-3 border-t border-border/70 p-3">
                    <label className="grid gap-2 text-sm">
                      <span className="font-medium text-foreground">{copy.reasonCode}</span>
                      <select
                        className="h-10 rounded-lg border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                        disabled={decisionDisabled}
                        onChange={(event) => setReasonCode(event.target.value)}
                        value={reasonCode}
                      >
                        <option value="">{copy.useSuggestedReason}</option>
                        {REASON_CODE_OPTIONS.map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="grid gap-2 text-sm">
                      <span className="font-medium text-foreground">{copy.reviewerNote}</span>
                      <Textarea
                        className="min-h-20 rounded-lg bg-background"
                        disabled={decisionDisabled}
                        onChange={(event) => setReasonText(event.target.value)}
                        placeholder={copy.auditContextPlaceholder}
                        value={reasonText}
                      />
                    </label>
                  </div>
                </details>
              </div>
            )}
          </article>

          {diffPreview.length > 0 ? (
            <article className="border-y border-border/80 bg-card/95 px-5 py-5">
              <SectionHeading eyebrow={copy.editedApproval} title={copy.diffPreview} />
              <div className="mt-4 divide-y divide-border/80">
                {diffPreview.map((item) => (
                  <div className="py-3 first:pt-0 last:pb-0" key={item.fieldName}>
                    <p className="text-sm font-medium text-foreground">{toTitleCase(item.fieldName)}</p>
                    <p className="mt-2 text-xs text-muted-foreground">{copy.agentValue}</p>
                    <p className="mt-1 break-words text-sm leading-6 text-muted-foreground">{formatValue(item.before, locale)}</p>
                    <p className="mt-3 text-xs text-muted-foreground">{copy.reviewedValue}</p>
                    <p className="mt-1 break-words text-sm leading-6 text-foreground">{formatValue(item.after, locale)}</p>
                  </div>
                ))}
              </div>
            </article>
          ) : null}
        </aside>
      </div>

      <EvidenceTracePanel activeField={activeField} copy={copy} detail={detail} locale={locale} onSelectField={setSelectedFieldName} />
      <AuditContextPanel copy={copy} detail={detail} locale={locale} />
    </section>
  );
}

type ReviewProductFact = {
  label: string;
  value: string;
};

function ReviewProductPresentation({
  copy,
  detail,
  editableValues,
  locale,
}: {
  copy: ReviewDetailCopy;
  detail: ReviewTaskDetailResponse;
  editableValues: Record<string, string>;
  locale: AdminLocale;
}) {
  const product = buildReviewProductView(detail, editableValues, copy, locale);

  return (
    <article className="overflow-hidden rounded-lg border border-border/80 bg-card/95 shadow-sm">
      <div className="border-b border-border/80 bg-muted/20 p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-md border border-primary/20 bg-primary/5 px-2 py-1 text-xs font-medium text-primary">{copy.candidateProduct}</span>
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
                {copy.openOriginSource}
              </a>
            </Button>
          ) : null}
        </div>

        <dl className="mt-5 grid overflow-hidden rounded-lg border border-border/80 bg-background sm:grid-cols-3 sm:divide-x sm:divide-border/80">
          {product.metrics.map((metric, index) => (
            <ReviewMetricTile highlight={index === 0} key={metric.label} label={metric.label} value={metric.value} />
          ))}
        </dl>
      </div>

      <div className="grid gap-4 p-5 lg:grid-cols-[minmax(0,1fr)_22rem] lg:items-start">
        <section>
          <SectionHeading eyebrow={copy.candidateDetails} title={copy.productFacts} />
          <dl className="mt-4 grid gap-x-6 gap-y-4 sm:grid-cols-2">
            {product.facts.map((fact) => (
              <ReviewProductFactRow key={fact.label} {...fact} />
            ))}
          </dl>
        </section>
        <section className="rounded-lg border border-border/80 bg-muted/20 p-4">
          <SectionHeading eyebrow={copy.reviewFocus} title={copy.keyConditions} />
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
    <div className={cn("min-h-24 p-3", highlight ? "bg-primary/5" : "bg-background/80")}>
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

function buildReviewProductView(
  detail: ReviewTaskDetailResponse,
  editableValues: Record<string, string>,
  copy: ReviewDetailCopy,
  locale: AdminLocale,
) {
  const value = (fieldName: string) => reviewProductValue(detail, editableValues, fieldName);
  const display = (item: unknown) => displayReviewValue(item, copy);
  const rateValue = (item: unknown) => formatReviewRate(item, copy, locale);
  const currencyValue = (item: unknown) => formatReviewCurrency(item, detail.candidate.currency, copy, locale);
  const fact = (label: string, item: unknown, formatter?: (candidate: unknown) => string) =>
    reviewFact(label, item, copy, formatter);
  const productFamily = detail.candidate.product_family;
  const productType = detail.candidate.product_type;
  const name = optionalReviewValue(value("product_name"), copy) ?? detail.candidate.product_name;
  const rate = value("mortgage_rate") ?? value("interest_rate") ?? value("public_display_rate") ?? value("standard_rate") ?? value("base_12_month_rate");
  const depositEntry = value("minimum_deposit") ?? value("minimum_balance");
  const commonFacts = [
    fact(copy.productType, translateProductType(locale, productType)),
    fact(copy.eligibility, value("eligibility_text")),
    fact(copy.applicationMethod, value("application_method")),
  ];

  if (productFamily === "lending") {
    return {
      name,
      typeLabel: translateProductType(locale, productType),
      description: optionalReviewValue(value("description_short"), copy),
      metrics: [
        { label: copy.interestRate, value: rateValue(rate) },
        { label: copy.rateType, value: display(value("rate_type")) },
        { label: copy.term, value: display(value("term_length_text") ?? value("term_length_days")) },
      ],
      facts: compactReviewFacts([
        fact(copy.interestRate, rate, rateValue),
        fact(copy.rateType, value("rate_type")),
        fact(copy.term, value("term_length_text") ?? value("term_length_days")),
        fact(copy.amortization, value("amortization_text")),
        fact(copy.paymentFrequency, value("payment_frequency")),
        fact(copy.prepayment, value("prepayment_privileges")),
        fact(copy.loanAmount, value("loan_amount_text")),
        fact(copy.monthlyPayment, value("monthly_payment_text")),
        fact(copy.creditLimit, value("credit_limit_text")),
        fact(copy.securityRequirement, value("security_requirement") ?? value("collateral_text")),
        ...commonFacts,
      ]),
      conditions: reviewConditionFacts([
        fact(copy.eligibility, value("eligibility_text")),
        fact(copy.applicationMethod, value("application_method")),
        fact(copy.prepayment, value("prepayment_privileges")),
        fact(copy.security, value("security_requirement") ?? value("collateral_text")),
      ], copy),
    };
  }

  if (productType === "chequing") {
    return {
      name,
      typeLabel: translateProductType(locale, productType),
      description: optionalReviewValue(value("description_short"), copy),
      metrics: [
        { label: copy.monthlyFee, value: currencyValue(value("monthly_fee") ?? value("public_display_fee")) },
        { label: copy.minimumBalance, value: currencyValue(value("minimum_balance")) },
        { label: copy.transactions, value: display(value("unlimited_transactions_flag")) },
      ],
      facts: compactReviewFacts([
        fact(copy.monthlyFee, value("monthly_fee") ?? value("public_display_fee"), currencyValue),
        fact(copy.minimumBalance, value("minimum_balance"), currencyValue),
        fact(copy.feeWaiver, value("fee_waiver_condition")),
        fact(copy.transactions, value("unlimited_transactions_flag")),
        ...commonFacts,
        fact(copy.depositInsurance, value("deposit_insurance")),
      ]),
      conditions: reviewConditionFacts([
        fact(copy.feeWaiver, value("fee_waiver_condition")),
        fact(copy.eligibility, value("eligibility_text")),
        fact(copy.applicationMethod, value("application_method")),
      ], copy),
    };
  }

  return {
    name,
    typeLabel: translateProductType(locale, productType),
    description: optionalReviewValue(value("description_short"), copy),
    metrics: [
      { label: copy.interestRate, value: rateValue(rate) },
      { label: copy.term, value: display(value("term_length_text") ?? value("term_length_days")) },
      { label: copy.entryAmount, value: currencyValue(depositEntry) },
    ],
    facts: compactReviewFacts([
      fact(copy.interestRate, rate, rateValue),
      fact(copy.promotionalRate, value("promotional_rate"), rateValue),
      fact(copy.term, value("term_length_text") ?? value("term_length_days")),
      fact(copy.entryAmount, depositEntry, currencyValue),
      fact(copy.monthlyFee, value("monthly_fee") ?? value("public_display_fee"), currencyValue),
      fact(copy.payoutOption, value("payout_option")),
      fact(copy.cashability, value("cashability")),
      fact(copy.depositInsurance, value("deposit_insurance")),
      ...commonFacts,
    ]),
    conditions: reviewConditionFacts([
      fact(copy.eligibility, value("eligibility_text")),
      fact(copy.applicationMethod, value("application_method")),
      fact(copy.depositInsurance, value("deposit_insurance")),
      fact(copy.term, value("term_length_text") ?? value("term_length_days")),
    ], copy),
  };
}

function reviewProductValue(detail: ReviewTaskDetailResponse, editableValues: Record<string, string>, fieldName: string): unknown {
  if (Object.prototype.hasOwnProperty.call(editableValues, fieldName)) {
    return editableValues[fieldName];
  }
  return detail.review_field_items.find((item) => item.field_name === fieldName)?.effective_value ?? detail.candidate.candidate_payload[fieldName];
}

function reviewFact(
  label: string,
  value: unknown,
  copy: ReviewDetailCopy,
  formatter: (item: unknown) => string = (item) => displayReviewValue(item, copy),
): ReviewProductFact | null {
  const formatted = formatter(value);
  return formatted === copy.notDisclosed ? null : { label, value: formatted };
}

function compactReviewFacts(facts: Array<ReviewProductFact | null>) {
  return facts.filter((fact): fact is ReviewProductFact => Boolean(fact));
}

function reviewConditionFacts(facts: Array<ReviewProductFact | null>, copy: ReviewDetailCopy) {
  const visible = compactReviewFacts(facts);
  return visible.length > 0 ? visible : [{ label: copy.status, value: copy.noAdditionalConditions }];
}

function displayReviewValue(value: unknown, copy: ReviewDetailCopy): string {
  if (value === null || value === undefined || value === "") {
    return copy.notDisclosed;
  }
  if (typeof value === "boolean") {
    return value ? copy.yes : copy.no;
  }
  if (Array.isArray(value)) {
    return value.map((item) => displayReviewValue(item, copy)).join(", ");
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function optionalReviewValue(value: unknown, copy: ReviewDetailCopy) {
  const formatted = displayReviewValue(value, copy);
  return formatted === copy.notDisclosed ? null : formatted;
}

function formatReviewRate(value: unknown, copy: ReviewDetailCopy, locale: AdminLocale) {
  if (typeof value === "number" && Number.isFinite(value)) {
    return new Intl.NumberFormat(getAdminIntlLocale(locale), { maximumFractionDigits: 2 }).format(value) + "%";
  }
  const text = displayReviewValue(value, copy);
  if (text === copy.notDisclosed || text.includes("%")) {
    return text;
  }
  const numeric = Number(text.replace(/,/g, ""));
  return Number.isFinite(numeric)
    ? new Intl.NumberFormat(getAdminIntlLocale(locale), { maximumFractionDigits: 2 }).format(numeric) + "%"
    : text;
}

function formatReviewCurrency(value: unknown, currency: string, copy: ReviewDetailCopy, locale: AdminLocale) {
  if (typeof value === "number" && Number.isFinite(value)) {
    return new Intl.NumberFormat(getAdminIntlLocale(locale), { style: "currency", currency: normalizeReviewCurrency(currency), maximumFractionDigits: Number.isInteger(value) ? 0 : 2 }).format(value);
  }
  const text = displayReviewValue(value, copy);
  if (text === copy.notDisclosed) {
    return text;
  }
  const numeric = Number(text.replace(/[$,]/g, ""));
  return Number.isFinite(numeric)
    ? new Intl.NumberFormat(getAdminIntlLocale(locale), { style: "currency", currency: normalizeReviewCurrency(currency), maximumFractionDigits: Number.isInteger(numeric) ? 0 : 2 }).format(numeric)
    : text;
}

function normalizeReviewCurrency(currency: string) {
  const normalized = currency.trim().toUpperCase();
  return /^[A-Z]{3}$/.test(normalized) ? normalized : "CAD";
}

function DecisionRecommendationCard({
  copy,
  recommendation,
}: {
  copy: ReviewDetailCopy;
  recommendation: Recommendation;
}) {
  return (
    <article className={cn("rounded-lg border p-5 shadow-sm", recommendationCardClasses(recommendation.tone))}>
      <div className="flex items-start gap-3">
        <Bot aria-hidden="true" className="mt-1 h-4 w-4 shrink-0" />
        <div className="min-w-0">
          <p className="text-sm font-medium">{copy.recommended}</p>
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

function SourceDecisionCard({
  copy,
  detail,
  locale,
}: {
  copy: ReviewDetailCopy;
  detail: ReviewTaskDetailResponse;
  locale: AdminLocale;
}) {
  return (
    <article className="rounded-lg border border-border/80 bg-card/95 p-5 shadow-sm">
      <p className="text-sm font-medium text-muted-foreground">{copy.sourceCheck}</p>
      <dl className="mt-4 grid gap-3 text-sm">
        <MetaRow label={copy.confidence} value={formatConfidence(detail.candidate.source_confidence, locale)} />
        <MetaRow
          label={copy.evidenceFields}
          value={`${formatCount(locale, detail.evidence_summary.field_count)} ${copy.fields} / ${formatCount(locale, detail.evidence_summary.item_count)} ${copy.links}`}
        />
        {detail.source_context.discovery_role ? <MetaRow label={copy.sourceRole} value={toTitleCase(detail.source_context.discovery_role)} /> : null}
      </dl>
      {detail.source_context.source_url ? (
        <Button asChild className="mt-4 w-full" variant="outline">
          <a href={detail.source_context.source_url} rel="noreferrer" target="_blank">
            {copy.openSource} <ExternalLink />
          </a>
        </Button>
      ) : null}
    </article>
  );
}

function FieldReviewRow({
  copy,
  item,
  locale,
  editableValue,
  onValueChange,
  trace,
}: {
  copy: ReviewDetailCopy;
  item: ReviewFieldItem;
  locale: AdminLocale;
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
        "grid gap-3 py-4",
        hasIssue ? "border-l-2 border-warning bg-warning-soft/30 px-4" : "",
      )}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium text-foreground">{item.label}</p>
            {hasIssue ? (
              <span className="rounded-full bg-warning-soft px-2.5 py-1 text-[11px] font-medium text-warning">
                {fieldIssueLabel(item, locale)}
              </span>
            ) : null}
          </div>
          <p className="mt-1 break-words text-sm leading-6 text-muted-foreground">{copy.agentValue}: {formatValue(item.agent_value, locale)}</p>
          {effectiveDiffers ? (
            <p className="mt-1 break-words text-sm leading-6 text-foreground">{copy.currentApprovedValue}: {formatValue(item.effective_value, locale)}</p>
          ) : null}
          {trace?.mapping.field_note ? (
            <p className="mt-2 break-words text-xs leading-5 text-muted-foreground">
              <sup className="mr-1 font-semibold text-foreground">*</sup>
              {trace.mapping.field_note}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-medium", item.evidence_count > 0 ? "bg-success-soft text-success" : "bg-muted text-muted-foreground")}>
            {formatCount(locale, item.evidence_count)} {copy.evidence}
          </span>
          {editable ? (
            <span className="rounded-full bg-info-soft px-2.5 py-1 text-[11px] font-medium text-info">{copy.editable}</span>
          ) : (
            <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">{copy.readOnly}</span>
          )}
        </div>
      </div>

      {editable ? (
        <label className="grid gap-2 text-sm">
          <span className="text-muted-foreground">{copy.reviewedValue}</span>
          {useTextarea ? (
            <Textarea className="min-h-24 rounded-lg bg-background" onChange={(event) => onValueChange(event.target.value)} value={editableValue} />
          ) : typeof item.effective_value === "boolean" ? (
            <select
              className="h-10 rounded-lg border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
              onChange={(event) => onValueChange(event.target.value)}
              value={editableValue}
            >
              <option value="true">{copy.yes}</option>
              <option value="false">{copy.no}</option>
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
            {copy.evidence} ({trace.evidence_links.length})
          </summary>
          <div className="grid gap-3 border-t border-border/70 p-3">
            {trace.evidence_links.map((evidence) => (
              <TraceEvidenceCard copy={copy} item={evidence} key={`${evidence.field_name}-${evidence.evidence_chunk_id}`} locale={locale} />
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
  copy,
  locale,
  onSelectField,
}: {
  detail: ReviewTaskDetailResponse;
  activeField: ReviewFieldTraceGroup | null;
  copy: ReviewDetailCopy;
  locale: AdminLocale;
  onSelectField: (fieldName: string) => void;
}) {
  return (
    <details className="rounded-lg border border-border/80 bg-card/95 shadow-sm">
      <summary className="cursor-pointer px-5 py-4 text-sm font-medium text-foreground">{copy.evidenceTrace}</summary>
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
              <span className="mt-1 block text-xs text-muted-foreground">{formatCount(locale, item.evidence_count)} {copy.evidence}</span>
            </button>
          ))}
        </div>

        {!activeField ? (
          <p className="text-sm leading-6 text-muted-foreground">{copy.noFieldTrace}</p>
        ) : (
          <div className="grid gap-4">
            <div>
              <p className="text-sm font-medium text-foreground">{activeField.label}</p>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{formatValue(activeField.value, locale)}</p>
            </div>
            <dl className="grid gap-2 text-sm md:grid-cols-2">
              <MetaRow label={copy.sourceField} value={activeField.mapping.source_field_name ?? localizedMissing(locale)} />
              <MetaRow label={copy.normalization} value={activeField.mapping.normalization_method ?? localizedMissing(locale)} />
              <MetaRow label={copy.extraction} value={activeField.mapping.extraction_method ?? localizedMissing(locale)} />
              <MetaRow label={copy.confidence} value={formatConfidence(activeField.mapping.extraction_confidence, locale)} />
            </dl>
            {activeField.evidence_links.length === 0 ? (
              <p className="text-sm leading-6 text-muted-foreground">{copy.noDirectEvidence}</p>
            ) : (
              <div className="grid gap-3">
                {activeField.evidence_links.map((item) => (
                  <TraceEvidenceCard copy={copy} item={item} key={`${item.field_name}-${item.evidence_chunk_id}`} locale={locale} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </details>
  );
}

function AuditContextPanel({
  copy,
  detail,
  locale,
}: {
  copy: ReviewDetailCopy;
  detail: ReviewTaskDetailResponse;
  locale: AdminLocale;
}) {
  return (
    <details className="rounded-lg border border-border/80 bg-card/95 shadow-sm">
      <summary className="cursor-pointer px-5 py-4 text-sm font-medium text-foreground">{copy.auditContext}</summary>
      <div className="grid gap-5 border-t border-border/80 p-5 lg:grid-cols-3">
        <div>
          <p className="text-sm font-medium text-foreground">{copy.decisionHistory}</p>
          {detail.decision_history.length === 0 ? (
            <p className="mt-3 text-sm leading-6 text-muted-foreground">{copy.noDecisions}</p>
          ) : (
            <div className="mt-3 divide-y divide-border/80">
              {detail.decision_history.map((item) => (
                <div className="py-3 first:pt-0 last:pb-0" key={item.review_decision_id}>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <span className={cn("rounded-full px-2.5 py-1 text-xs font-medium", stateBadgeClasses(decisionActionState(item.action_type)))}>
                      {translateReviewAction(locale, item.action_type)}
                    </span>
                    <span className="text-xs text-muted-foreground">{formatTimestamp(item.decided_at, locale)}</span>
                  </div>
                  <p className="mt-2 text-sm text-foreground">{item.actor.display_name ?? item.actor.email ?? copy.unknownReviewer}</p>
                  {item.diff_summary ? <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.diff_summary}</p> : null}
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <p className="text-sm font-medium text-foreground">{copy.modelRuns}</p>
          {detail.model_executions.length === 0 ? (
            <p className="mt-3 text-sm leading-6 text-muted-foreground">{copy.noModelRuns}</p>
          ) : (
            <div className="mt-3 divide-y divide-border/80">
              {detail.model_executions.map((item) => (
                <ModelExecutionCard copy={copy} item={item} key={item.model_execution_id} locale={locale} />
              ))}
            </div>
          )}
        </div>

        <div>
          <p className="text-sm font-medium text-foreground">{copy.canonicalContext}</p>
          {detail.current_product ? (
            <dl className="mt-3 grid gap-3 text-sm">
              <MetaRow label={copy.product} value={detail.current_product.product_name} />
              <MetaRow label={copy.productId} value={detail.current_product.product_id} />
              <MetaRow label={copy.version} value={formatCount(locale, detail.current_product.current_version_no)} />
              <MetaRow label={copy.status} value={detail.current_product.status} />
              <MetaRow label={copy.lastVerified} value={formatTimestamp(detail.current_product.last_verified_at, locale)} />
            </dl>
          ) : (
            <p className="mt-3 text-sm leading-6 text-muted-foreground">{copy.firstCanonical}</p>
          )}
        </div>
      </div>
    </details>
  );
}

function TraceEvidenceCard({
  copy,
  item,
  locale,
}: {
  copy: ReviewDetailCopy;
  item: ReviewEvidenceLink;
  locale: AdminLocale;
}) {
  return (
    <div className="py-3 first:pt-0 last:pb-0">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-foreground">{item.label}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {item.source_id ?? item.source_document_id ?? copy.unknownSource} - {item.anchor_label}
          </p>
        </div>
        <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
          {formatConfidence(item.citation_confidence, locale)}
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">{item.evidence_excerpt ?? copy.noExcerpt}</p>
      {item.source_url ? (
        <a
          className="mt-3 inline-flex min-h-10 items-center gap-1 text-sm font-medium text-primary underline-offset-4 hover:underline"
          href={item.source_url}
          rel="noreferrer"
          target="_blank"
        >
          <ExternalLink className="h-4 w-4" />
          {copy.originSource}
        </a>
      ) : null}
    </div>
  );
}

function ModelExecutionCard({
  copy,
  item,
  locale,
}: {
  copy: ReviewDetailCopy;
  item: ReviewModelExecution;
  locale: AdminLocale;
}) {
  const tokenSummary =
    item.usage.prompt_tokens !== null || item.usage.completion_tokens !== null
      ? `${formatCount(locale, item.usage.prompt_tokens ?? 0)} / ${formatCount(locale, item.usage.completion_tokens ?? 0)} ${copy.tokens.toLocaleLowerCase(getAdminIntlLocale(locale))}`
      : localizedMissing(locale);

  return (
    <div className="py-3 first:pt-0 last:pb-0">
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
        <MetaRow label={copy.started} value={formatTimestamp(item.started_at, locale)} />
        <MetaRow label={copy.completed} value={formatTimestamp(item.completed_at, locale)} />
        <MetaRow label={copy.tokens} value={tokenSummary} />
        <MetaRow label={copy.cost} value={formatCost(item.usage.estimated_cost, locale)} />
      </dl>
    </div>
  );
}

function SectionHeading({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div>
      <p className="text-xs font-semibold text-muted-foreground">{eyebrow}</p>
      <h2 className="mt-1 text-lg font-semibold tracking-tight text-foreground">{title}</h2>
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
      aria-live={tone === "destructive" ? "assertive" : "polite"}
      className={cn(
        "rounded-lg border px-4 py-3 text-sm",
        tone === "success" ? "border-success/20 bg-success-soft text-success" : "border-destructive/20 bg-destructive/5 text-destructive",
      )}
      role={tone === "destructive" ? "alert" : "status"}
    >
      {children}
    </div>
  );
}

function DecisionActionButton({
  action,
  disabled,
  locale,
  onClick,
  pending,
  primary,
}: {
  action: ReviewDecisionAction;
  disabled: boolean;
  locale: AdminLocale;
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
      {pending ? pendingDecisionLabel(action, locale) : actionLabel(action, locale)}
    </Button>
  );
}

function buildRecommendation(detail: ReviewTaskDetailResponse, locale: AdminLocale): Recommendation {
  const action = detail.review_diagnosis.recommended_action;
  return {
    action,
    title: actionLabel(action, locale),
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

function formatTimestamp(value: string | null, locale: AdminLocale) {
  if (!value) {
    return localizedMissing(locale);
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(getAdminIntlLocale(locale), {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatConfidence(value: number | null, locale: AdminLocale) {
  if (value === null) {
    return localizedMissing(locale);
  }
  return new Intl.NumberFormat(getAdminIntlLocale(locale), {
    style: "percent",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatCost(value: number | null, locale: AdminLocale) {
  if (value === null) {
    return localizedMissing(locale);
  }
  return new Intl.NumberFormat(getAdminIntlLocale(locale), {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 6,
  }).format(value);
}

function formatCount(locale: AdminLocale, value: number) {
  return new Intl.NumberFormat(getAdminIntlLocale(locale)).format(value);
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

function formatValue(value: unknown, locale: AdminLocale = "en") {
  if (value === null || value === undefined || value === "") {
    return localizedMissing(locale);
  }
  if (typeof value === "number") {
    return new Intl.NumberFormat(getAdminIntlLocale(locale), { maximumFractionDigits: 8 }).format(value);
  }
  if (typeof value === "string" || typeof value === "boolean") {
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

function actionLabel(action: ReviewDecisionAction, locale: AdminLocale) {
  const labels: Record<AdminLocale, Record<ReviewDecisionAction, string>> = {
    en: { approve: "Approve", edit_approve: "Edit & approve", defer: "Defer", reject: "Reject" },
    ko: { approve: "승인", edit_approve: "수정 후 승인", defer: "보류", reject: "반려" },
    ja: { approve: "承認", edit_approve: "修正して承認", defer: "保留", reject: "却下" },
  };
  return labels[locale][action];
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

function pendingDecisionLabel(action: ReviewDecisionAction, locale: AdminLocale) {
  const labels: Record<AdminLocale, Record<ReviewDecisionAction, string>> = {
    en: { approve: "Approving…", edit_approve: "Submitting edit…", defer: "Deferring…", reject: "Rejecting…" },
    ko: { approve: "승인 중…", edit_approve: "수정 승인 제출 중…", defer: "보류 중…", reject: "반려 중…" },
    ja: { approve: "承認中…", edit_approve: "修正承認を送信中…", defer: "保留中…", reject: "却下中…" },
  };
  return labels[locale][action];
}

function fieldIssueLabel(item: ReviewFieldItem, locale: AdminLocale) {
  const labels: Record<AdminLocale, Record<string, string>> = {
    en: {
      missing: "Missing",
      navigation_copy: "Navigation copy",
      non_value_copy: "Not a value",
      invalid_type: "Wrong type",
      unresolved_placeholder: "Broken template",
      cross_field_conflict: "Conflicts with term",
      source_identity_mismatch: "Wrong product",
      page_copy: "Page copy",
      duplicated_page_copy: "Duplicated copy",
      fallback: "Check value",
    },
    ko: {
      missing: "누락",
      navigation_copy: "탐색 문구",
      non_value_copy: "값이 아닌 문구",
      invalid_type: "잘못된 형식",
      unresolved_placeholder: "깨진 템플릿",
      cross_field_conflict: "기간과 충돌",
      source_identity_mismatch: "다른 상품",
      page_copy: "페이지 문구",
      duplicated_page_copy: "중복 문구",
      fallback: "값 확인",
    },
    ja: {
      missing: "欠落",
      navigation_copy: "ナビゲーション文言",
      non_value_copy: "値ではない文言",
      invalid_type: "不正な型",
      unresolved_placeholder: "未解決テンプレート",
      cross_field_conflict: "期間と不整合",
      source_identity_mismatch: "別の商品",
      page_copy: "ページ文言",
      duplicated_page_copy: "重複文言",
      fallback: "値を確認",
    },
  };
  if (item.missing) {
    return labels[locale].missing;
  }
  return labels[locale][item.issue_type ?? ""] ?? labels[locale].fallback;
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
