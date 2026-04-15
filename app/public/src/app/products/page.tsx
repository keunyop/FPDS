import type { Metadata } from "next";

import { ProductGridSurface } from "@/components/fpds/public/product-grid-surface";
import { getPublicMessages, normalizePublicLocale } from "@/lib/public-locale";
import { fetchPublicFilters, fetchPublicProducts } from "@/lib/public-api";
import {
  buildGlobalFilterSearchParams,
  buildProductsSearchParams,
  parseProductGridPageFilters
} from "@/lib/public-query";

type ProductGridPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export async function generateMetadata({ searchParams }: ProductGridPageProps): Promise<Metadata> {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = normalizePublicLocale(typeof resolvedSearchParams.locale === "string" ? resolvedSearchParams.locale : "");
  const copy = getPublicMessages(locale);

  return {
    title: copy.grid.pageTitle,
    description: copy.grid.pageDescription
  };
}

export default async function ProductGridPage({ searchParams }: ProductGridPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parseProductGridPageFilters(resolvedSearchParams);

  let products = null;
  let filterOptions = null;
  let apiUnavailable = false;

  try {
    const [productsResponse, filterResponse] = await Promise.all([
      fetchPublicProducts(buildProductsSearchParams(filters)),
      fetchPublicFilters(buildGlobalFilterSearchParams(filters))
    ]);
    products = productsResponse;
    filterOptions = filterResponse;
  } catch {
    apiUnavailable = true;
  }

  return (
    <ProductGridSurface
      apiUnavailable={apiUnavailable}
      filterOptions={filterOptions}
      filters={filters}
      products={products}
    />
  );
}
