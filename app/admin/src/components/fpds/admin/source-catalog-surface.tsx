"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { OfferModal4 } from "@/components/offer-modal4";
import { SourceCatalogCreateDialogContent } from "@/components/fpds/admin/source-catalog-create-dialog-content";
import { SourceCatalogDetailDialogContent } from "@/components/fpds/admin/source-catalog-detail-dialog-content";
import type {
  SourceCatalogCollectionLaunchResponse,
  SourceCatalogDetailResponse,
  SourceCatalogItem,
  SourceCatalogListResponse,
} from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

export type SourceCatalogPageFilters = {
  q: string;
  bankCode: string;
  productType: string;
  status: string;
};

type SourceCatalogSurfaceProps = {
  catalog: SourceCatalogListResponse;
  filters: SourceCatalogPageFilters;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
  activeCatalogItemId: string | null;
  activeCatalogDetail: SourceCatalogDetailResponse | null;
  addModalOpen: boolean;
};

const CATALOG_COPY = {
  en: {
    addCoverage: "Add coverage",
    viewGeneratedSources: "View generated sources",
    description: "Coverage setup and collection launch.",
    path: ["Operations", "Source Catalog"],
    title: "Source Catalog",
    catalogItems: "Catalog items",
    generatedSources: "Generated sources",
    active: "Active",
    selected: "Selected",
    search: "Search",
    searchPlaceholder: "bank or catalog item id",
    bank: "Bank",
    productType: "Product type",
    status: "Status",
    apply: "Apply",
    reset: "Reset",
    coverageList: "Coverage list",
    launching: "Launching...",
    collectSelected: (count: number) => `Collect selected (${count})`,
    select: "Select",
    homepage: "Homepage",
    noRows: "No source catalog items matched the current filter set.",
    missing: "n/a",
    coverageSetup: "Coverage setup",
    currentScope: "Current scope",
    catalogItemCount: (count: number) => `${count} catalog items`,
    sourceCatalogWorkflow: "Source catalog workflow",
    activeCoverage: "Active coverage",
    inactiveCoverage: "Inactive coverage",
    recentRuns: "Recent runs",
    coverageDetail: "Coverage detail",
    detailLoadFailed: "Source catalog detail could not be loaded.",
    detailLoadApiFailed: "Source catalog detail could not be loaded. Check the admin API and try again.",
    selectFirst: "Select at least one source catalog item before starting collection.",
    collectFailed: "Collection could not be launched.",
    collectApiFailed: "Collection could not be launched. Check the admin API and try again.",
    queued: (count: number) => `Queued collection for ${count} catalog item(s).`,
    queuedDetail: (count: number) =>
      `${count} run(s) were created immediately, and homepage discovery plus source collection will continue on the server in the background.`,
    openRuns:
      "Open Runs after a short refresh to inspect no-detail, timeout, or collection outcomes.",
    noDetail: (count: number) =>
      `Homepage discovery completed for ${count} catalog item(s), but no detail sources were identified for collection.`,
    materialized: (count: number) => `Materialized ${count} source row(s).`,
    launched: (count: number) => `Collection launched for ${count} catalog item(s).`,
    produced: (ready: number, noDetail: number) =>
      `${ready} catalog item(s) produced detail sources${noDetail > 0 ? ` and ${noDetail} did not` : ""}.`,
    all: "All",
  },
  ko: {
    addCoverage: "Coverage 추가",
    viewGeneratedSources: "생성 소스 보기",
    description: "Coverage 설정과 collection 실행.",
    path: ["운영", "Source Catalog"],
    title: "Source Catalog",
    catalogItems: "Catalog 항목",
    generatedSources: "생성된 소스",
    active: "활성",
    selected: "선택됨",
    search: "검색",
    searchPlaceholder: "은행 또는 catalog item id",
    bank: "은행",
    productType: "상품 유형",
    status: "상태",
    apply: "적용",
    reset: "초기화",
    coverageList: "Coverage 목록",
    launching: "실행 중...",
    collectSelected: (count: number) => `선택 항목 Collect (${count})`,
    select: "선택",
    homepage: "홈페이지",
    noRows: "현재 필터에 맞는 source catalog 항목이 없습니다.",
    missing: "없음",
    coverageSetup: "Coverage 설정",
    currentScope: "현재 범위",
    catalogItemCount: (count: number) => `catalog 항목 ${count}개`,
    sourceCatalogWorkflow: "Source catalog workflow",
    activeCoverage: "활성 coverage",
    inactiveCoverage: "비활성 coverage",
    recentRuns: "최근 runs",
    coverageDetail: "Coverage 상세",
    detailLoadFailed: "Source catalog 상세를 불러올 수 없습니다.",
    detailLoadApiFailed: "Source catalog 상세를 불러올 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    selectFirst: "Collection을 시작하기 전에 source catalog 항목을 하나 이상 선택하세요.",
    collectFailed: "Collection을 실행할 수 없습니다.",
    collectApiFailed: "Collection을 실행할 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    queued: (count: number) => `catalog 항목 ${count}개의 collection이 대기열에 등록되었습니다.`,
    queuedDetail: (count: number) =>
      `run ${count}개가 즉시 생성되었고, homepage discovery와 source collection은 서버 백그라운드에서 계속됩니다.`,
    openRuns: "잠시 후 Runs에서 no-detail, timeout, collection 결과를 확인하세요.",
    noDetail: (count: number) =>
      `catalog 항목 ${count}개의 homepage discovery가 완료되었지만 collection할 detail source를 찾지 못했습니다.`,
    materialized: (count: number) => `Source row ${count}개를 생성했습니다.`,
    launched: (count: number) => `catalog 항목 ${count}개의 collection이 실행되었습니다.`,
    produced: (ready: number, noDetail: number) =>
      `catalog 항목 ${ready}개가 detail source를 생성했습니다${noDetail > 0 ? `, ${noDetail}개는 생성하지 못했습니다` : ""}.`,
    all: "전체",
  },
  ja: {
    addCoverage: "Coverage を追加",
    viewGeneratedSources: "生成ソースを見る",
    description: "Coverage 設定と collection 実行。",
    path: ["運用", "Source Catalog"],
    title: "Source Catalog",
    catalogItems: "Catalog 項目",
    generatedSources: "生成済みソース",
    active: "有効",
    selected: "選択中",
    search: "検索",
    searchPlaceholder: "銀行または catalog item id",
    bank: "銀行",
    productType: "商品タイプ",
    status: "状態",
    apply: "適用",
    reset: "リセット",
    coverageList: "Coverage 一覧",
    launching: "実行中...",
    collectSelected: (count: number) => `選択項目を Collect (${count})`,
    select: "選択",
    homepage: "ホームページ",
    noRows: "現在のフィルターに該当する source catalog 項目はありません。",
    missing: "なし",
    coverageSetup: "Coverage 設定",
    currentScope: "現在の範囲",
    catalogItemCount: (count: number) => `catalog 項目 ${count} 件`,
    sourceCatalogWorkflow: "Source catalog workflow",
    activeCoverage: "有効 coverage",
    inactiveCoverage: "無効 coverage",
    recentRuns: "最近の runs",
    coverageDetail: "Coverage 詳細",
    detailLoadFailed: "Source catalog 詳細を読み込めません。",
    detailLoadApiFailed: "Source catalog 詳細を読み込めません。Admin APIを確認してから再試行してください。",
    selectFirst: "Collection を開始する前に source catalog 項目を1件以上選択してください。",
    collectFailed: "Collection を実行できません。",
    collectApiFailed: "Collection を実行できません。Admin APIを確認してから再試行してください。",
    queued: (count: number) => `${count} 件の catalog 項目の collection をキューに追加しました。`,
    queuedDetail: (count: number) =>
      `${count} 件の run が即時作成され、homepage discovery と source collection はサーバー上で継続します。`,
    openRuns: "少し待ってから Runs で no-detail、timeout、collection の結果を確認してください。",
    noDetail: (count: number) =>
      `${count} 件の catalog 項目で homepage discovery は完了しましたが、collection 対象の detail source は見つかりませんでした。`,
    materialized: (count: number) => `${count} 件の source row を生成しました。`,
    launched: (count: number) => `${count} 件の catalog 項目の collection を実行しました。`,
    produced: (ready: number, noDetail: number) =>
      `${ready} 件の catalog 項目が detail source を生成しました${noDetail > 0 ? `。${noDetail} 件は生成できませんでした` : ""}。`,
    all: "すべて",
  },
} as const;

