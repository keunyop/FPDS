import type { Metadata } from "next";

import { ProductGridSurface } from "@/components/fpds/public/product-grid-surface";
import { getPublicCatalogCopy, normalizePublicLocale } from "@/lib/public-locale";
import { fetchPublicFilters, fetchPublicProducts } from "@/lib/public-api";
import {
  buildProductsSearchParams,
  CARD_PRODUCT_TYPES,
  parseProductGridPageFilters
} from "@/lib/public-query";

type CardCatalogPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export async function generateMetadata({ searchParams }: CardCatalogPageProps): Promise<Metadata> {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = normalizePublicLocale(typeof resolvedSearchParams.locale === "string" ? resolvedSearchParams.locale : "");
  const copy = getPublicCatalogCopy(locale, "card");

  return {
    title: copy.pageTitle,
    description: copy.pageDescription
  };
}

export default async function CardCatalogPage({ searchParams }: CardCatalogPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parseProductGridPageFilters(resolvedSearchParams, CARD_PRODUCT_TYPES);

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
      catalog="card"
      filterOptions={filterOptions}
      filters={filters}
      products={products}
    />
  );
}
