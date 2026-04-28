"use client";

import Link from "next/link";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import type { SourceRegistryListResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

export type SourceRegistryPageFilters = {
  q: string;
  bankCode: string;
  countryCode: string;
  productType: string;
  status: string;
  discoveryRole: string;
};

type SourceRegistrySurfaceProps = {
  filters: SourceRegistryPageFilters;
  registry: SourceRegistryListResponse;
  locale: AdminLocale;
};

const SOURCE_COPY = {
  en: {
    manageBanks: "Manage banks",
    description: "Generated source rows for inspection.",
    path: ["Operations", "Sources"],
    title: "Sources",
    visibleSources: "Visible sources",
    candidateProducing: "Candidate-producing",
    active: "Active",
    detailRole: "Detail role",
    search: "Search",
    searchPlaceholder: "source id, name, or URL",
    bank: "Bank",
    country: "Country",
    productType: "Product type",
    status: "Status",
    role: "Role",
    apply: "Apply",
    reset: "Reset",
    generatedSourceDetail: "Generated source detail",
    source: "Source",
    product: "Product",
    type: "Type",
    url: "URL",
    updated: "Updated",
    all: "All",
    noRows: "No source rows matched the current filter set.",
    missing: "n/a",
  },
  ko: {
    manageBanks: "은행 관리",
    description: "검토할 생성 source row입니다.",
    path: ["운영", "소스"],
    title: "소스",
    visibleSources: "표시된 소스",
    candidateProducing: "Candidate 생성",
    active: "활성",
    detailRole: "Detail 역할",
    search: "검색",
    searchPlaceholder: "source id, 이름 또는 URL",
    bank: "은행",
    country: "국가",
    productType: "상품 유형",
    status: "상태",
    role: "역할",
    apply: "적용",
    reset: "초기화",
    generatedSourceDetail: "생성 source 상세",
    source: "소스",
    product: "상품",
    type: "유형",
    url: "URL",
    updated: "업데이트",
    all: "전체",
    noRows: "현재 필터에 맞는 source row가 없습니다.",
    missing: "없음",
  },
  ja: {
    manageBanks: "銀行を管理",
    description: "確認用に生成された source row です。",
    path: ["運用", "ソース"],
    title: "ソース",
    visibleSources: "表示中のソース",
    candidateProducing: "Candidate 生成",
    active: "有効",
    detailRole: "Detail ロール",
    search: "検索",
    searchPlaceholder: "source id、名前、URL",
    bank: "銀行",
    country: "国",
    productType: "商品タイプ",
    status: "状態",
    role: "ロール",
    apply: "適用",
    reset: "リセット",
    generatedSourceDetail: "生成 source 詳細",
    source: "ソース",
    product: "商品",
    type: "タイプ",
    url: "URL",
    updated: "更新",
    all: "すべて",
    noRows: "現在のフィルターに該当する source row はありません。",
    missing: "なし",
  },
} as const;

export function SourceRegistrySurface({ filters, registry, locale }: SourceRegistrySurfaceProps) {
  const copy = SOURCE_COPY[locale];
  return (
    <section className="grid min-w-0 gap-6">
      <AdminPageHeader
        actions={
          <>
            <Link className="rounded-full border border-border px-4 py-2 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/banks", new URLSearchParams(), locale)}>
              {copy.manageBanks}
            </Link>
          </>
        }
        description={copy.description}
        path={copy.path}
        title={copy.title}
      />

      <article className="grid min-w-0 gap-4 md:grid-cols-4">
        <StatCard label={copy.visibleSources} value={String(registry.summary.total_items)} />
        <StatCard label={copy.candidateProducing} value={String(registry.summary.candidate_producing_items)} />
        <StatCard label={copy.active} value={String(registry.summary.status_counts.active ?? 0)} />
        <StatCard label={copy.detailRole} value={String(registry.summary.role_counts.detail ?? 0)} />
      </article>

      <article className="min-w-0 rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <form action={buildAdminHref("/admin/sources", new URLSearchParams(), locale)} className="grid min-w-0 gap-4 lg:grid-cols-[1.4fr_repeat(5,minmax(0,1fr))_auto]">
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">{copy.search}</span>
            <input className="h-10 min-w-0 rounded-xl border border-border bg-background px-3 text-sm" defaultValue={filters.q} name="q" placeholder={copy.searchPlaceholder} type="search" />
          </label>
          <FilterSelect allLabel={copy.all} defaultValue={filters.bankCode} label={copy.bank} name="bank_code" options={registry.facets.bank_codes} />
          <FilterSelect allLabel={copy.all} defaultValue={filters.countryCode} label={copy.country} name="country_code" options={["CA"]} />
          <FilterSelect allLabel={copy.all} defaultValue={filters.productType} label={copy.productType} name="product_type" options={registry.facets.product_types} />
          <FilterSelect allLabel={copy.all} defaultValue={filters.status} label={copy.status} name="status" options={registry.facets.statuses} />
          <FilterSelect allLabel={copy.all} defaultValue={filters.discoveryRole} label={copy.role} name="discovery_role" options={registry.facets.discovery_roles} />
          <div className="flex items-end gap-2">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" type="submit">
              {copy.apply}
            </button>
            <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/sources", new URLSearchParams(), locale)}>
              {copy.reset}
            </Link>
          </div>
        </form>
      </article>

      <article className="min-w-0 overflow-hidden rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="border-b border-border/80 px-6 py-5">
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.generatedSourceDetail}</p>
        </div>

        <div className="max-w-full overflow-x-auto px-6 py-5">
          <table className="min-w-[1080px] table-fixed border-separate border-spacing-0">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                <th className="border-b border-border px-3 py-3 font-medium">{copy.source}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.bank}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.product}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.role}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.status}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.type}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.url}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.updated}</th>
              </tr>
            </thead>
            <tbody>
              {registry.items.length === 0 ? (
                <tr>
                  <td className="px-3 py-8 text-sm text-muted-foreground" colSpan={8}>
                    {copy.noRows}
                  </td>
                </tr>
              ) : (
                registry.items.map((item) => (
                  <tr className="align-top text-sm" key={item.source_id}>
                    <td className="border-b border-border/70 px-3 py-4">
                      <Link className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/sources/${item.source_id}`, new URLSearchParams(), locale)}>
                        {item.source_id}
                      </Link>
                      <p className="mt-1 break-words text-sm text-muted-foreground">{item.source_name}</p>
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.bank_code}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.product_type}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.discovery_role}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.status}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.source_type}</td>
                    <td className="border-b border-border/70 px-3 py-4">
                      <a className="line-clamp-2 break-all text-primary underline-offset-4 hover:underline" href={item.source_url} rel="noreferrer" target="_blank">
                        {item.source_url}
                      </a>
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-muted-foreground">{item.updated_at ?? copy.missing}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}

function FilterSelect({
  allLabel,
  defaultValue,
  label,
  name,
  options,
}: {
  allLabel: string;
  defaultValue: string;
  label: string;
  name: string;
  options: string[];
}) {
  return (
    <label className="grid min-w-0 gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <select className="h-10 min-w-0 rounded-xl border border-border bg-background px-3 text-sm text-foreground" defaultValue={defaultValue} name={name}>
        <option value="">{allLabel}</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="min-w-0 rounded-lg border border-border/80 bg-white p-4">
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{value}</p>
    </article>
  );
}
