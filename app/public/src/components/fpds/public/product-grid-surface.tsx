import { ArrowDownUp, ChevronDown, RefreshCw, Search, SlidersHorizontal, X } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { InstantFilterForm } from "@/components/fpds/public/instant-filter-form";
import { ProductCompareWorkspace } from "@/components/fpds/public/product-compare-workspace";
import { PublicFreshness } from "@/components/fpds/public/public-freshness";
import { ResponsiveCatalogViewToggle } from "@/components/fpds/public/responsive-catalog-view-toggle";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card";
import { formatPublicMessage, getIntlLocale, getPublicCatalogCopy, getPublicDiscoveryCopy, getPublicMessages } from "@/lib/public-locale";
import { type PublicFilterOption, type PublicFiltersResponse, type PublicProductsResponse } from "@/lib/public-api";
import { buildProductsSearchParams, buildPublicHref, type ProductGridPageFilters } from "@/lib/public-query";
import { cn } from "@/lib/utils";

type ProductGridSurfaceProps = {
  apiUnavailable: boolean;
  catalog: "deposit" | "card" | "loan";
  filterOptions: PublicFiltersResponse | null;
  filters: ProductGridPageFilters;
  products: PublicProductsResponse | null;
};

type SortOption = {
  label: string;
  order: "asc" | "desc";
  value: string;
};

