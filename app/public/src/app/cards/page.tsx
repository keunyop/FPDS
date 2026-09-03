import type { Metadata } from "next";

import { ProductGridSurface } from "@/components/fpds/public/product-grid-surface";
import {
  buildCatalogStructuredData,
  PublicStructuredData
} from "@/components/fpds/public/public-structured-data";
import { getPublicCatalogCopy } from "@/lib/public-locale";
import { fetchPublicFilters, fetchPublicProducts } from "@/lib/public-api";
import {
  buildProductsSearchParams,
  CARD_PRODUCT_TYPES,
  parseProductGridPageFilters
} from "@/lib/public-query";
import {
  buildPublicPageMetadata,
  hasNonCanonicalSearchParams
} from "@/lib/public-seo";

type CardCatalogPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export async function generateMetadata({ searchParams }: CardCatalogPageProps): Promise<Metadata> {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parseProductGridPageFilters(resolvedSearchParams, CARD_PRODUCT_TYPES);
  const copy = getPublicCatalogCopy(filters.locale, "card");

  return buildPublicPageMetadata({
    title: copy.pageTitle,
    description: copy.pageDescription,
    path: "/cards",
    locale: filters.locale,
    countryCode: filters.countryCode,
    index: !hasNonCanonicalSearchParams(resolvedSearchParams)
  });
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
    <>
      {products ? (
        <PublicStructuredData
          data={buildCatalogStructuredData(
            products.items,
            "card",
            filters.locale,
            filters.countryCode
          )}
        />
      ) : null}
      <ProductGridSurface
        apiUnavailable={apiUnavailable}
        catalog="card"
        filterOptions={filterOptions}
        filters={filters}
        products={products}
      />
    </>
  );
}
