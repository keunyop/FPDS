export type PublicScopeFilters = {
  locale: string;
  countryCode: string;
  searchQuery: string;
  bankCodes: string[];
  productTypes: string[];
  targetCustomerTags: string[];
  feeBucket: string;
  minimumBalanceBucket: string;
  minimumDepositBucket: string;
  termBucket: string;
};

export type ProductGridPageFilters = PublicScopeFilters & {
  catalogProductTypes: string[];
  sortBy: string;
  sortOrder: "asc" | "desc";
  viewMode: "grid" | "list";
  page: number;
};

export type DashboardPageFilters = PublicScopeFilters & {
  axisPreset: string;
};

export type PublicRoutePath = "/dashboard" | "/products" | "/cards" | "/loans" | "/methodology" | `/products/${string}`;

export const DEPOSIT_PRODUCT_TYPES = ["chequing", "savings", "gic"] as const;
export const LOAN_PRODUCT_TYPES = ["mortgage", "personal-loan", "line-of-credit"] as const;
export const CARD_PRODUCT_TYPES = ["credit-card"] as const;

const SORT_OPTIONS = new Set([
  "bank_name",
  "product_name",
  "display_rate",
  "monthly_fee",
  "minimum_balance",
  "minimum_deposit",
  "annual_fee",
  "last_changed_at"
]);

const VIEW_MODES = new Set(["grid", "list"]);
const SUPPORTED_LOCALES = new Set(["en", "ko", "ja"]);
export const DEFAULT_PUBLIC_COUNTRY_CODE = "CA";

type PageSearchParams = Record<string, string | string[] | undefined>;
type SearchParamsReader = {
  get(name: string): string | null;
  getAll(name: string): string[];
};

type PublicHrefState = PublicScopeFilters &
  Partial<{
    sortBy: string;
    sortOrder: "asc" | "desc";
    viewMode: "grid" | "list";
    page: number;
    axisPreset: string;
  }>;

export function parseProductGridPageFilters(searchParams: PageSearchParams, catalogProductTypes: readonly string[] = []): ProductGridPageFilters {
  const locale = firstValue(searchParams.locale).toLowerCase();
  const requestedSortBy = firstValue(searchParams.sort_by).toLowerCase();
  const sortOrder = firstValue(searchParams.sort_order).toLowerCase();
  const viewMode = firstValue(searchParams.view).toLowerCase();
  const defaultSort = getCatalogDefaultSort(catalogProductTypes);
  const sortBy = SORT_OPTIONS.has(requestedSortBy) ? requestedSortBy : defaultSort.sortBy;

  const parsedScope = parsePublicScopeFilters(searchParams);
  const allowedTypes = new Set(catalogProductTypes);
  const selectedProductTypes = allowedTypes.size
    ? parsedScope.productTypes.filter((productType) => allowedTypes.has(productType))
    : parsedScope.productTypes;

  return {
    ...parsedScope,
    productTypes: selectedProductTypes,
    catalogProductTypes: [...catalogProductTypes],
    locale: SUPPORTED_LOCALES.has(locale) ? locale : "en",
    sortBy,
    sortOrder: sortOrder === "asc" || sortOrder === "desc"
      ? sortOrder
      : getDefaultSortOrder(sortBy, catalogProductTypes),
    viewMode: VIEW_MODES.has(viewMode) ? viewMode as "grid" | "list" : "grid",
    page: 1
  };
}

export function parseDashboardPageFilters(searchParams: PageSearchParams): DashboardPageFilters {
  const globalScope = parsePublicScopeFilters(searchParams);

  return {
    ...globalScope,
    searchQuery: "",
    bankCodes: [],
    productTypes: [],
    targetCustomerTags: [],
    feeBucket: "",
    minimumBalanceBucket: "",
    minimumDepositBucket: "",
    termBucket: "",
    axisPreset: ""
  };
}

export function buildProductsSearchParams(filters: ProductGridPageFilters) {
  const params = buildScopedFilterSearchParams({
    ...filters,
    productTypes: filters.productTypes.length ? filters.productTypes : filters.catalogProductTypes,
  });
  params.set("sort_by", filters.sortBy);
  params.set("sort_order", filters.sortOrder);
  params.set("page", String(filters.page));
  return params;
}

export function buildDashboardSearchParams(filters: DashboardPageFilters) {
  const params = buildScopedFilterSearchParams(filters);
  if (filters.axisPreset) {
    params.set("axis_preset", filters.axisPreset);
  }
  return params;
}

export function buildGlobalFilterSearchParams(filters: Pick<PublicScopeFilters, "locale" | "countryCode">) {
  const params = new URLSearchParams();
  params.set("locale", filters.locale);
  params.set("country_code", filters.countryCode);
  return params;
}

