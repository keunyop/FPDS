import { redirect } from "next/navigation";

import { buildPublicHref, parseProductGridPageFilters } from "@/lib/public-query";

type HomePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function HomePage({ searchParams }: HomePageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parseProductGridPageFilters(resolvedSearchParams);
  redirect(buildPublicHref("/products", filters));
}
