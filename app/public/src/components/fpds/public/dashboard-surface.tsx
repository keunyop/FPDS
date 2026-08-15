import { ArrowRight, CreditCard, ExternalLink, FilterX, Landmark, PiggyBank, RefreshCw } from "lucide-react";
import Link from "next/link";

import { BankLogo } from "@/components/fpds/public/bank-logo";
import { PublicFreshness, formatSnapshotDate } from "@/components/fpds/public/public-freshness";
import { PublicScatterChart } from "@/components/fpds/public/public-dashboard-charts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card";
import { getIntlLocale, getPublicDesignCopy, getPublicMessages } from "@/lib/public-locale";
import {
  type PublicDashboardScatterResponse,
  type PublicDashboardSummaryResponse,
  type PublicProductsResponse
} from "@/lib/public-api";
import { buildPublicHref, type DashboardPageFilters } from "@/lib/public-query";

type DashboardSurfaceProps = {
  apiUnavailable: boolean;
  depositProducts: PublicProductsResponse | null;
  depositProductsUnavailable: boolean;
  filters: DashboardPageFilters;
  loanProducts: PublicProductsResponse | null;
  loanProductsUnavailable: boolean;
  scatter: PublicDashboardScatterResponse | null;
  summary: PublicDashboardSummaryResponse | null;
};

