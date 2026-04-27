"use client";

import Link from "next/link";
import { FileText, Layers3, Play } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupTextarea,
} from "@/components/ui/input-group";
import type {
  BankDetailResponse,
  ProductTypeItem,
  SourceCatalogCollectionLaunchResponse,
  SourceCatalogItem,
} from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";
import {
  buildAdminProductTypeLabelMap,
  buildAdminProductTypeOptions,
  formatAdminProductType,
} from "@/lib/admin-product-types";

type BankCoverageSectionProps = {
  bankCode: string;
  catalogItems: BankDetailResponse["catalog_items"];
  csrfToken: string | null | undefined;
  locale: AdminLocale;
  productTypes: ProductTypeItem[];
};

type CreateCoverageFormState = {
  product_type: string;
  status: string;
  change_reason: string;
};

const STATUS_OPTIONS = [
  { label: "active", value: "active" },
  { label: "inactive", value: "inactive" },
] as const;

const COVERAGE_COPY = {
  en: {
    sectionLabel: "Coverage",
    title: "Product coverage from this bank homepage",
    description:
      "Operators only choose which product families FPDS should cover. Source URLs are generated during collect from the bank homepage, not entered manually here.",
    noCoverage: "No coverage has been added for this bank yet.",
    generatedSources: (count: number) => `${count} generated source(s) currently available for this coverage.`,
    latestNote: "Latest note",
    viewSources: "View sources",
    collect: "Collect",
    collecting: "Collecting...",
    addCoverage: "Add coverage",
    addDescription:
      "Add only missing product families. FPDS will discover the actual product pages from this bank's homepage later.",
    allCovered: "All supported product families are already covered for this bank.",
    searchProductTypes: "Search product types",
    searchPlaceholder: "Search by name or description",
    productType: "Product type",
    status: "Status",
    changeReason: "Change reason",
    changeReasonPlaceholder: "Why is this coverage being added?",
    adding: "Adding...",
    active: "Active",
    inactive: "Inactive",
    addFailed: "Coverage could not be added.",
    addApiFailed: "Coverage could not be added. Check the admin API and try again.",
    added: (productType: string) => `${productType} coverage was added.`,
    collectFailed: "Collection could not be started.",
    collectApiFailed: "Collection could not be started. Check the admin API and try again.",
    queued: (productType: string) => `${productType} collection was queued.`,
    queuedDetail:
      "Homepage discovery and source collection are now running on the server in the background.",
    openRuns:
      "Open Runs after a short refresh to inspect no-detail, timeout, or collection outcomes.",
    noDetail: (productType: string) =>
      `${productType} homepage discovery completed, but no detail sources were identified for collection.`,
    materialized: (count: number) => `Materialized ${count} source row(s).`,
    started: (productType: string) => `${productType} collection started.`,
  },
  ko: {
    sectionLabel: "Coverage",
    title: "은행 홈페이지 기준 상품 coverage",
    description:
      "운영자는 FPDS가 다룰 상품군만 선택합니다. Source URL은 여기서 직접 입력하지 않고, collect 중 은행 홈페이지에서 생성됩니다.",
    noCoverage: "아직 이 은행에 추가된 coverage가 없습니다.",
    generatedSources: (count: number) => `현재 이 coverage에 생성된 source ${count}개가 있습니다.`,
    latestNote: "최근 메모",
    viewSources: "소스 보기",
    collect: "Collect",
    collecting: "Collecting...",
    addCoverage: "Coverage 추가",
    addDescription:
      "아직 없는 상품군만 추가하세요. 실제 상품 페이지는 나중에 이 은행 홈페이지에서 FPDS가 찾습니다.",
    allCovered: "지원되는 모든 상품군이 이미 이 은행에 추가되어 있습니다.",
    searchProductTypes: "상품 유형 검색",
    searchPlaceholder: "이름 또는 설명으로 검색",
    productType: "상품 유형",
    status: "상태",
    changeReason: "변경 사유",
    changeReasonPlaceholder: "이 coverage를 추가하는 이유",
    adding: "추가 중...",
    active: "활성",
    inactive: "비활성",
    addFailed: "Coverage를 추가할 수 없습니다.",
    addApiFailed: "Coverage를 추가할 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    added: (productType: string) => `${productType} coverage가 추가되었습니다.`,
    collectFailed: "Collection을 시작할 수 없습니다.",
    collectApiFailed: "Collection을 시작할 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    queued: (productType: string) => `${productType} collection이 대기열에 등록되었습니다.`,
    queuedDetail: "Homepage discovery와 source collection이 서버 백그라운드에서 실행 중입니다.",
    openRuns: "잠시 후 Runs에서 no-detail, timeout, collection 결과를 확인하세요.",
    noDetail: (productType: string) =>
      `${productType} homepage discovery가 완료되었지만 collection할 detail source를 찾지 못했습니다.`,
    materialized: (count: number) => `Source row ${count}개를 생성했습니다.`,
    started: (productType: string) => `${productType} collection이 시작되었습니다.`,
  },
  ja: {
    sectionLabel: "Coverage",
    title: "銀行ホームページからの商品 coverage",
    description:
      "オペレーターは FPDS が扱う商品ファミリーだけを選択します。Source URL はここで手入力せず、collect 中に銀行ホームページから生成されます。",
    noCoverage: "この銀行にはまだ coverage が追加されていません。",
    generatedSources: (count: number) => `この coverage で現在 ${count} 件の source が生成されています。`,
    latestNote: "最新メモ",
    viewSources: "ソースを見る",
    collect: "Collect",
    collecting: "Collecting...",
    addCoverage: "Coverage を追加",
    addDescription:
      "不足している商品ファミリーだけを追加してください。実際の商品ページは後で FPDS がこの銀行ホームページから検出します。",
    allCovered: "対応しているすべての商品ファミリーは、この銀行ですでに coverage 済みです。",
    searchProductTypes: "商品タイプを検索",
    searchPlaceholder: "名前または説明で検索",
    productType: "商品タイプ",
    status: "状態",
    changeReason: "変更理由",
    changeReasonPlaceholder: "この coverage を追加する理由",
    adding: "追加中...",
    active: "有効",
    inactive: "無効",
    addFailed: "Coverage を追加できません。",
    addApiFailed: "Coverage を追加できません。Admin APIを確認してから再試行してください。",
    added: (productType: string) => `${productType} coverage を追加しました。`,
    collectFailed: "Collection を開始できません。",
    collectApiFailed: "Collection を開始できません。Admin APIを確認してから再試行してください。",
    queued: (productType: string) => `${productType} collection をキューに追加しました。`,
    queuedDetail: "Homepage discovery と source collection はサーバー上でバックグラウンド実行中です。",
    openRuns: "少し待ってから Runs で no-detail、timeout、collection の結果を確認してください。",
    noDetail: (productType: string) =>
      `${productType} homepage discovery は完了しましたが、collection 対象の detail source は見つかりませんでした。`,
    materialized: (count: number) => `${count} 件の source row を生成しました。`,
    started: (productType: string) => `${productType} collection を開始しました。`,
  },
} as const;

