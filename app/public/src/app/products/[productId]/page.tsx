import type { Metadata } from "next";
import { notFound } from "next/navigation";

import {
  buildProductStructuredData,
  PublicStructuredData
} from "@/components/fpds/public/public-structured-data";
import { ProductDetailSurface } from "@/components/fpds/public/product-detail-surface";
import {
  fetchPublicProductDetail,
  fetchPublicFilters,
  fetchPublicProducts,
  isPublicApiError,
  type PublicProduct,
  type PublicProductDetailResponse
} from "@/lib/public-api";
import { getPublicMessages } from "@/lib/public-locale";
import {
  buildGlobalFilterSearchParams,
  buildPublicHref,
  CARD_PRODUCT_TYPES,
  DEPOSIT_PRODUCT_TYPES,
  LOAN_PRODUCT_TYPES,
  parseProductGridPageFilters
} from "@/lib/public-query";
import {
  buildProductSeoDescription,
  buildProductSeoTitle,
  buildPublicPageMetadata,
  type PublicSeoPath
} from "@/lib/public-seo";
import { isIndexableProductLocale } from "@/lib/public-url-policy";

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
      title: buildProductSeoTitle(detail.product),
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
      title: unavailableProductTitle(filters.locale),
      description: copy.grid.retryBody,
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

  let detail: PublicProductDetailResponse | null = null;
  let relatedProducts: PublicProduct[] = [];
  let apiUnavailable = false;
  let otherBanksHref: string | null = null;

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
    const currentProduct = detail.product;
    const relatedParams = new URLSearchParams({ locale: filters.locale, country_code: currentProduct.country_code,
      bank_code: currentProduct.bank_code, product_type: currentProduct.product_type,
      sort_by: 'product_name', sort_order: 'asc', page: '1', page_size: '6' });
    const [bankOptions, related] = await Promise.allSettled([
      fetchPublicFilters(new URLSearchParams({ locale: filters.locale, country_code: currentProduct.country_code, product_type: currentProduct.product_type })),
      fetchPublicProducts(relatedParams)
    ]);
    if (bankOptions.status === 'fulfilled') {
      const bankCodes = bankOptions.value.banks.filter(bank => bank.value !== currentProduct.bank_code && bank.count > 0).map(bank => bank.value);
      if (bankCodes.length) otherBanksHref = buildPublicHref(currentProduct.product_type === 'credit-card' ? '/cards' : currentProduct.product_family === 'lending' ? '/loans' : '/products', {
        ...parseProductGridPageFilters({ locale: filters.locale, country_code: currentProduct.country_code }),
        bankCodes, productTypes: [currentProduct.product_type], sortBy: 'bank_name', sortOrder: 'asc'
      });
    }
    if (related.status === 'fulfilled') relatedProducts = related.value.items.filter(product => product.product_id !== currentProduct.product_id).slice(0, 4);

  } catch (error) {
    if (isPublicApiError(error, 404)) {
      notFound();
    }
    apiUnavailable = true;
  }

  return (
    <>
      {detail && isIndexableProductLocale(filters.locale) ? (
        <PublicStructuredData
          data={buildProductStructuredData(detail.product, filters.locale)}
        />
      ) : null}
      <ProductDetailSurface
        apiUnavailable={apiUnavailable}
        detail={detail}
        filters={filters}
        relatedProducts={relatedProducts}
        otherBanksHref={otherBanksHref}
      />
    </>
  );
}

function unavailableProductTitle(locale: string) {
  if (locale === "ko") {
    return "상품 정보를 일시적으로 사용할 수 없음";
  }
  if (locale === "ja") {
    return "商品情報を一時的に利用できません";
  }
  return "Product details temporarily unavailable";
}
