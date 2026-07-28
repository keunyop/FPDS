"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import type { BankItem, ProductTypeItem, SourceCatalogDetailResponse } from "@/lib/admin-api";
import { buildAdminHref, formatAdminDateTimeValue, type AdminLocale } from "@/lib/admin-i18n";
import { buildAdminProductTypeOptions } from "@/lib/admin-product-types";

type SourceCatalogDetailSurfaceProps = {
  bankOptions: BankItem[];
  detail: SourceCatalogDetailResponse;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
  productTypes?: ProductTypeItem[];
};

const DETAIL_COPY = {
  en: {
    path: ["Operations", "Source Catalog", "Coverage detail"],
    description: "Inspect collection coverage and evidence before changing its operating state.",
    back: "Back to source catalog",
    viewSources: "View generated sources",
    coverageId: "Coverage id",
    status: "Status",
    generatedSources: "Generated sources",
    lastCollection: "Last collection",
    active: "Active",
    inactive: "Inactive",
    bank: "Bank",
    productType: "Product type",
    changeReason: "Change reason",
    updateCoverage: "Update coverage",
    saving: "Saving...",
    save: "Save coverage",
    homepage: "Homepage URL",
    sampleSources: "Sample source ids",
    noSources: "No generated sources yet",
    recentHistory: "Recent collection history",
    noRuns: "No collection runs are linked to this coverage yet.",
    run: "Run",
    started: "Started",
    candidates: "Candidates",
    result: "Result",
    missing: "n/a",
    updated: "Source catalog item was updated.",
    updateFailed: "Source catalog item could not be updated.",
    updateApiFailed: "Source catalog item could not be updated. Check the admin API and try again.",
  },
  ko: {
    path: ["운영", "Source Catalog", "Coverage 상세"],
    description: "운영 상태를 변경하기 전에 collection 범위와 근거를 확인합니다.",
    back: "Source catalog로 돌아가기",
    viewSources: "생성 소스 보기",
    coverageId: "Coverage id",
    status: "상태",
    generatedSources: "생성된 소스",
    lastCollection: "최근 collection",
    active: "활성",
    inactive: "비활성",
    bank: "은행",
    productType: "상품 유형",
    changeReason: "변경 사유",
    updateCoverage: "Coverage 변경",
    saving: "저장 중...",
    save: "Coverage 저장",
    homepage: "홈페이지 URL",
    sampleSources: "샘플 source id",
    noSources: "아직 생성된 소스가 없습니다",
    recentHistory: "최근 collection 이력",
    noRuns: "이 coverage와 연결된 collection run이 없습니다.",
    run: "Run",
    started: "시작",
    candidates: "Candidates",
    result: "결과",
    missing: "없음",
    updated: "Source catalog 항목을 업데이트했습니다.",
    updateFailed: "Source catalog 항목을 업데이트할 수 없습니다.",
    updateApiFailed: "Source catalog 항목을 업데이트할 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
  },
  ja: {
    path: ["運用", "Source Catalog", "Coverage 詳細"],
    description: "運用状態を変更する前に collection 範囲と根拠を確認します。",
    back: "Source catalog に戻る",
    viewSources: "生成ソースを見る",
    coverageId: "Coverage id",
    status: "状態",
    generatedSources: "生成済みソース",
    lastCollection: "最新 collection",
    active: "有効",
    inactive: "無効",
    bank: "銀行",
    productType: "商品タイプ",
    changeReason: "変更理由",
    updateCoverage: "Coverage を変更",
    saving: "保存中...",
    save: "Coverage を保存",
    homepage: "ホームページ URL",
    sampleSources: "サンプル source id",
    noSources: "生成済みソースはありません",
    recentHistory: "最近の collection 履歴",
    noRuns: "この coverage に紐づく collection run はありません。",
    run: "Run",
    started: "開始",
    candidates: "Candidates",
    result: "結果",
    missing: "なし",
    updated: "Source catalog 項目を更新しました。",
    updateFailed: "Source catalog 項目を更新できません。",
    updateApiFailed: "Source catalog 項目を更新できません。Admin APIを確認してから再試行してください。",
  },
} as const;

