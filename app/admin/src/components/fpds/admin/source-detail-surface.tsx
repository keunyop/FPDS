"use client";

import Link from "next/link";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import type { SourceRegistryDetailResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

type SourceDetailSurfaceProps = {
  detail: SourceRegistryDetailResponse;
  locale: AdminLocale;
};

const SOURCE_DETAIL_COPY = {
  en: {
    back: "Back to sources",
    openUrl: "Open source URL",
    description: "Read-only generated source metadata.",
    path: ["Operations", "Sources", "Source Detail"],
    bank: "Bank",
    country: "Country",
    productType: "Product type",
    productKey: "Product key",
    sourceName: "Source name",
    sourceType: "Source type",
    role: "Role",
    status: "Status",
    priority: "Priority",
    language: "Language",
    purpose: "Purpose",
    candidateProducing: "Candidate-producing",
    sourceUrl: "Source URL",
    normalizedUrl: "Normalized URL",
    expectedFields: "Expected fields",
    aliasUrls: "Alias URLs",
    redirectTargetUrl: "Redirect target URL",
    changeReason: "Change reason",
    discoveryExplainability: "Discovery explainability",
    promotedTitle: "Why this source was promoted",
    promotedDescription: "Bounded discovery scoring and selection signals.",
    selectionPathMissing: "selection path n/a",
    confidenceMissing: "confidence n/a",
    noMetadata: "No discovery explainability metadata was persisted for this source.",
    candidateOrigin: "Candidate origin",
    heuristicScore: "Heuristic score",
    aiParallelScore: "AI parallel score",
    aiPredictedRole: "AI predicted role",
    aiConfidenceBand: "AI confidence band",
    pageEvidenceScore: "Page evidence score",
    primaryHeading: "Primary heading",
    pageTitle: "Page title",
    attributeSignalCount: "Attribute signal count",
    negativeSignalCount: "Negative signal count",
    aiRationale: "AI rationale",
    selectionReasonCodes: "Selection reason codes",
    aiReasonCodes: "AI reason codes",
    pageEvidenceCodes: "Page evidence codes",
    recentHistory: "Recent collection history",
    noRecentRuns: "No recent collection runs were linked to this source yet.",
    started: "started",
    candidates: (count: number) => `${count} candidates`,
    reviewQueued: (count: number) => `${count} review queued`,
    yes: "yes",
    no: "no",
    missing: "n/a",
  },
  ko: {
    back: "소스로 돌아가기",
    openUrl: "소스 URL 열기",
    description: "읽기 전용 생성 source 메타데이터입니다.",
    path: ["운영", "소스", "소스 상세"],
    bank: "은행",
    country: "국가",
    productType: "상품 유형",
    productKey: "상품 키",
    sourceName: "소스 이름",
    sourceType: "소스 유형",
    role: "역할",
    status: "상태",
    priority: "우선순위",
    language: "언어",
    purpose: "목적",
    candidateProducing: "Candidate 생성",
    sourceUrl: "Source URL",
    normalizedUrl: "정규화 URL",
    expectedFields: "예상 필드",
    aliasUrls: "Alias URL",
    redirectTargetUrl: "Redirect target URL",
    changeReason: "변경 사유",
    discoveryExplainability: "Discovery 설명",
    promotedTitle: "이 소스가 승격된 이유",
    promotedDescription: "제한된 discovery scoring 및 선택 신호입니다.",
    selectionPathMissing: "selection path 없음",
    confidenceMissing: "confidence 없음",
    noMetadata: "이 소스에 저장된 discovery 설명 메타데이터가 없습니다.",
    candidateOrigin: "Candidate 출처",
    heuristicScore: "Heuristic score",
    aiParallelScore: "AI parallel score",
    aiPredictedRole: "AI 예측 역할",
    aiConfidenceBand: "AI confidence band",
    pageEvidenceScore: "Page evidence score",
    primaryHeading: "Primary heading",
    pageTitle: "Page title",
    attributeSignalCount: "Attribute signal count",
    negativeSignalCount: "Negative signal count",
    aiRationale: "AI rationale",
    selectionReasonCodes: "Selection reason codes",
    aiReasonCodes: "AI reason codes",
    pageEvidenceCodes: "Page evidence codes",
    recentHistory: "최근 collection 이력",
    noRecentRuns: "아직 이 소스와 연결된 최근 collection run이 없습니다.",
    started: "시작",
    candidates: (count: number) => `candidate ${count}개`,
    reviewQueued: (count: number) => `review queued ${count}개`,
    yes: "예",
    no: "아니오",
    missing: "없음",
  },
  ja: {
    back: "ソースに戻る",
    openUrl: "ソースURLを開く",
    description: "読み取り専用の生成 source メタデータです。",
    path: ["運用", "ソース", "ソース詳細"],
    bank: "銀行",
    country: "国",
    productType: "商品タイプ",
    productKey: "商品キー",
    sourceName: "ソース名",
    sourceType: "ソースタイプ",
    role: "ロール",
    status: "状態",
    priority: "優先度",
    language: "言語",
    purpose: "目的",
    candidateProducing: "Candidate 生成",
    sourceUrl: "Source URL",
    normalizedUrl: "正規化URL",
    expectedFields: "想定フィールド",
    aliasUrls: "Alias URL",
    redirectTargetUrl: "Redirect target URL",
    changeReason: "変更理由",
    discoveryExplainability: "Discovery 説明",
    promotedTitle: "このソースが昇格された理由",
    promotedDescription: "制限された discovery scoring と選択シグナルです。",
    selectionPathMissing: "selection path なし",
    confidenceMissing: "confidence なし",
    noMetadata: "このソースには discovery 説明メタデータが保存されていません。",
    candidateOrigin: "Candidate 起点",
    heuristicScore: "Heuristic score",
    aiParallelScore: "AI parallel score",
    aiPredictedRole: "AI 予測ロール",
    aiConfidenceBand: "AI confidence band",
    pageEvidenceScore: "Page evidence score",
    primaryHeading: "Primary heading",
    pageTitle: "Page title",
    attributeSignalCount: "Attribute signal count",
    negativeSignalCount: "Negative signal count",
    aiRationale: "AI rationale",
    selectionReasonCodes: "Selection reason codes",
    aiReasonCodes: "AI reason codes",
    pageEvidenceCodes: "Page evidence codes",
    recentHistory: "最近の collection 履歴",
    noRecentRuns: "このソースに紐づく最近の collection run はまだありません。",
    started: "開始",
    candidates: (count: number) => `candidate ${count} 件`,
    reviewQueued: (count: number) => `review queued ${count} 件`,
    yes: "はい",
    no: "いいえ",
    missing: "なし",
  },
} as const;

export function SourceDetailSurface({ detail, locale }: SourceDetailSurfaceProps) {
  const copy = SOURCE_DETAIL_COPY[locale];
  const discoveryMetadata = detail.source.discovery_metadata ?? {};
  const selectionReasonCodes = asStringArray(discoveryMetadata.selection_reason_codes);
  const aiReasonCodes = asStringArray(discoveryMetadata.ai_reason_codes);
  const pageReasonCodes = asStringArray(discoveryMetadata.page_evidence_reason_codes);

  return (
    <section className="grid gap-6">
      <AdminPageHeader
        actions={
          <>
            <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/sources", new URLSearchParams(), locale)}>
              {copy.back}
            </Link>
            <a className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" href={detail.source.source_url} rel="noreferrer" target="_blank">
              {copy.openUrl}
            </a>
          </>
        }
        badges={
          <>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{detail.source.discovery_role}</span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{detail.source.status}</span>
          </>
        }
        description={copy.description}
        path={copy.path}
        title={detail.source.source_id}
      />

      <article className="grid gap-4 lg:grid-cols-2">
        <ReadonlyField label={copy.bank} value={detail.source.bank_code} />
        <ReadonlyField label={copy.country} value={detail.source.country_code} />
        <ReadonlyField label={copy.productType} value={detail.source.product_type} />
        <ReadonlyField label={copy.productKey} value={detail.source.product_key ?? copy.missing} />
        <ReadonlyField label={copy.sourceName} value={detail.source.source_name} />
        <ReadonlyField label={copy.sourceType} value={detail.source.source_type} />
        <ReadonlyField label={copy.role} value={detail.source.discovery_role} />
        <ReadonlyField label={copy.status} value={detail.source.status} />
        <ReadonlyField label={copy.priority} value={detail.source.priority} />
        <ReadonlyField label={copy.language} value={detail.source.source_language} />
        <ReadonlyField label={copy.purpose} value={detail.source.purpose || copy.missing} />
        <ReadonlyField label={copy.candidateProducing} value={detail.source.candidate_producing_flag ? copy.yes : copy.no} />
        <ReadonlyField className="lg:col-span-2" label={copy.sourceUrl} value={detail.source.source_url} />
        <ReadonlyField className="lg:col-span-2" label={copy.normalizedUrl} value={detail.source.normalized_url} />
        <ReadonlyField className="lg:col-span-2" label={copy.expectedFields} value={detail.source.expected_fields.join(", ") || copy.missing} />
        <ReadonlyField className="lg:col-span-2" label={copy.aliasUrls} value={detail.source.alias_urls.join(", ") || copy.missing} />
        <ReadonlyField className="lg:col-span-2" label={copy.redirectTargetUrl} value={detail.source.redirect_target_url ?? copy.missing} />
        <ReadonlyField className="lg:col-span-2" label={copy.changeReason} value={detail.source.change_reason ?? copy.missing} />
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.discoveryExplainability}</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{copy.promotedTitle}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {copy.promotedDescription}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              {asString(discoveryMetadata.selection_path) ?? copy.selectionPathMissing}
            </span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              {asString(discoveryMetadata.selection_confidence) ?? copy.confidenceMissing}
            </span>
          </div>
        </div>

        {Object.keys(discoveryMetadata).length === 0 ? (
          <p className="mt-6 text-sm leading-6 text-muted-foreground">
            {copy.noMetadata}
          </p>
        ) : (
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <ReadonlyField label={copy.candidateOrigin} value={asString(discoveryMetadata.candidate_origin) ?? copy.missing} />
            <ReadonlyField label={copy.heuristicScore} value={asNumber(discoveryMetadata.heuristic_score) ?? copy.missing} />
            <ReadonlyField label={copy.aiParallelScore} value={asNumber(discoveryMetadata.ai_parallel_score) ?? copy.missing} />
            <ReadonlyField label={copy.aiPredictedRole} value={asString(discoveryMetadata.ai_predicted_role) ?? copy.missing} />
            <ReadonlyField label={copy.aiConfidenceBand} value={asString(discoveryMetadata.ai_confidence_band) ?? copy.missing} />
            <ReadonlyField label={copy.pageEvidenceScore} value={asNumber(discoveryMetadata.page_evidence_score) ?? copy.missing} />
            <ReadonlyField label={copy.primaryHeading} value={asString(discoveryMetadata.primary_heading) ?? copy.missing} />
            <ReadonlyField className="lg:col-span-2" label={copy.pageTitle} value={asString(discoveryMetadata.page_title) ?? copy.missing} />
            <ReadonlyField label={copy.attributeSignalCount} value={asNumber(discoveryMetadata.attribute_signal_count) ?? copy.missing} />
            <ReadonlyField label={copy.negativeSignalCount} value={asNumber(discoveryMetadata.negative_signal_count) ?? copy.missing} />
            <ReadonlyField className="lg:col-span-2" label={copy.aiRationale} value={asString(discoveryMetadata.ai_short_rationale) ?? copy.missing} />
          </div>
        )}

        {selectionReasonCodes.length > 0 ? (
          <TagRow label={copy.selectionReasonCodes} values={selectionReasonCodes} />
        ) : null}
        {aiReasonCodes.length > 0 ? <TagRow label={copy.aiReasonCodes} values={aiReasonCodes} /> : null}
        {pageReasonCodes.length > 0 ? <TagRow label={copy.pageEvidenceCodes} values={pageReasonCodes} /> : null}
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.recentHistory}</p>
        {detail.recent_runs.length === 0 ? (
          <p className="mt-4 text-sm leading-6 text-muted-foreground">{copy.noRecentRuns}</p>
        ) : (
          <div className="mt-4 grid gap-3">
            {detail.recent_runs.map((item) => (
              <div className="rounded-2xl border border-border/80 bg-background p-4" key={item.run_id}>
                <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <Link className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/runs/${item.run_id}`, new URLSearchParams(), locale)}>
                      {item.run_id}
                    </Link>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {item.pipeline_stage || item.trigger_type} {copy.started} {item.started_at ?? copy.missing}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{item.run_status}</span>
                    <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{copy.candidates(item.candidate_count)}</span>
                    <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{copy.reviewQueued(item.review_queued_count)}</span>
                  </div>
                </div>
                {item.error_summary ? <p className="mt-3 text-sm leading-6 text-destructive">{item.error_summary}</p> : null}
              </div>
            ))}
          </div>
        )}
      </article>
    </section>
  );
}

function TagRow({ label, values }: { label: string; values: string[] }) {
  return (
    <div className="mt-4">
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {values.map((value) => (
          <span className="rounded-full bg-info-soft px-2.5 py-1 text-[11px] font-medium text-info" key={`${label}-${value}`}>
            {value}
          </span>
        ))}
      </div>
    </div>
  );
}

function ReadonlyField({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <article className={`rounded-[1.5rem] border border-border/80 bg-card/95 p-5 shadow-sm ${className ?? ""}`}>
      <p className="text-sm font-medium uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-3 break-words text-sm leading-6 text-foreground">{value}</p>
    </article>
  );
}

function asString(value: unknown) {
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim();
  return normalized.length > 0 ? normalized : null;
}

function asNumber(value: unknown) {
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  return null;
}

function asStringArray(value: unknown) {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => (typeof item === "string" ? item.trim() : ""))
    .filter((item) => item.length > 0);
}
