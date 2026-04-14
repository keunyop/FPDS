import { ProductGridSurface } from "@/components/fpds/public/product-grid-surface";
import { fetchPublicFilters, fetchPublicProducts } from "@/lib/public-api";
import {
  buildGlobalFilterSearchParams,
  buildProductsSearchParams,
  parseProductGridPageFilters
} from "@/lib/public-query";

type ProductGridPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

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