export function SourceCatalogDetailSurface({
  bankOptions,
  detail,
  locale,
  csrfToken,
  productTypes = [],
}: SourceCatalogDetailSurfaceProps) {
  const copy = DETAIL_COPY[locale];
  const router = useRouter();
  const baseProductTypeOptions = buildAdminProductTypeOptions(productTypes);
  const productTypeOptions = baseProductTypeOptions.some(
    (option) => option.value === detail.catalog_item.product_type,
  )
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
  const latestRun = detail.recent_runs[0] ?? null;

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
      const response = await fetch(
        `/admin/source-catalog/${detail.catalog_item.catalog_item_id}/update`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
          },
          body: JSON.stringify(form),
        },
      );
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
    <section
      aria-busy={pending}
      className="grid gap-5"
      data-admin-dirty={formDirty ? "true" : undefined}
    >
      <AdminPageHeader
        actions={
          <>
            <Link
              className="inline-flex h-10 items-center justify-center rounded-md border border-border bg-card px-4 text-sm font-semibold text-foreground transition-colors hover:border-primary hover:text-primary"
              href={buildAdminHref("/admin/source-catalog", new URLSearchParams(), locale)}
            >
              {copy.back}
            </Link>
            <Link
              className="inline-flex h-10 items-center justify-center rounded-md border border-border bg-card px-4 text-sm font-semibold text-foreground transition-colors hover:border-primary hover:text-primary"
              href={buildAdminHref(
                "/admin/sources",
                new URLSearchParams(
                  `bank_code=${detail.catalog_item.bank_code}&product_type=${detail.catalog_item.product_type}`,
                ),
                locale,
              )}
            >
              {copy.viewSources}
            </Link>
          </>
        }
        badges={
          <span
            className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
              detail.catalog_item.status === "active"
                ? "bg-success/10 text-success"
                : "bg-warning/10 text-warning"
            }`}
          >
            {detail.catalog_item.status === "active" ? copy.active : copy.inactive}
          </span>
        }
        description={copy.description}
        path={[...copy.path]}
        title={`${detail.catalog_item.bank_name} · ${detail.catalog_item.product_type}`}
      />

      <dl className="grid overflow-hidden rounded-lg border border-border bg-card md:grid-cols-4">
        <SummaryCell label={copy.coverageId} mono value={detail.catalog_item.catalog_item_id} />
        <SummaryCell
          label={copy.status}
          value={detail.catalog_item.status === "active" ? copy.active : copy.inactive}
        />
        <SummaryCell
          label={copy.generatedSources}
          mono
          value={String(detail.catalog_item.generated_source_count)}
        />
        <SummaryCell
          label={copy.lastCollection}
          value={formatAdminDateTimeValue(latestRun?.started_at, copy.missing)}
        />
      </dl>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(19rem,0.65fr)]">
        <article className="overflow-hidden rounded-lg border border-border bg-card">
          <div className="border-b border-border px-4 py-4">
            <h2 className="text-base font-semibold text-foreground">{copy.recentHistory}</h2>
            <p className="mt-1 break-all text-xs text-muted-foreground">
              {copy.homepage}: {detail.catalog_item.homepage_url ?? copy.missing}
            </p>
          </div>
          {detail.recent_runs.length === 0 ? (
            <p className="px-4 py-10 text-center text-sm text-muted-foreground">{copy.noRuns}</p>
          ) : (
            <div
              aria-label={copy.recentHistory}
              className="overflow-x-auto"
              role="region"
              tabIndex={0}
            >
              <table className="min-w-[720px] table-fixed">
                <thead>
                  <tr className="text-left text-xs text-muted-foreground">
                    <th className="w-[34%] px-4 py-3 font-semibold">{copy.run}</th>
                    <th className="w-[24%] px-4 py-3 font-semibold">{copy.started}</th>
                    <th className="w-[16%] px-4 py-3 font-semibold">{copy.candidates}</th>
                    <th className="px-4 py-3 font-semibold">{copy.result}</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.recent_runs.map((item) => (
                    <tr className="align-top" key={item.run_id}>
                      <td className="border-t border-border px-4 py-3">
                        <Link
                          className="font-mono text-sm font-semibold text-foreground underline-offset-4 hover:text-primary hover:underline"
                          href={buildAdminHref(
                            `/admin/runs/${item.run_id}`,
                            new URLSearchParams(),
                            locale,
                          )}
                        >
                          {item.run_id}
                        </Link>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {item.pipeline_stage || item.trigger_type}
                        </p>
                      </td>
                      <td className="border-t border-border px-4 py-3 text-sm text-muted-foreground">
                        {formatAdminDateTimeValue(item.started_at, copy.missing)}
                      </td>
                      <td className="border-t border-border px-4 py-3 font-mono text-sm text-foreground">
                        {item.candidate_count}
                      </td>
                      <td className="border-t border-border px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${getRunStatusClass(item.run_status)}`}
                        >
                          {item.run_status}
                        </span>
                        {item.error_summary ? (
                          <p className="mt-2 border-l-2 border-destructive pl-2 text-xs leading-5 text-destructive">
                            {item.error_summary}
                          </p>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="border-t border-border px-4 py-3 text-xs text-muted-foreground">
            {copy.sampleSources}:{" "}
            <span className="font-mono text-foreground">
              {detail.sample_source_ids.join(", ") || copy.noSources}
            </span>
          </div>
        </article>

        <article className="self-start rounded-lg border border-border bg-card p-4 xl:sticky xl:top-24">
          <h2 className="text-base font-semibold text-foreground">{copy.updateCoverage}</h2>
          {message ? (
            <p
              aria-live="polite"
              className="mt-4 rounded-md border border-success/25 bg-success/10 px-4 py-3 text-sm text-success"
              role="status"
            >
              {message}
            </p>
          ) : null}
          {error ? (
            <p
              aria-live="assertive"
              className="mt-4 rounded-md border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive"
              role="alert"
            >
              {error}
            </p>
          ) : null}
          <form aria-busy={pending} className="mt-4 grid gap-4" onSubmit={handleSave}>
            <SelectField
              label={copy.bank}
              onChange={(value) => setForm((current) => ({ ...current, bank_code: value }))}
              options={bankOptions.map((option) => ({
                label: option.bank_name,
                value: option.bank_code,
              }))}
              value={form.bank_code}
            />
            <SelectField
              label={copy.productType}
              onChange={(value) =>
                setForm((current) => ({ ...current, product_type: value }))
              }
              options={productTypeOptions}
              value={form.product_type}
            />
            <SelectField
              label={copy.status}
              onChange={(value) => setForm((current) => ({ ...current, status: value }))}
              options={[
                { label: copy.active, value: "active" },
                { label: copy.inactive, value: "inactive" },
              ]}
              value={form.status}
            />
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.changeReason}</span>
              <textarea
                className="min-h-24 rounded-md border border-input bg-card px-3 py-2 text-sm"
                onChange={(event) =>
                  setForm((current) => ({ ...current, change_reason: event.target.value }))
                }
                value={form.change_reason}
              />
            </label>
            <button
              className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={pending || !formDirty}
              type="submit"
            >
              {pending ? copy.saving : copy.save}
            </button>
          </form>
        </article>
      </div>
    </section>
  );
}

function SummaryCell({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="border-b border-border px-4 py-4 last:border-b-0 md:border-b-0 md:border-r md:last:border-r-0">
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd
        className={`mt-1 break-words text-sm font-semibold text-foreground ${mono ? "font-mono" : ""}`}
      >
        {value}
      </dd>
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
      <select
        className="h-10 rounded-md border border-input bg-card px-3 text-sm text-foreground"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
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
