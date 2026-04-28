"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { OfferModal4 } from "@/components/offer-modal4";
import { BankCreateDialogContent } from "@/components/fpds/admin/bank-create-dialog-content";
import { BankDetailDialogContent } from "@/components/fpds/admin/bank-detail-dialog-content";
import type {
  BankDetailResponse,
  BankItem,
  BankListResponse,
  ProductTypeItem,
  SourceCatalogCollectionLaunchResponse,
} from "@/lib/admin-api";
import { buildAdminHref, localizedMissing, type AdminLocale } from "@/lib/admin-i18n";
import { buildAdminProductTypeLabelMap, formatAdminProductType } from "@/lib/admin-product-types";

export type BankRegistryPageFilters = {
  q: string;
  status: string;
};

type BankRegistrySurfaceProps = {
  banks: BankListResponse;
  filters: BankRegistryPageFilters;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
  activeBankCode: string | null;
  activeBankDetail: BankDetailResponse | null;
  addModalOpen: boolean;
  productTypes: ProductTypeItem[];
};

const BANK_COPY = {
  en: {
    addBank: "Add bank",
    description: "Bank profiles, coverage, and collection launch.",
    path: ["Operations", "Banks"],
    title: "Banks",
    banks: "Banks",
    active: "Active",
    inactive: "Inactive",
    managed: "Managed",
    search: "Search",
    searchPlaceholder: "bank name or homepage URL",
    status: "Status",
    all: "All",
    apply: "Apply",
    reset: "Reset",
    bankList: "Bank list",
    collecting: "Collecting...",
    collectSelected: (count: number) => `Collect selected${count > 0 ? ` (${count})` : ""}`,
    selectAllBanks: "Select all visible banks",
    bank: "Bank",
    code: "Code",
    homepage: "Homepage",
    catalogs: "Catalogs",
    generatedSources: "Generated sources",
    noBanks: "No banks matched the current filter set.",
    selectBankFirst: "Select at least one bank with added coverage before starting collection.",
    loadFailed: "Bank detail could not be loaded.",
    loadApiFailed: "Bank detail could not be loaded. Check the admin API and try again.",
    collectFailed: "Collection could not be started.",
    collectApiFailed: "Collection could not be started. Check the admin API and try again.",
    none: "none",
    bankDetail: "Bank detail",
  },
  ko: {
    addBank: "은행 추가",
    description: "은행 프로필, coverage, collection 실행.",
    path: ["운영", "은행"],
    title: "은행",
    banks: "은행",
    active: "활성",
    inactive: "비활성",
    managed: "관리 대상",
    search: "검색",
    searchPlaceholder: "은행명 또는 홈페이지 URL",
    status: "상태",
    all: "전체",
    apply: "적용",
    reset: "초기화",
    bankList: "은행 목록",
    collecting: "수집 중...",
    collectSelected: (count: number) => `선택 항목 수집${count > 0 ? ` (${count})` : ""}`,
    selectAllBanks: "표시된 은행 모두 선택",
    bank: "은행",
    code: "코드",
    homepage: "홈페이지",
    catalogs: "Catalogs",
    generatedSources: "생성된 소스",
    noBanks: "현재 필터에 맞는 은행이 없습니다.",
    selectBankFirst: "수집을 시작하기 전에 coverage가 추가된 은행을 하나 이상 선택하세요.",
    loadFailed: "은행 상세를 불러올 수 없습니다.",
    loadApiFailed: "은행 상세를 불러올 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    collectFailed: "Collection을 시작할 수 없습니다.",
    collectApiFailed: "Collection을 시작할 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    none: "없음",
    bankDetail: "은행 상세",
  },
  ja: {
    addBank: "銀行を追加",
    description: "銀行プロファイル、カバレッジ、collection 実行。",
    path: ["運用", "銀行"],
    title: "銀行",
    banks: "銀行",
    active: "有効",
    inactive: "無効",
    managed: "管理対象",
    search: "検索",
    searchPlaceholder: "銀行名またはホームページURL",
    status: "状態",
    all: "すべて",
    apply: "適用",
    reset: "リセット",
    bankList: "銀行一覧",
    collecting: "収集中...",
    collectSelected: (count: number) => `選択項目を収集${count > 0 ? ` (${count})` : ""}`,
    selectAllBanks: "表示中の銀行をすべて選択",
    bank: "銀行",
    code: "コード",
    homepage: "ホームページ",
    catalogs: "Catalogs",
    generatedSources: "生成済みソース",
    noBanks: "現在のフィルターに該当する銀行はありません。",
    selectBankFirst: "Collection を開始する前に、coverage が追加された銀行を1件以上選択してください。",
    loadFailed: "銀行詳細を読み込めません。",
    loadApiFailed: "銀行詳細を読み込めません。Admin APIを確認してから再試行してください。",
    collectFailed: "Collection を開始できません。",
    collectApiFailed: "Collection を開始できません。Admin APIを確認してから再試行してください。",
    none: "なし",
    bankDetail: "銀行詳細",
  },
} as const;

