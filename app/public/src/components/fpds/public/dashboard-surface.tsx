import Link from "next/link";

import { Button } from "@/components/ui/button";
import { formatPublicMessage, getIntlLocale, getPublicMessages } from "@/lib/public-locale";
import {
  type PublicDashboardBreakdownItem,
  type PublicDashboardRankingsResponse,
  type PublicDashboardScatterResponse,
  type PublicDashboardSummaryResponse,
  type PublicFilterOption,
  type PublicFiltersResponse
} from "@/lib/public-api";
import { buildPublicHref, type DashboardPageFilters } from "@/lib/public-query";
import { cn } from "@/lib/utils";

type DashboardSurfaceProps = {
  apiUnavailable: boolean;
  filterOptions: PublicFiltersResponse | null;
  filters: DashboardPageFilters;
  rankings: PublicDashboardRankingsResponse | null;
  scatter: PublicDashboardScatterResponse | null;
  summary: PublicDashboardSummaryResponse | null;
};

export function DashboardSurface({ apiUnavailable, filterOptions, filters, rankings, scatter, summary }: DashboardSurfaceProps) {
  const productGridHref = buildPublicHref("/products", filters);
  const copy = getPublicMessages(filters.locale);
  const gicScatterOptions = [
    {
      value: "gic_rate_vs_minimum_deposit",
      label: filters.locale === "ko" ? "금리 대비 예치금" : filters.locale === "ja" ? "金利と預入額" : "Rate vs deposit"
    },
    {
      value: "gic_term_vs_rate",
      label: filters.locale === "ko" ? "기간 대비 금리" : filters.locale === "ja" ? "期間と金利" : "Term vs rate"
    }
  ];

  if (apiUnavailable || !filterOptions || !rankings || !scatter || !summary) {
    return (
      <main className="mx-auto flex w-full max-w-6xl px-4 py-12 md:px-6 md:py-16">
        <section className="w-full rounded-[2rem] border border-destructive/20 bg-card/95 p-8 shadow-[0_24px_60px_rgba(15,23,42,0.08)] md:p-10">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-destructive">{copy.dashboard.apiUnavailableTitle}</p>
          <h1 className="mt-4 max-w-2xl text-4xl font-semibold tracking-tight text-foreground">{copy.dashboard.apiUnavailableTitle}</h1>
          <p className="mt-4 max-w-3xl text-base leading-7 text-muted-foreground">
            {copy.dashboard.apiUnavailableBody}
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild>
              <Link href={buildPublicHref("/dashboard", filters)}>{copy.dashboard.retryDashboard}</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href={productGridHref}>{copy.dashboard.openProductGrid}</Link>
            </Button>
          </div>
        </section>
      </main>
    );
  }

  const totalProducts = getMetric(summary, "total_active_products")?.value ?? 0;
  const banksInScope = getMetric(summary, "banks_in_scope")?.value ?? 0;
  const highestRate = getMetric(summary, "highest_display_rate");
  const selectedProductType = filters.productTypes.length === 1 ? filters.productTypes[0] : "";
  const overviewLabel = selectedProductType ? titleCase(selectedProductType) : copy.dashboard.mixedMarket;
  const scopeSummary = buildScopeSummary(filters, filterOptions);
  const activeChips = buildActiveChips(filters, filterOptions);
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

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 md:px-6 md:py-10">
      <section className="rounded-[2rem] border border-border/80 bg-card/85 p-6 shadow-[0_30px_80px_rgba(15,23,42,0.06)] md:p-8">
        <div className="flex flex-col gap-8">
          <header className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(18rem,0.8fr)] lg:items-end">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-primary">{copy.dashboard.eyebrow}</p>
              <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight text-foreground md:text-5xl">{copy.dashboard.title}</h1>
              <p className="mt-4 max-w-3xl text-base leading-7 text-muted-foreground">{copy.dashboard.description}</p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Button asChild>
                  <Link href={productGridHref}>{copy.dashboard.openProductGrid}</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href={clearHref}>{copy.dashboard.clearScope}</Link>
                </Button>
              </div>
            </div>
            <div className="rounded-[1.5rem] border border-border/70 bg-background/80 p-5">
              <p className="text-sm font-medium text-foreground">{copy.grid.currentScope}</p>
              <p className="mt-2 text-3xl font-semibold tracking-tight text-foreground">{formatCount(totalProducts, filters.locale)}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {formatPublicMessage(copy.dashboard.productsAcrossBanks, { banks: formatCount(banksInScope, filters.locale) })}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <ScopeBadge label={overviewLabel} tone="primary" />
                {highestRate?.value != null ? <ScopeBadge label={`${copy.dashboard.peakRate} ${formatMetricValue(highestRate.value, highestRate.unit, filters.locale)}`} tone="info" /> : null}
              </div>
              <p className="mt-4 text-sm text-muted-foreground">{formatFreshnessLine(summary.freshness, filters.locale)}</p>
            </div>
          </header>

          <section className="rounded-[1.75rem] border border-border/80 bg-background/65 p-5">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-3">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">{copy.dashboard.scopeSummary}</p>
                  <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{copy.dashboard.scopeTitle}</h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                    {scopeSummary}{" "}
                    {filters.locale === "ko"
                      ? "Product Grid 형제 라우트에서 필터를 조정한 뒤 돌아오면 같은 범위를 시장 스냅샷으로 읽을 수 있습니다."
                      : filters.locale === "ja"
                        ? "Product Grid でフィルターを調整して戻ると、同じ範囲を市場スナップショットとして確認できます。"
                        : "Adjust filter selections on the Product Grid sibling route and return here to read the same scope as a market snapshot."}
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
                  <p className="text-sm text-muted-foreground">{copy.dashboard.noActiveFilters}</p>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Button asChild variant="outline">
                  <Link href={productGridHref}>{copy.dashboard.adjustScope}</Link>
                </Button>
              </div>
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {summary.metrics.map((metric) => (
              <MetricCard key={metric.metric_key} locale={filters.locale} metric={metric} />
            ))}
          </section>

          <section className="grid gap-4 lg:grid-cols-2">
            <BreakdownCard
              title={copy.dashboard.breakdownByBank}
              subtitle={copy.dashboard.breakdownByBankDescription}
              items={summary.breakdowns.products_by_bank.map((item) => ({
                key: item.bank_code,
                label: item.bank_name,
                count: item.count,
                share_percent: item.share_percent,
                href: buildGridDrilldownHref(filters, { bankCode: item.bank_code })
              }))}
              locale={filters.locale}
            />
            <BreakdownCard
              title={copy.dashboard.breakdownByType}
              subtitle={copy.dashboard.breakdownByTypeDescription}
              items={summary.breakdowns.products_by_product_type.map((item) => ({
                key: item.product_type,
                label: item.product_type_label,
                count: item.count,
                share_percent: item.share_percent,
                href: buildGridDrilldownHref(filters, { productType: item.product_type })
              }))}
              locale={filters.locale}
            />
          </section>

          <section className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(20rem,0.8fr)]">
            <ScatterCard filters={filters} scatter={scatter} />
            <section className="space-y-4">
              <div className="rounded-[1.5rem] border border-border/80 bg-card/90 p-5 shadow-[0_20px_50px_rgba(15,23,42,0.05)]">
                <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">{copy.dashboard.rankingWidgets}</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{copy.dashboard.rankingTitle}</h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy.dashboard.rankingDescription}</p>
              </div>
              {rankings.widgets.length ? (
                rankings.widgets.map((widget) => (
                  <RankingWidgetCard key={widget.ranking_key} filters={filters} locale={filters.locale} widget={widget} />
                ))
              ) : (
                <section className="rounded-[1.5rem] border border-dashed border-border bg-card/90 p-6">
                  <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">{copy.dashboard.insufficientData}</p>
                  <h3 className="mt-2 text-xl font-semibold tracking-tight text-foreground">{copy.dashboard.noRankingWidgets}</h3>
                  <p className="mt-3 text-sm leading-6 text-muted-foreground">
                    {rankings.insufficiency_note ?? getBroadenScopeHint(filters.locale)}
                  </p>
                </section>
              )}
            </section>
          </section>

          <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(18rem,0.65fr)]">
            <NoteCard
              eyebrow={copy.dashboard.methodology}
              title={copy.dashboard.methodologyTitle}
              body={scatter.methodology_note ?? (filters.locale === "ko"
                ? "지표는 최신 성공 집계 스냅샷을 기준으로 계산되며, 필요한 수치 필드가 없는 상품은 해당 지표에서 제외됩니다."
                : filters.locale === "ja"
                  ? "指標は最新の成功した集計スナップショットから算出され、必要な数値項目が欠けている商品は該当指標から除外されます。"
                  : "Metrics are derived from the latest successful aggregate snapshot and exclude products missing required numeric fields where applicable.")}
            />
            <NoteCard
              eyebrow={copy.dashboard.freshness}
              title={copy.dashboard.freshnessTitle}
              body={formatFreshnessLine(summary.freshness, filters.locale)}
            />
          </section>
        </div>
      </section>
    </main>
  );
}

