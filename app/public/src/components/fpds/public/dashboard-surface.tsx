import { ArrowUpRight, Building2, ExternalLink, FilterX, Landmark, PackageCheck, PiggyBank, RefreshCw, type LucideIcon } from "lucide-react";
import Link from "next/link";

import { BankLogo } from "@/components/fpds/public/bank-logo";
import { PublicScatterChart } from "@/components/fpds/public/public-dashboard-charts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
  const activeChips = buildScopeChips(filters, summary);
  const bankComposition = buildBankComposition(filters, summary);
  const productTypeLinks = buildProductTypeDashboardLinks(filters, summary);
  const depositComparisonScope = summary.breakdowns.products_by_product_type.every((item) => ["chequing", "gic", "savings"].includes(item.product_type));
  const decisionWidgets = depositComparisonScope
    ? rankings.widgets.filter((widget) => widget.ranking_key !== "recently_changed_30d")
    : [];
  const hasScatter = Boolean(scatter?.points.length && scatter.x_axis && scatter.y_axis);
  const marketGreeting = formatPublicMessage(copy.dashboard.marketGreeting, {
    banks: formatCount(banksInScope, filters.locale),
    countries: formatCount(countriesInScope, filters.locale),
    products: formatCount(totalProducts, filters.locale)
  });

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-7 md:px-6 md:py-9">
      <div className="flex flex-col gap-6">
        <section className="grid gap-6 overflow-hidden rounded-2xl border border-border/80 bg-card p-5 shadow-sm md:p-7 lg:grid-cols-[minmax(0,1fr)_minmax(20rem,0.52fr)] lg:items-end">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold text-primary">{copy.dashboard.kpiSubtitle}</p>
            <h1 className="mt-3 text-4xl font-semibold leading-[1.05] tracking-tight text-foreground md:text-5xl">{copy.dashboard.title}</h1>
            <p className="mt-4 text-base leading-7 text-muted-foreground md:text-lg">{marketGreeting}</p>
            <div className="mt-5 flex flex-wrap gap-2">
              <Button asChild>
                <Link href={productsHref}>
                  <PiggyBank className="size-4" aria-hidden="true" />
                  {copy.nav.products}
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link href={loansHref}>
                  <Landmark className="size-4" aria-hidden="true" />
                  {copy.nav.loan}
                </Link>
              </Button>
              {activeChips.length ? (
                <Button asChild variant="outline">
                  <Link href={clearHref}>
                    <FilterX className="size-4" aria-hidden="true" />
                    {copy.common.clearFilters}
                  </Link>
                </Button>
              ) : null}
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
            <MetricCard icon={Building2} label={copy.dashboard.banksInScope} tone="success" value={formatCount(banksInScope, filters.locale)} />
            <MetricCard icon={PackageCheck} label={copy.dashboard.visibleProducts} tone="primary" value={formatCount(totalProducts, filters.locale)} />
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

        <section className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(20rem,0.9fr)]">
          <div className="space-y-4">
            {decisionWidgets.length ? (
              decisionWidgets.map((widget) => <RankingCards key={widget.ranking_key} filters={filters} locale={filters.locale} productsHref={productsHref} widget={widget} />)
            ) : (
              <EmptyPanel text={rankings.insufficiency_note ?? copy.dashboard.noRankingWidgets} />
            )}
          </div>

          <Card className="border-border/80 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">{copy.dashboard.productsByBank}</CardTitle>
              <CardDescription>{copy.dashboard.compositionSubtitle}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {bankComposition.length ? <CoverageBars items={bankComposition} /> : <EmptyPanel text={copy.dashboard.noRankingWidgets} />}
            </CardContent>
          </Card>
        </section>

        {hasScatter || filters.productTypes.length === 1 ? (
          <section>
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
          </section>
        ) : null}
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
  tone: "info" | "primary" | "success";
  value: string;
}) {
  const toneClassName = {
    info: "border-info/15 bg-info-soft text-info",
    primary: "border-primary/15 bg-secondary text-primary",
    success: "border-success/15 bg-success-soft text-success",
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

function RankingCards({
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
    <section className="overflow-hidden rounded-xl border border-border/80 bg-card shadow-sm" aria-labelledby={`${widget.ranking_key}-title`}>
      <div className="flex flex-col gap-3 border-b border-border/70 bg-muted/25 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-primary">{widget.metric_label}</p>
          <h2 id={`${widget.ranking_key}-title`} className="mt-1 text-xl font-semibold leading-tight text-foreground">
            {title}
          </h2>
        </div>
        <Button asChild variant="outline" size="sm" className="self-start sm:self-auto">
          <Link href={productsHref}>
            {copy.common.more}
            <ArrowUpRight className="size-3.5" aria-hidden="true" />
          </Link>
        </Button>
      </div>
      <div className="grid divide-y divide-border/70">
        {widget.items.slice(0, 5).map((item) => (
          <div className="grid gap-3 px-4 py-3 sm:grid-cols-[auto_auto_minmax(0,1fr)_auto] sm:items-center" key={item.product_id}>
            <span className="w-6 text-left text-sm font-semibold text-muted-foreground tabular-nums sm:text-right">
              {item.rank}
            </span>
            <BankLogo bankCode={item.bank_code} bankName={item.bank_name} size="sm" />
            <div className="min-w-0">
              <Link className="break-words text-sm font-semibold text-foreground hover:text-primary" href={buildProductDetailHref(filters, item.product_id)}>
                {item.product_name}
              </Link>
              <p className="mt-0.5 truncate text-xs text-muted-foreground">{item.bank_name}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2 sm:justify-end">
              <span className="rounded-lg border border-border bg-background px-3 py-2 text-sm font-semibold text-foreground tabular-nums">
                {formatMetricValue(item.metric_value, item.metric_unit, locale)}
              </span>
              {item.product_url ? (
                <Button asChild variant="outline" size="xs">
                  <a href={item.product_url} target="_blank" rel="noreferrer">
                    {copy.common.bankPage}
                    <ExternalLink className="size-3" aria-hidden="true" />
                  </a>
                </Button>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function CoverageBars({ items }: { items: CompositionLinkItem[] }) {
  return (
    <div className="grid gap-3">
      {items.map((item) => (
        <Link className="group grid gap-1.5" href={item.href} key={item.key}>
          <span className="flex items-center justify-between gap-3 text-sm">
            <span className="truncate font-medium text-foreground group-hover:text-primary">{item.label}</span>
            <span className="shrink-0 text-xs font-semibold text-muted-foreground tabular-nums">{item.count}</span>
          </span>
          <span className="h-2 overflow-hidden rounded-full bg-muted">
            <span className="block h-full rounded-full bg-primary/75 transition-colors group-hover:bg-primary" style={{ width: `${Math.max(4, Math.min(100, item.share_percent))}%` }} />
          </span>
        </Link>
      ))}
    </div>
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
