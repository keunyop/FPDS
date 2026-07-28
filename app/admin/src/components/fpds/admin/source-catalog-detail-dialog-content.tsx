"use client";

import Link from "next/link";
import { FileText } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, FieldLabel } from "@/components/ui/field";
import { InputGroup, InputGroupAddon, InputGroupTextarea } from "@/components/ui/input-group";
import type { ProductTypeItem, SourceCatalogDetailResponse } from "@/lib/admin-api";
import { buildAdminHref, formatAdminDateTimeValue, type AdminLocale } from "@/lib/admin-i18n";
import { buildAdminProductTypeOptions } from "@/lib/admin-product-types";

type SourceCatalogDetailDialogContentProps = {
  bankOptions: Array<{ bank_code: string; bank_name: string }>;
  detail: SourceCatalogDetailResponse;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
  productTypes?: ProductTypeItem[];
};

const STATUS_OPTIONS = [
  { label: "active", value: "active" },
  { label: "inactive", value: "inactive" },
] as const;

const DETAIL_CATALOG_COPY = {
  en: {
    catalogItemId: "Catalog item id",
    generatedSources: "Generated sources",
    lastCollection: "Last collection",
    homepageUrl: "Homepage URL",
    sampleSourceIds: "Sample source ids",
    noGeneratedSources: "No generated sources yet",
    bank: "Bank",
    productType: "Product type",
    status: "Status",
    changeReason: "Change reason",
    placeholder: "Why was this coverage updated?",
    viewGeneratedSources: "View generated sources",
    saving: "Saving...",
    saveCoverage: "Save coverage",
    recentHistory: "Recent collection history",
    noRecentRuns: "No collection runs were linked to this coverage yet.",
    started: "started",
    candidates: (count: number) => `${count} candidates`,
    showingLatest: "Showing the latest 3 runs here. Open a run detail to inspect older collection history.",
    updateFailed: "Source catalog item could not be updated.",
    updateApiFailed: "Source catalog item could not be updated. Check the admin API and try again.",
    updated: "Source catalog item was updated.",
    active: "Active",
    inactive: "Inactive",
    missing: "n/a",
  },
  ko: {
    catalogItemId: "Catalog item id",
    generatedSources: "생성된 소스",
    lastCollection: "최근 collection",
    homepageUrl: "홈페이지 URL",
    sampleSourceIds: "샘플 source id",
    noGeneratedSources: "아직 생성된 소스가 없습니다",
    bank: "은행",
    productType: "상품 유형",
    status: "상태",
    changeReason: "변경 사유",
    placeholder: "이 coverage를 변경한 이유",
    viewGeneratedSources: "생성 소스 보기",
    saving: "저장 중...",
    saveCoverage: "Coverage 저장",
    recentHistory: "최근 collection 이력",
    noRecentRuns: "아직 이 coverage와 연결된 collection run이 없습니다.",
    started: "시작",
    candidates: (count: number) => `candidate ${count}개`,
    showingLatest: "여기에는 최근 3개 run만 표시합니다. 이전 collection 이력은 run 상세에서 확인하세요.",
    updateFailed: "Source catalog 항목을 업데이트할 수 없습니다.",
    updateApiFailed: "Source catalog 항목을 업데이트할 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    updated: "Source catalog 항목이 업데이트되었습니다.",
    active: "활성",
    inactive: "비활성",
    missing: "없음",
  },
  ja: {
    catalogItemId: "Catalog item id",
    generatedSources: "生成済みソース",
    lastCollection: "最新 collection",
    homepageUrl: "ホームページURL",
    sampleSourceIds: "サンプル source id",
    noGeneratedSources: "生成済みソースはまだありません",
    bank: "銀行",
    productType: "商品タイプ",
    status: "状態",
    changeReason: "変更理由",
    placeholder: "この coverage を更新した理由",
    viewGeneratedSources: "生成ソースを見る",
    saving: "保存中...",
    saveCoverage: "Coverage を保存",
    recentHistory: "最近の collection 履歴",
    noRecentRuns: "この coverage に紐づく collection run はまだありません。",
    started: "開始",
    candidates: (count: number) => `candidate ${count} 件`,
    showingLatest: "ここでは最新3件の run を表示しています。以前の collection 履歴は run 詳細で確認してください。",
    updateFailed: "Source catalog 項目を更新できません。",
    updateApiFailed: "Source catalog 項目を更新できません。Admin APIを確認してから再試行してください。",
    updated: "Source catalog 項目を更新しました。",
    active: "有効",
    inactive: "無効",
    missing: "なし",
  },
} as const;