function MetricCard({
  locale,
  metric
}: {
  locale: string;
  metric: PublicDashboardSummaryResponse["metrics"][number];
}) {
  return (
    <article className="rounded-[1.5rem] border border-border/80 bg-card/95 p-5 shadow-[0_20px_45px_rgba(15,23,42,0.05)]">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">{metric.label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-foreground">{formatMetricValue(metric.value, metric.unit, locale)}</p>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">{metric.scope_note ?? getDefaultMetricScopeNote(locale)}</p>
    </article>
  );
}

function BreakdownCard({
  items,
  locale,
  subtitle,
  title
}: {
  items: Array<PublicDashboardBreakdownItem & { key: string; label: string; href?: string }>;
  locale: string;
  subtitle: string;
  title: string;
}) {
  const copy = getPublicMessages(locale);

  return (
    <section className="rounded-[1.5rem] border border-border/80 bg-card/90 p-5 shadow-[0_20px_50px_rgba(15,23,42,0.05)]">
      <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">{title}</p>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{subtitle}</p>
      <div className="mt-5 space-y-4">
        {items.length ? (
          items.map((item) => (
            <div key={item.key}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-foreground">{item.label}</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {formatCount(item.count, locale)} | {formatSharePercent(item.share_percent, locale)}
                  </p>
                </div>
                {item.href ? (
                  <Link
                    href={item.href}
                    className="inline-flex items-center rounded-full border border-border bg-background px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                  >
                    {copy.dashboard.openInGrid}
                  </Link>
                ) : null}
              </div>
              <div className="mt-2 h-2 rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-[linear-gradient(90deg,_rgb(67_56_202),_rgb(2_132_199))]"
                  style={{ width: `${Math.max(item.share_percent, item.count > 0 ? 6 : 0)}%` }}
                />
              </div>
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">{copy.dashboard.noProductsInScope}</p>
        )}
      </div>
    </section>
  );
}

function RankingWidgetCard({
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
    <section className="rounded-[1.5rem] border border-border/80 bg-card/90 p-5 shadow-[0_20px_50px_rgba(15,23,42,0.05)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">{widget.title}</p>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            {buildRankingCaption(widget, locale)}
          </p>
        </div>
        <ScopeBadge label={formatPublicMessage(copy.dashboard.topComparisons, { count: widget.items.length })} tone="muted" />
      </div>

      <div className="mt-5 space-y-3">
        {widget.items.map((item) => (
          <article key={item.product_id} className="rounded-[1.1rem] border border-border/70 bg-background/75 p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="inline-flex size-7 items-center justify-center rounded-full bg-secondary text-xs font-semibold text-secondary-foreground">
                    {item.rank}
                  </span>
                  <p className="truncate text-sm font-medium text-muted-foreground">{item.bank_name}</p>
                </div>
                <h3 className="mt-3 text-base font-semibold leading-6 tracking-tight text-foreground">{item.product_name}</h3>
              </div>
              <div className="text-right">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">{widget.metric_label}</p>
                <p className="mt-2 text-lg font-semibold tracking-tight text-foreground">
                  {formatMetricValue(item.metric_value, item.metric_unit, locale)}
                </p>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border/70 pt-3 text-sm text-muted-foreground">
              <span>{titleCase(item.product_type)}</span>
              <span>{item.last_changed_at ? `${copy.common.changedOn} ${formatCompactDate(item.last_changed_at, locale)}` : copy.dashboard.noRecentChangeDate}</span>
            </div>
            <div className="mt-3 flex justify-end">
              <Link
                href={buildRankingGridHref(filters, widget.ranking_key, item)}
                className="inline-flex items-center rounded-full border border-border bg-card px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                {copy.dashboard.openInGrid}
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ScatterCard({ filters, scatter }: { filters: DashboardPageFilters; scatter: PublicDashboardScatterResponse }) {
  const copy = getPublicMessages(filters.locale);
  const isGicScope = filters.productTypes.length === 1 && filters.productTypes[0] === "gic";
  const scatterOptions = [
    { value: "gic_rate_vs_minimum_deposit", label: getGicScatterOptionLabel("gic_rate_vs_minimum_deposit", filters.locale) },
    { value: "gic_term_vs_rate", label: getGicScatterOptionLabel("gic_term_vs_rate", filters.locale) }
  ];

  return (
    <section className="rounded-[1.5rem] border border-border/80 bg-card/90 p-5 shadow-[0_20px_50px_rgba(15,23,42,0.05)]">
      <div className="flex flex-col gap-4 border-b border-border/70 pb-5 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">{copy.dashboard.comparativeChart}</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
            {scatter.title ?? copy.dashboard.chartTitleFallback}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            {copy.dashboard.chartDescription}
          </p>
        </div>
        {isGicScope ? (
          <div className="flex flex-wrap gap-2">
            {scatterOptions.map((option) => {
              const href = buildPublicHref("/dashboard", { ...filters, axisPreset: option.value });
              const active = (scatter.chart_key ?? filters.axisPreset) === option.value;

              return (
                <Link
                  key={option.value}
                  href={href}
                  className={cn(
                    "rounded-full border px-3 py-2 text-sm font-medium transition-colors",
                    active ? "border-primary/40 bg-secondary text-secondary-foreground" : "border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  {option.label}
                </Link>
              );
            })}
          </div>
        ) : null}
      </div>

      {scatter.availability_status === "ready" && scatter.x_axis && scatter.y_axis ? (
        <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_18rem]">
          <div className="rounded-[1.25rem] border border-border/70 bg-background/80 p-4">
            <div className="mb-4 flex flex-wrap gap-2 text-xs font-medium text-muted-foreground">
              <ScopeBadge label={`X: ${scatter.x_axis.label}`} tone="muted" />
              <ScopeBadge label={`Y: ${scatter.y_axis.label}`} tone="muted" />
            </div>
            <ScatterPlot filters={filters} locale={filters.locale} scatter={scatter} />
          </div>
          <div className="space-y-3">
            <div className="rounded-[1.1rem] border border-border/70 bg-background/75 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">{copy.dashboard.interpretation}</p>
              <p className="mt-3 text-sm leading-6 text-foreground">{buildScatterGuidance(scatter.chart_key, filters.locale)}</p>
            </div>
            <div className="rounded-[1.1rem] border border-border/70 bg-background/75 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">{copy.dashboard.visiblePoints}</p>
              <div className="mt-3 space-y-3">
                {scatter.points.slice(0, 10).map((point) => (
                  <div key={point.product_id} className="rounded-xl border border-border/70 bg-card px-3 py-3">
                    <p className="text-sm font-medium text-foreground">{point.bank_name}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{point.product_name}</p>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                      <span>{scatter.x_axis?.label}: {formatMetricValue(point.x_value, scatter.x_axis?.unit ?? "", filters.locale)}</span>
                      <span>{scatter.y_axis?.label}: {formatMetricValue(point.y_value, scatter.y_axis?.unit ?? "", filters.locale)}</span>
                    </div>
                    <div className="mt-3">
                      <Link
                        href={buildGridDrilldownHref(filters, { bankCode: point.bank_code, productType: point.product_type })}
                        className="inline-flex items-center rounded-full border border-border bg-background px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                      >
                        {copy.dashboard.openInGrid}
                      </Link>
                    </div>
                  </div>
                ))}
                {scatter.points.length > 10 ? (
                  <p className="text-xs text-muted-foreground">
                    + {formatCount(scatter.points.length - 10, filters.locale)} {copy.dashboard.morePoints}
                  </p>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-5 rounded-[1.25rem] border border-dashed border-border bg-background/80 p-6">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">
            {scatter.availability_status === "scope_selection_required" ? copy.dashboard.selectOneProductType : copy.dashboard.insufficientData}
          </p>
          <h3 className="mt-2 text-xl font-semibold tracking-tight text-foreground">
            {scatter.availability_status === "scope_selection_required"
              ? copy.dashboard.singleTypeOnly
              : copy.dashboard.chartInsufficient}
          </h3>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
            {scatter.insufficiency_note ?? getBroadenScopeHint(filters.locale)}
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Button asChild>
              <Link href={buildPublicHref("/products", filters)}>{copy.dashboard.openProductGrid}</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/dashboard">{copy.dashboard.resetDashboardScope}</Link>
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}

function ScatterPlot({
  filters,
  locale,
  scatter
}: {
  filters: DashboardPageFilters;
  locale: string;
  scatter: PublicDashboardScatterResponse;
}) {
  const copy = getPublicMessages(locale);
  const width = 640;
  const height = 360;
  const padding = { top: 24, right: 24, bottom: 42, left: 56 };
  const xValues = scatter.points.map((point) => point.x_value);
  const yValues = scatter.points.map((point) => point.y_value);
  const xBounds = extendBounds(Math.min(...xValues), Math.max(...xValues));
  const yBounds = extendBounds(Math.min(...yValues), Math.max(...yValues));
  const usableWidth = width - padding.left - padding.right;
  const usableHeight = height - padding.top - padding.bottom;
  const ticks = 5;

  const xPosition = (value: number) => padding.left + ((value - xBounds.min) / (xBounds.max - xBounds.min)) * usableWidth;
  const yPosition = (value: number) => height - padding.bottom - ((value - yBounds.min) / (yBounds.max - yBounds.min)) * usableHeight;

  return (
    <svg className="h-auto w-full" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={scatter.title ?? copy.dashboard.comparativeChart}>
      {Array.from({ length: ticks }).map((_, index) => {
        const xTick = padding.left + (usableWidth / (ticks - 1)) * index;
        const yTick = padding.top + (usableHeight / (ticks - 1)) * index;
        const xValue = xBounds.min + ((xBounds.max - xBounds.min) / (ticks - 1)) * index;
        const yValue = yBounds.max - ((yBounds.max - yBounds.min) / (ticks - 1)) * index;

        return (
          <g key={`tick-${index}`}>
            <line x1={xTick} x2={xTick} y1={padding.top} y2={height - padding.bottom} stroke="rgba(148, 163, 184, 0.22)" strokeDasharray="4 8" />
            <line x1={padding.left} x2={width - padding.right} y1={yTick} y2={yTick} stroke="rgba(148, 163, 184, 0.22)" strokeDasharray="4 8" />
            <text x={xTick} y={height - 12} fill="rgba(91, 101, 120, 1)" fontSize="11" textAnchor="middle">
              {formatMetricValue(xValue, scatter.x_axis?.unit ?? "", locale)}
            </text>
            <text x={20} y={yTick + 4} fill="rgba(91, 101, 120, 1)" fontSize="11" textAnchor="start">
              {formatMetricValue(yValue, scatter.y_axis?.unit ?? "", locale)}
            </text>
          </g>
        );
      })}

      <line x1={padding.left} x2={padding.left} y1={padding.top} y2={height - padding.bottom} stroke="rgba(15, 23, 42, 0.45)" strokeWidth="1.5" />
      <line
        x1={padding.left}
        x2={width - padding.right}
        y1={height - padding.bottom}
        y2={height - padding.bottom}
        stroke="rgba(15, 23, 42, 0.45)"
        strokeWidth="1.5"
      />

      {scatter.points.map((point, index) => {
        const href = buildGridDrilldownHref(filters, { bankCode: point.bank_code, productType: point.product_type });

        return (
          <a key={point.product_id} href={href}>
            <title>{buildScatterPointTitle(point.bank_name, point.product_name, locale)}</title>
            <circle
              className="cursor-pointer"
              cx={xPosition(point.x_value)}
              cy={yPosition(point.y_value)}
              r={7}
              fill={point.highlight_badge_code ? "rgba(2, 132, 199, 0.95)" : pickPointColor(index)}
              stroke="rgba(255,255,255,0.95)"
              strokeWidth="2"
            />
          </a>
        );
      })}
    </svg>
  );
}

function NoteCard({ body, eyebrow, title }: { body: string; eyebrow: string; title: string }) {
  return (
    <section className="rounded-[1.5rem] border border-border/80 bg-card/90 p-5 shadow-[0_20px_50px_rgba(15,23,42,0.05)]">
      <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">{eyebrow}</p>
      <h2 className="mt-2 text-xl font-semibold tracking-tight text-foreground">{title}</h2>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">{body}</p>
    </section>
  );
}

function getDefaultMetricScopeNote(locale: string) {
  if (locale === "ko") {
    return "이 KPI는 현재 공개 범위의 최신 성공 aggregate snapshot을 기준으로 계산됩니다.";
  }
  if (locale === "ja") {
    return "この KPI は、現在の公開スコープに対する最新の成功 aggregate snapshot を基準に計算されます。";
  }
  return "This KPI is computed from the latest successful aggregate snapshot for the current public scope.";
}

function getBroadenScopeHint(locale: string) {
  if (locale === "ko") {
    return "Product Grid에서 범위를 조금 더 넓힌 뒤 다시 돌아오면 비교용 위젯과 차트를 더 쉽게 확인할 수 있습니다.";
  }
  if (locale === "ja") {
    return "Product Grid でスコープを少し広げてから戻ると、比較ウィジェットやチャートを見つけやすくなります。";
  }
  return "Try broadening the current scope from the Product Grid sibling route and return here for richer comparisons.";
}

function getGicScatterOptionLabel(axisPreset: string, locale: string) {
  if (axisPreset === "gic_term_vs_rate") {
    if (locale === "ko") {
      return "기간 대비 금리";
    }
    if (locale === "ja") {
      return "期間と金利";
    }
    return "Term vs rate";
  }

  if (locale === "ko") {
    return "금리 대비 예치금";
  }
  if (locale === "ja") {
    return "金利と預入額";
  }
  return "Rate vs deposit";
}

function ScopeBadge({ label, tone }: { label: string; tone: "info" | "muted" | "primary" }) {
  return (
    <span
      className={cn(
        "rounded-full border px-3 py-1 text-xs font-semibold",
        tone === "primary" && "border-primary/15 bg-secondary text-secondary-foreground",
        tone === "info" && "border-info/15 bg-info-soft text-info",
        tone === "muted" && "border-border bg-background text-muted-foreground"
      )}
    >
      {label}
    </span>
  );
}

function buildScopeSummary(filters: DashboardPageFilters, filterOptions: PublicFiltersResponse) {
  const parts: string[] = [];
  if (filters.bankCodes.length) {
    parts.push(
      filters.locale === "ko"
        ? `${filters.bankCodes.length}개 은행 필터가 적용 중입니다.`
        : filters.locale === "ja"
          ? `${filters.bankCodes.length} 件の銀行フィルターが適用中です。`
          : `${filters.bankCodes.length} bank filter${filters.bankCodes.length > 1 ? "s" : ""} active.`
    );
  }
  if (filters.productTypes.length) {
    parts.push(
      filters.locale === "ko"
        ? `${filters.productTypes.length}개 상품 유형 필터가 적용 중입니다.`
        : filters.locale === "ja"
          ? `${filters.productTypes.length} 件の商品タイプフィルターが適用中です。`
          : `${filters.productTypes.length} product type filter${filters.productTypes.length > 1 ? "s" : ""} active.`
    );
  }
  if (filters.targetCustomerTags.length) {
    parts.push(
      filters.locale === "ko"
        ? `${filters.targetCustomerTags.length}개 대상 태그 필터가 적용 중입니다.`
        : filters.locale === "ja"
          ? `${filters.targetCustomerTags.length} 件の対象タグフィルターが適用中です。`
          : `${filters.targetCustomerTags.length} target-tag filter${filters.targetCustomerTags.length > 1 ? "s" : ""} active.`
    );
  }
  if (filters.feeBucket || filters.minimumBalanceBucket || filters.minimumDepositBucket || filters.termBucket) {
    parts.push(
      filters.locale === "ko"
        ? "버킷 필터가 비교 범위를 더 좁히고 있습니다."
        : filters.locale === "ja"
          ? "バケットフィルターが比較スコープをさらに絞り込んでいます。"
          : "Bucket filters are narrowing the comparison scope."
    );
  }

  if (!parts.length) {
    if (filters.locale === "ko") {
      return `${filterOptions.banks.length}개 은행 기준의 전체 공개 범위를 그대로 보고 있습니다.`;
    }
    if (filters.locale === "ja") {
      return `${filterOptions.banks.length} 銀行基準の公開ベースライン全体をそのまま表示しています。`;
    }
    return `All banks and product types remain visible from a ${filterOptions.banks.length}-bank public baseline.`;
  }
  return parts.join(" ");
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
      href: buildPublicHref("/dashboard", { ...filters, productTypes: filters.productTypes.filter((value) => value !== productType) }),
      label: findLabel(filterOptions.product_types, productType),
      value: productType
    });
  }
  for (const tag of filters.targetCustomerTags) {
    chips.push({
      group: "target_customer_tag",
      href: buildPublicHref("/dashboard", {
        ...filters,
        targetCustomerTags: filters.targetCustomerTags.filter((value) => value !== tag)
      }),
      label: findLabel(filterOptions.target_customer_tags, tag),
      value: tag
    });
  }

  addSingleChip(
    chips,
    "fee_bucket",
    filters.feeBucket,
    filterOptions.fee_buckets,
    buildPublicHref("/dashboard", { ...filters, feeBucket: "" })
  );
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
  addSingleChip(
    chips,
    "term_bucket",
    filters.termBucket,
    filterOptions.term_buckets,
    buildPublicHref("/dashboard", { ...filters, termBucket: "" })
  );

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

function findLabel(options: Array<{ label: string; value: string }>, value: string) {
  return options.find((option) => option.value === value)?.label ?? value;
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
    return new Intl.NumberFormat(normalizeLocale(locale), {
      style: "currency",
      currency: "CAD",
      maximumFractionDigits: Number.isInteger(value) ? 0 : 2
    }).format(value);
  }
  if (unit === "days") {
    const rounded = value < 10 ? value.toFixed(1).replace(/\.0$/, "") : Math.round(value).toString();
    if (locale === "ko") {
      return `${rounded}일`;
    }
    if (locale === "ja") {
      return `${rounded}日`;
    }
    return `${rounded} day${rounded === "1" ? "" : "s"}`;
  }
  return formatCount(value, locale);
}

function formatCount(value: number, locale: string) {
  return new Intl.NumberFormat(normalizeLocale(locale), {
    maximumFractionDigits: Number.isInteger(value) ? 0 : 2
  }).format(value);
}

function formatSharePercent(value: number, locale: string) {
  return new Intl.NumberFormat(normalizeLocale(locale), {
    style: "percent",
    minimumFractionDigits: value >= 10 ? 0 : 1,
    maximumFractionDigits: value >= 10 ? 0 : 1
  }).format(value / 100);
}

function formatCompactDate(value: string | null, locale: string) {
  const copy = getPublicMessages(locale);
  if (!value) {
    return copy.common.noDate;
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

function formatFreshnessLine(freshness: PublicDashboardSummaryResponse["freshness"], locale: string) {
  const copy = getPublicMessages(locale);
  if (!freshness.refreshed_at) {
    return copy.common.noSuccessfulSnapshot;
  }
  const refreshedLabel = formatLongDateTime(freshness.refreshed_at, locale);
  if (freshness.status === "stale") {
    if (locale === "ko") {
      return `스냅샷이 stale 상태입니다. 마지막 성공 refresh 시각은 ${refreshedLabel} 입니다.`;
    }
    if (locale === "ja") {
      return `スナップショットは stale 状態です。最後に成功した refresh 時刻は ${refreshedLabel} です。`;
    }
    return `Snapshot is stale. Last successful refresh was ${refreshedLabel}.`;
  }

  if (locale === "ko") {
    return `스냅샷이 ${refreshedLabel} 기준으로 refresh 되었습니다.`;
  }
  if (locale === "ja") {
    return `スナップショットは ${refreshedLabel} 時点で refresh されています。`;
  }
  return `Snapshot refreshed ${refreshedLabel}.`;
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

function extendBounds(minimum: number, maximum: number) {
  if (minimum === maximum) {
    const padding = minimum === 0 ? 1 : Math.abs(minimum) * 0.25;
    return { min: minimum - padding, max: maximum + padding };
  }
  const range = maximum - minimum;
  const padding = range * 0.1;
  return { min: minimum - padding, max: maximum + padding };
}

function pickPointColor(index: number) {
  const colors = ["rgba(67, 56, 202, 0.92)", "rgba(15, 118, 110, 0.92)", "rgba(180, 83, 9, 0.92)", "rgba(190, 24, 93, 0.92)"];
  return colors[index % colors.length];
}

function buildScatterGuidance(chartKey: string | null, locale: string) {
  switch (chartKey) {
    case "chequing_fee_vs_minimum_balance":
      if (locale === "ko") {
        return "보통 왼쪽 아래 구간은 월 수수료와 진입 장벽이 낮다는 뜻이지만, 면제 조건과 거래 규칙은 카드 본문까지 함께 봐야 합니다.";
      }
      if (locale === "ja") {
        return "一般に左下の領域は月額手数料と参入障壁が低いことを示しますが、免除条件や取引ルールはカード本文まで合わせて確認する必要があります。";
      }
      return "Lower-left points usually indicate easier entry with lower monthly cost, but fee waivers and transaction rules still need the product card view for full context.";
    case "savings_rate_vs_minimum_balance":
      if (locale === "ko") {
        return "보통 왼쪽 위 구간은 더 낮은 최소 잔액으로 더 강한 표시 금리를 뜻할 수 있지만, 우대 조건은 여전히 함께 확인해야 합니다.";
      }
      if (locale === "ja") {
        return "一般に左上の領域は、より低い最低残高でより高い表示金利を意味し得ますが、優遇条件は引き続き確認が必要です。";
      }
      return "Upper-left territory can indicate stronger displayed rate without requiring as much minimum balance, though promotional conditions may still matter.";
    case "gic_rate_vs_minimum_deposit":
      if (locale === "ko") {
        return "보통 왼쪽 위 구간은 더 낮은 예치금으로 더 강한 표시 금리를 뜻해, GIC의 1차 비교에서 가장 읽기 쉬운 trade-off가 됩니다.";
      }
      if (locale === "ja") {
        return "一般に左上の領域は、より低い預入額でより高い表示金利を示し、GIC の一次比較で最も読み取りやすい trade-off になります。";
      }
      return "Upper-left territory can indicate stronger displayed rate at a lower entry deposit, which is often the clearest first-pass GIC trade-off.";
    case "gic_term_vs_rate":
      if (locale === "ko") {
        return "기간이 길다고 자동으로 더 좋은 상품은 아니므로, 이 뷰는 단일 최적 구간 탐색보다 기간 대비 금리 지도를 읽는 용도로 사용해야 합니다.";
      }
      if (locale === "ja") {
        return "期間が長いことが自動的に有利とは限らないため、このビューは単一の最良象限を探すより、期間と金利の trade-off を読む用途に向いています。";
      }
      return "Longer term does not automatically mean better value, so use this view as a term-versus-rate trade-off map rather than a single best quadrant search.";
    default:
      if (locale === "ko") {
        return "같은 의미 기준의 비교 차트를 보려면 상품 유형 하나를 선택하세요.";
      }
      if (locale === "ja") {
        return "同じ意味基準の比較チャートを開くには、商品タイプを 1 つ選択してください。";
      }
      return "Choose a single product type to unlock a same-meaning comparative chart.";
  }
}

function buildRankingCaption(widget: PublicDashboardRankingsResponse["widgets"][number], locale: string) {
  const copy = getPublicMessages(locale);
  if (!widget.window_days) {
    return `${copy.dashboard.rankedBy} ${widget.metric_label}.`;
  }
  return `${copy.dashboard.rankedBy} ${widget.metric_label} ${formatPublicMessage(copy.dashboard.trailingDays, { days: widget.window_days })}`;
}

function buildScatterPointTitle(bankName: string, productName: string, locale: string) {
  if (locale === "ko") {
    return `Product Grid에서 ${bankName} ${productName} 열기`;
  }
  if (locale === "ja") {
    return `Product Grid で ${bankName} ${productName} を開く`;
  }
  return `Open ${bankName} ${productName} in the Product Grid`;
}

function titleCase(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function buildRankingGridHref(
  filters: DashboardPageFilters,
  rankingKey: string,
  item: PublicDashboardRankingsResponse["widgets"][number]["items"][number]
) {
  const sort = getGridSortForRanking(rankingKey);
  return buildGridDrilldownHref(filters, {
    bankCode: item.bank_code,
    productType: item.product_type,
    sortBy: sort.sortBy,
    sortOrder: sort.sortOrder
  });
}

function buildGridDrilldownHref(
  filters: DashboardPageFilters,
  overrides: {
    bankCode?: string;
    productType?: string;
    sortBy?: string;
    sortOrder?: "asc" | "desc";
  }
) {
  const nextProductType = overrides.productType ?? (filters.productTypes.length === 1 ? filters.productTypes[0] : "");
  const nextState = normalizeGridBucketsForProductType(
    {
      ...filters,
      bankCodes: overrides.bankCode ? [overrides.bankCode] : filters.bankCodes,
      productTypes: overrides.productType ? [overrides.productType] : filters.productTypes,
      sortBy: overrides.sortBy ?? "default",
      sortOrder: overrides.sortOrder ?? "desc",
      page: 1
    },
    nextProductType
  );

  return buildPublicHref("/products", nextState);
}

function normalizeGridBucketsForProductType<
  T extends {
    minimumBalanceBucket: string;
    minimumDepositBucket: string;
    termBucket: string;
  }
>(state: T, productType: string) {
  if (productType === "gic") {
    return {
      ...state,
      minimumBalanceBucket: ""
    };
  }

  if (productType === "chequing" || productType === "savings") {
    return {
      ...state,
      minimumDepositBucket: "",
      termBucket: ""
    };
  }

  return state;
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
