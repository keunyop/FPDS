import { ArrowUpRight, BarChart3, Database, Gauge, RefreshCw } from "lucide-react";
import Link from "next/link";
import type { ComponentType } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatPublicMessage, getIntlLocale, getPublicMessages } from "@/lib/public-locale";
import {
  type PublicDashboardRankingsResponse,
  type PublicDashboardSummaryResponse,
  type PublicFilterOption,
  type PublicFiltersResponse
} from "@/lib/public-api";
import { buildPublicHref, type DashboardPageFilters } from "@/lib/public-query";

type DashboardSurfaceProps = {
  apiUnavailable: boolean;
  filterOptions: PublicFiltersResponse | null;
  filters: DashboardPageFilters;
  rankings: PublicDashboardRankingsResponse | null;
  summary: PublicDashboardSummaryResponse | null;
};

export function DashboardSurface({ apiUnavailable, filterOptions, filters, rankings, summary }: DashboardSurfaceProps) {
  const copy = getPublicMessages(filters.locale);
  const productsHref = buildPublicHref("/products", filters);
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

  if (apiUnavailable || !filterOptions || !rankings || !summary) {
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
  const highestRate = getMetric(summary, "highest_display_rate");
  const activeChips = buildActiveChips(filters, filterOptions);
  const selectedProductType = filters.productTypes.length === 1 ? filters.productTypes[0] : "";
  const scopeLabel = selectedProductType ? findLabel(filterOptions.product_types, selectedProductType) : copy.dashboard.mixedMarket;

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 md:px-6">
      <div className="flex flex-col gap-6">
        <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
          <div>
            <p className="text-sm font-medium text-primary">{copy.dashboard.marketSnapshot}</p>
            <h1 className="mt-2 max-w-3xl text-3xl font-semibold tracking-tight text-foreground md:text-4xl">{copy.dashboard.title}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">{copy.dashboard.description}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button asChild>
              <Link href={productsHref}>
                {copy.dashboard.openProducts}
                <ArrowUpRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link href={clearHref}>{copy.dashboard.clearScope}</Link>
            </Button>
          </div>
        </section>

        <section className="flex flex-col gap-3 rounded-lg border border-border bg-card px-4 py-3 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <ScopeBadge label={scopeLabel} />
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
              <span className="text-sm text-muted-foreground">{copy.dashboard.noActiveFilters}</span>
            )}
          </div>
          <p className="text-sm text-muted-foreground">{formatFreshnessLine(summary.freshness, filters.locale)}</p>
        </section>

        <section className="grid gap-4 md:grid-cols-3" aria-label={copy.dashboard.marketSnapshot}>
          <MetricCard
            icon={Gauge}
            label={copy.dashboard.visibleProducts}
            value={formatCount(totalProducts, filters.locale)}
            detail={copy.dashboard.activeProducts}
          />
          <MetricCard
            icon={Database}
            label={copy.dashboard.banksInScope}
            value={formatCount(banksInScope, filters.locale)}
            detail={copy.dashboard.kpiSubtitle}
          />
          <MetricCard
            icon={BarChart3}
            label={copy.dashboard.peakRate}
            value={highestRate ? formatMetricValue(highestRate.value, highestRate.unit, filters.locale) : copy.common.notDisclosed}
            detail={highestRate?.label ?? copy.dashboard.peakRate}
          />
        </section>

        <section>
          <Card>
            <CardHeader>
              <CardTitle>{copy.dashboard.rankings}</CardTitle>
              <CardDescription>{copy.dashboard.rankingsSubtitle}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {rankings.widgets.length ? (
                rankings.widgets.map((widget) => (
                  <RankingTable key={widget.ranking_key} filters={filters} locale={filters.locale} widget={widget} />
                ))
              ) : (
                <p className="rounded-lg border border-dashed border-border bg-background px-3 py-6 text-center text-sm text-muted-foreground">
                  {rankings.insufficiency_note ?? copy.dashboard.noRankingWidgets}
                </p>
              )}
            </CardContent>
          </Card>
        </section>
      </div>
    </main>
  );
}

function MetricCard({
  detail,
  icon: Icon,
  label,
  value
}: {
  detail: string;
  icon: ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-3">
        <div>
          <CardDescription>{label}</CardDescription>
          <CardTitle className="mt-2 text-2xl tabular-nums">{value}</CardTitle>
        </div>
        <span className="rounded-lg border border-border bg-background p-2 text-primary">
          <Icon className="size-4" aria-hidden="true" />
        </span>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground">{detail}</p>
      </CardContent>
    </Card>
  );
}