export function SourceCatalogSurface({
  catalog,
  filters,
  locale,
  csrfToken,
  activeCatalogItemId,
  activeCatalogDetail,
  addModalOpen,
}: SourceCatalogSurfaceProps) {
  const copy = CATALOG_COPY[locale];
  const router = useRouter();
  const [addDialogOpen, setAddDialogOpen] = useState(addModalOpen);
  const [catalogDialogOpen, setCatalogDialogOpen] = useState(Boolean(activeCatalogItemId && activeCatalogDetail));
  const [catalogDialogDetail, setCatalogDialogDetail] = useState<SourceCatalogDetailResponse | null>(activeCatalogDetail);
  const [selectedCatalogItemIds, setSelectedCatalogItemIds] = useState<string[]>([]);
  const [collectPending, setCollectPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const baseSearchParams = useMemo(() => buildCatalogSearchParams(filters), [filters]);
  const detailModalOpen = catalogDialogOpen && Boolean(catalogDialogDetail);

  useEffect(() => {
    setAddDialogOpen(addModalOpen);
  }, [addModalOpen]);

  useEffect(() => {
    setCatalogDialogOpen(Boolean(activeCatalogItemId && activeCatalogDetail));
    setCatalogDialogDetail(activeCatalogDetail);
  }, [activeCatalogItemId, activeCatalogDetail]);

  function syncUrlWithParams(params: URLSearchParams, options?: { replace?: boolean }) {
    const href = buildAdminHref("/admin/source-catalog", params, locale);
    if (options?.replace) {
      window.history.replaceState(null, "", href);
      return;
    }
    window.history.pushState(null, "", href);
  }

  function openAddModal() {
    const params = new URLSearchParams(baseSearchParams);
    params.set("modal", "add");
    params.delete("catalog");
    setAddDialogOpen(true);
    setCatalogDialogOpen(false);
    syncUrlWithParams(params);
  }

  function openDetailModal(catalogItemId: string) {
    const params = new URLSearchParams(baseSearchParams);
    params.set("catalog", catalogItemId);
    params.delete("modal");
    const item = catalog.items.find((catalogItem) => catalogItem.catalog_item_id === catalogItemId);
    setAddDialogOpen(false);
    setCatalogDialogOpen(true);
    setCatalogDialogDetail(item ? buildPreviewSourceCatalogDetail(item) : null);
    syncUrlWithParams(params);
    void hydrateCatalogDetail(catalogItemId);
  }

  function closeModal() {
    setAddDialogOpen(false);
    setCatalogDialogOpen(false);
    syncUrlWithParams(new URLSearchParams(baseSearchParams), { replace: true });
  }

  async function hydrateCatalogDetail(catalogItemId: string) {
    try {
      const response = await fetch(`/admin/source-catalog/${encodeURIComponent(catalogItemId)}/detail`, {
        cache: "no-store",
      });
      const payload = (await response.json()) as {
        data?: SourceCatalogDetailResponse;
        error?: { message?: string };
      };
      if (!response.ok || !payload.data) {
        setError(payload.error?.message ?? copy.detailLoadFailed);
        return;
      }
      setCatalogDialogDetail(payload.data);
    } catch {
      setError(copy.detailLoadApiFailed);
    }
  }

  function handleAddDialogChange(open: boolean) {
    if (!open) {
      closeModal();
    }
  }

  function handleDetailDialogChange(open: boolean) {
    if (!open) {
      closeModal();
    }
  }

  function handleCatalogItemCreated(item: SourceCatalogItem | null) {
    if (item?.catalog_item_id) {
      openDetailModal(item.catalog_item_id);
      return;
    }
    closeModal();
  }

  async function handleCollect() {
    if (selectedCatalogItemIds.length === 0) {
      setError(copy.selectFirst);
      setMessage(null);
      return;
    }

    setCollectPending(true);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch("/admin/source-catalog/collect", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify({ catalog_item_ids: selectedCatalogItemIds }),
      });
      const payload = (await response.json()) as { data?: SourceCatalogCollectionLaunchResponse; error?: { message?: string } };
      if (!response.ok) {
        setError(payload.error?.message ?? copy.collectFailed);
        return;
      }
      setMessage(buildCatalogCollectMessage(locale, payload.data, selectedCatalogItemIds.length));
      setSelectedCatalogItemIds([]);
      router.refresh();
    } catch {
      setError(copy.collectApiFailed);
    } finally {
      setCollectPending(false);
    }
  }

  function toggleCatalogItem(catalogItemId: string, checked: boolean) {
    setSelectedCatalogItemIds((current) => {
      if (checked) {
        return [...current, catalogItemId];
      }
      return current.filter((item) => item !== catalogItemId);
    });
  }

  return (
    <section className="grid gap-6">
      <AdminPageHeader
        actions={
          <>
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" onClick={openAddModal} type="button">
              {copy.addCoverage}
            </button>
            <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/sources", new URLSearchParams(), locale)}>
              {copy.viewGeneratedSources}
            </Link>
          </>
        }
        description={copy.description}
        path={copy.path}
        title={copy.title}
      />

      <article className="grid gap-4 md:grid-cols-4">
        <StatCard label={copy.catalogItems} value={String(catalog.summary.total_items)} />
        <StatCard label={copy.generatedSources} value={String(catalog.summary.generated_source_count)} />
        <StatCard label={copy.active} value={String(catalog.summary.status_counts.active ?? 0)} />
        <StatCard label={copy.selected} value={String(selectedCatalogItemIds.length)} />
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <form action={buildAdminHref("/admin/source-catalog", new URLSearchParams(), locale)} className="grid gap-4 lg:grid-cols-[1.4fr_repeat(3,minmax(0,1fr))_auto]">
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">{copy.search}</span>
            <input className="h-10 rounded-xl border border-border bg-background px-3 text-sm" defaultValue={filters.q} name="q" placeholder={copy.searchPlaceholder} type="search" />
          </label>
          <BankSelect allLabel={copy.all} defaultValue={filters.bankCode} label={copy.bank} name="bank_code" options={catalog.facets.bank_options} />
          <SelectField allLabel={copy.all} label={copy.productType} options={catalog.facets.product_types} defaultValue={filters.productType} name="product_type" />
          <SelectField allLabel={copy.all} label={copy.status} options={catalog.facets.statuses} defaultValue={filters.status} name="status" />
          <div className="flex items-end gap-2">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" type="submit">
              {copy.apply}
            </button>
            <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/source-catalog", new URLSearchParams(), locale)}>
              {copy.reset}
            </Link>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="flex flex-col gap-3 border-b border-border/80 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.coverageList}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" onClick={openAddModal} type="button">
              {copy.addCoverage}
            </button>
            <button className="inline-flex h-10 items-center justify-center rounded-xl border border-border bg-background px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70" disabled={collectPending || selectedCatalogItemIds.length === 0} onClick={handleCollect} type="button">
              {collectPending ? copy.launching : copy.collectSelected(selectedCatalogItemIds.length)}
            </button>
          </div>
        </div>

        {message ? <p className="mx-6 mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="mx-6 mt-4 rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p> : null}

        <div className="overflow-x-auto px-6 py-5">
          <table className="min-w-[940px] table-fixed border-separate border-spacing-0">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                <th className="border-b border-border px-3 py-3 font-medium">{copy.select}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.bank}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.productType}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.status}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.homepage}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.generatedSources}</th>
              </tr>
            </thead>
            <tbody>
              {catalog.items.length === 0 ? (
                <tr>
                  <td className="px-3 py-8 text-sm text-muted-foreground" colSpan={6}>
                    {copy.noRows}
                  </td>
                </tr>
              ) : (
                catalog.items.map((item) => (
                  <tr className="align-top text-sm" key={item.catalog_item_id}>
                    <td className="border-b border-border/70 px-3 py-4">
                      <input checked={selectedCatalogItemIds.includes(item.catalog_item_id)} className="h-4 w-4 rounded border-border text-primary focus:ring-primary" onChange={(event) => toggleCatalogItem(item.catalog_item_id, event.target.checked)} type="checkbox" />
                    </td>
                    <td className="border-b border-border/70 px-3 py-4">
                      <button className="bg-transparent p-0 text-left font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" onClick={() => openDetailModal(item.catalog_item_id)} type="button">
                        {item.bank_name}
                      </button>
                      <p className="mt-1 text-sm text-muted-foreground">{item.bank_code}</p>
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.product_type}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.status}</td>
                    <td className="border-b border-border/70 px-3 py-4">
                      {item.homepage_url ? (
                        <a className="text-primary underline-offset-4 hover:underline" href={item.homepage_url} rel="noreferrer" target="_blank">
                          {item.homepage_url}
                        </a>
                      ) : (
                        <span className="text-muted-foreground">{copy.missing}</span>
                      )}
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.generated_source_count}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </article>

      <OfferModal4
        onOpenChange={handleAddDialogChange}
        open={addDialogOpen}
        panelBadge={copy.coverageSetup}
        panelStats={[
          { label: copy.currentScope, value: copy.catalogItemCount(catalog.summary.total_items) },
          { label: copy.generatedSources, value: `${catalog.summary.generated_source_count}` },
        ]}
        panelTitle={copy.sourceCatalogWorkflow}
        title={copy.addCoverage}
      >
        <SourceCatalogCreateDialogContent bankOptions={catalog.facets.bank_options} csrfToken={csrfToken} locale={locale} onCreated={handleCatalogItemCreated} />
      </OfferModal4>

      <OfferModal4
        onOpenChange={handleDetailDialogChange}
        open={detailModalOpen}
        panelBadge={catalogDialogDetail?.catalog_item.status === "active" ? copy.activeCoverage : copy.inactiveCoverage}
        panelStats={catalogDialogDetail ? [{ label: copy.generatedSources, value: `${catalogDialogDetail.catalog_item.generated_source_count}` }, { label: copy.recentRuns, value: `${catalogDialogDetail.recent_runs.length}` }] : []}
        panelTitle={catalogDialogDetail ? `${catalogDialogDetail.catalog_item.bank_name} ${catalogDialogDetail.catalog_item.product_type}` : copy.coverageDetail}
        title={catalogDialogDetail ? `${catalogDialogDetail.catalog_item.bank_name} ${catalogDialogDetail.catalog_item.product_type}` : copy.coverageDetail}
      >
        {catalogDialogDetail ? (
          <SourceCatalogDetailDialogContent
            bankOptions={catalog.facets.bank_options}
            csrfToken={csrfToken}
            detail={catalogDialogDetail}
            key={catalogDialogDetail.catalog_item.catalog_item_id}
            locale={locale}
          />
        ) : null}
      </OfferModal4>
    </section>
  );
}