export function buildScopedFilterSearchParams(filters: PublicScopeFilters) {
  const params = new URLSearchParams();
  params.set("locale", filters.locale);
  params.set("country_code", filters.countryCode);
  if (filters.searchQuery) {
    params.set("q", filters.searchQuery);
  }

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

export function buildPublicHref(path: PublicRoutePath, state: PublicHrefState) {
  const params = new URLSearchParams();

  if (state.locale !== "en") {
    params.set("locale", state.locale);
  }
  if (state.countryCode !== DEFAULT_PUBLIC_COUNTRY_CODE) {
    params.set("country_code", state.countryCode);
  }
  if (path !== "/dashboard") {
    if (state.searchQuery) {
      params.set("q", state.searchQuery);
    }
    for (const bankCode of state.bankCodes) {
      params.append("bank_code", bankCode);
    }
    for (const productType of state.productTypes) {
      params.append("product_type", productType);
    }
    for (const tag of state.targetCustomerTags) {
      params.append("target_customer_tag", tag);
    }
    if (state.feeBucket) {
      params.set("fee_bucket", state.feeBucket);
    }
    if (state.minimumBalanceBucket) {
      params.set("minimum_balance_bucket", state.minimumBalanceBucket);
    }
    if (state.minimumDepositBucket) {
      params.set("minimum_deposit_bucket", state.minimumDepositBucket);
    }
    if (state.termBucket) {
      params.set("term_bucket", state.termBucket);
    }
  }

  const carriesCatalogState = path === "/products" || path === "/cards" || path === "/loans" || path.startsWith("/products/");
  if (carriesCatalogState) {
    if (state.sortBy) {
      params.set("sort_by", state.sortBy);
    }
    if (state.sortOrder && state.sortOrder !== "desc") {
      params.set("sort_order", state.sortOrder);
    }
    if (state.viewMode === "list") {
      params.set("view", "list");
    }
  }

  if (path === "/dashboard" && state.axisPreset) {
    params.set("axis_preset", state.axisPreset);
  }

  const query = params.toString();
  return query ? `${path}?${query}` : path;
}

export function buildScopedPublicHrefFromSearchParams(path: PublicRoutePath, searchParams: SearchParamsReader) {
  return buildPublicHref(path, {
    locale: normalizeLocaleValue(searchParams.get("locale") ?? ""),
    countryCode: normalizeCountryCodeValue(searchParams.get("country_code") ?? ""),
    searchQuery: normalizeSearchQueryValue(searchParams.get("q") ?? ""),
    bankCodes: normalizeMultiValues(searchParams.getAll("bank_code"), true),
    productTypes: normalizeMultiValues(searchParams.getAll("product_type")),
    targetCustomerTags: normalizeMultiValues(searchParams.getAll("target_customer_tag")),
    feeBucket: normalizeScalarValue(searchParams.get("fee_bucket") ?? ""),
    minimumBalanceBucket: normalizeScalarValue(searchParams.get("minimum_balance_bucket") ?? ""),
    minimumDepositBucket: normalizeScalarValue(searchParams.get("minimum_deposit_bucket") ?? ""),
    termBucket: normalizeScalarValue(searchParams.get("term_bucket") ?? "")
  });
}

export function buildCountryHref(pathname: string, searchParams: SearchParamsReader, countryCode: string) {
  const params = new URLSearchParams();
  const locale = normalizeLocaleValue(searchParams.get("locale") ?? "");
  const normalizedCountryCode = normalizeCountryCodeValue(countryCode);

  if (locale !== "en") {
    params.set("locale", locale);
  }
  if (normalizedCountryCode !== DEFAULT_PUBLIC_COUNTRY_CODE) {
    params.set("country_code", normalizedCountryCode);
  }

  const query = params.toString();
  return query ? `${pathname}?${query}` : pathname;
}

function parsePublicScopeFilters(searchParams: PageSearchParams): PublicScopeFilters {
  return {
    locale: normalizeLocaleValue(firstValue(searchParams.locale)),
    countryCode: normalizeCountryCodeValue(firstValue(searchParams.country_code)),
    searchQuery: normalizeSearchQueryValue(firstValue(searchParams.q)),
    bankCodes: normalizeMultiValues(multiValue(searchParams.bank_code), true),
    productTypes: normalizeMultiValues(multiValue(searchParams.product_type)),
    targetCustomerTags: normalizeMultiValues(multiValue(searchParams.target_customer_tag)),
    feeBucket: normalizeScalarValue(firstValue(searchParams.fee_bucket)),
    minimumBalanceBucket: normalizeScalarValue(firstValue(searchParams.minimum_balance_bucket)),
    minimumDepositBucket: normalizeScalarValue(firstValue(searchParams.minimum_deposit_bucket)),
    termBucket: normalizeScalarValue(firstValue(searchParams.term_bucket))
  };
}

function normalizeLocaleValue(value: string) {
  const locale = value.toLowerCase();
  return SUPPORTED_LOCALES.has(locale) ? locale : "en";
}

export function normalizeCountryCodeValue(value: string) {
  const countryCode = value.trim().toUpperCase();
  return /^[A-Z]{2}$/.test(countryCode) ? countryCode : DEFAULT_PUBLIC_COUNTRY_CODE;
}

function normalizeSearchQueryValue(value: string) {
  return value.trim().replace(/\s+/g, " ").slice(0, 120);
}

function normalizeScalarValue(value: string) {
  return value.trim().toLowerCase();
}

function normalizeMultiValues(values: string[], uppercase = false) {
  return values
    .map((value) => normalizeScalarValue(value))
    .filter(Boolean)
    .map((value) => (uppercase ? value.toUpperCase() : value));
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

function getCatalogDefaultSort(catalogProductTypes: readonly string[]) {
  if (catalogProductTypes.includes("credit-card")) {
    return { sortBy: "annual_fee", sortOrder: "asc" as const };
  }
  if (catalogProductTypes.some((productType) => LOAN_PRODUCT_TYPES.includes(productType as typeof LOAN_PRODUCT_TYPES[number]))) {
    return { sortBy: "display_rate", sortOrder: "asc" as const };
  }
  return { sortBy: "display_rate", sortOrder: "desc" as const };
}

function getDefaultSortOrder(sortBy: string, catalogProductTypes: readonly string[]): "asc" | "desc" {
  if (sortBy === "display_rate") {
    return getCatalogDefaultSort(catalogProductTypes).sortOrder;
  }
  return sortBy === "last_changed_at" ? "desc" : "asc";
}
