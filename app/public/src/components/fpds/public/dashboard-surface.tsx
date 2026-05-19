import { ArrowUpRight, Building2, ExternalLink, PackageCheck, RefreshCw, TrendingUp, type LucideIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatPublicMessage, getIntlLocale, getPublicMessages } from "@/lib/public-locale";
import {
  type PublicDashboardRankingsResponse,
  type PublicDashboardSummaryResponse
} from "@/lib/public-api";
import { buildPublicHref, type DashboardPageFilters } from "@/lib/public-query";

type DashboardSurfaceProps = {
  apiUnavailable: boolean;
  filters: DashboardPageFilters;
  rankings: PublicDashboardRankingsResponse | null;
  summary: PublicDashboardSummaryResponse | null;
};

export function DashboardSurface({ apiUnavailable, filters, rankings, summary }: DashboardSurfaceProps) {
  const copy = getPublicMessages(filters.locale);
  const productsHref = buildPublicHref("/products", filters);

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
  const marketGreeting = formatPublicMessage(copy.dashboard.marketGreeting, {
    banks: formatCount(banksInScope, filters.locale),
    countries: formatCount(countriesInScope, filters.locale),
    products: formatCount(totalProducts, filters.locale)
  });
  const visibleRankingWidgets = rankings.widgets.filter((widget) => widget.ranking_key !== "recently_changed_30d");

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 md:px-6">
      <div className="flex flex-col gap-7">
        <section className="pt-2 md:pt-5">
          <div className="max-w-3xl">
            <h1 className="text-4xl font-semibold leading-[1.05] text-foreground md:text-5xl">{copy.dashboard.title}</h1>
            <p className="mt-4 text-base leading-7 text-muted-foreground md:text-lg">{marketGreeting}</p>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <MetricCard icon={PackageCheck} label={copy.dashboard.visibleProducts} tone="primary" value={formatCount(totalProducts, filters.locale)} />
          <MetricCard icon={Building2} label={copy.dashboard.banksInScope} tone="success" value={formatCount(banksInScope, filters.locale)} />
          <MetricCard
            icon={TrendingUp}
            label={copy.dashboard.peakRate}
            tone="warning"
            value={highestRate ? formatMetricValue(highestRate.value, highestRate.unit, filters.locale) : copy.common.notDisclosed}
          />
        </section>

        <section className="space-y-4">
          {visibleRankingWidgets.length ? (
            visibleRankingWidgets.map((widget) => (
              <RankingTable
                key={widget.ranking_key}
                filters={filters}
                locale={filters.locale}
                productsHref={productsHref}
                widget={widget}
              />
            ))
          ) : (
            <p className="rounded-lg border border-dashed border-border bg-card px-3 py-6 text-center text-sm text-muted-foreground">
              {rankings.insufficiency_note ?? copy.dashboard.noRankingWidgets}
            </p>
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
  tone: "primary" | "success" | "warning";
  value: string;
}) {
  const toneClassName = {
    primary: "border-primary/15 bg-secondary text-primary",
    success: "border-success/15 bg-success-soft text-success",
    warning: "border-warning/15 bg-warning-soft text-warning"
  }[tone];

  return (
    <Card className="border-border/80 shadow-sm">
      <CardHeader className="grid-cols-[minmax(0,1fr)_auto] items-center gap-4">
        <div>
          <CardDescription>{label}</CardDescription>
          <CardTitle className="mt-2 text-3xl tabular-nums">{value}</CardTitle>
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
        <h2 id={`${widget.ranking_key}-title`} className="text-2xl font-semibold leading-tight text-foreground">
          {title}
        </h2>
        <Button asChild variant="outline" size="sm" className="self-start sm:self-auto">
          <Link href={productsHref}>
            {copy.common.more}
            <ArrowUpRight className="size-3.5" aria-hidden="true" />
          </Link>
        </Button>
      </div>
      <Card className="bg-card py-0 shadow-sm">
        <CardContent className="px-0">
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
                    <span className="inline-flex size-6 items-center justify-center rounded-md bg-muted text-xs text-muted-foreground">
                      {item.rank}
                    </span>
                  </TableCell>
                  <TableCell className="px-4 py-3">
                    <Link className="font-medium text-foreground hover:text-primary" href={buildProductDetailHref(filters, item.product_id)}>
                      {item.product_name}
                    </Link>
                  </TableCell>
                  <TableCell className="px-4 py-3 text-muted-foreground">{item.bank_name}</TableCell>
                  <TableCell className="px-4 py-3 text-right font-medium tabular-nums">
                    {formatMetricValue(item.metric_value, item.metric_unit, locale)}
                  </TableCell>
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

function getMetric(summary: PublicDashboardSummaryResponse, metricKey: string) {
  return summary.metrics.find((metric) => metric.metric_key === metricKey) ?? null;
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

function buildProductDetailHref(filters: DashboardPageFilters, productId: string) {
  return buildPublicHref(`/products/${encodeURIComponent(productId)}`, filters);
}
