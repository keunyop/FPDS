import { ArrowDownUp, ArrowRight, ChevronDown, ExternalLink, RefreshCw, SlidersHorizontal, Trophy } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { BankLogo } from "@/components/fpds/public/bank-logo";
import { ProductCompareWorkspace } from "@/components/fpds/public/product-compare-workspace";
import { PurposeEntryPoints } from "@/components/fpds/public/purpose-entry-points";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatPublicMessage, getIntlLocale, getPublicMessages } from "@/lib/public-locale";
import { type PublicFilterOption, type PublicFiltersResponse, type PublicProduct, type PublicProductsResponse } from "@/lib/public-api";
import { buildPublicHref, type ProductGridPageFilters } from "@/lib/public-query";
import { cn } from "@/lib/utils";

type ProductGridSurfaceProps = {
  apiUnavailable: boolean;
  filterOptions: PublicFiltersResponse | null;
  filters: ProductGridPageFilters;
  products: PublicProductsResponse | null;
  topProducts: PublicProductsResponse | null;
};

export function ProductGridSurface({ apiUnavailable, filterOptions, filters, products, topProducts }: ProductGridSurfaceProps) {
  const copy = getPublicMessages(filters.locale);
  const clearHref = buildPublicHref("/products", {
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
          <CardContent className="flex flex-wrap gap-2">
            <Button asChild>
              <Link href={buildPublicHref("/products", filters)}>
                <RefreshCw className="size-4" aria-hidden="true" />
                {copy.grid.retryButton}
              </Link>
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  const activeChips = buildActiveChips(filters, filterOptions);
  const dashboardHref = buildPublicHref("/dashboard", filters);
  const selectedTypes = new Set(filters.productTypes);
  const gicOnly = selectedTypes.size === 1 && selectedTypes.has("gic");
  const showMinimumBalance = !gicOnly;
  const showMinimumDeposit = selectedTypes.size === 0 || selectedTypes.has("gic");
  const showTermBucket = gicOnly;
  const pagination = buildPagination(products, filters);
  const topListItems = topProducts?.items ?? products.items.slice(0, 5);
  const sortOptions = [
    { value: "display_rate", label: copy.grid.sortDisplayRate, order: "desc" as const },
    { value: "monthly_fee", label: copy.grid.sortMonthlyFee, order: "asc" as const },
    { value: "minimum_balance", label: copy.grid.sortMinimumBalance, order: "asc" as const }
  ];

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-7 md:px-6 md:py-9">
      <div className="flex flex-col gap-5">
        <section className="grid gap-5 rounded-xl border border-border/80 bg-[linear-gradient(135deg,#ffffff_0%,#f7f9ff_55%,#eefbf7_100%)] p-5 shadow-sm md:p-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
          <div className="max-w-3xl">
            <p className="text-sm font-medium text-primary">{copy.grid.resultSummary}</p>
            <h1 className="mt-2 text-3xl font-semibold leading-tight text-foreground md:text-4xl">{copy.grid.title}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">{copy.grid.description}</p>
          </div>
          <div className="flex flex-wrap gap-2 lg:justify-end">
            <Button asChild>
              <Link href={dashboardHref}>{copy.grid.openDashboard}</Link>
            </Button>
          </div>
        </section>

        <PurposeEntryPoints filters={filters} locale={filters.locale} />

        <Card className="gap-0 overflow-hidden border-border/80 shadow-sm">
          <details className="group" open>
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 border-b border-transparent px-4 py-3 text-sm font-medium text-foreground outline-none transition hover:bg-muted/40 hover:text-primary focus-visible:ring-3 focus-visible:ring-ring/50 group-open:border-border/70 group-open:bg-muted/25 sm:px-5 [&::-webkit-details-marker]:hidden">
              <span className="flex items-center gap-2">
                <SlidersHorizontal className="size-4 text-muted-foreground" aria-hidden="true" />
                {copy.grid.searchConditions}
              </span>
              <ChevronDown className="size-4 text-muted-foreground transition-transform group-open:rotate-180" aria-hidden="true" />
            </summary>
            <CardContent className="px-4 py-4 sm:px-5">
              <form action="/products" className="grid gap-4">
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
                  <FilterGroup label={copy.grid.targetTags}>
                    <OptionGrid
                      locale={filters.locale}
                      name="target_customer_tag"
                      options={filterOptions.target_customer_tags}
                      selectedValues={new Set(filters.targetCustomerTags)}
                    />
                  </FilterGroup>
                </div>

                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                  <SelectField locale={filters.locale} label={copy.grid.feeBucket} name="fee_bucket" options={filterOptions.fee_buckets} value={filters.feeBucket} />
                  {showMinimumBalance ? (
                    <SelectField
                      locale={filters.locale}
                      label={copy.grid.minimumBalance}
                      name="minimum_balance_bucket"
                      options={filterOptions.minimum_balance_buckets}
                      value={filters.minimumBalanceBucket}
                    />
                  ) : null}
                  {showMinimumDeposit ? (
                    <SelectField
                      locale={filters.locale}
                      label={copy.grid.minimumDeposit}
                      name="minimum_deposit_bucket"
                      options={filterOptions.minimum_deposit_buckets}
                      value={filters.minimumDepositBucket}
                    />
                  ) : null}
                  {showTermBucket ? (
                    <SelectField locale={filters.locale} label={copy.grid.termBucket} name="term_bucket" options={filterOptions.term_buckets} value={filters.termBucket} />
                  ) : null}
                </div>

                <div className="flex flex-col-reverse gap-2 border-t border-border/70 pt-4 sm:flex-row sm:justify-end">
                  <Button type="submit" className="sm:min-w-20">
                    {copy.common.applyFilters}
                  </Button>
                  <Button asChild type="button" variant="outline">
                    <Link href={clearHref}>{copy.common.clearFilters}</Link>
                  </Button>
                </div>
              </form>
            </CardContent>
          </details>
        </Card>

        <section className="grid gap-3 rounded-lg border border-border bg-card px-4 py-3 shadow-sm lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <p className="text-sm font-semibold text-foreground">
                {formatPublicMessage(copy.grid.productCount, { count: formatCount(products.total_items, filters.locale) })}
              </p>
              <p className="text-xs font-medium text-muted-foreground">
                {formatPublicMessage(copy.grid.snapshotUpdated, { date: formatFreshnessDate(products.freshness.refreshed_at, filters.locale) })}
              </p>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {activeChips.length ? (
                activeChips.map((chip) => (
                  <Link
                    key={`${chip.group}-${chip.value}`}
                    href={chip.href}
                    className="rounded-md border border-border bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
                  >
                    {chip.label}
                  </Link>
                ))
              ) : (
                <span className="rounded-md border border-border bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground">{copy.grid.noActiveFilters}</span>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-2 lg:justify-end">
            {activeChips.length ? (
              <Button asChild variant="outline" size="sm">
                <Link href={clearHref}>{copy.common.clearAllFilters}</Link>
              </Button>
            ) : null}
          </div>
        </section>

        <SortToolbar filters={filters} locale={filters.locale} options={sortOptions} />

        <TopProductList filters={filters} locale={filters.locale} products={topListItems} />

        {products.items.length ? (
          <ProductCompareWorkspace filters={filters} locale={filters.locale} products={products.items} />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>{copy.grid.noResultTitle}</CardTitle>
              <CardDescription>{copy.grid.noResultBody}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              <Button asChild>
                <Link href={clearHref}>{copy.common.clearFilters}</Link>
              </Button>
            </CardContent>
          </Card>
        )}

        {pagination ? (
          <section className="flex flex-col gap-3 rounded-lg border border-border bg-card px-4 py-3 md:flex-row md:items-center md:justify-between">
            <p className="text-sm text-muted-foreground">
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
          </section>
        ) : null}
      </div>
    </main>
  );
}

function ProductCard({ filters, locale, product }: { filters: ProductGridPageFilters; locale: string; product: PublicProduct }) {
  const copy = getPublicMessages(locale);
  const metrics = buildComparisonMetrics(product, locale);
  const tags = product.target_customer_tag_labels.slice(0, 2);
  const detailHref = buildProductDetailHref(filters, product.product_id);

  return (
    <Card className="h-full gap-3 overflow-hidden border-border/80 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md hover:ring-1 hover:ring-primary/15">
      <CardHeader className="pb-2">
        <div className="flex flex-col gap-4">
          <div className="flex items-start justify-between gap-3">
            <BankLogo bankCode={product.bank_code} bankName={product.bank_name} size="sm" />
            {product.product_url ? (
              <Button asChild variant="outline" size="xs" className="shrink-0">
                <a href={product.product_url} target="_blank" rel="noreferrer">
                  {copy.common.bankPage}
                  <ExternalLink className="size-3" aria-hidden="true" />
                </a>
              </Button>
            ) : null}
          </div>
          <div className="min-w-0">
            <CardDescription className="mb-2">
              <span className="inline-flex rounded-md bg-primary/5 px-2 py-1 text-[11px] font-semibold uppercase text-primary">{product.product_type_label}</span>
            </CardDescription>
            <CardTitle className="text-lg leading-snug">
              <Link className="break-words hover:text-primary" href={detailHref}>
                {product.product_name}
              </Link>
            </CardTitle>
          </div>
        </div>
        {product.product_highlight_badge_label || tags.length ? (
          <div className="flex flex-wrap gap-2 pt-2">
            {product.product_highlight_badge_label ? <Badge>{product.product_highlight_badge_label}</Badge> : null}
            {tags.map((tag) => (
              <Badge key={tag} muted>
                {tag}
              </Badge>
            ))}
          </div>
        ) : null}
      </CardHeader>
      <CardContent className="pt-0">
        <dl className="grid gap-2 sm:grid-cols-3">
          {metrics.map((metric, index) => (
            <div key={metric.label} className={cn("min-h-24 rounded-lg border p-3", index === 0 ? "border-primary/25 bg-primary/5" : "border-border bg-muted/30")}>
              <dt className="text-xs font-medium text-muted-foreground">{metric.label}</dt>
              <dd className="mt-2 break-words text-lg font-semibold tabular-nums leading-tight text-foreground">{metric.value}</dd>
            </div>
          ))}
        </dl>
        <div className="mt-4 flex items-center justify-between gap-3 border-t border-border/70 pt-3">
          <Link className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80" href={detailHref}>
            {copy.grid.compareDetails}
            <ArrowRight className="size-3.5" aria-hidden="true" />
          </Link>
          {product.subtype_label ? <span className="truncate text-xs font-medium text-muted-foreground">{product.subtype_label}</span> : null}
        </div>
      </CardContent>
    </Card>
  );
}

function TopProductList({
  filters,
  locale,
  products
}: {
  filters: ProductGridPageFilters;
  locale: string;
  products: PublicProduct[];
}) {
  const copy = getPublicMessages(locale);
  const sortLabel = getSortLabel(filters.sortBy, copy);
  const title =
    filters.sortBy === "default"
      ? copy.grid.topFiveDefaultTitle
      : formatPublicMessage(copy.grid.topFiveTitle, { sort: sortLabel });

  if (!products.length) {
    return null;
  }

  return (
    <section className="overflow-hidden rounded-xl border border-border/80 bg-card shadow-sm" aria-labelledby="top-products-title">
      <div className="grid gap-3 border-b border-border/70 bg-muted/25 px-4 py-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-sm font-medium text-primary">
            <Trophy className="size-4" aria-hidden="true" />
            {copy.grid.sortBy}
          </p>
          <h2 id="top-products-title" className="mt-1 text-xl font-semibold leading-tight text-foreground">
            {title}
          </h2>
        </div>
        <p className="max-w-xl text-sm leading-6 text-muted-foreground">{copy.grid.topFiveSubtitle}</p>
      </div>
      <div className="divide-y divide-border/70">
        {products.map((product, index) => {
          const metric = getSortMetric(product, filters.sortBy, locale);
          return (
            <Link
              className="grid gap-3 px-4 py-3 transition-colors hover:bg-muted/30 sm:grid-cols-[auto_auto_minmax(0,1fr)_auto] sm:items-center"
              href={buildProductDetailHref(filters, product.product_id)}
              key={product.product_id}
            >
              <span className="inline-flex size-8 items-center justify-center rounded-md bg-primary text-sm font-semibold text-primary-foreground tabular-nums">
                {index + 1}
              </span>
              <BankLogo bankCode={product.bank_code} bankName={product.bank_name} size="sm" />
              <span className="min-w-0">
                <span className="block break-words text-sm font-semibold text-foreground">{product.product_name}</span>
                <span className="mt-1 inline-flex rounded-md bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">{product.product_type_label}</span>
              </span>
              <span className="rounded-lg border border-border bg-background px-3 py-2 text-left sm:min-w-36 sm:text-right">
                <span className="block text-[11px] font-medium uppercase text-muted-foreground">{metric.label}</span>
                <span className="mt-1 block text-base font-semibold text-foreground tabular-nums">{metric.value}</span>
              </span>
            </Link>
          );
        })}
      </div>
    </section>
  );
}

function SortToolbar({
  filters,
  locale,
  options
}: {
  filters: ProductGridPageFilters;
  locale: string;
  options: Array<{ label: string; order: "asc" | "desc"; value: string }>;
}) {
  const copy = getPublicMessages(locale);
  return (
    <section className="flex flex-col gap-3 rounded-lg border border-border bg-card px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-2 text-sm font-medium text-foreground">
        <ArrowDownUp className="size-4 text-muted-foreground" aria-hidden="true" />
        {copy.grid.sortBy}
      </div>
      <div className="flex flex-wrap gap-2">
        <Link
          aria-current={filters.sortBy === "default" ? "page" : undefined}
          className={cn(
            "rounded-md border px-3 py-1.5 text-sm font-medium transition-colors",
            filters.sortBy === "default" ? "border-primary/40 bg-primary/5 text-primary" : "border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground"
          )}
          href={buildProductsHref(filters, { page: 1, sortBy: "default", sortOrder: "desc" })}
        >
          {copy.grid.sortDefault}
        </Link>
        {options.map((option) => {
          const active = filters.sortBy === option.value;
          return (
            <Link
              aria-current={active ? "page" : undefined}
              className={cn(
                "rounded-md border px-3 py-1.5 text-sm font-medium transition-colors",
                active ? "border-primary/40 bg-primary/5 text-primary" : "border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
              href={buildProductsHref(filters, { page: 1, sortBy: option.value, sortOrder: option.order })}
              key={option.value}
            >
              {option.label}
            </Link>
          );
        })}
      </div>
    </section>
  );
}

function Badge({ children, muted = false }: { children: ReactNode; muted?: boolean }) {
  return (
    <span className={cn("rounded-md border px-2 py-1 text-xs font-medium", muted ? "border-border bg-background text-muted-foreground" : "border-primary/20 bg-secondary text-secondary-foreground")}>
      {children}
    </span>
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
    <div className="grid gap-2 sm:grid-cols-2">
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
            <span className="shrink-0 rounded-md bg-muted px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground">{option.count}</span>
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
        className="h-9 w-full rounded-lg border border-input bg-background px-2.5 text-sm text-foreground outline-none transition focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
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

function getSortMetric(product: PublicProduct, sortBy: string, locale: string) {
  const copy = getPublicMessages(locale);
  switch (sortBy) {
    case "display_rate":
      return { label: copy.grid.metricDisplayRate, value: formatRate(product.public_display_rate, locale) };
    case "monthly_fee":
      return { label: copy.grid.metricMonthlyFee, value: formatCurrency(product.public_display_fee, product.currency, locale) };
    case "minimum_balance":
      return { label: copy.grid.metricMinBalance, value: formatCurrency(product.minimum_balance, product.currency, locale) };
    case "minimum_deposit":
      return { label: copy.grid.metricMinDeposit, value: formatCurrency(product.minimum_deposit, product.currency, locale) };
    case "last_changed_at":
      return { label: copy.grid.metricLastChange, value: formatDate(product.last_changed_at, locale) };
    default:
      return buildComparisonMetrics(product, locale)[0];
  }
}

function getSortLabel(sortBy: string, copy: ReturnType<typeof getPublicMessages>) {
  switch (sortBy) {
    case "display_rate":
      return copy.grid.sortDisplayRate;
    case "monthly_fee":
      return copy.grid.sortMonthlyFee;
    case "minimum_balance":
      return copy.grid.sortMinimumBalance;
    case "minimum_deposit":
      return copy.grid.sortMinimumDeposit;
    case "last_changed_at":
      return copy.grid.sortLastChange;
    case "bank_name":
      return copy.grid.sortBankName;
    case "product_name":
      return copy.grid.sortProductName;
    default:
      return copy.grid.sortDefault;
  }
}

function buildComparisonMetrics(product: PublicProduct, locale: string) {
  const copy = getPublicMessages(locale);
  if (product.product_type === "chequing") {
    return [
      { label: copy.grid.metricMonthlyFee, value: formatCurrency(product.public_display_fee, product.currency, locale) },
      { label: copy.grid.metricMinBalance, value: formatCurrency(product.minimum_balance, product.currency, locale) },
      { label: copy.grid.metricKeyDetail, value: buildKeyDetail(product, locale) }
    ];
  }

  if (product.product_type === "gic") {
    return [
      { label: copy.grid.metricDisplayRate, value: formatRate(product.public_display_rate, locale) },
      { label: copy.grid.metricTerm, value: formatTerm(product.term_length_days, locale) },
      { label: copy.grid.metricMinDeposit, value: formatCurrency(product.minimum_deposit, product.currency, locale) }
    ];
  }

  return [
    { label: copy.grid.metricDisplayRate, value: formatRate(product.public_display_rate, locale) },
    { label: copy.grid.metricMinBalance, value: formatCurrency(product.minimum_balance, product.currency, locale) },
    { label: copy.grid.metricKeyDetail, value: buildKeyDetail(product, locale) }
  ];
}

function buildKeyDetail(product: PublicProduct, locale: string) {
  const copy = getPublicMessages(locale);
  return product.product_highlight_badge_label ?? product.subtype_label ?? product.target_customer_tag_labels[0] ?? copy.common.notDisclosed;
}

function buildActiveChips(filters: ProductGridPageFilters, filterOptions: PublicFiltersResponse) {
  const chips: Array<{ group: string; href: string; label: string; value: string }> = [];

  for (const bankCode of filters.bankCodes) {
    chips.push({
      group: "bank_code",
      href: buildProductsHref(filters, { bankCodes: filters.bankCodes.filter((value) => value !== bankCode), page: 1 }),
      label: findLabel(filterOptions.banks, bankCode),
      value: bankCode
    });
  }
  for (const productType of filters.productTypes) {
    chips.push({
      group: "product_type",
      href: buildProductsHref(filters, { productTypes: filters.productTypes.filter((value) => value !== productType), page: 1 }),
      label: findLabel(filterOptions.product_types, productType),
      value: productType
    });
  }
  for (const tag of filters.targetCustomerTags) {
    chips.push({
      group: "target_customer_tag",
      href: buildProductsHref(filters, { targetCustomerTags: filters.targetCustomerTags.filter((value) => value !== tag), page: 1 }),
      label: findLabel(filterOptions.target_customer_tags, tag),
      value: tag
    });
  }

  addSingleChip(chips, "fee_bucket", filters.feeBucket, filterOptions.fee_buckets, buildProductsHref(filters, { feeBucket: "", page: 1 }));
  addSingleChip(
    chips,
    "minimum_balance_bucket",
    filters.minimumBalanceBucket,
    filterOptions.minimum_balance_buckets,
    buildProductsHref(filters, { minimumBalanceBucket: "", page: 1 })
  );
  addSingleChip(
    chips,
    "minimum_deposit_bucket",
    filters.minimumDepositBucket,
    filterOptions.minimum_deposit_buckets,
    buildProductsHref(filters, { minimumDepositBucket: "", page: 1 })
  );
  addSingleChip(chips, "term_bucket", filters.termBucket, filterOptions.term_buckets, buildProductsHref(filters, { termBucket: "", page: 1 }));

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

function buildPagination(products: PublicProductsResponse, filters: ProductGridPageFilters) {
  if (products.total_pages <= 1) {
    return null;
  }

  return {
    hasPrevious: products.page > 1,
    hasNext: products.page < products.total_pages,
    previousHref: buildProductsHref(filters, { page: Math.max(1, products.page - 1) }),
    nextHref: buildProductsHref(filters, { page: Math.min(products.total_pages, products.page + 1) })
  };
}

function buildProductsHref(filters: ProductGridPageFilters, overrides: Partial<ProductGridPageFilters>) {
  return buildPublicHref("/products", { ...filters, ...overrides });
}

function buildProductDetailHref(filters: ProductGridPageFilters, productId: string) {
  return buildPublicHref(`/products/${encodeURIComponent(productId)}`, filters);
}

function findLabel(options: Array<{ label: string; value: string }>, value: string) {
  return options.find((option) => option.value === value)?.label ?? value;
}

function formatCurrency(value: number | null, currency: string, locale: string) {
  const copy = getPublicMessages(locale);
  if (value === null || !Number.isFinite(value)) {
    return copy.common.notDisclosed;
  }
  const safeCurrency = normalizeCurrency(currency);
  return new Intl.NumberFormat(getIntlLocale(locale), {
    style: "currency",
    currency: safeCurrency,
    maximumFractionDigits: Number.isInteger(value) ? 0 : 2
  }).format(value);
}

function formatRate(value: number | null, locale: string) {
  const copy = getPublicMessages(locale);
  if (value === null || !Number.isFinite(value)) {
    return copy.common.notDisclosed;
  }
  return `${value.toFixed(2).replace(/\.?0+$/, "")}%`;
}

function formatCount(value: number, locale: string) {
  return new Intl.NumberFormat(getIntlLocale(locale), {
    maximumFractionDigits: 0
  }).format(value);
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
  return new Intl.DateTimeFormat(getIntlLocale(locale), {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(date);
}

function formatDate(value: string | null, locale: string) {
  const copy = getPublicMessages(locale);
  if (!value) {
    return copy.common.noDate;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(getIntlLocale(locale), {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(date);
}

function normalizeCurrency(currency: string) {
  const normalized = currency.trim().toUpperCase();
  return /^[A-Z]{3}$/.test(normalized) ? normalized : "CAD";
}

function formatTerm(termLengthDays: number | null, locale: string) {
  const copy = getPublicMessages(locale);
  if (termLengthDays === null || !Number.isFinite(termLengthDays)) {
    return copy.common.notDisclosed;
  }
  if (termLengthDays % 365 === 0) {
    const years = termLengthDays / 365;
    if (locale === "ko") {
      return `${years}년`;
    }
    if (locale === "ja") {
      return `${years}年`;
    }
    return `${years} year${years === 1 ? "" : "s"}`;
  }
  if (termLengthDays % 30 === 0) {
    const months = Math.round(termLengthDays / 30);
    if (locale === "ko") {
      return `${months}개월`;
    }
    if (locale === "ja") {
      return `${months}か月`;
    }
    return `${months} month${months === 1 ? "" : "s"}`;
  }
  if (locale === "ko") {
    return `${termLengthDays}일`;
  }
  if (locale === "ja") {
    return `${termLengthDays}日`;
  }
  return `${termLengthDays} days`;
}
