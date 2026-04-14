import Link from "next/link";

import { Button } from "@/components/ui/button";
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

const GIC_SCATTER_OPTIONS = [
  { value: "gic_rate_vs_minimum_deposit", label: "Rate vs deposit" },
  { value: "gic_term_vs_rate", label: "Term vs rate" }
];

export function DashboardSurface({ apiUnavailable, filterOptions, filters, rankings, scatter, summary }: DashboardSurfaceProps) {
  if (apiUnavailable || !filterOptions || !rankings || !scatter || !summary) {
    return (
      <main className="mx-auto flex w-full max-w-6xl px-4 py-12 md:px-6 md:py-16">
        <section className="w-full rounded-[2rem] border border-destructive/20 bg-card/95 p-8 shadow-[0_24px_60px_rgba(15,23,42,0.08)] md:p-10">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-destructive">Public API unavailable</p>
          <h1 className="mt-4 max-w-2xl text-4xl font-semibold tracking-tight text-foreground">
            Insight Dashboard could not load because the public aggregate API is not reachable.
          </h1>
          <p className="mt-4 max-w-3xl text-base leading-7 text-muted-foreground">
            Start the FastAPI service and refresh this page. The public dashboard depends on
            `GET /api/public/dashboard-summary`, `GET /api/public/dashboard-rankings`, `GET /api/public/dashboard-scatter`,
            and `GET /api/public/filters`.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild>
              <Link href="/dashboard">Retry dashboard</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/products">Open product grid</Link>
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
  const overviewLabel = selectedProductType ? titleCase(selectedProductType) : "Mixed market";
  const scopeSummary = buildScopeSummary(filters, filterOptions);
  const activeChips = buildActiveChips(filters, filterOptions);
  const productGridHref = buildPublicHref("/products", filters);
  const clearHref = "/dashboard";

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 md:px-6 md:py-10">
      <section className="rounded-[2rem] border border-border/80 bg-card/85 p-6 shadow-[0_30px_80px_rgba(15,23,42,0.06)] md:p-8">
        <div className="flex flex-col gap-8">
          <header className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(18rem,0.8fr)] lg:items-end">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-primary">WBS 5.10 Insight Dashboard</p>
              <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight text-foreground md:text-5xl">
                Read the Canada deposit market at a glance before diving back into product-level detail.
              </h1>
              <p className="mt-4 max-w-3xl text-base leading-7 text-muted-foreground">
                The dashboard uses the same public filter vocabulary as the Product Grid, but reframes the current scope
                through KPI cards, composition views, ranking widgets, and a comparative chart when one product type is in focus.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Button asChild>
                  <Link href={productGridHref}>Open product grid with this scope</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href={clearHref}>Clear scope</Link>
                </Button>
              </div>
            </div>
            <div className="rounded-[1.5rem] border border-border/70 bg-background/80 p-5">
              <p className="text-sm font-medium text-foreground">Current scope</p>
              <p className="mt-2 text-3xl font-semibold tracking-tight text-foreground">{formatCount(totalProducts, filters.locale)}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                active products across {formatCount(banksInScope, filters.locale)} banks
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <ScopeBadge label={overviewLabel} tone="primary" />
                {highestRate?.value != null ? <ScopeBadge label={`Peak rate ${formatMetricValue(highestRate.value, highestRate.unit, filters.locale)}`} tone="info" /> : null}
              </div>
              <p className="mt-4 text-sm text-muted-foreground">{formatFreshnessLine(summary.freshness, filters.locale)}</p>
            </div>
          </header>

          <section className="rounded-[1.75rem] border border-border/80 bg-background/65 p-5">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-3">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">Scope summary</p>
                  <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Dashboarding the current public filter scope</h2>
                  <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                    {scopeSummary} Adjust filter selections on the Product Grid sibling route and return here to read the same scope as a market snapshot.
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
                  <p className="text-sm text-muted-foreground">No active filters. You are reading the full Canada public dashboard scope.</p>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Button asChild variant="outline">
                  <Link href={productGridHref}>Adjust scope on product grid</Link>
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
              title="Products by bank"
              subtitle="Composition of active products in the current scope."
              items={summary.breakdowns.products_by_bank.map((item) => ({
                key: item.bank_code,
                label: item.bank_name,
                count: item.count,
                share_percent: item.share_percent
              }))}
              locale={filters.locale}
            />
            <BreakdownCard
              title="Products by product type"
              subtitle="Mix of chequing, savings, and GIC exposure after filtering."
              items={summary.breakdowns.products_by_product_type.map((item) => ({
                key: item.product_type,
                label: item.product_type_label,
                count: item.count,
                share_percent: item.share_percent
              }))}
              locale={filters.locale}
            />
          </section>

          <section className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(20rem,0.8fr)]">
            <ScatterCard filters={filters} scatter={scatter} />
            <section className="space-y-4">
              <div className="rounded-[1.5rem] border border-border/80 bg-card/90 p-5 shadow-[0_20px_50px_rgba(15,23,42,0.05)]">
                <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">Ranking widgets</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Top comparisons for this scope</h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Widget order follows the approved product-type emphasis rules and only renders when enough eligible products remain.
                </p>
              </div>
              {rankings.widgets.length ? (
                rankings.widgets.map((widget) => <RankingWidgetCard key={widget.ranking_key} locale={filters.locale} widget={widget} />)
              ) : (
                <section className="rounded-[1.5rem] border border-dashed border-border bg-card/90 p-6">
                  <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">Insufficient data</p>
                  <h3 className="mt-2 text-xl font-semibold tracking-tight text-foreground">No ranking widgets are eligible for the current scope.</h3>
                  <p className="mt-3 text-sm leading-6 text-muted-foreground">
                    {rankings.insufficiency_note ?? "Try broadening the current scope from the Product Grid sibling route."}
                  </p>
                </section>
              )}
            </section>
          </section>

          <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(18rem,0.65fr)]">
            <NoteCard
              eyebrow="Methodology"
              title="How to read this dashboard"
              body={scatter.methodology_note ?? "Metrics are derived from the latest successful aggregate snapshot and exclude products missing required numeric fields where applicable."}
            />
            <NoteCard
              eyebrow="Freshness"
              title="Snapshot handling"
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
      <p className="mt-3 text-sm leading-6 text-muted-foreground">{metric.scope_note ?? "Computed from the latest successful public aggregate snapshot."}</p>
    </article>
  );
}

