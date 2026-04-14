import { ProductGridSurface, type ProductGridPageFilters } from "@/components/fpds/public/product-grid-surface";
import { fetchPublicFilters, fetchPublicProducts } from "@/lib/public-api";

type ProductGridPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

const SORT_OPTIONS = new Set([
  "default",
  "bank_name",
  "product_name",
  "display_rate",
  "monthly_fee",
  "minimum_balance",
  "minimum_deposit",
  "last_changed_at"
]);

const SUPPORTED_LOCALES = new Set(["en", "ko", "ja"]);

export default async function ProductGridPage({ searchParams }: ProductGridPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parsePageFilters(resolvedSearchParams);

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

function parsePageFilters(searchParams: Record<string, string | string[] | undefined>): ProductGridPageFilters {
  const locale = firstValue(searchParams.locale).toLowerCase();
  const sortBy = firstValue(searchParams.sort_by).toLowerCase();
  const sortOrder = firstValue(searchParams.sort_order).toLowerCase();

  return {
    locale: SUPPORTED_LOCALES.has(locale) ? locale : "en",
    bankCodes: multiValue(searchParams.bank_code).map((value) => value.toUpperCase()),
    productTypes: multiValue(searchParams.product_type),
    targetCustomerTags: multiValue(searchParams.target_customer_tag),
    feeBucket: firstValue(searchParams.fee_bucket).toLowerCase(),
    minimumBalanceBucket: firstValue(searchParams.minimum_balance_bucket).toLowerCase(),
    minimumDepositBucket: firstValue(searchParams.minimum_deposit_bucket).toLowerCase(),
    termBucket: firstValue(searchParams.term_bucket).toLowerCase(),
    sortBy: SORT_OPTIONS.has(sortBy) ? sortBy : "default",
    sortOrder: sortOrder === "asc" ? "asc" : "desc",
    page: positiveInteger(firstValue(searchParams.page)) ?? 1
  };
}

function buildProductsSearchParams(filters: ProductGridPageFilters) {
  const params = buildScopedFilterSearchParams(filters);
  params.set("sort_by", filters.sortBy);
  params.set("sort_order", filters.sortOrder);
  params.set("page", String(filters.page));
  return params;
}

function buildGlobalFilterSearchParams(filters: ProductGridPageFilters) {
  const params = new URLSearchParams();
  params.set("locale", filters.locale);
  params.set("country_code", "CA");
  return params;
}

function buildScopedFilterSearchParams(filters: ProductGridPageFilters) {
  const params = new URLSearchParams();
  params.set("locale", filters.locale);
  params.set("country_code", "CA");

  for (const bankCode of filters.bankCodes) {
    params.append("bank_code", bankCode);
  }
  for (const productType of filters.productTypes) {
    params.append("product_type", productType);
  }
  for (const targetCustomerTag of filters.targetCustomerTags) {
    params.append("target_customer_tag", targetCustomerTag);
  }

  if (filters.feeBucket) {
    params.set("fee_bucket", filters.feeBucket);
  }
  if (filters.minimumBalanceBucket) {
    params.set("minimum_balance_bucket", filters.minimumBalanceBucket);
  }
  if (filters.minimumDepositBucket) {
    params.set("minimum_deposit_bucket", filters.minimumDepositBucket);
  }
  if (filters.termBucket) {
    params.set("term_bucket", filters.termBucket);
  }

  return params;
}

function firstValue(value: string | string[] | undefined) {
  if (Array.isArray(value)) {
    return value[0]?.trim() ?? "";
  }
  return value?.trim() ?? "";
}

function multiValue(value: string | string[] | undefined) {
  if (Array.isArray(value)) {
    return value.map((entry) => entry.trim().toLowerCase()).filter(Boolean);
  }
  if (typeof value === "string" && value.trim()) {
    return [value.trim().toLowerCase()];
  }
  return [];
}

function positiveInteger(value: string) {
  if (!value) {
    return null;
  }

  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed < 1) {
    return null;
  }

  return parsed;
}
