import type { Metadata } from "next";

import { ProductGridSurface } from "@/components/fpds/public/product-grid-surface";
import { getPublicCatalogCopy } from "@/lib/public-locale";
import { fetchPublicFilters, fetchPublicProducts } from "@/lib/public-api";
import {
  buildProductsSearchParams,
  DEPOSIT_PRODUCT_TYPES,
  parseProductGridPageFilters
} from "@/lib/public-query";
import {
  buildPublicPageMetadata,
  hasNonCanonicalSearchParams
} from "@/lib/public-seo";

type ProductGridPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export async function generateMetadata({ searchParams }: ProductGridPageProps): Promise<Metadata> {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parseProductGridPageFilters(resolvedSearchParams, DEPOSIT_PRODUCT_TYPES);
  const copy = getPublicCatalogCopy(filters.locale, "deposit");

  return buildPublicPageMetadata({
    title: copy.pageTitle,
    description: copy.pageDescription,
    path: "/products",
    locale: filters.locale,
    countryCode: filters.countryCode,
    index: !hasNonCanonicalSearchParams(resolvedSearchParams)
  });
}

export default async function ProductGridPage({ searchParams }: ProductGridPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parseProductGridPageFilters(resolvedSearchParams, DEPOSIT_PRODUCT_TYPES);

  let products = null;
  let filterOptions = null;
  let apiUnavailable = false;

  try {
    const [productsResponse, filterResponse] = await Promise.all([
      fetchPublicProducts(buildProductsSearchParams(filters)),
      fetchPublicFilters(buildProductsSearchParams(filters))
    ]);
    products = productsResponse;
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
    />
  );
}
