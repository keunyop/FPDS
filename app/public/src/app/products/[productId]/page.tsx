import type { Metadata } from "next";
import { notFound } from "next/navigation";

import {
  buildProductStructuredData,
  PublicStructuredData
} from "@/components/fpds/public/public-structured-data";
import { ProductDetailSurface } from "@/components/fpds/public/product-detail-surface";
import {
  fetchPublicProductDetail,
  isPublicApiError
} from "@/lib/public-api";
import { getPublicMessages } from "@/lib/public-locale";
import {
  buildGlobalFilterSearchParams,
  CARD_PRODUCT_TYPES,
  DEPOSIT_PRODUCT_TYPES,
  LOAN_PRODUCT_TYPES,
  parseProductGridPageFilters
} from "@/lib/public-query";
import {
  buildProductSeoDescription,
  buildPublicPageMetadata,
  type PublicSeoPath
} from "@/lib/public-seo";

type ProductDetailPageProps = {
  params: Promise<{ productId: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export async function generateMetadata({
  params,
  searchParams
}: ProductDetailPageProps): Promise<Metadata> {
  const [{ productId }, resolvedSearchParams] = await Promise.all([
    params,
    searchParams ?? Promise.resolve({})
  ]);
  const filters = parseProductGridPageFilters(resolvedSearchParams);
  const path = ("/products/" + encodeURIComponent(productId)) as PublicSeoPath;

  try {
    const detail = await fetchPublicProductDetail(
      productId,
      buildGlobalFilterSearchParams(filters)
    );
    return buildPublicPageMetadata({
      title: detail.product.product_name + " | " + detail.product.bank_name,
      description: buildProductSeoDescription(detail.product, filters.locale),
      path,
      locale: filters.locale,
      countryCode: detail.product.country_code
    });
  } catch (error) {
    if (isPublicApiError(error, 404)) {
      notFound();
    }

    const copy = getPublicMessages(filters.locale);
    return buildPublicPageMetadata({
      title: copy.grid.pageTitle,
      description: copy.grid.pageDescription,
      path,
      locale: filters.locale,
      countryCode: filters.countryCode,
      index: false
    });
  }
}

export default async function ProductDetailPage({ params, searchParams }: ProductDetailPageProps) {
  const [{ productId }, resolvedSearchParams] = await Promise.all([params, searchParams ?? Promise.resolve({})]);
  let filters = parseProductGridPageFilters(resolvedSearchParams);

  let detail = null;
  let apiUnavailable = false;

  try {
    detail = await fetchPublicProductDetail(productId, buildGlobalFilterSearchParams(filters));
    const catalogProductTypes = detail.product.product_type === "credit-card"
      ? CARD_PRODUCT_TYPES
      : detail.product.product_family === "lending"
        ? LOAN_PRODUCT_TYPES
        : DEPOSIT_PRODUCT_TYPES;
    filters = parseProductGridPageFilters(
      resolvedSearchParams,
      catalogProductTypes
    );
  } catch (error) {
    if (isPublicApiError(error, 404)) {
      notFound();
    }
    apiUnavailable = true;
  }

  return (
    <>
      {detail ? (
        <PublicStructuredData
          data={buildProductStructuredData(detail.product, filters.locale)}
        />
      ) : null}
      <ProductDetailSurface
        apiUnavailable={apiUnavailable}
        detail={detail}
        filters={filters}
      />
    </>
  );
}