export function SourceCatalogDetailDialogContent({
  bankOptions,
  detail,
  locale,
  csrfToken,
  productTypes = [],
}: SourceCatalogDetailDialogContentProps) {
  const copy = DETAIL_CATALOG_COPY[locale];
  const router = useRouter();
  const baseProductTypeOptions = buildAdminProductTypeOptions(productTypes);
  const productTypeOptions = baseProductTypeOptions.some((option) => option.value === detail.catalog_item.product_type)
    ? baseProductTypeOptions
    : [
        ...baseProductTypeOptions,
        {
          label: detail.catalog_item.product_type,
          value: detail.catalog_item.product_type,
          description: "",
        },
      ];
  const [form, setForm] = useState({
    bank_code: detail.catalog_item.bank_code,
    product_type: detail.catalog_item.product_type,
    status: detail.catalog_item.status,
    change_reason: detail.catalog_item.change_reason ?? "",
  });
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const formDirty =
    form.bank_code !== detail.catalog_item.bank_code ||
    form.product_type !== detail.catalog_item.product_type ||
    form.status !== detail.catalog_item.status ||
    form.change_reason !== (detail.catalog_item.change_reason ?? "");

  useEffect(() => {
    if (pending) {
      document.body.dataset.adminMutationPending = "true";
    } else {
      delete document.body.dataset.adminMutationPending;
    }

    return () => {
      delete document.body.dataset.adminMutationPending;
    };
  }, [pending]);

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch(`/admin/source-catalog/${detail.catalog_item.catalog_item_id}/update`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify(form),
      });
      const payload = (await response.json()) as { error?: { message?: string } };
      if (!response.ok) {
        setError(payload.error?.message ?? copy.updateFailed);
        return;
      }
      setMessage(copy.updated);
      router.refresh();
    } catch {
      setError(copy.updateApiFailed);
    } finally {
      setPending(false);
    }
  }

  return (
    <div
      aria-busy={pending}
      className="space-y-4 lg:grid lg:grid-cols-[minmax(0,1.15fr)_minmax(18rem,0.85fr)] lg:gap-5 lg:space-y-0"
      data-admin-dirty={formDirty ? "true" : undefined}
    >
      <div className="space-y-4">
        <dl className="grid overflow-hidden rounded-lg border border-border sm:grid-cols-2">
          <ReadonlySummary label={copy.catalogItemId} value={detail.catalog_item.catalog_item_id} />
          <ReadonlySummary label={copy.status} value={formatStatus(locale, detail.catalog_item.status)} />
          <ReadonlySummary label={copy.generatedSources} value={String(detail.catalog_item.generated_source_count)} />
          <ReadonlySummary label={copy.lastCollection} value={formatAdminDateTimeValue(detail.recent_runs[0]?.started_at, copy.missing)} />
          <ReadonlySummary label={copy.homepageUrl} value={detail.catalog_item.homepage_url ?? copy.missing} />
          <ReadonlySummary label={copy.sampleSourceIds} value={detail.sample_source_ids.join(", ") || copy.noGeneratedSources} />
        </dl>

        {message ? <p aria-live="polite" className="rounded-md border border-success/25 bg-success/10 px-4 py-3 text-sm text-success" role="status">{message}</p> : null}
        {error ? <p aria-live="assertive" className="rounded-md border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive" role="alert">{error}</p> : null}

        <form aria-busy={pending} className="space-y-4 border-t border-border pt-4" onSubmit={handleSave}>
          <div className="grid gap-4 lg:grid-cols-3">
            <SelectField
              label={copy.bank}
              options={bankOptions.map((option) => ({ label: option.bank_name, value: option.bank_code }))}
              value={form.bank_code}
              onChange={(value) => setForm((current) => ({ ...current, bank_code: value }))}
            />
            <SelectField
              label={copy.productType}
              options={productTypeOptions}
              value={form.product_type}
              onChange={(value) => setForm((current) => ({ ...current, product_type: value }))}
            />
            <SelectField
              label={copy.status}
              options={STATUS_OPTIONS.map((option) => ({ ...option, label: formatStatus(locale, option.value) }))}
              value={form.status}
              onChange={(value) => setForm((current) => ({ ...current, status: value }))}
            />
          </div>

          <Field data-invalid={Boolean(error)}>
            <FieldLabel>{copy.changeReason}</FieldLabel>
            <InputGroup className="min-h-20 items-start">
              <InputGroupAddon align="block-start">
                <FileText aria-hidden="true" className="size-4" />
              </InputGroupAddon>
              <InputGroupTextarea
                aria-invalid={Boolean(error)}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    change_reason: event.target.value,
                  }))
                }
                placeholder={copy.placeholder}
                rows={2}
                value={form.change_reason}
              />
            </InputGroup>
          </Field>

          <div className="flex flex-col gap-3 sm:flex-row sm:justify-between">
            <Link
              className="inline-flex h-10 items-center justify-center rounded-md border border-border px-4 text-sm font-semibold text-foreground transition-colors hover:border-primary hover:text-primary"
              href={buildAdminHref("/admin/sources", new URLSearchParams(`bank_code=${detail.catalog_item.bank_code}&product_type=${detail.catalog_item.product_type}`), locale)}
            >
              {copy.viewGeneratedSources}
            </Link>
            <Button disabled={pending} type="submit">
              {pending ? copy.saving : copy.saveCoverage}
            </Button>
          </div>
        </form>
      </div>

      <section className="overflow-hidden rounded-lg border border-border bg-card" aria-labelledby="catalog-recent-history">
        <div className="border-b border-border px-4 py-3">
          <h2 className="text-sm font-semibold text-foreground" id="catalog-recent-history">{copy.recentHistory}</h2>
        </div>
        {detail.recent_runs.length === 0 ? (
          <p className="px-4 py-6 text-sm leading-6 text-muted-foreground">{copy.noRecentRuns}</p>
        ) : (
          <div>
            {detail.recent_runs.slice(0, 3).map((item) => (
              <div className="border-b border-border px-4 py-3 last:border-b-0" key={item.run_id}>
                <div className="flex flex-col gap-2">
                  <div>
                    <Link className="font-mono text-sm font-semibold text-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/runs/${item.run_id}`, new URLSearchParams(), locale)}>
                      {item.run_id}
                    </Link>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {item.pipeline_stage || item.trigger_type} {copy.started} {formatAdminDateTimeValue(item.started_at, copy.missing)}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${getRunStatusClass(item.run_status)}`}>{item.run_status}</span>
                    <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">{copy.candidates(item.candidate_count)}</span>
                  </div>
                </div>
                {item.error_summary ? <p className="mt-3 border-l-2 border-destructive pl-3 text-sm leading-6 text-destructive">{item.error_summary}</p> : null}
              </div>
            ))}
          </div>
        )}
        {detail.recent_runs.length > 3 ? (
          <p className="border-t border-border px-4 py-3 text-xs leading-5 text-muted-foreground">
            {copy.showingLatest}
          </p>
        ) : null}
      </section>
    </div>
  );
}

function formatStatus(locale: AdminLocale, value: string) {
  if (value === "active") {
    return DETAIL_CATALOG_COPY[locale].active;
  }
  if (value === "inactive") {
    return DETAIL_CATALOG_COPY[locale].inactive;
  }
  return value;
}

function ReadonlySummary({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-b border-border px-4 py-3 last:border-b-0 sm:border-r sm:[&:nth-child(2n)]:border-r-0 sm:[&:nth-last-child(-n+2)]:border-b-0">
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-1 break-words font-mono text-sm font-medium leading-6 text-foreground">{value}</dd>
    </div>
  );
}

function SelectField({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: ReadonlyArray<{ label: string; value: string }>;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <select className="h-10 rounded-md border border-input bg-card px-3 text-sm text-foreground" onChange={(event) => onChange(event.target.value)} value={value}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function getRunStatusClass(status: string) {
  const normalized = status.toLowerCase();
  if (normalized === "completed" || normalized === "succeeded" || normalized === "success") {
    return "bg-success/10 text-success";
  }
  if (normalized === "failed" || normalized === "error") {
    return "bg-destructive/10 text-destructive";
  }
  if (normalized === "partial" || normalized === "timed_out" || normalized === "timeout") {
    return "bg-warning/10 text-warning";
  }
  return "bg-info/10 text-info";
}
