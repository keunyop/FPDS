import type { Metadata } from "next";

import { DashboardSurface } from "@/components/fpds/public/dashboard-surface";
import { getPublicMessages } from "@/lib/public-locale";
import {
  fetchPublicDashboardScatter,
  fetchPublicDashboardSummary,
  fetchPublicHomeCountries,
  fetchPublicProducts
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

  let summary = null;
  let countries = null;
  let depositProducts = null;
  let loanProducts = null;
  let scatter = null;
  let apiUnavailable = false;
  let countriesUnavailable = false;
  let depositProductsUnavailable = false;
  let loanProductsUnavailable = false;

  const [summaryResult, countriesResult, depositProductsResult, loanProductsResult] = await Promise.allSettled([
    fetchPublicDashboardSummary(buildDashboardSearchParams(filters)),
    fetchPublicHomeCountries(filters.locale),
    fetchPublicProducts(buildDepositProductsSearchParams(filters)),
    fetchPublicProducts(buildLoanProductsSearchParams(filters))
  ]);

  if (summaryResult.status === "fulfilled") {
    summary = summaryResult.value;
  } else {
    apiUnavailable = true;
  }

  if (countriesResult.status === "fulfilled") {
    countries = countriesResult.value;
  } else {
    countriesUnavailable = true;
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
      countries={countries}
      countriesUnavailable={countriesUnavailable}
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
