import Link from "next/link";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { type PublicFilterOption, type PublicFiltersResponse, type PublicProduct, type PublicProductsResponse } from "@/lib/public-api";
import { cn } from "@/lib/utils";

export type ProductGridPageFilters = {
  locale: string;
  bankCodes: string[];
  productTypes: string[];
  targetCustomerTags: string[];
  feeBucket: string;
  minimumBalanceBucket: string;
  minimumDepositBucket: string;
  termBucket: string;
  sortBy: string;
  sortOrder: "asc" | "desc";
  page: number;
};

type ProductGridSurfaceProps = {
  apiUnavailable: boolean;
  filterOptions: PublicFiltersResponse | null;
  filters: ProductGridPageFilters;
  products: PublicProductsResponse | null;
};

const SORT_OPTIONS = [
  { value: "default", label: "Default order" },
  { value: "display_rate", label: "Display rate" },
  { value: "monthly_fee", label: "Monthly fee" },
  { value: "minimum_balance", label: "Minimum balance" },
  { value: "minimum_deposit", label: "Minimum deposit" },
  { value: "last_changed_at", label: "Last change" },
  { value: "bank_name", label: "Bank name" },
  { value: "product_name", label: "Product name" }
];

export function ProductGridSurface({ apiUnavailable, filterOptions, filters, products }: ProductGridSurfaceProps) {
  if (apiUnavailable || !products || !filterOptions) {
    return (
      <main className="mx-auto flex w-full max-w-6xl px-4 py-12 md:px-6 md:py-16">
        <section className="w-full rounded-[2rem] border border-destructive/20 bg-card/95 p-8 shadow-[0_24px_60px_rgba(15,23,42,0.08)] md:p-10">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-destructive">Public API unavailable</p>
          <h1 className="mt-4 max-w-2xl text-4xl font-semibold tracking-tight text-foreground">
            Product Grid could not load because the public aggregate API is not reachable.
          </h1>
          <p className="mt-4 max-w-3xl text-base leading-7 text-muted-foreground">
            Start the FastAPI service and refresh this page. The public Product Grid depends on
            `GET /api/public/products` and `GET /api/public/filters`.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild>
              <Link href="/products">Retry Product Grid</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/dashboard">Open dashboard placeholder</Link>
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
  const dashboardHref = buildProductsHref(filters, { page: 1 }).replace("/products", "/dashboard");
  const pagination = buildPagination(products, filters);
  const scopeBankCount = filters.bankCodes.length || filterOptions.banks.length;

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 md:px-6 md:py-10">
      <section className="rounded-[2rem] border border-border/80 bg-card/85 p-6 shadow-[0_30px_80px_rgba(15,23,42,0.06)] md:p-8">
        <div className="flex flex-col gap-8">
          <header className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(20rem,0.8fr)] lg:items-end">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-primary">WBS 5.9 Product Grid</p>
              <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight text-foreground md:text-5xl">
                Compare Canada deposit products with one shared public filter vocabulary.
              </h1>
              <p className="mt-4 max-w-3xl text-base leading-7 text-muted-foreground">
                Browse active chequing, savings, and GIC products from the latest successful aggregate snapshot. Product
                names stay source-derived, while labels, bucket filters, and freshness notes stay UI-owned.
              </p>
            </div>
            <div className="rounded-[1.5rem] border border-border/70 bg-background/80 p-5">
              <p className="text-sm font-medium text-foreground">Current scope</p>
              <p className="mt-2 text-3xl font-semibold tracking-tight text-foreground">{products.total_items}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                active products{scopeBankCount ? ` across ${scopeBankCount} banks` : ""}
              </p>
              <p className="mt-4 text-sm text-muted-foreground">{formatFreshnessLine(products.freshness, filters.locale)}</p>
            </div>
          </header>

          <section className="sticky top-[4.5rem] z-20 rounded-[1.75rem] border border-border/80 bg-card/92 p-5 shadow-[0_18px_40px_rgba(15,23,42,0.08)] backdrop-blur">
            <form action="/products" className="space-y-6">
              <input name="locale" type="hidden" value={filters.locale} />
              <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)]">
                <FilterGroup helper="Primary filter" label="Banks">
                  <OptionGrid name="bank_code" options={filterOptions.banks} selectedValues={new Set(filters.bankCodes)} />
                </FilterGroup>
                <FilterGroup helper="Primary filter" label="Product types">
                  <OptionGrid name="product_type" options={filterOptions.product_types} selectedValues={new Set(filters.productTypes)} />
                </FilterGroup>
                <FilterGroup helper="Primary filter" label="Target tags">
                  <OptionGrid
                    name="target_customer_tag"
                    options={filterOptions.target_customer_tags}
                    selectedValues={new Set(filters.targetCustomerTags)}
                  />
                </FilterGroup>
              </div>

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
                <SelectField label="Fee bucket" name="fee_bucket" options={filterOptions.fee_buckets} value={filters.feeBucket} />
                {showMinimumBalance ? (
                  <SelectField
                    label="Minimum balance"
                    name="minimum_balance_bucket"
                    options={filterOptions.minimum_balance_buckets}
                    value={filters.minimumBalanceBucket}
                  />
                ) : (
                  <div className="hidden xl:block" />
                )}
                {showMinimumDeposit ? (
                  <SelectField
                    label="Minimum deposit"
                    name="minimum_deposit_bucket"
                    options={filterOptions.minimum_deposit_buckets}
                    value={filters.minimumDepositBucket}
                  />
                ) : (
                  <div className="hidden xl:block" />
                )}
                {showTermBucket ? (
                  <SelectField label="Term bucket" name="term_bucket" options={filterOptions.term_buckets} value={filters.termBucket} />
                ) : (
                  <div className="hidden xl:block" />
                )}
                <SelectField label="Sort by" name="sort_by" options={SORT_OPTIONS} value={filters.sortBy} />
                <SelectField
                  label="Direction"
                  name="sort_order"
                  options={[
                    { value: "desc", label: "Descending" },
                    { value: "asc", label: "Ascending" }
                  ]}
                  value={filters.sortOrder}
                />
              </div>

              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border/70 pt-4">
                <p className="text-sm text-muted-foreground">
                  Apply filters to refresh the grid. Pagination resets to page one when scope changes.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button type="submit">Apply filters</Button>
                  <Button asChild type="button" variant="outline">
                    <Link href="/products">Clear filters</Link>
                  </Button>
                </div>
              </div>
            </form>
          </section>

          <section className="rounded-[1.75rem] border border-border/80 bg-background/65 p-5">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-3">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">Result summary</p>
                  <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                    Showing {products.total_items} active products
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {buildScopeSummary(filters, filterOptions)} Snapshot freshness is carried from the latest successful
                    aggregate refresh.
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
                  <p className="text-sm text-muted-foreground">No active filters. You are viewing the full public Canada scope.</p>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <Button asChild variant="outline">
                  <Link href={dashboardHref}>Open dashboard sibling</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href="/products">Clear all filters</Link>
                </Button>
              </div>
            </div>
          </section>

          {products.items.length ? (
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {products.items.map((product) => (
                <ProductCard key={product.product_id} locale={filters.locale} product={product} />
              ))}
            </section>
          ) : (
            <section className="rounded-[1.75rem] border border-dashed border-border bg-card/80 p-8 text-center">
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-primary">No result</p>
              <h2 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">No products matched the current filter scope.</h2>
              <p className="mt-3 text-sm leading-7 text-muted-foreground">
                Clear the active chips or move to the dashboard sibling surface if you want a higher-level market view for
                this slice.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-3">
                <Button asChild>
                  <Link href="/products">Clear filters</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href={dashboardHref}>Go to dashboard placeholder</Link>
                </Button>
              </div>
            </section>
          )}

          {pagination ? (
            <section className="flex flex-col gap-3 rounded-[1.5rem] border border-border/80 bg-card/80 p-4 md:flex-row md:items-center md:justify-between">
              <p className="text-sm text-muted-foreground">
                Page {products.page} of {products.total_pages}. Up to {products.page_size} products per page.
              </p>
              <div className="flex flex-wrap gap-3">
                <Button asChild variant="outline">
                  <Link
                    aria-disabled={!pagination.hasPrevious}
                    className={cn(!pagination.hasPrevious && "pointer-events-none opacity-50")}
                    href={pagination.previousHref}
                  >
                    Previous
                  </Link>
                </Button>
                <Button asChild variant="outline">
                  <Link
                    aria-disabled={!pagination.hasNext}
                    className={cn(!pagination.hasNext && "pointer-events-none opacity-50")}
                    href={pagination.nextHref}
                  >
                    Next
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
        <span>Verified {formatCompactDate(product.last_verified_at, locale)}</span>
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
  options,
  selectedValues
}: Readonly<{
  name: string;
  options: PublicFilterOption[];
  selectedValues: Set<string>;
}>) {
  if (!options.length) {
    return <p className="rounded-xl border border-dashed border-border px-3 py-4 text-sm text-muted-foreground">No options available yet.</p>;
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
              <span className="block text-xs text-muted-foreground">{option.count} products</span>
            </span>
          </span>
        </label>
      ))}
    </div>
  );
}

