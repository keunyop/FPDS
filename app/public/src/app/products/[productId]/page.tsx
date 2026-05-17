import type { Metadata } from "next";

import { ProductDetailSurface } from "@/components/fpds/public/product-detail-surface";
import { fetchPublicProductDetail } from "@/lib/public-api";
import { getPublicMessages, normalizePublicLocale } from "@/lib/public-locale";
import {
  buildGlobalFilterSearchParams,
  parseProductGridPageFilters
} from "@/lib/public-query";

type ProductDetailPageProps = {
  params: Promise<{ productId: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export async function generateMetadata({ searchParams }: ProductDetailPageProps): Promise<Metadata> {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = normalizePublicLocale(typeof resolvedSearchParams.locale === "string" ? resolvedSearchParams.locale : "");
  const copy = getPublicMessages(locale);

  return {
    title: copy.grid.pageTitle,
    description: copy.grid.pageDescription
  };
}

export default async function ProductDetailPage({ params, searchParams }: ProductDetailPageProps) {
  const [{ productId }, resolvedSearchParams] = await Promise.all([params, searchParams ?? Promise.resolve({})]);
  const filters = parseProductGridPageFilters(resolvedSearchParams);

  let detail = null;
  let apiUnavailable = false;

  try {
    detail = await fetchPublicProductDetail(productId, buildGlobalFilterSearchParams(filters));
  } catch {
    apiUnavailable = true;
  }

  return <ProductDetailSurface apiUnavailable={apiUnavailable} detail={detail} filters={filters} />;
}
