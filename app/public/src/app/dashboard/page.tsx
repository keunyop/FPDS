import type { Metadata } from "next";
import { Suspense } from "react";

import {
  DashboardFinderFallback,
  DashboardHero
} from "@/components/fpds/public/dashboard-hero";
import { DashboardSurface } from "@/components/fpds/public/dashboard-surface";
import { ProductRecommendationFinder } from "@/components/fpds/public/product-recommendation-finder";
import { getPublicMessages } from "@/lib/public-locale";
import {
  fetchPublicDashboardScatter,
  fetchPublicDashboardSummary,
  fetchPublicProducts,
  type PublicDashboardSummaryResponse,
  type PublicProductsResponse
} from "@/lib/public-api";
import {
  buildDashboardSearchParams,
  DEPOSIT_PRODUCT_TYPES,
  LOAN_PRODUCT_TYPES,
  parseDashboardPageFilters,
  type DashboardPageFilters
} from "@/lib/public-query";
import {
  buildPublicPageMetadata,
  hasNonCanonicalSearchParams
} from "@/lib/public-seo";

type DashboardPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export async function generateMetadata({ searchParams }: DashboardPageProps): Promise<Metadata> {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parseDashboardPageFilters(resolvedSearchParams);
  const copy = getPublicMessages(filters.locale);

  return buildPublicPageMetadata({
    title: copy.dashboard.pageTitle + " — SwitchaBank",
    description: copy.dashboard.pageDescription,
    path: "/",
    locale: filters.locale,
    countryCode: filters.countryCode,
    index: !hasNonCanonicalSearchParams(resolvedSearchParams)
  });
}

export default async function DashboardPage({ searchParams }: DashboardPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parseDashboardPageFilters(resolvedSearchParams);
  const summaryPromise = fetchPublicDashboardSummary(buildDashboardSearchParams(filters));
  const depositProductsPromise = fetchPublicProducts(buildDepositProductsSearchParams(filters));
  const loanProductsPromise = fetchPublicProducts(buildLoanProductsSearchParams(filters));

  return (
    <main className="mx-auto min-w-0 w-full max-w-7xl px-4 py-6 md:px-6 md:py-9">
      <div className="flex min-w-0 flex-col gap-10 md:gap-14">
        <DashboardHero
          filters={filters}
          finder={
            <Suspense fallback={<DashboardFinderFallback />}>
              <DashboardFinder filters={filters} summaryPromise={summaryPromise} />
            </Suspense>
          }
        />
        <Suspense fallback={<DashboardDataFallback />}>
          <DashboardData
            depositProductsPromise={depositProductsPromise}
            filters={filters}
            loanProductsPromise={loanProductsPromise}
            summaryPromise={summaryPromise}
          />
        </Suspense>
      </div>
    </main>
  );
}

async function DashboardFinder({
  filters,
  summaryPromise
}: {
  filters: DashboardPageFilters;
  summaryPromise: Promise<PublicDashboardSummaryResponse>;
}) {
  let summary: PublicDashboardSummaryResponse | null = null;
  try {
    summary = await summaryPromise;
  } catch {
    summary = null;
  }

  return (
    <ProductRecommendationFinder
      banks={summary?.breakdowns.products_by_bank ?? []}
      countryCode={filters.countryCode}
      locale={filters.locale}
      productTypes={summary?.breakdowns.products_by_product_type ?? []}
    />
  );
}

async function DashboardData({
  depositProductsPromise,
  filters,
  loanProductsPromise,
  summaryPromise
}: {
  depositProductsPromise: Promise<PublicProductsResponse>;
  filters: DashboardPageFilters;
  loanProductsPromise: Promise<PublicProductsResponse>;
  summaryPromise: Promise<PublicDashboardSummaryResponse>;
}) {
  let summary = null;
  let depositProducts = null;
  let loanProducts = null;
  let scatter = null;
  let apiUnavailable = false;
  let depositProductsUnavailable = false;
  let loanProductsUnavailable = false;

  const [summaryResult, depositProductsResult, loanProductsResult] = await Promise.allSettled([
    summaryPromise,
    depositProductsPromise,
    loanProductsPromise
  ]);

  if (summaryResult.status === "fulfilled") {
    summary = summaryResult.value;
  } else {
    apiUnavailable = true;
  }

  if (depositProductsResult.status === "fulfilled") {
    depositProducts = depositProductsResult.value;
  } else {
    depositProductsUnavailable = true;
  }

  if (loanProductsResult.status === "fulfilled") {
    loanProducts = loanProductsResult.value;
  } else {
    loanProductsUnavailable = true;
  }

  if (!apiUnavailable) {
    const scatterFilters = buildScatterFilters(filters);
    if (scatterFilters) {
      try {
        scatter = await fetchPublicDashboardScatter(buildDashboardSearchParams(scatterFilters));
      } catch {
        scatter = null;
      }
    }
  }

  return (
    <DashboardSurface
      apiUnavailable={apiUnavailable}
      depositProducts={depositProducts}
      depositProductsUnavailable={depositProductsUnavailable}
      filters={filters}
      loanProducts={loanProducts}
      loanProductsUnavailable={loanProductsUnavailable}
      scatter={scatter}
      summary={summary}
    />
  );
}

function DashboardDataFallback() {
  return (
    <section
      aria-busy="true"
      aria-label="Loading current product rankings"
      className="grid min-w-0 gap-8 lg:grid-cols-2"
    >
      <div className="h-80 animate-pulse border border-border bg-card/60" />
      <div className="h-80 animate-pulse border border-border bg-card/60" />
    </section>
  );
}

function buildDepositProductsSearchParams(filters: DashboardPageFilters) {
  const params = buildDashboardSearchParams({
    ...filters,
    axisPreset: "",
    productTypes: [...DEPOSIT_PRODUCT_TYPES]
  });
  params.set("page", "1");
  params.set("page_size", "5");
  params.set("sort_by", "display_rate");
  params.set("sort_order", "desc");
  return params;
}

function buildLoanProductsSearchParams(filters: DashboardPageFilters) {
  const params = buildDashboardSearchParams({
    ...filters,
    axisPreset: "",
    feeBucket: "",
    minimumBalanceBucket: "",
    minimumDepositBucket: "",
    productTypes: [...LOAN_PRODUCT_TYPES],
    termBucket: ""
  });
  params.set("page", "1");
  params.set("page_size", "5");
  params.set("sort_by", "display_rate");
  params.set("sort_order", "asc");
  return params;
}

function buildScatterFilters(filters: DashboardPageFilters): DashboardPageFilters | null {
  const axisPreset = filters.axisPreset || defaultAxisPreset(filters.productTypes);
  if (!axisPreset) {
    return null;
  }
  return { ...filters, axisPreset };
}

function defaultAxisPreset(productTypes: string[]) {
  if (productTypes.length !== 1) {
    return "";
  }
  switch (productTypes[0]) {
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