function SelectField({
  label,
  name,
  options,
  value
}: Readonly<{
  label: string;
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
        <option value="">All</option>
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
  if (product.product_type === "chequing") {
    return [
      { label: "Monthly fee", value: formatCurrency(product.public_display_fee, product.currency, locale) },
      { label: "Min. balance", value: formatCurrency(product.minimum_balance, product.currency, locale) },
      {
        label: product.product_highlight_badge_label ? "Key detail" : "Last change",
        value: product.product_highlight_badge_label ?? formatCompactDate(product.last_changed_at, locale)
      }
    ];
  }

  if (product.product_type === "gic") {
    return [
      { label: "Display rate", value: formatRate(product.public_display_rate) },
      { label: "Term", value: formatTerm(product.term_length_days) },
      { label: "Min. deposit", value: formatCurrency(product.minimum_deposit, product.currency, locale) }
    ];
  }

  return [
    { label: "Display rate", value: formatRate(product.public_display_rate) },
    { label: "Min. balance", value: formatCurrency(product.minimum_balance, product.currency, locale) },
    {
      label: product.product_highlight_badge_label ? "Rate note" : "Last change",
      value: product.product_highlight_badge_label ?? formatCompactDate(product.last_changed_at, locale)
    }
  ];
}

function buildScopeSummary(filters: ProductGridPageFilters, filterOptions: PublicFiltersResponse) {
  const parts: string[] = [];
  if (filters.bankCodes.length) {
    parts.push(`${filters.bankCodes.length} bank filter${filters.bankCodes.length > 1 ? "s" : ""} active.`);
  }
  if (filters.productTypes.length) {
    parts.push(`${filters.productTypes.length} product type filter${filters.productTypes.length > 1 ? "s" : ""} active.`);
  }
  if (filters.targetCustomerTags.length) {
    parts.push(`${filters.targetCustomerTags.length} target-tag filter${filters.targetCustomerTags.length > 1 ? "s" : ""} active.`);
  }

  if (!parts.length) {
    return `All banks and product types are visible from a ${filterOptions.banks.length}-bank public baseline.`;
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
  const next = { ...filters, ...overrides };
  const params = new URLSearchParams();

  if (next.locale !== "en") {
    params.set("locale", next.locale);
  }
  for (const bankCode of next.bankCodes) {
    params.append("bank_code", bankCode);
  }
  for (const productType of next.productTypes) {
    params.append("product_type", productType);
  }
  for (const tag of next.targetCustomerTags) {
    params.append("target_customer_tag", tag);
  }
  if (next.feeBucket) {
    params.set("fee_bucket", next.feeBucket);
  }
  if (next.minimumBalanceBucket) {
    params.set("minimum_balance_bucket", next.minimumBalanceBucket);
  }
  if (next.minimumDepositBucket) {
    params.set("minimum_deposit_bucket", next.minimumDepositBucket);
  }
  if (next.termBucket) {
    params.set("term_bucket", next.termBucket);
  }
  if (next.sortBy !== "default") {
    params.set("sort_by", next.sortBy);
  }
  if (next.sortOrder !== "desc") {
    params.set("sort_order", next.sortOrder);
  }
  if (next.page > 1) {
    params.set("page", String(next.page));
  }

  const query = params.toString();
  return query ? `/products?${query}` : "/products";
}

function formatFreshnessLine(freshness: PublicProductsResponse["freshness"], locale: string) {
  if (!freshness.refreshed_at) {
    return "No successful aggregate snapshot is available yet.";
  }
  const refreshedLabel = formatLongDateTime(freshness.refreshed_at, locale);
  return freshness.status === "stale"
    ? `Snapshot is stale. Last successful refresh was ${refreshedLabel}.`
    : `Snapshot refreshed ${refreshedLabel}.`;
}

function buildChangeHint(timestamp: string | null, locale: string) {
  if (!timestamp) {
    return "No recent change timestamp";
  }
  return `Changed ${formatCompactDate(timestamp, locale)}`;
}

function formatCurrency(value: number | null, currency: string, locale: string) {
  if (value === null || Number.isNaN(value)) {
    return "Not disclosed";
  }
  return new Intl.NumberFormat(normalizeLocale(locale), {
    style: "currency",
    currency,
    maximumFractionDigits: Number.isInteger(value) ? 0 : 2
  }).format(value);
}

function formatRate(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "Not disclosed";
  }
  return `${value.toFixed(2).replace(/\.?0+$/, "")}%`;
}

function formatTerm(termLengthDays: number | null) {
  if (termLengthDays === null || !Number.isFinite(termLengthDays)) {
    return "Not disclosed";
  }
  if (termLengthDays % 365 === 0) {
    const years = termLengthDays / 365;
    return `${years} year${years === 1 ? "" : "s"}`;
  }
  if (termLengthDays % 30 === 0) {
    const months = Math.round(termLengthDays / 30);
    return `${months} month${months === 1 ? "" : "s"}`;
  }
  return `${termLengthDays} days`;
}

function formatCompactDate(value: string | null, locale: string) {
  if (!value) {
    return "No date";
  }
  return new Intl.DateTimeFormat(normalizeLocale(locale), {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(new Date(value));
}

function formatLongDateTime(value: string, locale: string) {
  return new Intl.DateTimeFormat(normalizeLocale(locale), {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC"
  }).format(new Date(value));
}

function normalizeLocale(locale: string) {
  switch (locale) {
    case "ko":
      return "ko-KR";
    case "ja":
      return "ja-JP";
    default:
      return "en-CA";
  }
}

function findLabel(options: Array<{ label: string; value: string }>, value: string) {
  return options.find((option) => option.value === value)?.label ?? value;
}