export function BankRegistrySurface({
  banks,
  filters,
  locale,
  csrfToken,
  activeBankCode,
  activeBankDetail,
  addModalOpen,
  productTypes,
}: BankRegistrySurfaceProps) {
  const copy = BANK_COPY[locale];
  const router = useRouter();
  const [addDialogOpen, setAddDialogOpen] = useState(addModalOpen);
  const [bankDialogOpen, setBankDialogOpen] = useState(Boolean(activeBankCode && activeBankDetail));
  const [bankDialogDetail, setBankDialogDetail] = useState<BankDetailResponse | null>(activeBankDetail);
  const baseSearchParams = useMemo(() => buildRegistrySearchParams(filters), [filters]);
  const productTypeLabelMap = useMemo(() => buildAdminProductTypeLabelMap(productTypes), [productTypes]);
  const [selectedBankCodes, setSelectedBankCodes] = useState<string[]>([]);
  const [bulkPending, setBulkPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const selectedCatalogItems = useMemo(
    () =>
      banks.items
        .filter((item) => selectedBankCodes.includes(item.bank_code))
        .flatMap((item) => item.catalog_items),
    [banks.items, selectedBankCodes],
  );
  const selectedCoverageCount = selectedCatalogItems.length;
  const allVisibleSelected = banks.items.length > 0 && banks.items.every((item) => selectedBankCodes.includes(item.bank_code));
  const detailModalOpen = bankDialogOpen && Boolean(bankDialogDetail);

  useEffect(() => {
    setAddDialogOpen(addModalOpen);
  }, [addModalOpen]);

  useEffect(() => {
    setBankDialogOpen(Boolean(activeBankCode && activeBankDetail));
    setBankDialogDetail(activeBankDetail);
  }, [activeBankCode, activeBankDetail]);

  function syncUrlWithParams(params: URLSearchParams, options?: { replace?: boolean }) {
    const href = buildAdminHref("/admin/banks", params, locale);
    if (options?.replace) {
      window.history.replaceState(null, "", href);
      return;
    }
    window.history.pushState(null, "", href);
  }

  function openAddModal() {
    const params = new URLSearchParams(baseSearchParams);
    params.set("modal", "add");
    params.delete("bank");
    setAddDialogOpen(true);
    setBankDialogOpen(false);
    syncUrlWithParams(params);
  }

  function openBankModal(bankCode: string) {
    const params = new URLSearchParams(baseSearchParams);
    params.set("bank", bankCode);
    params.delete("modal");
    const bank = banks.items.find((item) => item.bank_code === bankCode);
    setAddDialogOpen(false);
    setBankDialogOpen(true);
    setBankDialogDetail(bank ? buildPreviewBankDetail(bank) : null);
    syncUrlWithParams(params);
    void hydrateBankDetail(bankCode);
  }

  function closeModal() {
    setAddDialogOpen(false);
    setBankDialogOpen(false);
    syncUrlWithParams(new URLSearchParams(baseSearchParams), { replace: true });
  }

  async function hydrateBankDetail(bankCode: string) {
    try {
      const response = await fetch(`/admin/banks/${encodeURIComponent(bankCode)}/detail`, {
        cache: "no-store",
      });
      const payload = (await response.json()) as {
        data?: BankDetailResponse;
        error?: { message?: string };
      };
      if (!response.ok || !payload.data) {
        setError(payload.error?.message ?? copy.loadFailed);
        return;
      }
      setBankDialogDetail(payload.data);
    } catch {
      setError(copy.loadApiFailed);
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

  function handleBankCreated(bank: BankItem | null) {
    if (bank?.bank_code) {
      openBankModal(bank.bank_code);
      return;
    }
    closeModal();
  }

  function toggleBankSelection(bankCode: string) {
    setSelectedBankCodes((current) =>
      current.includes(bankCode)
        ? current.filter((item) => item !== bankCode)
        : [...current, bankCode],
    );
  }

  function toggleAllVisibleBanks() {
    setSelectedBankCodes((current) => {
      if (allVisibleSelected) {
        return current.filter((item) => !banks.items.some((bank) => bank.bank_code === item));
      }
      const next = new Set(current);
      for (const item of banks.items) {
        next.add(item.bank_code);
      }
      return Array.from(next);
    });
  }

  async function handleBulkCollect() {
    setBulkPending(true);
    setMessage(null);
    setError(null);

    const catalogItemIds = selectedCatalogItems.map((item) => item.catalog_item_id);
    if (catalogItemIds.length === 0) {
      setError(copy.selectBankFirst);
      setBulkPending(false);
      return;
    }

    try {
      const response = await fetch("/admin/source-catalog/collect", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify({
          catalog_item_ids: catalogItemIds,
        }),
      });
      const payload = (await response.json()) as {
        data?: SourceCatalogCollectionLaunchResponse;
        error?: { message?: string };
      };
      if (!response.ok) {
        setError(payload.error?.message ?? copy.collectFailed);
        return;
      }
      setMessage(
        buildBulkCollectMessage({
          locale,
          payload: payload.data,
          selectedBankCount: selectedBankCodes.length,
          selectedCoverageCount,
        }),
      );
      setSelectedBankCodes([]);
      router.refresh();
    } catch {
      setError(copy.collectApiFailed);
    } finally {
      setBulkPending(false);
    }
  }

  return (
    <section className="grid gap-6">
      <AdminPageHeader
        description={copy.description}
        path={copy.path}
        title={copy.title}
      />

      <article className="grid gap-4 md:grid-cols-3">
        <StatCard label={copy.banks} value={String(banks.summary.total_items)} />
        <StatCard label={copy.active} value={String(banks.summary.status_counts.active ?? 0)} />
        <StatCard label={copy.managed} value={String(banks.items.filter((item) => item.managed_flag).length)} />
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <form action={buildAdminHref("/admin/banks", new URLSearchParams(), locale)} className="grid gap-4 lg:grid-cols-[1.4fr_minmax(0,220px)_auto]">
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">{copy.search}</span>
            <input className="h-10 rounded-xl border border-border bg-background px-3 text-sm" defaultValue={filters.q} name="q" placeholder={copy.searchPlaceholder} type="search" />
          </label>
          <FilterSelect allLabel={copy.all} defaultValue={filters.status} label={copy.status} name="status" options={banks.facets.statuses} />
          <div className="flex items-end gap-2">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" type="submit">
              {copy.apply}
            </button>
            <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/banks", new URLSearchParams(), locale)}>
              {copy.reset}
            </Link>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="flex flex-col gap-3 border-b border-border/80 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.bankList}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" onClick={openAddModal} type="button">
              {copy.addBank}
            </button>
            <button
              className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
              disabled={bulkPending}
              onClick={() => void handleBulkCollect()}
              type="button"
            >
              {bulkPending ? copy.collecting : copy.collectSelected(selectedCoverageCount)}
            </button>
          </div>
        </div>
        {message ? (
          <p className="mx-6 mt-5 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            {message}
          </p>
        ) : null}
        {error ? (
          <p className="mx-6 mt-5 rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </p>
        ) : null}
        <div className="overflow-x-auto px-6 py-5">
          <table className="min-w-[980px] table-fixed border-separate border-spacing-0">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                <th className="border-b border-border px-3 py-3 font-medium">
                  <input
                    aria-label={copy.selectAllBanks}
                    checked={allVisibleSelected}
                    className="h-4 w-4 rounded border-border"
                    onChange={toggleAllVisibleBanks}
                    type="checkbox"
                  />
                </th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.bank}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.code}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.homepage}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.status}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.catalogs}</th>
                <th className="border-b border-border px-3 py-3 font-medium">{copy.generatedSources}</th>
              </tr>
            </thead>
            <tbody>
              {banks.items.length === 0 ? (
                <tr>
                  <td className="px-3 py-8 text-sm text-muted-foreground" colSpan={7}>
                    {copy.noBanks}
                  </td>
                </tr>
              ) : (
                banks.items.map((item) => (
                  <tr className="align-top text-sm" key={item.bank_code}>
                    <td className="border-b border-border/70 px-3 py-4">
                      <input
                        aria-label={`Select ${item.bank_name}`}
                        checked={selectedBankCodes.includes(item.bank_code)}
                        className="h-4 w-4 rounded border-border"
                        onChange={() => toggleBankSelection(item.bank_code)}
                        type="checkbox"
                      />
                    </td>
                    <td className="border-b border-border/70 px-3 py-4">
                      <button className="bg-transparent p-0 text-left font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" onClick={() => openBankModal(item.bank_code)} type="button">
                        {item.bank_name}
                      </button>
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.bank_code}</td>
                    <td className="border-b border-border/70 px-3 py-4">
                      {item.homepage_url ? (
                        <a className="text-primary underline-offset-4 hover:underline" href={item.homepage_url} rel="noreferrer" target="_blank">
                          {item.homepage_url}
                        </a>
                      ) : (
                        <span className="text-muted-foreground">{localizedMissing(locale)}</span>
                      )}
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{formatStatus(locale, item.status)}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">
                      {item.catalog_product_types.length > 0 ? (
                        formatProductTypeList(item.catalog_product_types, productTypeLabelMap)
                      ) : (
                        <span className="text-muted-foreground">{copy.none}</span>
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
        showPanel={false}
        title={copy.addBank}
        width="medium"
      >
        <BankCreateDialogContent csrfToken={csrfToken} locale={locale} onCreated={handleBankCreated} productTypes={productTypes} />
      </OfferModal4>

      <OfferModal4
        onOpenChange={handleDetailDialogChange}
        open={detailModalOpen}
        showPanel={false}
        title={bankDialogDetail ? bankDialogDetail.bank.bank_name : copy.bankDetail}
        width="medium"
      >
        {bankDialogDetail ? (
          <BankDetailDialogContent
            csrfToken={csrfToken}
            detail={bankDialogDetail}
            key={bankDialogDetail.bank.bank_code}
            locale={locale}
            productTypes={productTypes}
          />
        ) : null}
      </OfferModal4>
    </section>
  );
}

function buildBulkCollectMessage({
  locale,
  payload,
  selectedBankCount,
  selectedCoverageCount,
}: {
  locale: AdminLocale;
  payload: SourceCatalogCollectionLaunchResponse | undefined;
  selectedBankCount: number;
  selectedCoverageCount: number;
}) {
  if (payload?.workflow_state === "queued") {
    if (locale === "ko") {
      return [
        `${selectedBankCount}개 은행, ${selectedCoverageCount}개 coverage item에 대한 collection을 대기열에 넣었습니다.`,
        `${payload.run_ids.length}개 run이 생성되었고 homepage discovery와 source collection은 서버 background에서 계속됩니다.`,
        "잠시 후 Runs 화면에서 no-detail, timeout, collection 결과를 확인하세요.",
      ].join(" ");
    }
    if (locale === "ja") {
      return [
        `${selectedBankCount}件の銀行、${selectedCoverageCount}件の coverage item の collection をキューに登録しました。`,
        `${payload.run_ids.length}件の run が作成され、homepage discovery と source collection はサーバーの background で続行されます。`,
        "少し待ってから Runs 画面で no-detail、timeout、collection 結果を確認してください。",
      ].join(" ");
    }
    return [
      `Queued collection for ${selectedBankCount} bank(s) across ${selectedCoverageCount} coverage item(s).`,
      `${payload.run_ids.length} run(s) were created immediately, and homepage discovery plus source collection will continue on the server in the background.`,
      "Open Runs after a short refresh to inspect no-detail, timeout, or collection outcomes.",
    ].join(" ");
  }

  const materializedItems = payload?.materialized_items ?? [];
  const generatedCount = materializedItems.reduce(
    (total, item) => total + item.generated_source_ids.length,
    0,
  );
  const readyCount = materializedItems.filter(
    (item) => item.discovery_status === "detail_sources_ready",
  ).length;
  const noDetailCount = materializedItems.length - readyCount;
  const firstNote =
    materializedItems.find((item) => item.discovery_notes.length > 0)?.discovery_notes[0] ?? null;

  if (!payload?.run_ids?.length || readyCount === 0) {
    if (locale === "ko") {
      return [
        `${selectedBankCount}개 은행, ${selectedCoverageCount}개 coverage item의 homepage discovery가 완료됐지만 collection 대상 detail source를 찾지 못했습니다.`,
        `${generatedCount}개 source row를 materialize했습니다.`,
        firstNote,
      ]
        .filter(Boolean)
        .join(" ");
    }
    if (locale === "ja") {
      return [
        `${selectedBankCount}件の銀行、${selectedCoverageCount}件の coverage item の homepage discovery は完了しましたが、collection 対象の detail source は見つかりませんでした。`,
        `${generatedCount}件の source row を materialize しました。`,
        firstNote,
      ]
        .filter(Boolean)
        .join(" ");
    }
    return [
      `Homepage discovery completed for ${selectedBankCount} bank(s) across ${selectedCoverageCount} coverage item(s), but no detail sources were identified for collection.`,
      `Materialized ${generatedCount} source row(s).`,
      firstNote,
    ]
      .filter(Boolean)
      .join(" ");
  }

  if (locale === "ko") {
    return [
      `${selectedBankCount}개 은행, ${selectedCoverageCount}개 coverage item의 collection을 시작했습니다.`,
      `${readyCount}개 coverage item이 detail source를 만들었습니다${noDetailCount > 0 ? `; ${noDetailCount}개는 만들지 못했습니다` : ""}.`,
      `${generatedCount}개 source row를 materialize했습니다.`,
      firstNote,
    ]
      .filter(Boolean)
      .join(" ");
  }
  if (locale === "ja") {
    return [
      `${selectedBankCount}件の銀行、${selectedCoverageCount}件の coverage item の collection を開始しました。`,
      `${readyCount}件の coverage item が detail source を生成しました${noDetailCount > 0 ? `; ${noDetailCount}件は生成しませんでした` : ""}。`,
      `${generatedCount}件の source row を materialize しました。`,
      firstNote,
    ]
      .filter(Boolean)
      .join(" ");
  }
  return [
    `Started collection for ${selectedBankCount} bank(s) across ${selectedCoverageCount} coverage item(s).`,
    `${readyCount} coverage item(s) produced detail sources${noDetailCount > 0 ? ` and ${noDetailCount} did not` : ""}.`,
    `Materialized ${generatedCount} source row(s).`,
    firstNote,
  ]
    .filter(Boolean)
    .join(" ");
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-lg border border-border/80 bg-white p-4">
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{value}</p>
    </article>
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

function formatStatus(locale: AdminLocale, value: string) {
  if (value === "active") {
    return BANK_COPY[locale].active;
  }
  if (value === "inactive") {
    return BANK_COPY[locale].inactive;
  }
  return value;
}

function buildRegistrySearchParams(filters: BankRegistryPageFilters) {
  const params = new URLSearchParams();
  if (filters.q) {
    params.set("q", filters.q);
  }
  if (filters.status) {
    params.set("status", filters.status);
  }
  return params;
}

function buildPreviewBankDetail(bank: BankItem): BankDetailResponse {
  return {
    bank,
    catalog_items: bank.catalog_items.map((item) => ({
      catalog_item_id: item.catalog_item_id,
      bank_code: bank.bank_code,
      bank_name: bank.bank_name,
      country_code: bank.country_code,
      product_type: item.product_type,
      status: item.status,
      homepage_url: bank.homepage_url,
      normalized_homepage_url: bank.normalized_homepage_url,
      source_language: bank.source_language,
      generated_source_count: item.generated_source_count,
      change_reason: null,
      created_at: null,
      updated_at: null,
    })),
  };
}

function formatProductTypeList(productTypes: string[], labelMap?: Record<string, string>) {
  return productTypes.map((item) => formatAdminProductType(item, labelMap)).join(", ");
}
