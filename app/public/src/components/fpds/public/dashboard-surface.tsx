import { ArrowRight, ArrowUpRight, Check, ExternalLink, FilterX, Landmark, PiggyBank, RefreshCw } from "lucide-react";
import Link from "next/link";

import { BankLogo } from "@/components/fpds/public/bank-logo";
import { PublicFreshness, formatSnapshotDate } from "@/components/fpds/public/public-freshness";
import { PublicScatterChart } from "@/components/fpds/public/public-dashboard-charts";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card";
import { getIntlLocale, getPublicDesignCopy, getPublicMessages } from "@/lib/public-locale";
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
  const designCopy = getPublicDesignCopy(filters.locale);
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
  const bankComposition = buildBankComposition(filters, summary);
  const productTypeLinks = buildProductTypeDashboardLinks(filters, summary);
  const depositComparisonScope = summary.breakdowns.products_by_product_type.every((item) => ["chequing", "gic", "savings"].includes(item.product_type));
  const decisionWidgets = depositComparisonScope
    ? rankings.widgets.filter((widget) => widget.ranking_key !== "recently_changed_30d")
    : [];
  const hasScatter = Boolean(scatter?.points.length && scatter.x_axis && scatter.y_axis);
  const snapshotDate = formatSnapshotDate(summary.freshness.refreshed_at, copy.common.noDate);

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6 md:py-9">
      <div className="flex flex-col gap-8 md:gap-12">
        <section className="relative overflow-hidden border-y border-foreground/15 py-8 md:py-12">
          <div className="ledger-rule pointer-events-none absolute inset-y-0 right-0 hidden w-[42%] opacity-35 lg:block" aria-hidden="true" />
          <div className="relative grid gap-10 lg:grid-cols-[minmax(0,1.05fr)_minmax(24rem,0.72fr)] lg:items-center">
            <div className="max-w-3xl">
              <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.16em] text-verification">{designCopy.homeKicker}</p>
              <h1 className="text-balance mt-5 max-w-4xl font-display text-[clamp(2.4rem,7vw,6.4rem)] font-semibold leading-[1.02] tracking-[-0.055em] text-foreground md:leading-[0.94] md:tracking-[-0.065em]">
                {designCopy.homeTitle}
              </h1>
              <p className="mt-6 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg md:leading-8">{designCopy.homeBody}</p>
              <div className="mt-7 flex flex-wrap gap-3">
                <Button asChild size="lg" className="min-h-12 rounded-full px-5">
                <Link href={productsHref}>
                  <PiggyBank className="size-4" aria-hidden="true" />
                  {copy.nav.products}
                </Link>
              </Button>
                <Button asChild size="lg" variant="outline" className="min-h-12 rounded-full border-foreground/20 bg-transparent px-5">
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
            <SnapshotLedger
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

        <section aria-labelledby="coverage-title">
          <div className="mb-5 flex items-end justify-between gap-4 border-b border-foreground/15 pb-4">
            <div>
              <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">{designCopy.coverage}</p>
              <h2 id="coverage-title" className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-foreground md:text-3xl">{copy.dashboard.composition}</h2>
            </div>
            <span className="hidden font-mono text-xs text-muted-foreground sm:block">{designCopy.asOf} {snapshotDate}</span>
          </div>
          <div className="grid divide-y divide-border border-y border-border md:grid-cols-2 md:divide-x md:divide-y-0">
            <CoverageEntry href={productsHref} icon={PiggyBank} label={copy.nav.products} text={designCopy.depositCoverage} tone="deposit" />
            <CoverageEntry href={loansHref} icon={Landmark} label={copy.nav.loan} text={designCopy.loanCoverage} tone="loan" />
          </div>
        </section>

        <section className="grid gap-8 lg:grid-cols-[minmax(0,1.15fr)_minmax(20rem,0.85fr)] lg:gap-0">
          <div className="space-y-4 lg:pr-8">
            {decisionWidgets.length ? (
              decisionWidgets.map((widget) => <RankingCards key={widget.ranking_key} filters={filters} locale={filters.locale} productsHref={productsHref} widget={widget} />)
            ) : (
              <EmptyPanel text={rankings.insufficiency_note ?? copy.dashboard.noRankingWidgets} />
            )}
          </div>

          <div className="border-t border-foreground/15 pt-6 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0">
            <div>
              <h2 className="text-xl font-semibold tracking-[-0.02em]">{copy.dashboard.productsByBank}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{copy.dashboard.compositionSubtitle}</p>
            </div>
            <div className="mt-5 space-y-4">
              {bankComposition.length ? <CoverageBars items={bankComposition} /> : <EmptyPanel text={copy.dashboard.noRankingWidgets} />}
            </div>
          </div>
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

