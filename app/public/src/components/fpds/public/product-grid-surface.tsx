import { ArrowDownUp, ChevronDown, RefreshCw, SlidersHorizontal, X } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { ProductCompareWorkspace } from "@/components/fpds/public/product-compare-workspace";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatPublicMessage, getIntlLocale, getPublicCatalogCopy, getPublicMessages } from "@/lib/public-locale";
import { type PublicFilterOption, type PublicFiltersResponse, type PublicProductsResponse } from "@/lib/public-api";
import { buildPublicHref, type ProductGridPageFilters } from "@/lib/public-query";
import { cn } from "@/lib/utils";

type ProductGridSurfaceProps = {
  apiUnavailable: boolean;
  catalog: "deposit" | "loan";
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
  const catalogCopy = getPublicCatalogCopy(filters.locale, catalog);
  const catalogPath = catalog === "loan" ? "/loans" : "/products";
  const clearHref = buildCatalogHref(catalogPath, {
    ...filters,
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
            <CardTitle>{copy.grid.retryTitle}</CardTitle>
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
  const pagination = buildPagination(products, filters, catalogPath);
  const sortOptions: SortOption[] = catalog === "loan"
    ? [
        { value: "display_rate", label: copy.grid.sortDisplayRate, order: "asc" },
        { value: "bank_name", label: copy.grid.sortBankName, order: "asc" },
        { value: "product_name", label: copy.grid.sortProductName, order: "asc" }
      ]
    : [
        { value: "display_rate", label: copy.grid.sortDisplayRate, order: "desc" },
        { value: "monthly_fee", label: copy.grid.sortMonthlyFee, order: "asc" },
        { value: "minimum_balance", label: copy.grid.sortMinimumBalance, order: "asc" }
      ];

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6 md:py-8">
      <div className="flex flex-col gap-4">
        <section className="overflow-hidden rounded-2xl border border-border/80 bg-card shadow-sm">
          <div className="grid gap-5 px-5 py-6 md:px-7 md:py-8 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
            <div className="max-w-3xl">
              <p className="text-sm font-semibold text-primary">{catalog === "loan" ? copy.nav.loan : copy.nav.products}</p>
              <h1 className="mt-2 text-3xl font-semibold leading-tight tracking-tight text-foreground md:text-4xl">{catalogCopy.title}</h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">{catalogCopy.description}</p>
            </div>
            <div className="grid min-w-0 grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-2 lg:min-w-72">
              <CatalogStat label={copy.grid.resultSummary} value={formatPublicMessage(copy.grid.productCount, { count: formatCount(products.total_items, filters.locale) })} />
              <CatalogStat label={copy.dashboard.freshness} value={formatFreshnessDate(products.freshness.refreshed_at, filters.locale)} />
            </div>
          </div>
        </section>

        <Card className="gap-0 overflow-hidden border-border/80 shadow-sm">
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
              <form action={catalogPath} className="grid gap-4">
                <input name="locale" type="hidden" value={filters.locale} />
                <input name="sort_by" type="hidden" value={filters.sortBy} />
                <input name="sort_order" type="hidden" value={filters.sortOrder} />

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

                <div className="flex flex-col-reverse gap-2 border-t border-border/70 pt-4 sm:flex-row sm:justify-end">
                  <Button asChild type="button" variant="outline">
                    <Link href={clearHref}>{copy.common.clearFilters}</Link>
                  </Button>
                  <Button className="sm:min-w-24" type="submit">{copy.common.applyFilters}</Button>
                </div>
              </form>
            </CardContent>
          </details>
        </Card>

        <DiscoveryToolbar
          activeChips={activeChips}
          catalogPath={catalogPath}
          clearHref={clearHref}
          filters={filters}
          options={sortOptions}
        />

        {products.items.length ? (
          <ProductCompareWorkspace filters={filters} locale={filters.locale} products={products.items} />
        ) : (
          <Card className="border-dashed">
            <CardHeader>
              <CardTitle>{copy.grid.noResultTitle}</CardTitle>
              <CardDescription>{copy.grid.noResultBody}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild>
                <Link href={clearHref}>{copy.common.clearFilters}</Link>
              </Button>
            </CardContent>
          </Card>
        )}

        {pagination ? (
          <nav className="flex items-center justify-between gap-3 rounded-xl border border-border bg-card px-4 py-3" aria-label={copy.common.pageLabel}>
            <p className="text-sm text-muted-foreground tabular-nums">
              {copy.common.pageLabel} {products.page} / {products.total_pages}
            </p>
            <div className="flex gap-2">
              <Button asChild variant="outline">
                <Link aria-disabled={!pagination.hasPrevious} className={cn(!pagination.hasPrevious && "pointer-events-none opacity-50")} href={pagination.previousHref}>
                  {copy.common.previous}
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link aria-disabled={!pagination.hasNext} className={cn(!pagination.hasNext && "pointer-events-none opacity-50")} href={pagination.nextHref}>
                  {copy.common.next}
                </Link>
              </Button>
            </div>
          </nav>
        ) : null}
      </div>
    </main>
  );
}

function CatalogStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-xl border border-border/80 bg-muted/25 px-3 py-3">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-1 break-words text-sm font-semibold leading-snug text-foreground tabular-nums">{value}</p>
    </div>
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
  catalogPath: "/loans" | "/products";
  clearHref: string;
  filters: ProductGridPageFilters;
  options: SortOption[];
}) {
  const copy = getPublicMessages(filters.locale);

  return (
    <section className="grid gap-3 rounded-xl border border-border bg-card px-4 py-3 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
      <div className="flex min-w-0 flex-wrap items-center gap-2">
        {activeChips.length ? (
          activeChips.map((chip) => (
            <Link
              className="inline-flex min-h-9 items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-semibold text-primary transition-colors hover:bg-primary/10"
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
          <Link className="min-h-9 px-2 py-2 text-xs font-medium text-muted-foreground hover:text-foreground" href={clearHref}>
            {copy.common.clearAllFilters}
          </Link>
        ) : null}
      </div>

      <div className="flex min-w-0 items-center gap-2 overflow-x-auto pb-1 lg:justify-end lg:pb-0">
        <span className="inline-flex shrink-0 items-center gap-1.5 pr-1 text-xs font-semibold text-muted-foreground">
          <ArrowDownUp className="size-3.5" aria-hidden="true" />
          {copy.grid.sortBy}
        </span>
        <SortLink active={filters.sortBy === "default"} href={buildCatalogHref(catalogPath, { ...filters, page: 1, sortBy: "default", sortOrder: "desc" })}>
          {copy.grid.sortDefault}
        </SortLink>
        {options.map((option) => (
          <SortLink
            active={filters.sortBy === option.value}
            href={buildCatalogHref(catalogPath, { ...filters, page: 1, sortBy: option.value, sortOrder: option.order })}
            key={option.value}
          >
            {option.label}
          </SortLink>
        ))}
      </div>
    </section>
  );
}

function SortLink({ active, children, href }: { active: boolean; children: ReactNode; href: string }) {
  return (
    <Link
      aria-current={active ? "page" : undefined}
      className={cn(
        "inline-flex min-h-9 shrink-0 items-center rounded-full border px-3 py-1 text-xs font-semibold transition-colors",
        active ? "border-primary bg-primary text-primary-foreground" : "border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground"
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
          key={option.value}
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

function buildActiveChips(filters: ProductGridPageFilters, filterOptions: PublicFiltersResponse, catalogPath: "/loans" | "/products") {
  const chips: Array<{ group: string; href: string; label: string; value: string }> = [];

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

function buildPagination(products: PublicProductsResponse, filters: ProductGridPageFilters, catalogPath: "/loans" | "/products") {
  if (products.total_pages <= 1) {
    return null;
  }

  return {
    hasPrevious: products.page > 1,
    hasNext: products.page < products.total_pages,
    previousHref: buildCatalogHref(catalogPath, { ...filters, page: Math.max(1, products.page - 1) }),
    nextHref: buildCatalogHref(catalogPath, { ...filters, page: Math.min(products.total_pages, products.page + 1) })
  };
}

function buildCatalogHref(catalogPath: "/loans" | "/products", filters: ProductGridPageFilters) {
  return buildPublicHref(catalogPath, filters);
}

function findLabel(options: Array<{ label: string; value: string }>, value: string) {
  return options.find((option) => option.value === value)?.label ?? value;
}

function formatCount(value: number, locale: string) {
  return new Intl.NumberFormat(getIntlLocale(locale), { maximumFractionDigits: 0 }).format(value);
}

function formatFreshnessDate(value: string | null, locale: string) {
  const copy = getPublicMessages(locale);
  if (!value) {
    return copy.common.noDate;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value.slice(0, 10);
  }
  return date.toISOString().slice(0, 10);
}