function BreakdownCard({
  items,
  locale,
  subtitle,
  title
}: {
  items: Array<PublicDashboardBreakdownItem & { key: string; label: string }>;
  locale: string;
  subtitle: string;
  title: string;
}) {
  return (
    <section className="rounded-[1.5rem] border border-border/80 bg-card/90 p-5 shadow-[0_20px_50px_rgba(15,23,42,0.05)]">
      <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">{title}</p>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{subtitle}</p>
      <div className="mt-5 space-y-4">
        {items.length ? (
          items.map((item) => (
            <div key={item.key}>
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-foreground">{item.label}</p>
                <p className="text-sm text-muted-foreground">
                  {formatCount(item.count, locale)} | {formatSharePercent(item.share_percent, locale)}
                </p>
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
          <p className="text-sm text-muted-foreground">No products are available in the current scope.</p>
        )}
      </div>
    </section>
  );
}

function RankingWidgetCard({
  locale,
  widget
}: {
  locale: string;
  widget: PublicDashboardRankingsResponse["widgets"][number];
}) {
  return (
    <section className="rounded-[1.5rem] border border-border/80 bg-card/90 p-5 shadow-[0_20px_50px_rgba(15,23,42,0.05)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">{widget.title}</p>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            Ranked by {widget.metric_label.toLowerCase()}
            {widget.window_days ? ` over the trailing ${widget.window_days} days.` : "."}
          </p>
        </div>
        <ScopeBadge label={`Top ${widget.items.length}`} tone="muted" />
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
              <span>{item.last_changed_at ? `Changed ${formatCompactDate(item.last_changed_at, locale)}` : "No recent change date"}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function ScatterCard({ filters, scatter }: { filters: DashboardPageFilters; scatter: PublicDashboardScatterResponse }) {
  const isGicScope = filters.productTypes.length === 1 && filters.productTypes[0] === "gic";

  return (
    <section className="rounded-[1.5rem] border border-border/80 bg-card/90 p-5 shadow-[0_20px_50px_rgba(15,23,42,0.05)]">
      <div className="flex flex-col gap-4 border-b border-border/70 pb-5 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">Comparative chart</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
            {scatter.title ?? "Comparative chart unlocks when one product type is in focus"}
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            When exactly one product type is selected, the dashboard can compare trade-offs within that meaningfully similar scope.
          </p>
        </div>
        {isGicScope ? (
          <div className="flex flex-wrap gap-2">
            {GIC_SCATTER_OPTIONS.map((option) => {
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
            <ScatterPlot locale={filters.locale} scatter={scatter} />
          </div>
          <div className="space-y-3">
            <div className="rounded-[1.1rem] border border-border/70 bg-background/75 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">Interpretation</p>
              <p className="mt-3 text-sm leading-6 text-foreground">{buildScatterGuidance(scatter.chart_key)}</p>
            </div>
            <div className="rounded-[1.1rem] border border-border/70 bg-background/75 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">Visible points</p>
              <div className="mt-3 space-y-3">
                {scatter.points.slice(0, 10).map((point) => (
                  <div key={point.product_id} className="rounded-xl border border-border/70 bg-card px-3 py-3">
                    <p className="text-sm font-medium text-foreground">{point.bank_name}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{point.product_name}</p>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                      <span>{scatter.x_axis?.label}: {formatMetricValue(point.x_value, scatter.x_axis?.unit ?? "", filters.locale)}</span>
                      <span>{scatter.y_axis?.label}: {formatMetricValue(point.y_value, scatter.y_axis?.unit ?? "", filters.locale)}</span>
                    </div>
                  </div>
                ))}
                {scatter.points.length > 10 ? (
                  <p className="text-xs text-muted-foreground">+ {formatCount(scatter.points.length - 10, filters.locale)} more points in the chart.</p>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-5 rounded-[1.25rem] border border-dashed border-border bg-background/80 p-6">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">
            {scatter.availability_status === "scope_selection_required" ? "Select one product type" : "Insufficient data"}
          </p>
          <h3 className="mt-2 text-xl font-semibold tracking-tight text-foreground">
            {scatter.availability_status === "scope_selection_required"
              ? "Comparative plotting is reserved for single-type scope."
              : "There are not enough eligible products to render this chart."}
          </h3>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">
            {scatter.insufficiency_note ?? "Use the Product Grid sibling route to narrow the scope and come back here for a chart-level view."}
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Button asChild>
              <Link href={buildPublicHref("/products", filters)}>Open product grid</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/dashboard">Reset dashboard scope</Link>
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}

function ScatterPlot({ locale, scatter }: { locale: string; scatter: PublicDashboardScatterResponse }) {
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
    <svg className="h-auto w-full" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={scatter.title ?? "Comparative chart"}>
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

      {scatter.points.map((point, index) => (
        <g key={point.product_id}>
          <circle
            cx={xPosition(point.x_value)}
            cy={yPosition(point.y_value)}
            r={7}
            fill={point.highlight_badge_code ? "rgba(2, 132, 199, 0.95)" : pickPointColor(index)}
            stroke="rgba(255,255,255,0.95)"
            strokeWidth="2"
          />
        </g>
      ))}
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
    parts.push(`${filters.bankCodes.length} bank filter${filters.bankCodes.length > 1 ? "s" : ""} active.`);
  }
  if (filters.productTypes.length) {
    parts.push(`${filters.productTypes.length} product type filter${filters.productTypes.length > 1 ? "s" : ""} active.`);
  }
  if (filters.targetCustomerTags.length) {
    parts.push(`${filters.targetCustomerTags.length} target-tag filter${filters.targetCustomerTags.length > 1 ? "s" : ""} active.`);
  }
  if (filters.feeBucket || filters.minimumBalanceBucket || filters.minimumDepositBucket || filters.termBucket) {
    parts.push("Bucket filters are narrowing the comparison scope.");
  }

  if (!parts.length) {
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
  if (value === null || Number.isNaN(value)) {
    return "Not disclosed";
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

function formatFreshnessLine(freshness: PublicDashboardSummaryResponse["freshness"], locale: string) {
  if (!freshness.refreshed_at) {
    return "No successful aggregate snapshot is available yet.";
  }
  const refreshedLabel = formatLongDateTime(freshness.refreshed_at, locale);
  return freshness.status === "stale"
    ? `Snapshot is stale. Last successful refresh was ${refreshedLabel}.`
    : `Snapshot refreshed ${refreshedLabel}.`;
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

function buildScatterGuidance(chartKey: string | null) {
  switch (chartKey) {
    case "chequing_fee_vs_minimum_balance":
      return "Lower-left points usually indicate easier entry with lower monthly cost, but fee waivers and transaction rules still need the product card view for full context.";
    case "savings_rate_vs_minimum_balance":
      return "Upper-left territory can indicate stronger displayed rate without requiring as much minimum balance, though promotional conditions may still matter.";
    case "gic_rate_vs_minimum_deposit":
      return "Upper-left territory can indicate stronger displayed rate at a lower entry deposit, which is often the clearest first-pass GIC trade-off.";
    case "gic_term_vs_rate":
      return "Longer term does not automatically mean better value, so use this view as a term-versus-rate trade-off map rather than a single best quadrant search.";
    default:
      return "Choose a single product type to unlock a same-meaning comparative chart.";
  }
}

function titleCase(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
