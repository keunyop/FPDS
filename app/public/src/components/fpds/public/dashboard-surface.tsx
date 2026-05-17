import { ArrowUpRight, ExternalLink, RefreshCw } from "lucide-react";
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
      <div className="flex flex-col gap-6">
        <section>
          <h1 className="max-w-4xl text-3xl font-semibold tracking-tight text-foreground md:text-4xl">{marketGreeting}</h1>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          <MetricCard label={copy.dashboard.visibleProducts} value={formatCount(totalProducts, filters.locale)} />
          <MetricCard label={copy.dashboard.banksInScope} value={formatCount(banksInScope, filters.locale)} />
          <MetricCard
            label={copy.dashboard.peakRate}
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

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="mt-2 text-2xl tabular-nums">{value}</CardTitle>
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

  return (
    <Card className="overflow-hidden bg-card">
      <CardHeader className="flex-row items-center justify-between gap-3 border-b border-border py-3">
        <CardTitle className="text-base">{widget.title}</CardTitle>
        <Button asChild variant="ghost" size="sm">
          <Link href={productsHref}>
            더보기
            <ArrowUpRight className="size-3.5" aria-hidden="true" />
          </Link>
        </Button>
      </CardHeader>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">#</TableHead>
            <TableHead>{copy.grid.sortProductName}</TableHead>
            <TableHead>{copy.grid.banks}</TableHead>
            <TableHead className="text-right">{widget.metric_label}</TableHead>
            <TableHead className="w-32 text-right">Bank page</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {widget.items.map((item) => (
            <TableRow key={item.product_id}>
              <TableCell className="font-medium">{item.rank}</TableCell>
              <TableCell>
                <Link className="font-medium text-foreground hover:text-primary" href={buildProductDetailHref(filters, item.product_id)}>
                  {item.product_name}
                </Link>
              </TableCell>
              <TableCell className="text-muted-foreground">{item.bank_name}</TableCell>
              <TableCell className="text-right font-medium tabular-nums">{formatMetricValue(item.metric_value, item.metric_unit, locale)}</TableCell>
              <TableCell className="text-right">
                {item.product_url ? (
                  <Button asChild variant="outline" size="xs">
                    <a href={item.product_url} target="_blank" rel="noreferrer">
                      Bank page
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
    </Card>
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
