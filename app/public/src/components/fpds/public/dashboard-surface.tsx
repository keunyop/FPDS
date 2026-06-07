import { ArrowUpRight, Building2, ExternalLink, FilterX, PackageCheck, RefreshCw, Search, TrendingUp, type LucideIcon } from "lucide-react";
import Link from "next/link";

import { CompositionBarChart, ProductTypeBarChart, PublicScatterChart } from "@/components/fpds/public/public-dashboard-charts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatPublicMessage, getIntlLocale, getPublicMessages } from "@/lib/public-locale";
import {
  type PublicDashboardRankingsResponse,
  type PublicDashboardScatterResponse,
  type PublicDashboardSummaryResponse
} from "@/lib/public-api";
import { buildPublicHref, type DashboardPageFilters } from "@/lib/public-query";

type DashboardSurfaceProps = {
  apiUnavailable: boolean;
  filters: DashboardPageFilters;
  rankings: PublicDashboardRankingsResponse | null;
  scatter: PublicDashboardScatterResponse | null;
  summary: PublicDashboardSummaryResponse | null;
};

type CompositionChartItem = {
  count: number;
  key: string;
  label: string;
  share_percent: number;
};

type CompositionLinkItem = CompositionChartItem & {
  href: string;
};

export function DashboardSurface({ apiUnavailable, filters, rankings, scatter, summary }: DashboardSurfaceProps) {
  const copy = getPublicMessages(filters.locale);
  const productsHref = buildPublicHref("/products", { ...filters, page: 1 });
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

  if (apiUnavailable || !rankings || !summary) {
    return (
      <main className="mx-auto w-full max-w-5xl px-4 py-10 md:px-6">
        <Card className="border-destructive/25">
          <CardHeader>
            <CardTitle>{copy.dashboard.apiUnavailableTitle}</CardTitle>
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
  const countriesInScope = 1;
  const highestRate = getMetric(summary, "highest_display_rate");
  const recentlyChanged = getMetric(summary, "recently_changed_products_30d");
  const activeChips = buildScopeChips(filters, summary);
  const bankComposition = buildBankComposition(filters, summary);
  const productTypeComposition = buildProductTypeComposition(filters, summary);
  const productTypeLinks = buildProductTypeDashboardLinks(filters, summary);
  const hasScatter = Boolean(scatter?.points.length && scatter.x_axis && scatter.y_axis);
  const marketGreeting = formatPublicMessage(copy.dashboard.marketGreeting, {
    banks: formatCount(banksInScope, filters.locale),
    countries: formatCount(countriesInScope, filters.locale),
    products: formatCount(totalProducts, filters.locale)
  });

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-7 md:px-6 md:py-9">
      <div className="flex flex-col gap-6">
        <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
          <div className="max-w-3xl">
            <p className="text-sm font-medium text-primary">{copy.dashboard.marketSnapshot}</p>
            <h1 className="mt-2 text-4xl font-semibold leading-[1.05] text-foreground md:text-5xl">{copy.dashboard.title}</h1>
            <p className="mt-4 text-base leading-7 text-muted-foreground md:text-lg">{marketGreeting}</p>
          </div>
          <div className="flex flex-wrap gap-2 lg:justify-end">
            <Button asChild>
              <Link href={productsHref}>
                <Search className="size-4" aria-hidden="true" />
                {copy.dashboard.openProducts}
              </Link>
            </Button>
            {activeChips.length ? (
              <Button asChild variant="outline">
                <Link href={clearHref}>
                  <FilterX className="size-4" aria-hidden="true" />
                  {copy.dashboard.clearScope}
                </Link>
              </Button>
            ) : null}
          </div>
        </section>

        {activeChips.length ? (
          <section aria-label={copy.grid.currentScope} className="flex flex-wrap gap-2 rounded-lg border border-border bg-card px-4 py-3 shadow-sm">
            {activeChips.map((chip) => (
              <Link
                key={chip.key}
                href={chip.href}
                className="rounded-md border border-border bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                {chip.label}
              </Link>
            ))}
          </section>
        ) : null}

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard icon={PackageCheck} label={copy.dashboard.visibleProducts} tone="primary" value={formatCount(totalProducts, filters.locale)} />
          <MetricCard icon={Building2} label={copy.dashboard.banksInScope} tone="success" value={formatCount(banksInScope, filters.locale)} />
          <MetricCard
            icon={TrendingUp}
            label={copy.dashboard.peakRate}
            tone="warning"
            value={highestRate ? formatMetricValue(highestRate.value, highestRate.unit, filters.locale) : copy.common.notDisclosed}
          />
          <MetricCard
            icon={RefreshCw}
            label={recentlyChanged?.label ?? copy.common.changedOn}
            tone="info"
            value={recentlyChanged ? formatMetricValue(recentlyChanged.value, recentlyChanged.unit, filters.locale) : copy.common.notDisclosed}
          />
        </section>

        <section className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
          <Card className="border-border/80 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">{copy.dashboard.productsByBank}</CardTitle>
              <CardDescription>{copy.dashboard.compositionSubtitle}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {bankComposition.length ? <CompositionBarChart items={bankComposition} /> : <EmptyPanel text={copy.dashboard.noRankingWidgets} />}
              <CompositionLinks items={bankComposition} />
            </CardContent>
          </Card>

          <Card className="border-border/80 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">{copy.dashboard.productsByType}</CardTitle>
              <CardDescription>{copy.dashboard.comparisonSubtitle}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {productTypeComposition.length ? <ProductTypeBarChart items={productTypeComposition} /> : <EmptyPanel text={copy.dashboard.noRankingWidgets} />}
              <CompositionLinks items={productTypeComposition} />
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(20rem,0.9fr)]">
          <Card className="border-border/80 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">{scatter?.title ?? copy.dashboard.comparisonMap}</CardTitle>
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
                  {productTypeLinks.length ? <CompositionLinks className="mt-4" items={productTypeLinks} /> : null}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-border/80 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">{copy.dashboard.dataNotes}</CardTitle>
              <CardDescription>{copy.dashboard.freshness}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm leading-6 text-muted-foreground">{copy.dashboard.dataNotesBody}</p>
              <dl className="grid gap-3 rounded-lg border border-border bg-muted/20 p-3">
                <Fact label={copy.dashboard.marketSnapshot} value={summary.freshness.snapshot_id ?? copy.common.noSuccessfulSnapshot} />
                <Fact label={copy.dashboard.freshness} value={formatDateTime(summary.freshness.refreshed_at, filters.locale)} />
              </dl>
              <Button asChild variant="outline" className="w-full justify-between">
                <Link href={buildPublicHref("/methodology", filters)}>
                  {copy.nav.methodology}
                  <ArrowUpRight className="size-3.5" aria-hidden="true" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        </section>

        <section className="space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 className="text-2xl font-semibold leading-tight text-foreground">{copy.dashboard.coverageTable}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{copy.dashboard.coverageSubtitle}</p>
            </div>
          </div>

          {rankings.widgets.length ? (
            rankings.widgets.map((widget) => <RankingTable key={widget.ranking_key} filters={filters} locale={filters.locale} productsHref={productsHref} widget={widget} />)
          ) : (
            <EmptyPanel text={rankings.insufficiency_note ?? copy.dashboard.noRankingWidgets} />
          )}
        </section>
      </div>
    </main>
  );
}