export function DashboardSurface({
  apiUnavailable,
  depositProducts,
  depositProductsUnavailable,
  filters,
  loanProducts,
  loanProductsUnavailable,
  scatter,
  summary
}: DashboardSurfaceProps) {
  const copy = getPublicMessages(filters.locale);
  const designCopy = getPublicDesignCopy(filters.locale);
  const productsHref = buildPublicHref("/products", { ...filters, page: 1 });
  const cardsHref = buildPublicHref("/cards", { ...filters, page: 1 });
  const loansHref = buildPublicHref("/loans", { ...filters, page: 1 });
  const clearHref = buildPublicHref("/dashboard", {
    ...filters,
    bankCodes: [],
    productTypes: [],
    targetCustomerTags: [],
    feeBucket: "",
    minimumBalanceBucket: "",
    minimumDepositBucket: "",
    termBucket: "",
    axisPreset: ""
  });

  if (apiUnavailable || !summary) {
    return (
      <main className="mx-auto w-full max-w-5xl px-4 py-10 md:px-6">
        <Card className="border-destructive/25">
          <CardHeader>
            <h1 className="text-lg font-semibold">{copy.dashboard.apiUnavailableTitle}</h1>
            <CardDescription>{copy.dashboard.apiUnavailableBody}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Button asChild>
              <Link href={buildPublicHref("/dashboard", filters)}>
                <RefreshCw className="size-4" aria-hidden="true" />
                {copy.dashboard.retryDashboard}
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link href={productsHref}>{copy.dashboard.openProducts}</Link>
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  const totalProducts = Number(getMetric(summary, "total_active_products")?.value ?? 0);
  const banksInScope = Number(getMetric(summary, "banks_in_scope")?.value ?? 0);
  const activeChips = buildScopeChips(filters, summary);
  const rankedDeposits = (depositProducts?.items ?? [])
    .filter((product) => product.card_display_rate !== null && Number.isFinite(product.card_display_rate))
    .slice(0, 5);
  const rankedLoans = (loanProducts?.items ?? []).filter((product) => product.card_display_rate !== null && Number.isFinite(product.card_display_rate)).slice(0, 5);
  const hasScatter = Boolean(scatter?.points.length && scatter.x_axis && scatter.y_axis);
  const snapshotDate = formatSnapshotDate(summary.freshness.refreshed_at, copy.common.noDate);

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6 md:py-9">
      <div className="flex flex-col gap-8 md:gap-12">
        <section className="border-y border-foreground/15 py-8 md:py-12">
          <div className="grid gap-9 lg:grid-cols-[minmax(0,1fr)_minmax(21rem,0.62fr)] lg:items-center">
            <div className="max-w-3xl">
              <p className="text-xs font-semibold tracking-[0.08em] text-verification">{designCopy.homeKicker}</p>
              <h1 className="text-balance mt-4 max-w-4xl font-display text-[clamp(2.4rem,6vw,5rem)] font-semibold leading-[1.02] tracking-[-0.055em] text-foreground">
                {designCopy.homeTitle}
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">{designCopy.homeBody}</p>
              <div className="mt-6 flex flex-wrap gap-2.5">
                <Button asChild size="lg" className="min-h-12 rounded-full px-5">
                  <Link href={productsHref}>
                    <PiggyBank className="size-4" aria-hidden="true" />
                    {copy.nav.products}
                  </Link>
                </Button>
                <Button asChild size="lg" variant="outline" className="min-h-12 rounded-full border-foreground/20 bg-transparent px-5">
                  <Link href={cardsHref}>
                    <CreditCard className="size-4" aria-hidden="true" />
                    {copy.nav.card}
                  </Link>
                </Button>
                <Button asChild size="lg" variant="outline" className="min-h-12 rounded-full border-foreground/20 bg-transparent px-5">
                  <Link href={loansHref}>
                    <Landmark className="size-4" aria-hidden="true" />
                    {copy.nav.loan}
                  </Link>
                </Button>
                {activeChips.length ? (
                  <Button asChild variant="ghost">
                    <Link href={clearHref}>
                      <FilterX className="size-4" aria-hidden="true" />
                      {copy.common.clearFilters}
                    </Link>
                  </Button>
                ) : null}
              </div>
            </div>
            <SnapshotSummary
              banks={formatCount(banksInScope, filters.locale)}
              date={snapshotDate}
              freshness={summary.freshness}
              locale={filters.locale}
              products={formatCount(totalProducts, filters.locale)}
            />
          </div>
        </section>

        {activeChips.length ? (
          <section aria-label={copy.grid.currentScope} className="flex flex-wrap gap-2 border-b border-border pb-5">
            {activeChips.map((chip) => (
              <Link
                key={chip.key}
                href={chip.href}
                className="inline-flex min-h-10 items-center rounded-full border border-border bg-card px-3 text-xs font-medium text-muted-foreground transition-colors hover:border-foreground/30 hover:text-foreground"
              >
                {chip.label}
              </Link>
            ))}
          </section>
        ) : null}

        <section className="grid items-start gap-6 lg:grid-cols-2" aria-label={copy.dashboard.rateSnapshotsLabel}>
          <ProductTopFive
            accent="deposit"
            emptyText={copy.dashboard.depositTopEmpty}
            filters={filters}
            headingId="deposit-top-title"
            href={productsHref}
            linkLabel={copy.dashboard.moreDeposits}
            products={rankedDeposits}
            subtitle={copy.dashboard.depositTopSubtitle}
            title={copy.dashboard.depositTopTitle}
            unavailable={depositProductsUnavailable}
            unavailableText={copy.dashboard.depositTopUnavailable}
          />
          <ProductTopFive
            accent="loan"
            emptyText={copy.dashboard.loanTopEmpty}
            filters={filters}
            headingId="loan-top-title"
            href={loansHref}
            linkLabel={copy.dashboard.moreLoans}
            products={rankedLoans}
            subtitle={copy.dashboard.loanTopSubtitle}
            title={copy.dashboard.loanTopTitle}
            unavailable={loanProductsUnavailable}
            unavailableText={copy.dashboard.loanTopUnavailable}
          />
        </section>

        {hasScatter || filters.productTypes.length === 1 ? (
          <section>
            <Card className="border-foreground/15 bg-card/70 shadow-none">
              <CardHeader>
                <h2 className="text-lg font-semibold">{scatter?.title ?? copy.dashboard.comparisonMap}</h2>
                <CardDescription>{hasScatter ? scatter?.methodology_note ?? copy.dashboard.comparisonSubtitle : copy.dashboard.comparisonSubtitle}</CardDescription>
              </CardHeader>
              <CardContent>
                {hasScatter && scatter ? (
                  <PublicScatterChart scatter={scatter} />
                ) : (
                  <div className="rounded-lg border border-dashed border-border bg-muted/20 px-4 py-6">
                    <p className="text-sm text-muted-foreground">
                      {scatter?.insufficiency_note ?? (filters.productTypes.length === 1 ? copy.dashboard.chartUnavailable : copy.dashboard.chartSingleTypeHint)}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </section>
        ) : null}
      </div>
    </main>
  );
}

function SnapshotSummary({
  banks,
  date,
  freshness,
  locale,
  products,
}: {
  banks: string;
  date: string;
  freshness: PublicDashboardSummaryResponse["freshness"];
  locale: string;
  products: string;
}) {
  const copy = getPublicMessages(locale);
  const designCopy = getPublicDesignCopy(locale);
  return (
    <aside className="min-w-0 border-y border-foreground/20 bg-card/55 px-1 py-5 md:px-5" aria-label={designCopy.publicSnapshot}>
      <div className="flex flex-col items-start gap-3 border-b border-border pb-4 sm:flex-row sm:justify-between">
        <div>
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">{designCopy.publicSnapshot}</p>
          <p className="mt-2 font-mono text-xs text-foreground">{date}</p>
        </div>
        <PublicFreshness compact freshness={freshness} locale={locale} />
      </div>
      <div className="grid grid-cols-2 divide-x divide-border">
        <div className="py-5 pr-4">
          <p className="font-display text-4xl font-semibold tracking-[-0.05em] tabular-nums">{products}</p>
          <p className="mt-1 text-xs text-muted-foreground">{copy.dashboard.visibleProducts}</p>
        </div>
        <div className="py-5 pl-4">
          <p className="font-display text-4xl font-semibold tracking-[-0.05em] tabular-nums">{banks}</p>
          <p className="mt-1 text-xs text-muted-foreground">{copy.dashboard.banksInScope}</p>
        </div>
      </div>
      <p className="border-t border-border pt-4 text-xs leading-5 text-muted-foreground">{designCopy.evidenceBoundary}</p>
    </aside>
  );
}

function ProductTopFive({
  accent,
  emptyText,
  filters,
  headingId,
  href,
  linkLabel,
  products,
  subtitle,
  title,
  unavailable,
  unavailableText
}: {
  accent: "deposit" | "loan";
  emptyText: string;
  filters: DashboardPageFilters;
  headingId: string;
  href: string;
  linkLabel: string;
  products: PublicProductsResponse["items"];
  subtitle: string;
  title: string;
  unavailable: boolean;
  unavailableText: string;
}) {
  const copy = getPublicMessages(filters.locale);
  const accentClass = accent === "loan" ? "text-loan" : "text-primary";
  const articleClass = accent === "loan"
    ? "border-loan/30 border-t-loan"
    : "border-primary/25 border-t-primary";
  const headerClass = accent === "loan" ? "bg-loan/[0.045]" : "bg-primary/[0.04]";
  const iconClass = accent === "loan" ? "bg-loan/10 text-loan" : "bg-primary/10 text-primary";
  const metricClass = accent === "loan" ? "border-loan" : "border-primary";
  const rowClass = accent === "loan" ? "divide-loan/15" : "divide-primary/15";
  const familyLabel = accent === "loan" ? copy.nav.loan : copy.nav.products;
  const FamilyIcon = accent === "loan" ? Landmark : PiggyBank;

  return (
    <article className={`overflow-hidden border border-t-4 bg-card/70 ${articleClass}`} aria-labelledby={headingId}>
      <div className={`min-h-[10.5rem] border-b border-border px-4 py-6 md:px-5 ${headerClass}`}>
        <div className="flex items-start gap-3">
          <span className={`grid size-9 shrink-0 place-items-center rounded-full ${iconClass}`} aria-hidden="true">
            <FamilyIcon className="size-4.5" />
          </span>
          <div className="min-w-0">
            <p className={`font-mono text-[10px] font-semibold uppercase tracking-[0.14em] ${accentClass}`}>{familyLabel}</p>
            <h2 id={headingId} className="mt-1 text-2xl font-semibold tracking-[-0.025em] text-foreground">{title}</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{subtitle}</p>
          </div>
        </div>
      </div>
      {unavailable ? (
        <div className="p-4 md:p-5">
          <EmptyPanel text={unavailableText} />
        </div>
      ) : products.length ? (
        <ol className={`grid divide-y ${rowClass}`}>
          {products.map((product, index) => (
            <li className="grid grid-cols-[1.5rem_auto_minmax(0,1fr)] items-center gap-x-3 px-4 py-4 md:px-5" key={product.product_id}>
              <span className="text-sm font-semibold text-muted-foreground tabular-nums">{index + 1}</span>
              <BankLogo bankCode={product.bank_code} bankName={product.bank_name} size="sm" />
              <div className="min-w-0">
                <Link className="inline-flex min-h-11 items-center break-words text-sm font-semibold text-foreground hover:text-primary" href={buildProductDetailHref(filters, product.product_id)}>
                  {product.product_name}
                </Link>
                <p className="truncate text-xs text-muted-foreground">{product.bank_name} · {product.product_type_label}</p>
              </div>
              <div className="col-start-3 mt-2 flex flex-wrap items-center justify-between gap-2">
                <span className={`border-b-2 px-2 py-1 text-base font-semibold text-foreground tabular-nums ${metricClass}`} aria-label={`${copy.grid.metricDisplayRate} ${formatMetricValue(product.card_display_rate, "percent", filters.locale)}`}>
                  {formatMetricValue(product.card_display_rate, "percent", filters.locale)}
                </span>
                {product.product_url ? (
                  <a
                    className="inline-flex min-h-11 items-center justify-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80"
                    href={product.product_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {copy.common.bankPage}
                    <ExternalLink className="size-3.5" aria-hidden="true" />
                  </a>
                ) : null}
              </div>
            </li>
          ))}
        </ol>
      ) : (
        <div className="p-4 md:p-5">
          <EmptyPanel text={emptyText} />
        </div>
      )}
      <div className={`border-t px-4 py-2 md:px-5 ${accent === "loan" ? "border-loan/15" : "border-primary/15"}`}>
        <Link className={`inline-flex min-h-11 items-center gap-2 text-sm font-semibold ${accentClass} hover:underline hover:underline-offset-4`} href={href}>
          {linkLabel}
          <ArrowRight className="size-3.5" aria-hidden="true" />
        </Link>
      </div>
    </article>
  );
}

function EmptyPanel({ text }: { text: string }) {
  return <p className="rounded-lg border border-dashed border-border bg-card px-3 py-6 text-center text-sm text-muted-foreground">{text}</p>;
}

function buildScopeChips(filters: DashboardPageFilters, summary: PublicDashboardSummaryResponse) {
  const bankLabels = new Map(summary.breakdowns.products_by_bank.map((item) => [item.bank_code, item.bank_name]));
  const productTypeLabels = new Map(summary.breakdowns.products_by_product_type.map((item) => [item.product_type, item.product_type_label]));
  const chips: Array<{ href: string; key: string; label: string }> = [];

  for (const bankCode of filters.bankCodes) {
    chips.push({
      key: `bank-${bankCode}`,
      href: buildPublicHref("/dashboard", { ...filters, bankCodes: filters.bankCodes.filter((value) => value !== bankCode), axisPreset: "" }),
      label: bankLabels.get(bankCode) ?? bankCode
    });
  }
  for (const productType of filters.productTypes) {
    chips.push({
      key: `type-${productType}`,
      href: buildPublicHref("/dashboard", { ...filters, productTypes: filters.productTypes.filter((value) => value !== productType), axisPreset: "" }),
      label: productTypeLabels.get(productType) ?? productType
    });
  }
  for (const tag of filters.targetCustomerTags) {
    chips.push({
      key: `tag-${tag}`,
      href: buildPublicHref("/dashboard", { ...filters, targetCustomerTags: filters.targetCustomerTags.filter((value) => value !== tag) }),
      label: formatBucketLabel(tag)
    });
  }

  addBucketChip(chips, "fee", filters.feeBucket, buildPublicHref("/dashboard", { ...filters, feeBucket: "" }));
  addBucketChip(chips, "balance", filters.minimumBalanceBucket, buildPublicHref("/dashboard", { ...filters, minimumBalanceBucket: "" }));
  addBucketChip(chips, "deposit", filters.minimumDepositBucket, buildPublicHref("/dashboard", { ...filters, minimumDepositBucket: "" }));
  addBucketChip(chips, "term", filters.termBucket, buildPublicHref("/dashboard", { ...filters, termBucket: "" }));

  return chips;
}

function addBucketChip(chips: Array<{ href: string; key: string; label: string }>, key: string, value: string, href: string) {
  if (value) {
    chips.push({ href, key: `${key}-${value}`, label: formatBucketLabel(value) });
  }
}

function getMetric(summary: PublicDashboardSummaryResponse, metricKey: string) {
  return summary.metrics.find((metric) => metric.metric_key === metricKey) ?? null;
}

function formatMetricValue(value: number | string | null, unit: string, locale: string) {
  const copy = getPublicMessages(locale);
  if (value === null || (typeof value === "number" && !Number.isFinite(value))) {
    return copy.common.notDisclosed;
  }
  if (typeof value === "string") {
    return value;
  }
  if (unit === "percent") {
    return `${value.toFixed(2).replace(/\.?0+$/, "")}%`;
  }
  if (unit === "currency") {
    return new Intl.NumberFormat(getIntlLocale(locale), {
      style: "currency",
      currency: "CAD",
      maximumFractionDigits: Number.isInteger(value) ? 0 : 2
    }).format(value);
  }
  return formatCount(value, locale);
}

function formatCount(value: number, locale: string) {
  return new Intl.NumberFormat(getIntlLocale(locale), {
    maximumFractionDigits: Number.isInteger(value) ? 0 : 2
  }).format(value);
}

function formatBucketLabel(value: string) {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function buildProductDetailHref(filters: DashboardPageFilters, productId: string) {
  return buildPublicHref(`/products/${encodeURIComponent(productId)}`, filters);
}
