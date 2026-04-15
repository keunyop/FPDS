export type PublicScopeFilters = {
  locale: string;
  bankCodes: string[];
  productTypes: string[];
  targetCustomerTags: string[];
  feeBucket: string;
  minimumBalanceBucket: string;
  minimumDepositBucket: string;
  termBucket: string;
};

export type ProductGridPageFilters = PublicScopeFilters & {
  sortBy: string;
  sortOrder: "asc" | "desc";
  page: number;
};

export type DashboardPageFilters = PublicScopeFilters & {
  axisPreset: string;
};

export type PublicRoutePath = "/products" | "/dashboard";

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
const SUPPORTED_AXIS_PRESETS = new Set([
  "chequing_fee_vs_minimum_balance",
  "savings_rate_vs_minimum_balance",
  "gic_rate_vs_minimum_deposit",
  "gic_term_vs_rate"
]);

type PageSearchParams = Record<string, string | string[] | undefined>;
type SearchParamsReader = {
  get(name: string): string | null;
  getAll(name: string): string[];
};

type PublicHrefState = PublicScopeFilters &
  Partial<{
    sortBy: string;
    sortOrder: "asc" | "desc";
    page: number;
    axisPreset: string;
  }>;

export function parseProductGridPageFilters(searchParams: PageSearchParams): ProductGridPageFilters {
  const locale = firstValue(searchParams.locale).toLowerCase();
  const sortBy = firstValue(searchParams.sort_by).toLowerCase();
  const sortOrder = firstValue(searchParams.sort_order).toLowerCase();

  return {
    ...parsePublicScopeFilters(searchParams),
    locale: SUPPORTED_LOCALES.has(locale) ? locale : "en",
    sortBy: SORT_OPTIONS.has(sortBy) ? sortBy : "default",
    sortOrder: sortOrder === "asc" ? "asc" : "desc",
    page: positiveInteger(firstValue(searchParams.page)) ?? 1
  };
}

export function parseDashboardPageFilters(searchParams: PageSearchParams): DashboardPageFilters {
  const axisPreset = firstValue(searchParams.axis_preset).toLowerCase();

  return {
    ...parsePublicScopeFilters(searchParams),
    axisPreset: SUPPORTED_AXIS_PRESETS.has(axisPreset) ? axisPreset : ""
  };
}

export function buildProductsSearchParams(filters: ProductGridPageFilters) {
  const params = buildScopedFilterSearchParams(filters);
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

export function buildGlobalFilterSearchParams(filters: Pick<PublicScopeFilters, "locale">) {
  const params = new URLSearchParams();
  params.set("locale", filters.locale);
  params.set("country_code", "CA");
  return params;
}

export function buildScopedFilterSearchParams(filters: PublicScopeFilters) {
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

export function buildPublicHref(path: PublicRoutePath, state: PublicHrefState) {
  const params = new URLSearchParams();

  if (state.locale !== "en") {
    params.set("locale", state.locale);
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

  if (path === "/products") {
    if (state.sortBy && state.sortBy !== "default") {
      params.set("sort_by", state.sortBy);
    }
    if (state.sortOrder && state.sortOrder !== "desc") {
      params.set("sort_order", state.sortOrder);
    }
    if (state.page && state.page > 1) {
      params.set("page", String(state.page));
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
    bankCodes: normalizeMultiValues(searchParams.getAll("bank_code"), true),
    productTypes: normalizeMultiValues(searchParams.getAll("product_type")),
    targetCustomerTags: normalizeMultiValues(searchParams.getAll("target_customer_tag")),
    feeBucket: normalizeScalarValue(searchParams.get("fee_bucket") ?? ""),
    minimumBalanceBucket: normalizeScalarValue(searchParams.get("minimum_balance_bucket") ?? ""),
    minimumDepositBucket: normalizeScalarValue(searchParams.get("minimum_deposit_bucket") ?? ""),
    termBucket: normalizeScalarValue(searchParams.get("term_bucket") ?? "")
  });
}

function parsePublicScopeFilters(searchParams: PageSearchParams): PublicScopeFilters {
  return {
    locale: normalizeLocaleValue(firstValue(searchParams.locale)),
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
