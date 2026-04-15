import Link from "next/link";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { formatPublicMessage, getIntlLocale, getPublicMessages } from "@/lib/public-locale";
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
  const dashboardHref = buildPublicHref("/dashboard", filters);
  const copy = getPublicMessages(filters.locale);
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

  if (apiUnavailable || !products || !filterOptions) {
    return (
      <main className="mx-auto flex w-full max-w-6xl px-4 py-12 md:px-6 md:py-16">
        <section className="w-full rounded-[2rem] border border-destructive/20 bg-card/95 p-8 shadow-[0_24px_60px_rgba(15,23,42,0.08)] md:p-10">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-destructive">{copy.grid.retryTitle}</p>
          <h1 className="mt-4 max-w-2xl text-4xl font-semibold tracking-tight text-foreground">{copy.grid.retryTitle}</h1>
          <p className="mt-4 max-w-3xl text-base leading-7 text-muted-foreground">
            {copy.grid.retryBody}
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild>
              <Link href={buildPublicHref("/products", filters)}>{copy.grid.retryButton}</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href={dashboardHref}>{copy.grid.openDashboard}</Link>
            </Button>
          </div>
        </section>
      </main>
    );
  }

  const activeChips = buildActiveChips(filters, filterOptions);
  const selectedProductTypes = new Set(filters.productTypes);
  const gicOnly = selectedProductTypes.size === 1 && selectedProductTypes.has("gic");
  const showMinimumBalance = !gicOnly;
  const showMinimumDeposit = selectedProductTypes.size === 0 || selectedProductTypes.has("gic");
  const showTermBucket = gicOnly;
  const pagination = buildPagination(products, filters);
  const scopeBankCount = filters.bankCodes.length || filterOptions.banks.length;
  const gridMetricNotes = buildGridMetricNotes(filterOptions, filters.locale);
  const gridFreshnessNotes = buildGridFreshnessNotes(products.freshness, filters.locale);

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 md:px-6 md:py-10">
      <section className="rounded-[2rem] border border-border/80 bg-card/85 p-6 shadow-[0_30px_80px_rgba(15,23,42,0.06)] md:p-8">
        <div className="flex flex-col gap-8">
          <header className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(20rem,0.8fr)] lg:items-end">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-primary">{copy.grid.eyebrow}</p>
              <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight text-foreground md:text-5xl">{copy.grid.title}</h1>
              <p className="mt-4 max-w-3xl text-base leading-7 text-muted-foreground">{copy.grid.description}</p>
            </div>
            <div className="rounded-[1.5rem] border border-border/70 bg-background/80 p-5">
              <p className="text-sm font-medium text-foreground">{copy.grid.currentScope}</p>
              <p className="mt-2 text-3xl font-semibold tracking-tight text-foreground">{products.total_items}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {buildActiveProductsLabel(products.total_items, scopeBankCount, filters.locale)}
              </p>
              <p className="mt-4 text-sm text-muted-foreground">{formatFreshnessLine(products.freshness, filters.locale)}</p>
            </div>
          </header>

          <section className="sticky top-[4.5rem] z-20 rounded-[1.75rem] border border-border/80 bg-card/92 p-5 shadow-[0_18px_40px_rgba(15,23,42,0.08)] backdrop-blur">
            <form action="/products" className="space-y-6">
              <input name="locale" type="hidden" value={filters.locale} />
              <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)]">
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

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
                <SelectField locale={filters.locale} label={copy.grid.feeBucket} name="fee_bucket" options={filterOptions.fee_buckets} value={filters.feeBucket} />
                {showMinimumBalance ? (
                  <SelectField
                    locale={filters.locale}
                    label={copy.grid.minimumBalance}
                    name="minimum_balance_bucket"
                    options={filterOptions.minimum_balance_buckets}
                    value={filters.minimumBalanceBucket}
                  />
                ) : (
                  <div className="hidden xl:block" />
                )}
                {showMinimumDeposit ? (
                  <SelectField
                    locale={filters.locale}
                    label={copy.grid.minimumDeposit}
                    name="minimum_deposit_bucket"
                    options={filterOptions.minimum_deposit_buckets}
                    value={filters.minimumDepositBucket}
                  />
                ) : (
                  <div className="hidden xl:block" />
                )}
                {showTermBucket ? (
                  <SelectField locale={filters.locale} label={copy.grid.termBucket} name="term_bucket" options={filterOptions.term_buckets} value={filters.termBucket} />
                ) : (
                  <div className="hidden xl:block" />
                )}
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

              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border/70 pt-4">
                <p className="text-sm text-muted-foreground">
                  {copy.grid.filterHint}
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button type="submit">{copy.common.applyFilters}</Button>
                  <Button asChild type="button" variant="outline">
                    <Link href={buildPublicHref("/products", { ...filters, bankCodes: [], productTypes: [], targetCustomerTags: [], feeBucket: "", minimumBalanceBucket: "", minimumDepositBucket: "", termBucket: "", page: 1 })}>
                      {copy.common.clearFilters}
                    </Link>
                  </Button>
                </div>
              </div>
            </form>
          </section>

          <section className="rounded-[1.75rem] border border-border/80 bg-background/65 p-5">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-3">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">{copy.grid.resultSummary}</p>
                  <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                    {buildResultTitle(products.total_items, filters.locale)}
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {buildScopeSummary(filters, filterOptions)}{" "}
                    {filters.locale === "ko"
                      ? "최신 성공 집계 새로고침 기준의 신선도를 함께 표시합니다."
                      : filters.locale === "ja"
                        ? "最新の成功した集計更新に基づく鮮度情報をあわせて表示します。"
                        : "Snapshot freshness is carried from the latest successful aggregate refresh."}
                  </p>
                </div>
                {activeChips.length ? (
                  <div className="flex flex-wrap gap-2">
                    {activeChips.map((chip) => (
                      <Link
                        key={`${chip.group}-${chip.value}`}
                        href={chip.href}
                        className="inline-flex items-center rounded-full border border-border bg-card px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted"
                      >
                        {chip.label}
                      </Link>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">{copy.grid.noActiveFilters}</p>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <Button asChild variant="outline">
                  <Link href={dashboardHref}>{copy.grid.openDashboard}</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href={buildPublicHref("/products", { ...filters, bankCodes: [], productTypes: [], targetCustomerTags: [], feeBucket: "", minimumBalanceBucket: "", minimumDepositBucket: "", termBucket: "", page: 1 })}>
                    {copy.common.clearAllFilters}
                  </Link>
                </Button>
              </div>
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <SurfaceNoteCard
              eyebrow={copy.dashboard.methodology}
              title={getGridMetricNoteTitle(filters.locale)}
              items={gridMetricNotes}
            />
            <SurfaceNoteCard
              eyebrow={copy.dashboard.freshness}
              title={copy.dashboard.freshnessTitle}
              items={gridFreshnessNotes}
            />
          </section>

          {products.items.length ? (
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {products.items.map((product) => (
                <ProductCard key={product.product_id} locale={filters.locale} product={product} />
              ))}
            </section>
          ) : (
            <section className="rounded-[1.75rem] border border-dashed border-border bg-card/80 p-8 text-center">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-primary">{copy.grid.noResultEyebrow}</p>
              <h2 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">{copy.grid.noResultTitle}</h2>
              <p className="mt-3 text-sm leading-7 text-muted-foreground">{copy.grid.noResultBody}</p>
              <div className="mt-6 flex flex-wrap justify-center gap-3">
                <Button asChild>
                  <Link href={buildPublicHref("/products", { ...filters, bankCodes: [], productTypes: [], targetCustomerTags: [], feeBucket: "", minimumBalanceBucket: "", minimumDepositBucket: "", termBucket: "", page: 1 })}>
                    {copy.common.clearFilters}
                  </Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href={dashboardHref}>{copy.grid.goToDashboard}</Link>
                </Button>
              </div>
            </section>
          )}

          {pagination ? (
            <section className="flex flex-col gap-3 rounded-[1.5rem] border border-border/80 bg-card/80 p-4 md:flex-row md:items-center md:justify-between">
              <p className="text-sm text-muted-foreground">
                {copy.common.pageLabel} {products.page} / {products.total_pages}. {products.page_size}{localeProductSuffix(filters.locale)}
              </p>
              <div className="flex flex-wrap gap-3">
                <Button asChild variant="outline">
                  <Link
                    aria-disabled={!pagination.hasPrevious}
                    className={cn(!pagination.hasPrevious && "pointer-events-none opacity-50")}
                    href={pagination.previousHref}
                  >
                    {copy.common.previous}
                  </Link>
                </Button>
                <Button asChild variant="outline">
                  <Link
                    aria-disabled={!pagination.hasNext}
                    className={cn(!pagination.hasNext && "pointer-events-none opacity-50")}
                    href={pagination.nextHref}
                  >
                    {copy.common.next}
                  </Link>
                </Button>
              </div>
            </section>
          ) : null}
        </div>
      </section>
    </main>
  );
}

function ProductCard({ locale, product }: { locale: string; product: PublicProduct }) {
  const copy = getPublicMessages(locale);
  const metrics = buildPrimaryMetrics(product, locale);
  const tags = product.target_customer_tag_labels.slice(0, 2);

  return (
    <article className="group rounded-[1.6rem] border border-border/80 bg-card/95 p-5 shadow-[0_20px_40px_rgba(15,23,42,0.06)] transition-transform duration-200 hover:-translate-y-0.5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">{product.bank_name}</p>
          <p className="mt-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary">{product.product_type_label}</p>
          <h3 className="mt-3 text-xl font-semibold leading-7 tracking-tight text-foreground">{product.product_name}</h3>
        </div>
        {product.product_highlight_badge_label ? (
          <span className="rounded-full border border-primary/15 bg-secondary px-3 py-1 text-xs font-semibold text-secondary-foreground">
            {product.product_highlight_badge_label}
          </span>
        ) : null}
      </div>

      {tags.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {tags.map((tag) => (
            <span key={tag} className="rounded-full border border-border bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground">
              {tag}
            </span>
          ))}
        </div>
      ) : null}

      <dl className="mt-5 grid gap-3 sm:grid-cols-3">
        {metrics.map((metric) => (
          <div key={metric.label} className="rounded-[1.1rem] border border-border/70 bg-background/75 p-3">
            <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">{metric.label}</dt>
            <dd className="mt-2 text-lg font-semibold tracking-tight text-foreground">{metric.value}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-border/70 pt-4 text-sm text-muted-foreground">
        <span>{buildChangeHint(product.last_changed_at, locale)}</span>
        <span>{copy.common.verifiedOn} {formatCompactDate(product.last_verified_at, locale)}</span>
      </div>
    </article>
  );
}

function FilterGroup({ helper, label, children }: Readonly<{ helper: string; label: string; children: ReactNode }>) {
  return (
    <fieldset className="space-y-3">
      <legend className="text-sm font-semibold text-foreground">{label}</legend>
      <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{helper}</p>
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
    return <p className="rounded-xl border border-dashed border-border px-3 py-4 text-sm text-muted-foreground">{getPublicMessages(locale).common.noOptions}</p>;
  }

  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {options.map((option) => (
        <label
          key={option.value}
          className={cn(
            "flex cursor-pointer items-start justify-between gap-3 rounded-xl border px-3 py-3 text-sm transition-colors hover:bg-muted/70",
            selectedValues.has(option.value) ? "border-primary/40 bg-secondary/70" : "border-border bg-background/70"
          )}
        >
          <span className="flex items-start gap-3">
            <input
              className="mt-0.5 size-4 rounded border-border text-primary focus:ring-primary"
              defaultChecked={selectedValues.has(option.value)}
              name={name}
              type="checkbox"
              value={option.value}
            />
            <span>
              <span className="block font-medium text-foreground">{option.label}</span>
              <span className="block text-xs text-muted-foreground">{option.count}</span>
            </span>
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
    <label className="space-y-2">
      <span className="text-sm font-medium text-foreground">{label}</span>
      <select
        className="h-11 w-full rounded-xl border border-input bg-background px-3 text-sm text-foreground outline-none transition focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
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
      {
        label: product.product_highlight_badge_label ? copy.grid.metricKeyDetail : copy.grid.metricLastChange,
        value: product.product_highlight_badge_label ?? formatCompactDate(product.last_changed_at, locale)
      }
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
    {
      label: product.product_highlight_badge_label ? copy.grid.metricRateNote : copy.grid.metricLastChange,
      value: product.product_highlight_badge_label ?? formatCompactDate(product.last_changed_at, locale)
    }
  ];
}

function buildScopeSummary(filters: ProductGridPageFilters, filterOptions: PublicFiltersResponse) {
  const locale = filters.locale;
  const parts: string[] = [];
  if (filters.bankCodes.length) {
    parts.push(locale === "ko" ? `은행 필터 ${filters.bankCodes.length}개 활성.` : locale === "ja" ? `銀行フィルター ${filters.bankCodes.length} 件が有効です。` : `${filters.bankCodes.length} bank filter${filters.bankCodes.length > 1 ? "s" : ""} active.`);
  }
  if (filters.productTypes.length) {
    parts.push(locale === "ko" ? `상품 유형 필터 ${filters.productTypes.length}개 활성.` : locale === "ja" ? `商品タイプフィルター ${filters.productTypes.length} 件が有効です。` : `${filters.productTypes.length} product type filter${filters.productTypes.length > 1 ? "s" : ""} active.`);
  }
  if (filters.targetCustomerTags.length) {
    parts.push(locale === "ko" ? `대상 태그 필터 ${filters.targetCustomerTags.length}개 활성.` : locale === "ja" ? `対象タグフィルター ${filters.targetCustomerTags.length} 件が有効です。` : `${filters.targetCustomerTags.length} target-tag filter${filters.targetCustomerTags.length > 1 ? "s" : ""} active.`);
  }

  if (!parts.length) {
    return locale === "ko"
      ? `전체 ${filterOptions.banks.length}개 은행 기준의 공개 범위에서 모든 은행과 상품 유형이 표시됩니다.`
      : locale === "ja"
        ? `${filterOptions.banks.length} 行公開ベースラインの範囲で、すべての銀行と商品タイプが表示されています。`
        : `All banks and product types are visible from a ${filterOptions.banks.length}-bank public baseline.`;
  }
  return parts.join(" ");
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
      href: buildProductsHref(filters, {
        targetCustomerTags: filters.targetCustomerTags.filter((value) => value !== tag),
        page: 1
      }),
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
  if (!value) {
    return;
  }
  chips.push({ group, href, label: findLabel(options, value), value });
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

function formatFreshnessLine(freshness: PublicProductsResponse["freshness"], locale: string) {
  const copy = getPublicMessages(locale);
  if (!freshness.refreshed_at) {
    return copy.common.noSuccessfulSnapshot;
  }
  const refreshedLabel = formatLongDateTime(freshness.refreshed_at, locale);
  return freshness.status === "stale"
    ? locale === "ko"
      ? `스냅샷이 오래되었습니다. 마지막 성공 새로고침은 ${refreshedLabel} 입니다.`
      : locale === "ja"
        ? `スナップショットは古くなっています。最後に成功した更新は ${refreshedLabel} です。`
        : `Snapshot is stale. Last successful refresh was ${refreshedLabel}.`
    : locale === "ko"
      ? `스냅샷이 ${refreshedLabel}에 새로고침되었습니다.`
      : locale === "ja"
        ? `スナップショットは ${refreshedLabel} に更新されました。`
        : `Snapshot refreshed ${refreshedLabel}.`;
}

function buildChangeHint(timestamp: string | null, locale: string) {
  const copy = getPublicMessages(locale);
  if (!timestamp) {
    return copy.common.noRecentChange;
  }
  return `${copy.common.changedOn} ${formatCompactDate(timestamp, locale)}`;
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
    return locale === "ko" ? `${years}년` : locale === "ja" ? `${years}年` : `${years} year${years === 1 ? "" : "s"}`;
  }
  if (termLengthDays % 30 === 0) {
    const months = Math.round(termLengthDays / 30);
    return locale === "ko" ? `${months}개월` : locale === "ja" ? `${months}か月` : `${months} month${months === 1 ? "" : "s"}`;
  }
  return locale === "ko" ? `${termLengthDays}일` : locale === "ja" ? `${termLengthDays}日` : `${termLengthDays} days`;
}

function formatCompactDate(value: string | null, locale: string) {
  const copy = getPublicMessages(locale);
  if (!value) {
    return copy.common.noDate;
  }
  return new Intl.DateTimeFormat(getIntlLocale(locale), {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(new Date(value));
}

function formatLongDateTime(value: string, locale: string) {
  return new Intl.DateTimeFormat(getIntlLocale(locale), {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC"
  }).format(new Date(value));
}

function SurfaceNoteCard({ eyebrow, items, title }: { eyebrow: string; items: string[]; title: string }) {
  return (
    <section className="rounded-[1.5rem] border border-border/80 bg-card/90 p-5 shadow-[0_20px_50px_rgba(15,23,42,0.05)]">
      <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">{eyebrow}</p>
      <h2 className="mt-2 text-xl font-semibold tracking-tight text-foreground">{title}</h2>
      <ul className="mt-4 space-y-3 text-sm leading-6 text-muted-foreground">
        {items.map((item) => (
          <li key={item} className="flex gap-3">
            <span className="mt-1 size-1.5 rounded-full bg-primary/70" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function findLabel(options: Array<{ label: string; value: string }>, value: string) {
  return options.find((option) => option.value === value)?.label ?? value;
}

function getGridMetricNoteTitle(locale: string) {
  if (locale === "ko") {
    return "상품 카드를 읽는 법";
  }
  if (locale === "ja") {
    return "商品カードの読み方";
  }
  return "How to read product cards";
}

function buildGridMetricNotes(filterOptions: PublicFiltersResponse, locale: string) {
  const chequingLabel = findLabel(filterOptions.product_types, "chequing");
  const savingsLabel = findLabel(filterOptions.product_types, "savings");
  const gicLabel = findLabel(filterOptions.product_types, "gic");
  const copy = getPublicMessages(locale);

  if (locale === "ko") {
    return [
      "카드 메트릭은 현재 공개 범위의 최신 성공 aggregate snapshot을 기준으로 표시됩니다.",
      `${chequingLabel} 카드는 ${copy.grid.metricMonthlyFee}, ${copy.grid.metricMinBalance}, 최근 수수료 맥락을 먼저 강조합니다.`,
      `${savingsLabel} 카드는 ${copy.grid.metricDisplayRate}, ${copy.grid.metricMinBalance}, 우대금리 또는 최근 변경 맥락을 먼저 강조합니다.`,
      `${gicLabel} 카드는 ${copy.grid.metricDisplayRate}, ${copy.grid.metricTerm}, ${copy.grid.metricMinDeposit}을 먼저 강조합니다.`,
      "상품명과 상품 조건처럼 source-derived 값은 번역하지 않고 원문 언어 그대로 유지합니다."
    ];
  }

  if (locale === "ja") {
    return [
      "カード指標は、現在の公開スコープに対する最新の成功 aggregate snapshot を基準に表示されます。",
      `${chequingLabel} カードは ${copy.grid.metricMonthlyFee}、${copy.grid.metricMinBalance}、最近の手数料文脈を優先して示します。`,
      `${savingsLabel} カードは ${copy.grid.metricDisplayRate}、${copy.grid.metricMinBalance}、優遇金利または最近の変更文脈を優先して示します。`,
      `${gicLabel} カードは ${copy.grid.metricDisplayRate}、${copy.grid.metricTerm}、${copy.grid.metricMinDeposit} を優先して示します。`,
      "商品名や条件のような source-derived 値は翻訳せず、原文の言語のまま保持します。"
    ];
  }

  return [
    "Card metrics are shown from the latest successful aggregate snapshot for the current public scope.",
    `${chequingLabel} cards emphasize ${copy.grid.metricMonthlyFee}, ${copy.grid.metricMinBalance}, and recent fee context first.`,
    `${savingsLabel} cards emphasize ${copy.grid.metricDisplayRate}, ${copy.grid.metricMinBalance}, and promo or recent-change context first.`,
    `${gicLabel} cards emphasize ${copy.grid.metricDisplayRate}, ${copy.grid.metricTerm}, and ${copy.grid.metricMinDeposit} first.`,
    "Source-derived values such as product names and conditions remain in the original source language."
  ];
}

function buildGridFreshnessNotes(freshness: PublicProductsResponse["freshness"], locale: string) {
  const items = [formatFreshnessLine(freshness, locale)];
  const ttlMinutes = Math.max(1, Math.round(freshness.cache_ttl_sec / 60));

  if (freshness.source_change_cutoff_at) {
    items.push(
      locale === "ko"
        ? `최근 변경 힌트는 ${formatLongDateTime(freshness.source_change_cutoff_at, locale)} 까지 포착된 source change 기준으로 계산됩니다.`
        : locale === "ja"
          ? `最近変更ヒントは ${formatLongDateTime(freshness.source_change_cutoff_at, locale)} までに取得された source change を基準に計算されます。`
          : `Recent-change hints are measured against source changes captured through ${formatLongDateTime(freshness.source_change_cutoff_at, locale)}.`
    );
  }

  items.push(
    locale === "ko"
      ? `공개 응답은 refresh 이후 최대 ${ttlMinutes}분까지 캐시된 결과를 계속 제공할 수 있습니다.`
      : locale === "ja"
        ? `公開レスポンスは refresh 後も最大 ${ttlMinutes} 分までキャッシュ結果を返す場合があります。`
        : `Public responses may continue serving cached results for up to ${ttlMinutes} minutes after refresh.`
  );

  items.push(
    freshness.status === "stale"
      ? locale === "ko"
        ? "더 새로운 refresh가 성공하기 전까지는 마지막 성공 snapshot을 계속 제공합니다."
        : locale === "ja"
          ? "より新しい refresh が成功するまでは、最後に成功した snapshot を継続して提供します。"
          : "The site keeps serving the latest successful snapshot until a fresher refresh succeeds."
      : locale === "ko"
        ? "현재 이 화면은 가장 최신에 성공한 공개 snapshot을 기준으로 제공되고 있습니다."
        : locale === "ja"
          ? "現在この画面は、もっとも新しく成功した公開 snapshot を基準に提供されています。"
          : "This surface is currently serving the freshest successful public snapshot."
  );

  return items;
}

function buildActiveProductsLabel(totalItems: number, scopeBankCount: number, locale: string) {
  const copy = getPublicMessages(locale);
  if (!scopeBankCount) {
    return buildResultTitle(totalItems, locale);
  }
  return formatPublicMessage(copy.dashboard.productsAcrossBanks, { banks: scopeBankCount });
}

function buildResultTitle(totalItems: number, locale: string) {
  const copy = getPublicMessages(locale);
  if (locale === "ko") {
    return `${totalItems}개 활성 상품 표시 중`;
  }
  if (locale === "ja") {
    return `${totalItems} 件の${copy.dashboard.activeProducts}`;
  }
  return `Showing ${totalItems} ${copy.dashboard.activeProducts}`;
}

function localeProductSuffix(locale: string) {
  if (locale === "ko") {
    return "개 상품 / 페이지";
  }
  if (locale === "ja") {
    return "件 / ページ";
  }
  return " products per page";
}
