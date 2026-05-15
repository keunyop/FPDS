import { ArrowUpRight, Filter, RefreshCw } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getIntlLocale, getPublicMessages } from "@/lib/public-locale";
import { type PublicFilterOption, type PublicFiltersResponse, type PublicProduct, type PublicProductsResponse } from "@/lib/public-api";
import { buildPublicHref, type ProductGridPageFilters } from "@/lib/public-query";
import { cn } from "@/lib/utils";

type ProductGridSurfaceProps = {
  apiUnavailable: boolean;
  filterOptions: PublicFiltersResponse | null;
  filters: ProductGridPageFilters;
  products: PublicProductsResponse | null;
};

export function ProductGridSurface({ apiUnavailable, filterOptions, filters, products }: ProductGridSurfaceProps) {
  const copy = getPublicMessages(filters.locale);
  const dashboardHref = buildPublicHref("/dashboard", filters);
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
            <Button asChild variant="outline">
              <Link href={dashboardHref}>{copy.grid.openDashboard}</Link>
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  const activeChips = buildActiveChips(filters, filterOptions);
  const selectedTypes = new Set(filters.productTypes);
  const gicOnly = selectedTypes.size === 1 && selectedTypes.has("gic");
  const showMinimumBalance = !gicOnly;
  const showMinimumDeposit = selectedTypes.size === 0 || selectedTypes.has("gic");
  const showTermBucket = gicOnly;
  const pagination = buildPagination(products, filters);
  const sortOptions = [
    { value: "default", label: copy.grid.sortDefault },
    { value: "display_rate", label: copy.grid.sortDisplayRate },
    { value: "monthly_fee", label: copy.grid.sortMonthlyFee },
    { value: "minimum_balance", label: copy.grid.sortMinimumBalance },
    { value: "minimum_deposit", label: copy.grid.sortMinimumDeposit },
    { value: "last_changed_at", label: copy.grid.sortLastChange },
    { value: "bank_name", label: copy.grid.sortBankName },
    { value: "product_name", label: copy.grid.sortProductName }
  ];

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 md:px-6">
      <div className="flex flex-col gap-6">
        <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
          <div>
            <p className="text-sm font-medium text-primary">{copy.nav.products}</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-foreground md:text-4xl">{copy.grid.title}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">{copy.grid.description}</p>
          </div>
          <Button asChild variant="outline">
            <Link href={dashboardHref}>
              {copy.grid.openDashboard}
              <ArrowUpRight className="size-4" aria-hidden="true" />
            </Link>
          </Button>
        </section>

        <Card>
          <CardHeader className="flex-row items-center justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Filter className="size-4 text-muted-foreground" aria-hidden="true" />
                {copy.grid.currentScope}
              </CardTitle>
              <CardDescription>{formatFreshnessLine(products.freshness, filters.locale)}</CardDescription>
            </div>
            <Button asChild variant="outline">
              <Link href={clearHref}>{copy.common.clearAllFilters}</Link>
            </Button>
          </CardHeader>
          <CardContent>
            <form action="/products" className="grid gap-5">
              <input name="locale" type="hidden" value={filters.locale} />
              <div className="grid gap-5 xl:grid-cols-3">
                <FilterGroup helper={copy.grid.primaryFilter} label={copy.grid.banks}>
                  <OptionGrid locale={filters.locale} name="bank_code" options={filterOptions.banks} selectedValues={new Set(filters.bankCodes)} />
                </FilterGroup>
                <FilterGroup helper={copy.grid.primaryFilter} label={copy.grid.productTypes}>
                  <OptionGrid locale={filters.locale} name="product_type" options={filterOptions.product_types} selectedValues={new Set(filters.productTypes)} />
                </FilterGroup>
                <FilterGroup helper={copy.grid.primaryFilter} label={copy.grid.targetTags}>
                  <OptionGrid
                    locale={filters.locale}
                    name="target_customer_tag"
                    options={filterOptions.target_customer_tags}
                    selectedValues={new Set(filters.targetCustomerTags)}
                  />
                </FilterGroup>
              </div>

              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
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
                <SelectField locale={filters.locale} label={copy.grid.sortBy} name="sort_by" options={sortOptions} value={filters.sortBy} />
                <SelectField
                  locale={filters.locale}
                  label={copy.grid.direction}
                  name="sort_order"
                  options={[
                    { value: "desc", label: copy.grid.descending },
                    { value: "asc", label: copy.grid.ascending }
                  ]}
                  value={filters.sortOrder}
                />
              </div>

              <div className="flex justify-end gap-2 border-t border-border pt-4">
                <Button type="submit">{copy.common.applyFilters}</Button>
                <Button asChild type="button" variant="outline">
                  <Link href={clearHref}>{copy.common.clearFilters}</Link>
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <section className="flex flex-col gap-3 rounded-lg border border-border bg-card px-4 py-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-medium text-foreground">{copy.grid.resultSummary}</p>
            <p className="text-sm text-muted-foreground">{buildResultTitle(products.total_items, filters.locale)}</p>
          </div>
          <div className="flex flex-wrap gap-2">
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
              <span className="text-sm text-muted-foreground">{copy.grid.noActiveFilters}</span>
            )}
          </div>
        </section>

        {products.items.length ? (
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {products.items.map((product) => (
              <ProductCard key={product.product_id} locale={filters.locale} product={product} />
            ))}
          </section>
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
              <Button asChild variant="outline">
                <Link href={dashboardHref}>{copy.grid.openDashboard}</Link>
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

function ProductCard({ locale, product }: { locale: string; product: PublicProduct }) {
  const copy = getPublicMessages(locale);
  const metrics = buildPrimaryMetrics(product, locale);
  const tags = product.target_customer_tag_labels.slice(0, 2);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardDescription>{product.bank_name}</CardDescription>
            <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-primary">{product.product_type_label}</p>
            <CardTitle className="mt-2 leading-snug">{product.product_name}</CardTitle>
          </div>
          {product.product_highlight_badge_label ? <Badge>{product.product_highlight_badge_label}</Badge> : null}
        </div>
        {tags.length ? (
          <div className="flex flex-wrap gap-2 pt-1">
            {tags.map((tag) => (
              <Badge key={tag} muted>
                {tag}
              </Badge>
            ))}
          </div>
        ) : null}
      </CardHeader>
      <CardContent>
        <dl className="grid gap-2 sm:grid-cols-3">
          {metrics.map((metric) => (
            <div key={metric.label} className="rounded-lg border border-border bg-background p-3">
              <dt className="text-xs font-medium text-muted-foreground">{metric.label}</dt>
              <dd className="mt-1 text-base font-semibold tabular-nums text-foreground">{metric.value}</dd>
            </div>
          ))}
        </dl>
        <div className="mt-4 flex flex-wrap justify-between gap-3 border-t border-border pt-3 text-xs text-muted-foreground">
          <span>{buildChangeHint(product.last_changed_at, locale)}</span>
          <span>
            {copy.common.verifiedOn} {formatCompactDate(product.last_verified_at, locale)}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

function Badge({ children, muted = false }: { children: ReactNode; muted?: boolean }) {
  return (
    <span className={cn("rounded-md border px-2 py-1 text-xs font-medium", muted ? "border-border bg-background text-muted-foreground" : "border-primary/20 bg-secondary text-secondary-foreground")}>
      {children}
    </span>
  );
}

function FilterGroup({ helper, label, children }: Readonly<{ helper: string; label: string; children: ReactNode }>) {
  return (
    <fieldset className="space-y-2">
      <legend className="text-sm font-medium text-foreground">{label}</legend>
      <p className="text-xs text-muted-foreground">{helper}</p>
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
            "flex cursor-pointer items-start gap-2 rounded-lg border px-3 py-2 text-sm transition-colors hover:bg-muted/70",
            selectedValues.has(option.value) ? "border-primary/35 bg-secondary" : "border-border bg-background"
          )}
        >
          <input className="mt-0.5 size-4 rounded border-border text-primary" defaultChecked={selectedValues.has(option.value)} name={name} type="checkbox" value={option.value} />
          <span className="min-w-0">
            <span className="block truncate font-medium text-foreground">{option.label}</span>
            <span className="text-xs text-muted-foreground">{option.count}</span>
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

function buildPrimaryMetrics(product: PublicProduct, locale: string) {
  const copy = getPublicMessages(locale);
  if (product.product_type === "chequing") {
    return [
      { label: copy.grid.metricMonthlyFee, value: formatCurrency(product.public_display_fee, product.currency, locale) },
      { label: copy.grid.metricMinBalance, value: formatCurrency(product.minimum_balance, product.currency, locale) },
      { label: product.product_highlight_badge_label ? copy.grid.metricKeyDetail : copy.grid.metricLastChange, value: product.product_highlight_badge_label ?? formatCompactDate(product.last_changed_at, locale) }
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
    { label: product.product_highlight_badge_label ? copy.grid.metricRateNote : copy.grid.metricLastChange, value: product.product_highlight_badge_label ?? formatCompactDate(product.last_changed_at, locale) }
  ];
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

function findLabel(options: Array<{ label: string; value: string }>, value: string) {
  return options.find((option) => option.value === value)?.label ?? value;
}

function buildResultTitle(totalItems: number, locale: string) {
  const copy = getPublicMessages(locale);
  if (locale === "ko") {
    return `${formatCount(totalItems, locale)}개 ${copy.common.active} 상품`;
  }
  if (locale === "ja") {
    return `${formatCount(totalItems, locale)} 件の${copy.common.active}商品`;
  }
  return `${formatCount(totalItems, locale)} ${copy.common.active.toLowerCase()} products`;
}

function buildChangeHint(timestamp: string | null, locale: string) {
  const copy = getPublicMessages(locale);
  if (!timestamp) {
    return copy.common.noRecentChange;
  }
  return `${copy.common.changedOn} ${formatCompactDate(timestamp, locale)}`;
}

function formatFreshnessLine(freshness: PublicProductsResponse["freshness"], locale: string) {
  const copy = getPublicMessages(locale);
  if (!freshness.refreshed_at) {
    return copy.common.noSuccessfulSnapshot;
  }
  return `${copy.dashboard?.freshness ?? "Freshness"}: ${formatFixedDateTime(freshness.refreshed_at)}`;
}

function formatCurrency(value: number | null, currency: string, locale: string) {
  const copy = getPublicMessages(locale);
  if (value === null || Number.isNaN(value)) {
    return copy.common.notDisclosed;
  }
  return new Intl.NumberFormat(getIntlLocale(locale), {
    style: "currency",
    currency,
    maximumFractionDigits: Number.isInteger(value) ? 0 : 2
  }).format(value);
}

function formatRate(value: number | null, locale: string) {
  const copy = getPublicMessages(locale);
  if (value === null || Number.isNaN(value)) {
    return copy.common.notDisclosed;
  }
  return `${value.toFixed(2).replace(/\.?0+$/, "")}%`;
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

function formatCompactDate(value: string | null, locale: string) {
  const copy = getPublicMessages(locale);
  if (!value) {
    return copy.common.noDate;
  }
  return formatFixedDate(value);
}

function formatFixedDate(value: string) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return value;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  const pad = (part: number) => String(part).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function formatFixedDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  const pad = (part: number) => String(part).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function formatCount(value: number, locale: string) {
  return new Intl.NumberFormat(getIntlLocale(locale), {
    maximumFractionDigits: Number.isInteger(value) ? 0 : 2
  }).format(value);
}
