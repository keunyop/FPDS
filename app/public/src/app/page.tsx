import { redirect } from "next/navigation";

import { buildPublicHref, parseDashboardPageFilters } from "@/lib/public-query";

type HomePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function HomePage({ searchParams }: HomePageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parseDashboardPageFilters(resolvedSearchParams);
  redirect(buildPublicHref("/dashboard", filters));
}