export function BankCoverageSection({
  bankCode,
  catalogItems,
  csrfToken,
  locale,
  productTypes,
}: BankCoverageSectionProps) {
  const copy = COVERAGE_COPY[locale];
  const router = useRouter();
  const [productTypeSearch, setProductTypeSearch] = useState("");
  const existingTypes = useMemo(
    () => new Set(catalogItems.map((item) => item.product_type)),
    [catalogItems],
  );
  const productTypeOptions = useMemo(
    () => buildAdminProductTypeOptions(productTypes.filter((item) => item.status === "active")),
    [productTypes],
  );
  const availableProductTypes = useMemo(
    () => productTypeOptions.filter((option) => !existingTypes.has(option.value)),
    [existingTypes, productTypeOptions],
  );
  const filteredProductTypes = useMemo(() => {
    const needle = productTypeSearch.trim().toLowerCase();
    if (!needle) {
      return availableProductTypes;
    }
    return availableProductTypes.filter((option) =>
      `${option.label} ${option.value} ${option.description}`.toLowerCase().includes(needle),
    );
  }, [availableProductTypes, productTypeSearch]);
  const productTypeLabelMap = useMemo(() => buildAdminProductTypeLabelMap(productTypes), [productTypes]);
  const [createForm, setCreateForm] = useState<CreateCoverageFormState>({
    product_type: availableProductTypes[0]?.value ?? "",
    status: "active",
    change_reason: "",
  });
  const [createPending, setCreatePending] = useState(false);
  const [collectingId, setCollectingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!createForm.product_type) {
      return;
    }
    setCreatePending(true);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch("/admin/source-catalog/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify({
          bank_code: bankCode,
          product_type: createForm.product_type,
          status: createForm.status,
          change_reason: createForm.change_reason,
        }),
      });
      const payload = (await response.json()) as {
        data?: { catalog_item?: SourceCatalogItem };
        error?: { message?: string };
      };
      if (!response.ok) {
        setError(payload.error?.message ?? copy.addFailed);
        return;
      }
      const createdProductType =
        payload.data?.catalog_item?.product_type ?? createForm.product_type;
      setMessage(copy.added(formatProductType(createdProductType, productTypeLabelMap)));
      const nextProductTypes = availableProductTypes.filter(
        (option) => option.value !== createdProductType,
      );
      setCreateForm({
        product_type: nextProductTypes[0]?.value ?? "",
        status: "active",
        change_reason: "",
      });
      router.refresh();
    } catch {
      setError(copy.addApiFailed);
    } finally {
      setCreatePending(false);
    }
  }

  async function handleCollect(item: BankDetailResponse["catalog_items"][number]) {
    setCollectingId(item.catalog_item_id);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch("/admin/source-catalog/collect", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify({
          catalog_item_ids: [item.catalog_item_id],
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
      setMessage(buildSingleCoverageCollectMessage(locale, item.product_type, payload.data, productTypeLabelMap));
      router.refresh();
    } catch {
      setError(copy.collectApiFailed);
    } finally {
      setCollectingId(null);
    }
  }

  return (
    <section className="rounded-[1.5rem] border border-border/80 bg-card/95 p-5 shadow-sm">
      <div className="space-y-2">
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
          {copy.sectionLabel}
        </p>
        <h2 className="text-xl font-semibold tracking-tight text-foreground">
          {copy.title}
        </h2>
        <p className="text-sm leading-6 text-muted-foreground">
          {copy.description}
        </p>
      </div>

      {message ? (
        <p className="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="mt-4 rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <div className="mt-5 grid gap-3">
        {catalogItems.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border bg-muted/20 px-4 py-4 text-sm leading-6 text-muted-foreground">
            {copy.noCoverage}
          </div>
        ) : (
          catalogItems.map((item) => (
            <article
              className="rounded-2xl border border-border/80 bg-background px-4 py-4"
              key={item.catalog_item_id}
            >
              <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-base font-semibold text-foreground">
                      {formatProductType(item.product_type, productTypeLabelMap)}
                    </p>
                    <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                    {formatStatus(locale, item.status)}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {copy.generatedSources(item.generated_source_count)}
                  </p>
                  {item.change_reason ? (
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">
                      {copy.latestNote}: {item.change_reason}
                    </p>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-2">
                  <Link
                    className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary"
                    href={buildAdminHref(
                      "/admin/sources",
                      new URLSearchParams(
                        `bank_code=${item.bank_code}&product_type=${item.product_type}`,
                      ),
                      locale,
                    )}
                  >
                    {copy.viewSources}
                  </Link>
                  <Button
                    disabled={collectingId === item.catalog_item_id}
                    onClick={() => void handleCollect(item)}
                    type="button"
                  >
                    <Play className="size-4" />
                    {collectingId === item.catalog_item_id ? copy.collecting : copy.collect}
                  </Button>
                </div>
              </div>
            </article>
          ))
        )}
      </div>

      <div className="mt-5 rounded-2xl border border-border/80 bg-muted/20 p-4">
        <div className="space-y-1">
          <p className="text-sm font-medium text-foreground">{copy.addCoverage}</p>
          <p className="text-sm leading-6 text-muted-foreground">
            {copy.addDescription}
          </p>
        </div>

        {availableProductTypes.length === 0 ? (
          <p className="mt-4 text-sm leading-6 text-muted-foreground">
            {copy.allCovered}
          </p>
        ) : (
          <form className="mt-4 space-y-4" onSubmit={handleCreate}>
            <div className="grid gap-4">
              <label className="grid gap-2 text-sm">
                <span className="font-medium text-foreground">{copy.searchProductTypes}</span>
                <input
                  className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground"
                  onChange={(event) => setProductTypeSearch(event.target.value)}
                  placeholder={copy.searchPlaceholder}
                  type="search"
                  value={productTypeSearch}
                />
              </label>
            </div>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
              <SelectField
                label={copy.productType}
                onChange={(value) =>
                  setCreateForm((current) => ({ ...current, product_type: value }))
                }
                options={filteredProductTypes.length > 0 ? filteredProductTypes : availableProductTypes}
                value={createForm.product_type}
              />
              <SelectField
                label={copy.status}
                onChange={(value) =>
                  setCreateForm((current) => ({ ...current, status: value }))
                }
                options={STATUS_OPTIONS.map((option) => ({ ...option, label: formatStatus(locale, option.value) }))}
                value={createForm.status}
              />
            </div>

            <Field data-invalid={Boolean(error)}>
              <FieldLabel>{copy.changeReason}</FieldLabel>
              <InputGroup className="min-h-20 items-start">
                <InputGroupAddon align="block-start">
                  <FileText className="size-4" />
                </InputGroupAddon>
                <InputGroupTextarea
                  aria-invalid={Boolean(error)}
                  onChange={(event) =>
                    setCreateForm((current) => ({
                      ...current,
                      change_reason: event.target.value,
                    }))
                  }
                  placeholder={copy.changeReasonPlaceholder}
                  rows={2}
                  value={createForm.change_reason}
                />
              </InputGroup>
              {error ? <FieldError>{error}</FieldError> : null}
            </Field>

            <div className="flex justify-end">
              <Button
                disabled={createPending || !createForm.product_type}
                type="submit"
              >
                <Layers3 className="size-4" />
                {createPending ? copy.adding : copy.addCoverage}
              </Button>
            </div>
          </form>
        )}
      </div>
    </section>
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
        className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground"
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

function formatProductType(productType: string, labelMap?: Record<string, string>) {
  return formatAdminProductType(productType, labelMap);
}

function formatStatus(locale: AdminLocale, value: string) {
  if (value === "active") {
    return COVERAGE_COPY[locale].active;
  }
  if (value === "inactive") {
    return COVERAGE_COPY[locale].inactive;
  }
  return value;
}

function buildSingleCoverageCollectMessage(
  locale: AdminLocale,
  productType: string,
  payload: SourceCatalogCollectionLaunchResponse | undefined,
  labelMap?: Record<string, string>,
) {
  const copy = COVERAGE_COPY[locale];
  const label = formatProductType(productType, labelMap);

  if (payload?.workflow_state === "queued") {
    return [
      copy.queued(label),
      copy.queuedDetail,
      copy.openRuns,
    ].join(" ");
  }

  const materializedItem = payload?.materialized_items?.[0];
  const generatedCount = materializedItem?.generated_source_ids?.length ?? 0;
  const firstNote = materializedItem?.discovery_notes?.[0];

  if (!payload?.run_ids?.length || materializedItem?.discovery_status === "no_detail_sources_discovered") {
    return [
      copy.noDetail(label),
      copy.materialized(generatedCount),
      firstNote ?? null,
    ]
      .filter(Boolean)
      .join(" ");
  }

  return [
    copy.started(label),
    copy.materialized(generatedCount),
    firstNote ?? null,
  ]
    .filter(Boolean)
    .join(" ");
}
