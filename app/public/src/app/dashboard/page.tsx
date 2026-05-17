import type { Metadata } from "next";

import { DashboardSurface } from "@/components/fpds/public/dashboard-surface";
import { getPublicMessages, normalizePublicLocale } from "@/lib/public-locale";
import {
  fetchPublicDashboardRankings,
  fetchPublicDashboardSummary
} from "@/lib/public-api";
import {
  buildDashboardSearchParams,
  parseDashboardPageFilters
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
  let apiUnavailable = false;

  try {
    const search = buildDashboardSearchParams(filters);
    const [summaryResponse, rankingsResponse] = await Promise.all([
      fetchPublicDashboardSummary(search),
      fetchPublicDashboardRankings(search)
    ]);
    summary = summaryResponse;
    rankings = rankingsResponse;
  } catch {
    apiUnavailable = true;
  }

  return (
    <DashboardSurface
      apiUnavailable={apiUnavailable}
      filters={filters}
      rankings={rankings}
      summary={summary}
    />
  );
}
