import type { Metadata } from "next";

import { ProductGridSurface } from "@/components/fpds/public/product-grid-surface";
import { getPublicCatalogCopy, normalizePublicLocale } from "@/lib/public-locale";
import { fetchPublicFilters, fetchPublicProducts } from "@/lib/public-api";
import {
  buildProductsSearchParams,
  LOAN_PRODUCT_TYPES,
  parseProductGridPageFilters
} from "@/lib/public-query";

type LoanCatalogPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export async function generateMetadata({ searchParams }: LoanCatalogPageProps): Promise<Metadata> {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = normalizePublicLocale(typeof resolvedSearchParams.locale === "string" ? resolvedSearchParams.locale : "");
  const copy = getPublicCatalogCopy(locale, "loan");

  return {
    title: copy.pageTitle,
    description: copy.pageDescription
  };
}

export default async function LoanCatalogPage({ searchParams }: LoanCatalogPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parseProductGridPageFilters(resolvedSearchParams, LOAN_PRODUCT_TYPES);

  let products = null;
  let topProducts = null;
  let filterOptions = null;
  let apiUnavailable = false;

  try {
    const topProductsSearchParams = buildProductsSearchParams({ ...filters, page: 1 });
    topProductsSearchParams.set("page_size", "5");

    const [productsResponse, topProductsResponse, filterResponse] = await Promise.all([
      fetchPublicProducts(buildProductsSearchParams(filters)),
      fetchPublicProducts(topProductsSearchParams),
      fetchPublicFilters(buildProductsSearchParams(filters))
    ]);
    products = productsResponse;
    topProducts = topProductsResponse;
    filterOptions = filterResponse;
  } catch {
    apiUnavailable = true;
  }

  return (
    <ProductGridSurface
      apiUnavailable={apiUnavailable}
      catalog="loan"
      filterOptions={filterOptions}
      filters={filters}
      products={products}
      topProducts={topProducts}
    />
  );
}