function buildCatalogCollectMessage(
  locale: AdminLocale,
  payload: SourceCatalogCollectionLaunchResponse | undefined,
  selectedCatalogItemCount: number,
) {
  const copy = CATALOG_COPY[locale];
  if (payload?.workflow_state === "queued") {
    return [
      copy.queued(selectedCatalogItemCount),
      copy.queuedDetail(payload.run_ids.length),
      copy.openRuns,
    ].join(" ");
  }

  const materializedItems = payload?.materialized_items ?? [];
  const generatedSourceCount = materializedItems.reduce(
    (sum, item) => sum + item.generated_source_ids.length,
    0,
  );
  const readyCount = materializedItems.filter(
    (item) => item.discovery_status === "detail_sources_ready",
  ).length;
  const noDetailCount = materializedItems.length - readyCount;
  const firstNote =
    materializedItems.find((item) => item.discovery_notes.length > 0)?.discovery_notes[0] ?? null;

  if (!payload?.run_ids?.length || readyCount === 0) {
    return [
      copy.noDetail(selectedCatalogItemCount),
      copy.materialized(generatedSourceCount),
      firstNote,
    ]
      .filter(Boolean)
      .join(" ");
  }

  return [
    copy.launched(selectedCatalogItemCount),
    copy.produced(readyCount, noDetailCount),
    copy.materialized(generatedSourceCount),
    firstNote,
  ]
    .filter(Boolean)
    .join(" ");
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-lg border border-border/80 bg-background p-4">
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{value}</p>
    </article>
  );
}

function BankSelect({
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
  options: Array<{ bank_code: string; bank_name: string }>;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <select className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground" defaultValue={defaultValue} name={name}>
        <option value="">{allLabel}</option>
        {options.map((option) => (
          <option key={option.bank_code} value={option.bank_code}>
            {option.bank_name}
          </option>
        ))}
      </select>
    </label>
  );
}

function SelectField({
  allLabel,
  label,
  options,
  defaultValue,
  name,
}: {
  allLabel: string;
  label: string;
  options: string[];
  defaultValue: string;
  name: string;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <select className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground" defaultValue={defaultValue} name={name}>
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

function buildCatalogSearchParams(filters: SourceCatalogPageFilters) {
  const params = new URLSearchParams();
  if (filters.q) {
    params.set("q", filters.q);
  }
  if (filters.bankCode) {
    params.set("bank_code", filters.bankCode);
  }
  if (filters.productType) {
    params.set("product_type", filters.productType);
  }
  if (filters.status) {
    params.set("status", filters.status);
  }
  return params;
}

function buildPreviewSourceCatalogDetail(item: SourceCatalogItem): SourceCatalogDetailResponse {
  return {
    catalog_item: item,
    sample_source_ids: [],
    recent_runs: [],
  };
}