function SnapshotLedger({
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
  const steps = [designCopy.officialRecord, designCopy.reviewedRecord, designCopy.publicSnapshot];
  return (
    <aside className="relative min-w-0 border border-foreground/20 bg-card/85 p-5 shadow-[8px_8px_0_rgba(28,39,35,0.06)] backdrop-blur-sm md:p-6 md:shadow-[10px_10px_0_rgba(28,39,35,0.06)]" aria-label={designCopy.recordPath}>
      <div className="flex flex-col items-start gap-3 border-b border-border pb-4 sm:flex-row sm:justify-between">
        <div>
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">{designCopy.publicSnapshot}</p>
          <p className="mt-2 font-mono text-xs text-foreground">{date}</p>
        </div>
        <PublicFreshness compact freshness={freshness} locale={locale} />
      </div>
      <div className="grid grid-cols-2 divide-x divide-border border-b border-border">
        <div className="py-5 pr-4">
          <p className="font-display text-4xl font-semibold tracking-[-0.05em] tabular-nums">{products}</p>
          <p className="mt-1 text-xs text-muted-foreground">{copy.dashboard.visibleProducts}</p>
        </div>
        <div className="py-5 pl-4">
          <p className="font-display text-4xl font-semibold tracking-[-0.05em] tabular-nums">{banks}</p>
          <p className="mt-1 text-xs text-muted-foreground">{copy.dashboard.banksInScope}</p>
        </div>
      </div>
      <ol className="relative mt-5 grid gap-4 before:absolute before:bottom-2 before:left-[0.6875rem] before:top-2 before:w-px before:bg-verification/25">
        {steps.map((step, index) => (
          <li className="relative flex items-center gap-3 text-sm" key={step}>
            <span className="relative z-10 grid size-[1.375rem] shrink-0 place-items-center rounded-full border border-verification/25 bg-verification-soft text-verification">
              <Check className="size-3" aria-hidden="true" />
            </span>
            <span className="font-medium text-foreground">{step}</span>
            <span className="ml-auto font-mono text-[10px] text-muted-foreground">0{index + 1}</span>
          </li>
        ))}
      </ol>
      <p className="mt-5 border-t border-border pt-4 text-xs leading-5 text-muted-foreground">{designCopy.evidenceBoundary}</p>
    </aside>
  );
}

function CoverageEntry({
  href,
  icon: Icon,
  label,
  text,
  tone,
}: {
  href: string;
  icon: typeof PiggyBank;
  label: string;
  text: string;
  tone: "deposit" | "loan";
}) {
  return (
    <Link className="group flex min-h-28 items-center gap-4 px-1 py-5 transition-colors hover:bg-card/60 md:px-5" href={href}>
      <span className={`grid size-11 shrink-0 place-items-center rounded-full ${tone === "deposit" ? "bg-verification-soft text-deposit" : "bg-accent text-loan"}`}>
        <Icon className="size-5" aria-hidden="true" />
      </span>
      <span className="min-w-0">
        <span className="block text-lg font-semibold text-foreground">{label}</span>
        <span className="mt-1 block text-sm text-muted-foreground">{text}</span>
      </span>
      <ArrowRight className="ml-auto size-5 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-1 group-hover:text-foreground" aria-hidden="true" />
    </Link>
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
    <section className="overflow-hidden border-y border-foreground/15 bg-card/65" aria-labelledby={`${widget.ranking_key}-title`}>
      <div className="flex flex-col gap-3 border-b border-border px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-verification">{widget.metric_label}</p>
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
          <div className="grid gap-3 px-4 py-4 sm:grid-cols-[auto_auto_minmax(0,1fr)_auto] sm:items-center" key={item.product_id}>
            <span className="w-6 text-left text-sm font-semibold text-muted-foreground tabular-nums sm:text-right">
              {item.rank}
            </span>
            <BankLogo bankCode={item.bank_code} bankName={item.bank_name} size="sm" />
            <div className="min-w-0">
              <Link className="inline-flex min-h-11 items-center break-words text-sm font-semibold text-foreground hover:text-primary" href={buildProductDetailHref(filters, item.product_id)}>
                {item.product_name}
              </Link>
              <p className="mt-0.5 truncate text-xs text-muted-foreground">{item.bank_name}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2 sm:justify-end">
              <span className="border-b-2 border-maple px-2 py-1 text-base font-semibold text-foreground tabular-nums">
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
        <Link className="group grid min-h-11 content-center gap-1.5" href={item.href} key={item.key}>
          <span className="flex items-center justify-between gap-3 text-sm">
            <span className="truncate font-medium text-foreground group-hover:text-primary">{item.label}</span>
            <span className="shrink-0 text-xs font-semibold text-muted-foreground tabular-nums">{item.count}</span>
          </span>
          <span className="h-1.5 overflow-hidden bg-muted">
            <span className="block h-full bg-verification/70 transition-colors group-hover:bg-verification" style={{ width: `${Math.max(4, Math.min(100, item.share_percent))}%` }} />
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
