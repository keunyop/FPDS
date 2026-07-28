"use client";

import { Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { DestructiveConfirmDialog } from "@/components/fpds/admin/destructive-confirm-dialog";
import { Button } from "@/components/ui/button";
import type { SourceRegistryDetailResponse } from "@/lib/admin-api";
import { buildAdminHref, formatAdminDateTimeValue, type AdminLocale } from "@/lib/admin-i18n";

type SourceDetailSurfaceProps = {
  detail: SourceRegistryDetailResponse;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
  userRole: string;
};

const SOURCE_DETAIL_EN_COPY = {
  back: "Back to sources",
  openUrl: "Open source URL",
  description: "Generated source metadata and collection history.",
  path: ["Operations", "Sources", "Source Detail"],
  bank: "Bank",
  country: "Country",
  productType: "Product type",
  productKey: "Product key",
  sourceName: "Source name",
  sourceType: "Source type",
  role: "Role",
  status: "Status",
  language: "Language",
  purpose: "Purpose",
  candidateProducing: "Candidate-producing",
  sourceUrl: "Source URL",
  normalizedUrl: "Normalized URL",
  discoveryExplainability: "Discovery explainability",
  promotedTitle: "Why this source was promoted",
  promotedDescription: "Bounded discovery scoring and selection signals.",
  selectionPathMissing: "selection path n/a",
  confidenceMissing: "confidence n/a",
  noMetadata: "No discovery explainability metadata was persisted for this source.",
  aiPredictedRole: "AI predicted role",
  aiConfidenceBand: "AI confidence band",
  pageTitle: "Page title",
  aiRationale: "AI rationale",
  recentHistory: "Recent collection history",
  noRecentRuns: "No recent collection runs were linked to this source yet.",
  lastVerified: "Last verified",
  lastSeen: "Last seen",
  updated: "Updated",
  started: "started",
  candidates: (count: number) => `${count} candidates`,
  reviewQueued: (count: number) => `${count} review queued`,
  yes: "yes",
  no: "no",
  missing: "n/a",
  deleting: "Removing...",
  removeSource: "Remove source",
  removeFailed: "Source detail could not be removed.",
  removeApiFailed: "Source detail could not be removed. Check the admin API and try again.",
  removeDescription: "This marks the source as removed, keeps the audit trail, and prevents the row from being selected for collection. It does not delete historical run or candidate records.",
  removeTitle: (sourceId: string) => `Remove ${sourceId}?`,
} as const;

const SOURCE_DETAIL_COPY = {
  en: SOURCE_DETAIL_EN_COPY,
  ko: {
    back: "소스 목록으로",
    openUrl: "소스 URL 열기",
    description: "생성된 소스 메타데이터와 수집 이력을 확인합니다.",
    path: ["운영", "소스", "소스 상세"],
    bank: "은행",
    country: "국가",
    productType: "상품 유형",
    productKey: "상품 키",
    sourceName: "소스명",
    sourceType: "소스 유형",
    role: "역할",
    status: "상태",
    language: "언어",
    purpose: "용도",
    candidateProducing: "후보 생성 여부",
    sourceUrl: "소스 URL",
    normalizedUrl: "정규화 URL",
    discoveryExplainability: "탐색 근거",
    promotedTitle: "이 소스가 승격된 이유",
    promotedDescription: "제한된 탐색 점수와 선택 신호입니다.",
    selectionPathMissing: "선택 경로 없음",
    confidenceMissing: "신뢰도 없음",
    noMetadata: "이 소스에 저장된 탐색 근거 메타데이터가 없습니다.",
    aiPredictedRole: "AI 예측 역할",
    aiConfidenceBand: "AI 신뢰 구간",
    pageTitle: "페이지 제목",
    aiRationale: "AI 판단 근거",
    recentHistory: "최근 수집 이력",
    noRecentRuns: "이 소스에 연결된 최근 수집 실행이 없습니다.",
    lastVerified: "최근 검증",
    lastSeen: "최근 관측",
    updated: "수정 시각",
    started: "시작",
    candidates: (count: number) => `후보 ${count.toLocaleString("ko-KR")}건`,
    reviewQueued: (count: number) => `검토 대기 ${count.toLocaleString("ko-KR")}건`,
    yes: "예",
    no: "아니요",
    missing: "없음",
    deleting: "제거 중...",
    removeSource: "소스 제거",
    removeFailed: "소스를 제거하지 못했습니다.",
    removeApiFailed: "소스를 제거하지 못했습니다. Admin API를 확인하고 다시 시도하세요.",
    removeDescription: "소스를 제거됨 상태로 표시하고 감사 이력을 유지하며 향후 수집 대상에서 제외합니다. 과거 실행 또는 후보 기록은 삭제하지 않습니다.",
    removeTitle: (sourceId: string) => `${sourceId} 소스를 제거할까요?`,
  },
  ja: {
    back: "ソース一覧へ",
    openUrl: "ソース URL を開く",
    description: "生成されたソースメタデータと収集履歴を確認します。",
    path: ["運用", "ソース", "ソース詳細"],
    bank: "銀行",
    country: "国",
    productType: "商品タイプ",
    productKey: "商品キー",
    sourceName: "ソース名",
    sourceType: "ソースタイプ",
    role: "役割",
    status: "状態",
    language: "言語",
    purpose: "用途",
    candidateProducing: "候補生成",
    sourceUrl: "ソース URL",
    normalizedUrl: "正規化 URL",
    discoveryExplainability: "探索根拠",
    promotedTitle: "このソースが昇格された理由",
    promotedDescription: "制約された探索スコアと選択シグナルです。",
    selectionPathMissing: "選択経路なし",
    confidenceMissing: "信頼度なし",
    noMetadata: "このソースには探索根拠メタデータが保存されていません。",
    aiPredictedRole: "AI 予測役割",
    aiConfidenceBand: "AI 信頼度帯",
    pageTitle: "ページタイトル",
    aiRationale: "AI 判断根拠",
    recentHistory: "最近の収集履歴",
    noRecentRuns: "このソースに関連する最近の収集実行はありません。",
    lastVerified: "最終検証",
    lastSeen: "最終観測",
    updated: "更新日時",
    started: "開始",
    candidates: (count: number) => `候補 ${count.toLocaleString("ja-JP")} 件`,
    reviewQueued: (count: number) => `レビュー待ち ${count.toLocaleString("ja-JP")} 件`,
    yes: "はい",
    no: "いいえ",
    missing: "なし",
    deleting: "削除中...",
    removeSource: "ソースを削除",
    removeFailed: "ソースを削除できませんでした。",
    removeApiFailed: "ソースを削除できませんでした。Admin API を確認して再試行してください。",
    removeDescription: "ソースを削除済みにして監査履歴を保持し、今後の収集対象から除外します。過去の実行や候補記録は削除しません。",
    removeTitle: (sourceId: string) => `${sourceId} を削除しますか？`,
  },
};

export function SourceDetailSurface({ detail, locale, csrfToken, userRole }: SourceDetailSurfaceProps) {
  const copy = SOURCE_DETAIL_COPY[locale];
  const router = useRouter();
  const discoveryMetadata = detail.source.discovery_metadata ?? {};
  const [pendingDelete, setPendingDelete] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const canDelete = userRole.toLowerCase() === "admin" && detail.source.status !== "removed";

  async function handleDelete() {
    setPendingDelete(true);
    document.body.dataset.adminMutationPending = "true";
    setError(null);

    try {
      const response = await fetch(`/admin/sources/${encodeURIComponent(detail.source.source_id)}/delete`, {
        method: "DELETE",
        headers: {
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
      });
      const payload = (await response.json()) as { error?: { message?: string } };
      if (!response.ok) {
        setError(payload.error?.message ?? copy.removeFailed);
        setDeleteDialogOpen(false);
        return;
      }
      setDeleteDialogOpen(false);
      router.push(buildAdminHref("/admin/sources", new URLSearchParams(), locale), { scroll: false });
      router.refresh();
    } catch {
      setError(copy.removeApiFailed);
      setDeleteDialogOpen(false);
    } finally {
      setPendingDelete(false);
      delete document.body.dataset.adminMutationPending;
    }
  }

  return (
    <section aria-busy={pendingDelete} className="grid gap-5">
      <AdminPageHeader
        actions={
          <>
            {canDelete ? (
              <Button disabled={pendingDelete} onClick={() => setDeleteDialogOpen(true)} type="button" variant="destructive">
                <Trash2 className="size-4" />
                {pendingDelete ? copy.deleting : copy.removeSource}
              </Button>
            ) : null}
            <Button asChild variant="outline">
              <Link href={buildAdminHref("/admin/sources", new URLSearchParams(), locale)}>{copy.back}</Link>
            </Button>
            <Button asChild>
              <a href={detail.source.source_url} rel="noreferrer" target="_blank">
                {copy.openUrl}
              </a>
            </Button>
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

      {error ? <p aria-live="assertive" className="border-l-4 border-destructive bg-destructive/10 px-4 py-3 text-sm text-destructive" role="alert">{error}</p> : null}

      <article className="grid gap-4 lg:grid-cols-2">
        <ReadonlyField label={copy.bank} value={detail.source.bank_code} />
        <ReadonlyField label={copy.country} value={detail.source.country_code} />
        <ReadonlyField label={copy.productType} value={detail.source.product_type} />
        <ReadonlyField label={copy.sourceName} value={detail.source.source_name} />
        <ReadonlyField label={copy.sourceType} value={detail.source.source_type} />
        <ReadonlyField label={copy.role} value={detail.source.discovery_role} />
        <ReadonlyField label={copy.status} value={detail.source.status} />
        <ReadonlyField label={copy.language} value={detail.source.source_language} />
        <ReadonlyField label={copy.purpose} value={detail.source.purpose || copy.missing} />
        <ReadonlyField label={copy.candidateProducing} value={detail.source.candidate_producing_flag ? copy.yes : copy.no} />
        <ReadonlyField label={copy.lastVerified} value={formatSourceDateTime(detail.source.last_verified_at, copy.missing)} />
        <ReadonlyField label={copy.lastSeen} value={formatSourceDateTime(detail.source.last_seen_at, copy.missing)} />
        <ReadonlyField label={copy.productKey} value={detail.source.product_key ?? copy.missing} />
        <ReadonlyField label={copy.updated} value={formatSourceDateTime(detail.source.updated_at, copy.missing)} />
        <ReadonlyField className="lg:col-span-2" label={copy.sourceUrl} value={detail.source.source_url} />
        <ReadonlyField className="lg:col-span-2" label={copy.normalizedUrl} value={detail.source.normalized_url} />
      </article>

      <article className="border border-border bg-card p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-xs font-medium text-muted-foreground">{copy.discoveryExplainability}</p>
            <h2 className="mt-1 text-lg font-semibold tracking-tight text-foreground">{copy.promotedTitle}</h2>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">{copy.promotedDescription}</p>
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
          <p className="mt-6 text-sm leading-6 text-muted-foreground">{copy.noMetadata}</p>
        ) : (
          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            <ReadonlyField label={copy.aiPredictedRole} value={asString(discoveryMetadata.ai_predicted_role) ?? copy.missing} />
            <ReadonlyField label={copy.aiConfidenceBand} value={asString(discoveryMetadata.ai_confidence_band) ?? copy.missing} />
            <ReadonlyField className="lg:col-span-2" label={copy.pageTitle} value={asString(discoveryMetadata.page_title) ?? asString(discoveryMetadata.primary_heading) ?? copy.missing} />
            <ReadonlyField className="lg:col-span-2" label={copy.aiRationale} value={asString(discoveryMetadata.ai_short_rationale) ?? copy.missing} />
          </div>
        )}
      </article>

      <article className="border border-border bg-card p-5">
        <h2 className="text-lg font-semibold text-foreground">{copy.recentHistory}</h2>
        {detail.recent_runs.length === 0 ? (
          <p className="mt-4 text-sm leading-6 text-muted-foreground">{copy.noRecentRuns}</p>
        ) : (
          <div className="mt-4 divide-y divide-border border-y border-border">
            {detail.recent_runs.map((item) => (
              <div className="py-4" key={item.run_id}>
                <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <Link className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/runs/${item.run_id}`, new URLSearchParams(), locale)}>
                      {item.run_id}
                    </Link>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {item.pipeline_stage || item.trigger_type} {copy.started} {formatSourceDateTime(item.started_at, copy.missing)}
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

      <DestructiveConfirmDialog
        confirmLabel={copy.removeSource}
        description={copy.removeDescription}
        onConfirm={handleDelete}
        onOpenChange={setDeleteDialogOpen}
        open={deleteDialogOpen}
        pending={pendingDelete}
        pendingLabel={copy.deleting}
        title={copy.removeTitle(detail.source.source_id)}
      />
    </section>
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
    <article className={`min-w-0 border border-border bg-card p-4 ${className ?? ""}`}>
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 break-words font-mono text-sm leading-6 text-foreground">{value}</p>
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

function formatSourceDateTime(value: string | null, missing: string) {
  return formatAdminDateTimeValue(value, missing, { seconds: true });
}
