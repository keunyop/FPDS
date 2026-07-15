import type { Metadata } from "next";

import { ProductGridSurface } from "@/components/fpds/public/product-grid-surface";
import { getPublicCatalogCopy, normalizePublicLocale } from "@/lib/public-locale";
import { fetchPublicFilters, fetchPublicProducts } from "@/lib/public-api";
import {
  buildProductsSearchParams,
  DEPOSIT_PRODUCT_TYPES,
  parseProductGridPageFilters
} from "@/lib/public-query";

type ProductGridPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export async function generateMetadata({ searchParams }: ProductGridPageProps): Promise<Metadata> {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = normalizePublicLocale(typeof resolvedSearchParams.locale === "string" ? resolvedSearchParams.locale : "");
  const copy = getPublicCatalogCopy(locale, "deposit");

  return {
    title: copy.pageTitle,
    description: copy.pageDescription
  };
}

export default async function ProductGridPage({ searchParams }: ProductGridPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parseProductGridPageFilters(resolvedSearchParams, DEPOSIT_PRODUCT_TYPES);

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
      catalog="deposit"
      filterOptions={filterOptions}
      filters={filters}
      products={products}
      topProducts={topProducts}
    />
  );
}
