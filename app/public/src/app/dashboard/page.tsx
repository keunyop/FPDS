import type { Metadata } from "next";

import { DashboardSurface } from "@/components/fpds/public/dashboard-surface";
import { getPublicMessages, normalizePublicLocale } from "@/lib/public-locale";
import {
  fetchPublicDashboardScatter,
  fetchPublicDashboardRankings,
  fetchPublicDashboardSummary
} from "@/lib/public-api";
import {
  buildDashboardSearchParams,
  parseDashboardPageFilters,
  type DashboardPageFilters
} from "@/lib/public-query";

type DashboardPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export async function generateMetadata({ searchParams }: DashboardPageProps): Promise<Metadata> {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = normalizePublicLocale(typeof resolvedSearchParams.locale === "string" ? resolvedSearchParams.locale : "");
  const copy = getPublicMessages(locale);

  return {
    title: copy.dashboard.pageTitle,
    description: copy.dashboard.pageDescription
  };
}

export default async function DashboardPage({ searchParams }: DashboardPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parseDashboardPageFilters(resolvedSearchParams);

  let summary = null;
  let rankings = null;
  let scatter = null;
  let apiUnavailable = false;

  try {
    const search = buildDashboardSearchParams(filters);
    const [summaryResponse, rankingsResponse] = await Promise.all([
      fetchPublicDashboardSummary(search),
      fetchPublicDashboardRankings(search)
    ]);
    summary = summaryResponse;
    rankings = rankingsResponse;

    const scatterFilters = buildScatterFilters(filters);
    if (scatterFilters) {
      try {
        scatter = await fetchPublicDashboardScatter(buildDashboardSearchParams(scatterFilters));
      } catch {
        scatter = null;
      }
    }
  } catch {
    apiUnavailable = true;
  }

  return (
    <DashboardSurface
      apiUnavailable={apiUnavailable}
      filters={filters}
      rankings={rankings}
      scatter={scatter}
      summary={summary}
    />
  );
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