function RankingTable({
  filters,
  locale,
  widget
}: {
  filters: DashboardPageFilters;
  locale: string;
  widget: PublicDashboardRankingsResponse["widgets"][number];
}) {
  const copy = getPublicMessages(locale);

  return (
    <div className="rounded-lg border border-border">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-3 py-2">
        <div>
          <p className="text-sm font-medium text-foreground">{widget.title}</p>
          <p className="text-xs text-muted-foreground">
            {copy.dashboard.rankedBy} {widget.metric_label}
            {widget.window_days ? `, ${formatPublicMessage(copy.dashboard.trailingDays, { days: widget.window_days })}` : ""}
          </p>
        </div>
        <ScopeBadge label={`${widget.items.length}`} />
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">#</TableHead>
            <TableHead>{copy.grid.sortProductName}</TableHead>
            <TableHead>{copy.grid.banks}</TableHead>
            <TableHead className="text-right">{widget.metric_label}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {widget.items.map((item) => (
            <TableRow key={item.product_id}>
              <TableCell className="font-medium">{item.rank}</TableCell>
              <TableCell>
                <Link className="font-medium text-foreground hover:text-primary" href={buildRankingGridHref(filters, widget.ranking_key, item)}>
                  {item.product_name}
                </Link>
              </TableCell>
              <TableCell className="text-muted-foreground">{item.bank_name}</TableCell>
              <TableCell className="text-right font-medium tabular-nums">{formatMetricValue(item.metric_value, item.metric_unit, locale)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function ScopeBadge({ label }: { label: string }) {
  return <span className="rounded-md border border-border bg-background px-2.5 py-1 text-xs font-medium text-foreground">{label}</span>;
}

function getMetric(summary: PublicDashboardSummaryResponse, metricKey: string) {
  return summary.metrics.find((metric) => metric.metric_key === metricKey) ?? null;
}

function buildActiveChips(filters: DashboardPageFilters, filterOptions: PublicFiltersResponse) {
  const chips: Array<{ group: string; href: string; label: string; value: string }> = [];

  for (const bankCode of filters.bankCodes) {
    chips.push({
      group: "bank_code",
      href: buildPublicHref("/dashboard", { ...filters, bankCodes: filters.bankCodes.filter((value) => value !== bankCode) }),
      label: findLabel(filterOptions.banks, bankCode),
      value: bankCode
    });
  }
  for (const productType of filters.productTypes) {
    chips.push({
      group: "product_type",
      href: buildPublicHref("/dashboard", { ...filters, productTypes: filters.productTypes.filter((value) => value !== productType), axisPreset: "" }),
      label: findLabel(filterOptions.product_types, productType),
      value: productType
    });
  }
  for (const tag of filters.targetCustomerTags) {
    chips.push({
      group: "target_customer_tag",
      href: buildPublicHref("/dashboard", { ...filters, targetCustomerTags: filters.targetCustomerTags.filter((value) => value !== tag) }),
      label: findLabel(filterOptions.target_customer_tags, tag),
      value: tag
    });
  }

  addSingleChip(chips, "fee_bucket", filters.feeBucket, filterOptions.fee_buckets, buildPublicHref("/dashboard", { ...filters, feeBucket: "" }));
  addSingleChip(
    chips,
    "minimum_balance_bucket",
    filters.minimumBalanceBucket,
    filterOptions.minimum_balance_buckets,
    buildPublicHref("/dashboard", { ...filters, minimumBalanceBucket: "" })
  );
  addSingleChip(
    chips,
    "minimum_deposit_bucket",
    filters.minimumDepositBucket,
    filterOptions.minimum_deposit_buckets,
    buildPublicHref("/dashboard", { ...filters, minimumDepositBucket: "" })
  );
  addSingleChip(chips, "term_bucket", filters.termBucket, filterOptions.term_buckets, buildPublicHref("/dashboard", { ...filters, termBucket: "" }));

  return chips;
}

function addSingleChip(
  chips: Array<{ group: string; href: string; label: string; value: string }>,
  group: string,
  value: string,
  options: PublicFilterOption[],
  href: string
) {
  if (value) {
    chips.push({ group, href, label: findLabel(options, value), value });
  }
}

function findLabel(options: Array<{ label: string; value: string }>, value: string) {
  return options.find((option) => option.value === value)?.label ?? value;
}

function formatMetricValue(value: number | string | null, unit: string, locale: string) {
  const copy = getPublicMessages(locale);
  if (value === null || Number.isNaN(value)) {
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

function formatFreshnessLine(freshness: PublicDashboardSummaryResponse["freshness"], locale: string) {
  const copy = getPublicMessages(locale);
  if (!freshness.refreshed_at) {
    return copy.common.noSuccessfulSnapshot;
  }
  return `${copy.dashboard.freshness}: ${formatFixedDateTime(freshness.refreshed_at)}`;
}

function formatFixedDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  const pad = (part: number) => String(part).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function buildRankingGridHref(
  filters: DashboardPageFilters,
  rankingKey: string,
  item: PublicDashboardRankingsResponse["widgets"][number]["items"][number]
) {
  const sort = getGridSortForRanking(rankingKey);
  return buildPublicHref("/products", {
    ...filters,
    bankCodes: [item.bank_code],
    productTypes: [item.product_type],
    page: 1,
    sortBy: sort.sortBy,
    sortOrder: sort.sortOrder
  });
}

function getGridSortForRanking(rankingKey: string) {
  switch (rankingKey) {
    case "highest_display_rate":
      return { sortBy: "display_rate", sortOrder: "desc" as const };
    case "lowest_monthly_fee":
      return { sortBy: "monthly_fee", sortOrder: "asc" as const };
    case "lowest_minimum_deposit":
      return { sortBy: "minimum_deposit", sortOrder: "asc" as const };
    case "recently_changed_30d":
      return { sortBy: "last_changed_at", sortOrder: "desc" as const };
    default:
      return { sortBy: "default", sortOrder: "desc" as const };
  }
}