function MetricCard({
  icon: Icon,
  label,
  tone,
  value
}: {
  icon: LucideIcon;
  label: string;
  tone: "info" | "primary" | "success" | "warning";
  value: string;
}) {
  const toneClassName = {
    info: "border-info/15 bg-info-soft text-info",
    primary: "border-primary/15 bg-secondary text-primary",
    success: "border-success/15 bg-success-soft text-success",
    warning: "border-warning/15 bg-warning-soft text-warning"
  }[tone];

  return (
    <Card className="border-border/80 shadow-sm">
      <CardHeader className="grid-cols-[minmax(0,1fr)_auto] items-center gap-4">
        <div className="min-w-0">
          <CardDescription className="truncate">{label}</CardDescription>
          <CardTitle className="mt-2 break-words text-3xl tabular-nums">{value}</CardTitle>
        </div>
        <span className={`flex size-9 items-center justify-center rounded-lg border ${toneClassName}`}>
          <Icon className="size-4" aria-hidden="true" />
        </span>
      </CardHeader>
    </Card>
  );
}

function RankingTable({
  filters,
  locale,
  productsHref,
  widget
}: {
  filters: DashboardPageFilters;
  locale: string;
  productsHref: string;
  widget: PublicDashboardRankingsResponse["widgets"][number];
}) {
  const copy = getPublicMessages(locale);
  const title = widget.ranking_key === "highest_display_rate" ? copy.dashboard.topInterestRateTitle : widget.title;

  return (
    <section className="space-y-3" aria-labelledby={`${widget.ranking_key}-title`}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h3 id={`${widget.ranking_key}-title`} className="text-xl font-semibold leading-tight text-foreground">
          {title}
        </h3>
        <Button asChild variant="outline" size="sm" className="self-start sm:self-auto">
          <Link href={productsHref}>
            {copy.common.more}
            <ArrowUpRight className="size-3.5" aria-hidden="true" />
          </Link>
        </Button>
      </div>
      <Card className="bg-card py-0 shadow-sm">
        <CardContent className="overflow-x-auto px-0">
          <Table className="min-w-[760px]">
            <TableHeader className="bg-muted/40">
              <TableRow>
                <TableHead className="w-14 px-4">#</TableHead>
                <TableHead className="px-4">{copy.grid.sortProductName}</TableHead>
                <TableHead className="px-4">{copy.grid.banks}</TableHead>
                <TableHead className="px-4 text-right">{widget.metric_label}</TableHead>
                <TableHead className="w-36 px-4 text-right">{copy.common.bankPage}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {widget.items.map((item) => (
                <TableRow key={item.product_id}>
                  <TableCell className="px-4 py-3 font-medium">
                    <span className="inline-flex size-6 items-center justify-center rounded-md bg-muted text-xs text-muted-foreground">{item.rank}</span>
                  </TableCell>
                  <TableCell className="px-4 py-3">
                    <Link className="font-medium text-foreground hover:text-primary" href={buildProductDetailHref(filters, item.product_id)}>
                      {item.product_name}
                    </Link>
                  </TableCell>
                  <TableCell className="px-4 py-3 text-muted-foreground">{item.bank_name}</TableCell>
                  <TableCell className="px-4 py-3 text-right font-medium tabular-nums">{formatMetricValue(item.metric_value, item.metric_unit, locale)}</TableCell>
                  <TableCell className="px-4 py-3 text-right">
                    {item.product_url ? (
                      <Button asChild variant="outline" size="xs">
                        <a href={item.product_url} target="_blank" rel="noreferrer">
                          {copy.common.bankPage}
                          <ExternalLink className="size-3" aria-hidden="true" />
                        </a>
                      </Button>
                    ) : (
                      <span className="text-xs text-muted-foreground">{copy.common.notDisclosed}</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </section>
  );
}

function CompositionLinks({ className = "", items }: { className?: string; items: CompositionLinkItem[] }) {
  if (!items.length) {
    return null;
  }

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {items.slice(0, 6).map((item) => (
        <Link
          key={item.key}
          href={item.href}
          className="inline-flex min-h-8 items-center gap-2 rounded-md border border-border bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <span>{item.label}</span>
          <span className="rounded bg-muted px-1.5 py-0.5 tabular-nums">{item.count}</span>
        </Link>
      ))}
    </div>
  );
}

function EmptyPanel({ text }: { text: string }) {
  return <p className="rounded-lg border border-dashed border-border bg-card px-3 py-6 text-center text-sm text-muted-foreground">{text}</p>;
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-1 break-words text-sm font-medium text-foreground">{value}</dd>
    </div>
  );
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

function buildBankComposition(filters: DashboardPageFilters, summary: PublicDashboardSummaryResponse): CompositionLinkItem[] {
  return summary.breakdowns.products_by_bank.map((item) => ({
    count: item.count,
    href: buildPublicHref("/products", { ...filters, bankCodes: [item.bank_code], page: 1 }),
    key: item.bank_code,
    label: item.bank_name,
    share_percent: item.share_percent
  }));
}

function buildProductTypeComposition(filters: DashboardPageFilters, summary: PublicDashboardSummaryResponse): CompositionLinkItem[] {
  return summary.breakdowns.products_by_product_type.map((item) => ({
    count: item.count,
    href: buildPublicHref("/products", { ...filters, productTypes: [item.product_type], page: 1 }),
    key: item.product_type,
    label: item.product_type_label,
    share_percent: item.share_percent
  }));
}

function buildProductTypeDashboardLinks(filters: DashboardPageFilters, summary: PublicDashboardSummaryResponse): CompositionLinkItem[] {
  return summary.breakdowns.products_by_product_type.map((item) => ({
    count: item.count,
    href: buildPublicHref("/dashboard", { ...filters, productTypes: [item.product_type], axisPreset: defaultAxisPreset(item.product_type) }),
    key: item.product_type,
    label: item.product_type_label,
    share_percent: item.share_percent
  }));
}

function defaultAxisPreset(productType: string) {
  switch (productType) {
    case "chequing":
      return "chequing_fee_vs_minimum_balance";
    case "savings":
      return "savings_rate_vs_minimum_balance";
    case "gic":
      return "gic_rate_vs_minimum_deposit";
    default:
      return "";
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

function formatDateTime(value: string | null, locale: string) {
  const copy = getPublicMessages(locale);
  if (!value) {
    return copy.common.noDate;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(getIntlLocale(locale), {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
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