export function ProductGridSurface({ apiUnavailable, catalog, filterOptions, filters, products }: ProductGridSurfaceProps) {
  const copy = getPublicMessages(filters.locale);
  const discoveryCopy = getPublicDiscoveryCopy(filters.locale);
  const catalogCopy = getPublicCatalogCopy(filters.locale, catalog);
  const catalogPath: CatalogPath = catalog === "loan" ? "/loans" : catalog === "card" ? "/cards" : "/products";
  const clearHref = buildCatalogHref(catalogPath, {
    ...filters,
    searchQuery: "",
    bankCodes: [],
    productTypes: [],
    targetCustomerTags: [],
    feeBucket: "",
    minimumBalanceBucket: "",
    minimumDepositBucket: "",
    termBucket: "",
    page: 1
  });

  if (apiUnavailable || !filterOptions || !products) {
    return (
      <main className="mx-auto w-full max-w-5xl px-4 py-10 md:px-6">
        <Card className="border-destructive/25">
          <CardHeader>
            <h1 className="text-lg font-semibold">{copy.grid.retryTitle}</h1>
            <CardDescription>{copy.grid.retryBody}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link href={buildCatalogHref(catalogPath, filters)}>
                <RefreshCw className="size-4" aria-hidden="true" />
                {copy.grid.retryButton}
              </Link>
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  const activeChips = buildActiveChips(filters, filterOptions, catalogPath);
  const selectedTypes = new Set(filters.productTypes);
  const gicOnly = selectedTypes.size === 1 && selectedTypes.has("gic");
  const isDeposit = catalog === "deposit";
  const sortOptions: SortOption[] = catalog === "loan"
    ? [
        { value: "display_rate", label: copy.grid.sortDisplayRate, order: "asc" },
        { value: "bank_name", label: copy.grid.sortBankName, order: "asc" },
        { value: "product_name", label: copy.grid.sortProductName, order: "asc" }
      ]
    : catalog === "card"
      ? [
          { value: "annual_fee", label: copy.grid.sortAnnualFee, order: "asc" },
          { value: "display_rate", label: copy.grid.sortDisplayRate, order: "asc" },
          { value: "bank_name", label: copy.grid.sortBankName, order: "asc" }
        ]
    : [
        { value: "display_rate", label: copy.grid.sortDisplayRate, order: "desc" },
        { value: "monthly_fee", label: copy.grid.sortMonthlyFee, order: "asc" },
        { value: "minimum_balance", label: copy.grid.sortMinimumBalance, order: "asc" }
      ];

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6 md:py-9">
      <div className="flex flex-col gap-5">
        <nav aria-label={breadcrumbLabel(filters.locale)} className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <Link className="transition-colors hover:text-foreground" href={buildPublicHref("/", filters)}>
            {copy.nav.dashboard}
          </Link>
          <span aria-hidden="true">/</span>
          <span aria-current="page" className="font-medium text-foreground">{catalogCopy.title}</span>
        </nav>

        <section className="border-y border-foreground/15 py-7 md:py-10">
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
            <div className="max-w-3xl">
              <p className={`font-mono text-[10px] font-semibold uppercase tracking-[0.16em] ${catalog === "deposit" ? "text-deposit" : "text-loan"}`}>
                {catalogCopy.coverage}
              </p>
              <h1 className="text-balance mt-3 max-w-full font-display text-4xl font-semibold leading-[0.98] tracking-[-0.05em] text-foreground [overflow-wrap:anywhere] md:text-6xl">{catalogCopy.title}</h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground [overflow-wrap:anywhere] md:text-base">{catalogCopy.description}</p>
            </div>
            <div className="flex flex-col items-start gap-3 lg:items-end">
              <p className="whitespace-nowrap font-mono text-xs font-semibold text-foreground">
                {formatPublicMessage(copy.grid.productCount, { count: formatCount(products.total_items, filters.locale) })}
              </p>
              <PublicFreshness freshness={products.freshness} locale={filters.locale} />
            </div>
          </div>
        </section>

        <section className="overflow-hidden border-y border-border bg-card/55">
          <details className="group" open={activeChips.length > 0}>
            <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-semibold text-foreground outline-none transition-colors hover:bg-muted/40 focus-visible:ring-3 focus-visible:ring-ring/50 sm:px-5 [&::-webkit-details-marker]:hidden">
              <span className="flex items-center gap-2">
                <SlidersHorizontal className="size-4 text-primary" aria-hidden="true" />
                {copy.grid.searchConditions}
                {activeChips.length ? (
                  <span className="rounded-full bg-primary px-2 py-0.5 text-[11px] font-semibold text-primary-foreground tabular-nums">{activeChips.length}</span>
                ) : null}
              </span>
              <ChevronDown className="size-4 text-muted-foreground transition-transform group-open:rotate-180" aria-hidden="true" />
            </summary>
            <CardContent className="border-t border-border/70 px-4 py-4 sm:px-5">
              <InstantFilterForm action={catalogPath} pendingMessage={discoveryCopy.updatingResults}>
                <input name="locale" type="hidden" value={filters.locale} />
                <input name="country_code" type="hidden" value={filters.countryCode} />
                <input name="sort_by" type="hidden" value={filters.sortBy} />
                <input name="sort_order" type="hidden" value={filters.sortOrder} />
                {filters.viewMode !== "auto" ? <input name="view" type="hidden" value={filters.viewMode} /> : null}

                <label className="grid max-w-2xl gap-1.5">
                  <span className="text-sm font-medium text-foreground">{discoveryCopy.searchLabel}</span>
                  <span className="relative">
                    <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
                    <input
                      className="h-11 w-full rounded-lg border border-input bg-background pl-10 pr-3 text-sm text-foreground outline-none transition placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                      defaultValue={filters.searchQuery}
                      key={filters.searchQuery || "empty-search"}
                      maxLength={120}
                      name="q"
                      placeholder={discoveryCopy.searchPlaceholder}
                      type="search"
                    />
                  </span>
                </label>

                <div className="grid gap-4 xl:grid-cols-[1.15fr_1fr_1fr]">
                  <FilterGroup label={copy.grid.banks}>
                    <OptionGrid locale={filters.locale} name="bank_code" options={filterOptions.banks} selectedValues={new Set(filters.bankCodes)} />
                  </FilterGroup>
                  <FilterGroup label={copy.grid.productTypes}>
                    <OptionGrid locale={filters.locale} name="product_type" options={filterOptions.product_types} selectedValues={new Set(filters.productTypes)} />
                  </FilterGroup>
                  {filterOptions.target_customer_tags.length ? (
                    <FilterGroup label={copy.grid.targetTags}>
                      <OptionGrid
                        locale={filters.locale}
                        name="target_customer_tag"
                        options={filterOptions.target_customer_tags}
                        selectedValues={new Set(filters.targetCustomerTags)}
                      />
                    </FilterGroup>
                  ) : null}
                </div>

                {isDeposit ? (
                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                    <SelectField locale={filters.locale} label={copy.grid.feeBucket} name="fee_bucket" options={filterOptions.fee_buckets} value={filters.feeBucket} />
                    {!gicOnly ? (
                      <SelectField
                        locale={filters.locale}
                        label={copy.grid.minimumBalance}
                        name="minimum_balance_bucket"
                        options={filterOptions.minimum_balance_buckets}
                        value={filters.minimumBalanceBucket}
                      />
                    ) : null}
                    {selectedTypes.size === 0 || selectedTypes.has("gic") ? (
                      <SelectField
                        locale={filters.locale}
                        label={copy.grid.minimumDeposit}
                        name="minimum_deposit_bucket"
                        options={filterOptions.minimum_deposit_buckets}
                        value={filters.minimumDepositBucket}
                      />
                    ) : null}
                    {gicOnly ? (
                      <SelectField locale={filters.locale} label={copy.grid.termBucket} name="term_bucket" options={filterOptions.term_buckets} value={filters.termBucket} />
                    ) : null}
                  </div>
                ) : null}

                <div className="flex justify-end border-t border-border/70 pt-4">
                  <Button asChild type="button" variant="outline">
                    <Link href={clearHref}>{copy.common.clearFilters}</Link>
                  </Button>
                </div>
              </InstantFilterForm>
            </CardContent>
          </details>
        </section>

        <DiscoveryToolbar
          activeChips={activeChips}
          catalogPath={catalogPath}
          clearHref={clearHref}
          filters={filters}
          options={sortOptions}
        />

        {products.items.length ? (
          <>
            <ProductCompareWorkspace
              filters={filters}
              initialProducts={products}
              locale={filters.locale}
              productsQuery={buildProductsSearchParams(filters).toString()}
            />
            <noscript>
              <nav aria-label={paginationLabel(filters.locale)} className="flex items-center justify-between gap-4 border-t border-border pt-4 text-sm">
                {products.page > 1 ? (
                  <Link className="font-medium text-primary underline-offset-4 hover:underline" href={buildCatalogHref(catalogPath, { ...filters, page: products.page - 1 })} rel="prev">
                    {previousPageLabel(filters.locale)}
                  </Link>
                ) : <span />}
                {products.has_next_page ? (
                  <Link className="font-medium text-primary underline-offset-4 hover:underline" href={buildCatalogHref(catalogPath, { ...filters, page: products.page + 1 })} rel="next">
                    {nextPageLabel(filters.locale)}
                  </Link>
                ) : null}
              </nav>
            </noscript>
          </>
        ) : (
          <Card className="border-dashed">
            <CardHeader>
              <h2 className="text-lg font-semibold">{copy.grid.noResultTitle}</h2>
              <CardDescription>{copy.grid.noResultBody}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild>
                <Link href={clearHref}>{copy.common.clearFilters}</Link>
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </main>
  );
}

function DiscoveryToolbar({
  activeChips,
  catalogPath,
  clearHref,
  filters,
  options
}: {
  activeChips: Array<{ group: string; href: string; label: string; value: string }>;
  catalogPath: CatalogPath;
  clearHref: string;
  filters: ProductGridPageFilters;
  options: SortOption[];
}) {
  const copy = getPublicMessages(filters.locale);

  return (
    <section className="grid gap-3 border-b border-foreground/15 pb-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
      <div className="flex min-w-0 flex-wrap items-center gap-2">
        {activeChips.length ? (
          activeChips.map((chip) => (
            <Link
              className="inline-flex min-h-11 items-center gap-1.5 whitespace-nowrap rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-semibold text-primary transition-colors hover:bg-primary/10"
              href={chip.href}
              key={`${chip.group}-${chip.value}`}
            >
              {chip.label}
              <X className="size-3" aria-hidden="true" />
            </Link>
          ))
        ) : (
          <span className="text-sm text-muted-foreground">{copy.grid.noActiveFilters}</span>
        )}
        {activeChips.length ? (
          <Link className="inline-flex min-h-11 items-center px-2 text-xs font-medium text-muted-foreground hover:text-foreground" href={clearHref}>
            {copy.common.clearAllFilters}
          </Link>
        ) : null}
      </div>

      <div className="flex min-w-0 items-center gap-2 overflow-x-auto pb-1 lg:justify-end lg:pb-0">
        <span className="inline-flex shrink-0 items-center gap-1.5 pr-1 text-xs font-semibold text-muted-foreground">
          <ArrowDownUp className="size-3.5" aria-hidden="true" />
          {copy.grid.sortBy}
        </span>
        {options.map((option) => (
          <SortLink
            active={filters.sortBy === option.value}
            href={buildCatalogHref(catalogPath, { ...filters, page: 1, sortBy: option.value, sortOrder: option.order })}
            key={option.value}
          >
            {option.label}
          </SortLink>
        ))}
        <span className="ml-1 h-6 w-px shrink-0 bg-border" aria-hidden="true" />
        <ResponsiveCatalogViewToggle
          gridHref={buildCatalogHref(catalogPath, { ...filters, viewMode: "grid" })}
          gridLabel={copy.grid.gridView}
          groupLabel={copy.grid.viewMode}
          listHref={buildCatalogHref(catalogPath, { ...filters, viewMode: "list" })}
          listLabel={copy.grid.listView}
          viewMode={filters.viewMode}
        />
      </div>
    </section>
  );
}

function SortLink({ active, children, href }: { active: boolean; children: ReactNode; href: string }) {
  return (
    <Link
      aria-current={active ? "page" : undefined}
      className={cn(
        "inline-flex min-h-11 shrink-0 items-center whitespace-nowrap rounded-full border px-3 py-1 text-xs font-semibold transition-colors",
        active ? "border-foreground bg-foreground text-background" : "border-border bg-card/60 text-muted-foreground hover:border-foreground/30 hover:text-foreground"
      )}
      href={href}
    >
      {children}
    </Link>
  );
}

function FilterGroup({ label, children }: Readonly<{ label: string; children: ReactNode }>) {
  return (
    <fieldset className="space-y-2">
      <legend className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</legend>
      {children}
    </fieldset>
  );
}

function OptionGrid({
  name,
  locale,
  options,
  selectedValues
}: Readonly<{
  name: string;
  locale: string;
  options: PublicFilterOption[];
  selectedValues: Set<string>;
}>) {
  if (!options.length) {
    return <p className="rounded-lg border border-dashed border-border px-3 py-4 text-sm text-muted-foreground">{getPublicMessages(locale).common.noOptions}</p>;
  }

  return (
    <div className="grid max-h-52 gap-2 overflow-y-auto pr-1 sm:grid-cols-2">
      {options.map((option) => (
        <label
          key={[option.value, selectedValues.has(option.value)].join("-")}
          className={cn(
            "flex min-h-11 cursor-pointer items-center gap-2 rounded-lg border px-2.5 py-2 text-sm transition-colors hover:bg-muted/70",
            selectedValues.has(option.value) ? "border-primary/40 bg-primary/5" : "border-border bg-background"
          )}
        >
          <input className="size-4 rounded border-border text-primary" defaultChecked={selectedValues.has(option.value)} name={name} type="checkbox" value={option.value} />
          <span className="flex min-w-0 flex-1 items-center justify-between gap-2">
            <span className="truncate font-medium text-foreground">{option.label}</span>
            <span className="shrink-0 rounded-md bg-muted px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground tabular-nums">{option.count}</span>
          </span>
        </label>
      ))}
    </div>
  );
}

function SelectField({
  label,
  locale,
  name,
  options,
  value
}: Readonly<{
  label: string;
  locale: string;
  name: string;
  options: Array<{ label: string; value: string }>;
  value: string;
}>) {
  return (
    <label className="space-y-1.5">
      <span className="text-sm font-medium text-foreground">{label}</span>
      <select
        className="h-11 w-full rounded-lg border border-input bg-background px-3 text-sm text-foreground outline-none transition focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        defaultValue={value}
        key={[name, value].join("-")}
        name={name}
      >
        <option value="">{getPublicMessages(locale).common.all}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function buildActiveChips(filters: ProductGridPageFilters, filterOptions: PublicFiltersResponse, catalogPath: CatalogPath) {
  const chips: Array<{ group: string; href: string; label: string; value: string }> = [];

  if (filters.searchQuery) {
    chips.push({
      group: "q",
      href: buildCatalogHref(catalogPath, { ...filters, searchQuery: "", page: 1 }),
      label: formatPublicMessage(getPublicDiscoveryCopy(filters.locale).searchChip, { query: filters.searchQuery }),
      value: filters.searchQuery
    });
  }

  for (const bankCode of filters.bankCodes) {
    chips.push({
      group: "bank_code",
      href: buildCatalogHref(catalogPath, { ...filters, bankCodes: filters.bankCodes.filter((value) => value !== bankCode), page: 1 }),
      label: findLabel(filterOptions.banks, bankCode),
      value: bankCode
    });
  }
  for (const productType of filters.productTypes) {
    chips.push({
      group: "product_type",
      href: buildCatalogHref(catalogPath, { ...filters, productTypes: filters.productTypes.filter((value) => value !== productType), page: 1 }),
      label: findLabel(filterOptions.product_types, productType),
      value: productType
    });
  }
  for (const tag of filters.targetCustomerTags) {
    chips.push({
      group: "target_customer_tag",
      href: buildCatalogHref(catalogPath, { ...filters, targetCustomerTags: filters.targetCustomerTags.filter((value) => value !== tag), page: 1 }),
      label: findLabel(filterOptions.target_customer_tags, tag),
      value: tag
    });
  }

  addSingleChip(chips, "fee_bucket", filters.feeBucket, filterOptions.fee_buckets, buildCatalogHref(catalogPath, { ...filters, feeBucket: "", page: 1 }));
  addSingleChip(chips, "minimum_balance_bucket", filters.minimumBalanceBucket, filterOptions.minimum_balance_buckets, buildCatalogHref(catalogPath, { ...filters, minimumBalanceBucket: "", page: 1 }));
  addSingleChip(chips, "minimum_deposit_bucket", filters.minimumDepositBucket, filterOptions.minimum_deposit_buckets, buildCatalogHref(catalogPath, { ...filters, minimumDepositBucket: "", page: 1 }));
  addSingleChip(chips, "term_bucket", filters.termBucket, filterOptions.term_buckets, buildCatalogHref(catalogPath, { ...filters, termBucket: "", page: 1 }));

  return chips;
}

function addSingleChip(
  chips: Array<{ group: string; href: string; label: string; value: string }>,
  group: string,
  value: string,
  options: Array<{ label: string; value: string }>,
  href: string
) {
  if (value) {
    chips.push({ group, href, label: findLabel(options, value), value });
  }
}

function buildCatalogHref(catalogPath: CatalogPath, filters: ProductGridPageFilters) {
  return buildPublicHref(catalogPath, filters);
}

type CatalogPath = "/cards" | "/loans" | "/products";

function findLabel(options: Array<{ label: string; value: string }>, value: string) {
  return options.find((option) => option.value === value)?.label ?? value;
}

function formatCount(value: number, locale: string) {
  return new Intl.NumberFormat(getIntlLocale(locale), { maximumFractionDigits: 0 }).format(value);
}

function breadcrumbLabel(locale: string) {
  return locale === "ko" ? "경로" : locale === "ja" ? "パンくず" : "Breadcrumb";
}

function paginationLabel(locale: string) {
  return locale === "ko" ? "상품 결과 페이지" : locale === "ja" ? "商品結果ページ" : "Product result pages";
}

function previousPageLabel(locale: string) {
  return locale === "ko" ? "이전 상품" : locale === "ja" ? "前の商品" : "Previous products";
}

function nextPageLabel(locale: string) {
  return locale === "ko" ? "다음 상품" : locale === "ja" ? "次の商品" : "Next products";
}
