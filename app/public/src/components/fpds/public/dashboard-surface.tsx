import { ProductTopFive } from "@/components/fpds/public/product-top-five";
import { DepositTopFive } from "@/components/fpds/public/deposit-top-five";
import { getComparablePublicRate } from "@/lib/public-rate";
import { RefreshCw } from "lucide-react";
import Link from "next/link";

import { PublicScatterChart } from "@/components/fpds/public/public-dashboard-charts";
import { PublicInformationNotice } from "@/components/fpds/public/public-information-notice";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card";
import { getPublicMessages } from "@/lib/public-locale";
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
  const productsHref = buildPublicHref("/products", { ...filters, page: 1 });
  const loansHref = buildPublicHref("/loans", { ...filters, page: 1 });

  if (apiUnavailable || !summary) {
    return (
      <Card className="border-destructive/25">
        <CardHeader>
          <h2 className="text-lg font-semibold">{copy.dashboard.apiUnavailableTitle}</h2>
          <CardDescription>{copy.dashboard.apiUnavailableBody}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button asChild>
            <Link href={buildPublicHref("/", filters)}>
              <RefreshCw className="size-4" aria-hidden="true" />
              {copy.dashboard.retryDashboard}
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href={productsHref}>{copy.dashboard.openProducts}</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  const activeChips = buildScopeChips(filters, summary);
  const rankedLoans = (loanProducts?.items ?? []).filter((product) => getComparablePublicRate(product) !== null).slice(0, 5);
  const hasScatter = Boolean(scatter?.points.length && scatter.x_axis && scatter.y_axis);

  return (
    <div className="flex min-w-0 flex-col gap-10 md:gap-14">
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

        <section className="grid min-w-0 items-start gap-8 lg:grid-cols-2" aria-label={copy.dashboard.rateSnapshotsLabel}>
          <DepositTopFive key={filters.countryCode + filters.locale} filters={filters} products={depositProducts?.items ?? []} unavailable={depositProductsUnavailable} />
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

        <PublicInformationNotice locale={filters.locale} />
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
      href: buildPublicHref("/", { ...filters, bankCodes: filters.bankCodes.filter((value) => value !== bankCode), axisPreset: "" }),
      label: bankLabels.get(bankCode) ?? bankCode
    });
  }
  for (const productType of filters.productTypes) {
    chips.push({
      key: `type-${productType}`,
      href: buildPublicHref("/", { ...filters, productTypes: filters.productTypes.filter((value) => value !== productType), axisPreset: "" }),
      label: productTypeLabels.get(productType) ?? productType
    });
  }
  for (const tag of filters.targetCustomerTags) {
    chips.push({
      key: `tag-${tag}`,
      href: buildPublicHref("/", { ...filters, targetCustomerTags: filters.targetCustomerTags.filter((value) => value !== tag) }),
      label: formatBucketLabel(tag)
    });
  }

  addBucketChip(chips, "fee", filters.feeBucket, buildPublicHref("/", { ...filters, feeBucket: "" }));
  addBucketChip(chips, "balance", filters.minimumBalanceBucket, buildPublicHref("/", { ...filters, minimumBalanceBucket: "" }));
  addBucketChip(chips, "deposit", filters.minimumDepositBucket, buildPublicHref("/", { ...filters, minimumDepositBucket: "" }));
  addBucketChip(chips, "term", filters.termBucket, buildPublicHref("/", { ...filters, termBucket: "" }));

  return chips;
}

function addBucketChip(chips: Array<{ href: string; key: string; label: string }>, key: string, value: string, href: string) {
  if (value) {
    chips.push({ href, key: `${key}-${value}`, label: formatBucketLabel(value) });
  }
}

function formatBucketLabel(value: string) {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
