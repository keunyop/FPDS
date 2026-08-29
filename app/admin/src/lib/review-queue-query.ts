export const DEFAULT_REVIEW_QUEUE_STATES = ["queued", "deferred"] as const;
export const REVIEW_QUEUE_PAGE_SIZES = [20, 50, 100] as const;
export const DEFAULT_REVIEW_QUEUE_PAGE_SIZE = 20;

const REVIEW_STATES = new Set(["queued", "deferred", "approved", "edited", "rejected"]);
const VALIDATION_STATUSES = new Set(["pass", "warning", "error"]);
const SORT_FIELDS = new Set(["priority", "created_at", "updated_at", "source_confidence", "product_name"]);
const RETURN_ORIGIN = "https://fpds.local";

type SearchParamRecord = Record<string, string | string[] | undefined>;

export type ReviewQueuePageFilters = {
  q: string;
  states: string[];
  bankCode: string;
  productType: string;
  validationStatus: string;
  createdFrom: string;
  createdTo: string;
  sortBy: string;
  sortOrder: "asc" | "desc";
  page: number;
  pageSize: number;
};

export function defaultReviewQueueFilters(): ReviewQueuePageFilters {
  return {
    q: "",
    states: [...DEFAULT_REVIEW_QUEUE_STATES],
    bankCode: "",
    productType: "",
    validationStatus: "",
    createdFrom: "",
    createdTo: "",
    sortBy: "priority",
    sortOrder: "desc",
    page: 1,
    pageSize: DEFAULT_REVIEW_QUEUE_PAGE_SIZE,
  };
}

export function parseReviewQueueFilters(source: SearchParamRecord | URLSearchParams): ReviewQueuePageFilters {
  const states = valuesFor(source, "state")
    .map((value) => value.toLowerCase())
    .filter((value) => REVIEW_STATES.has(value));
  const validationStatus = firstValue(source, "validation_status").toLowerCase();
  const sortBy = firstValue(source, "sort_by").toLowerCase();
  const requestedPageSize = positiveInteger(firstValue(source, "page_size"));

  return {
    q: firstValue(source, "q"),
    states: states.length > 0 ? states : [...DEFAULT_REVIEW_QUEUE_STATES],
    bankCode: firstValue(source, "bank_code").toUpperCase(),
    productType: firstValue(source, "product_type").toLowerCase(),
    validationStatus: VALIDATION_STATUSES.has(validationStatus) ? validationStatus : "",
    createdFrom: normalizeDate(firstValue(source, "created_from")),
    createdTo: normalizeDate(firstValue(source, "created_to")),
    sortBy: SORT_FIELDS.has(sortBy) ? sortBy : "priority",
    sortOrder: firstValue(source, "sort_order").toLowerCase() === "asc" ? "asc" : "desc",
    page: positiveInteger(firstValue(source, "page")) ?? 1,
    pageSize: REVIEW_QUEUE_PAGE_SIZES.includes(requestedPageSize as 20 | 50 | 100)
      ? requestedPageSize as 20 | 50 | 100
      : DEFAULT_REVIEW_QUEUE_PAGE_SIZE,
  };
}

export function buildReviewQueueBrowserSearchParams(filters: ReviewQueuePageFilters) {
  const params = buildSharedSearchParams(filters);
  if (filters.createdFrom) {
    params.set("created_from", filters.createdFrom);
  }
  if (filters.createdTo) {
    params.set("created_to", filters.createdTo);
  }
  if (filters.page > 1) {
    params.set("page", String(filters.page));
  }
  if (filters.pageSize !== DEFAULT_REVIEW_QUEUE_PAGE_SIZE) {
    params.set("page_size", String(filters.pageSize));
  }
  return params;
}

export function buildReviewQueueApiSearchParams(filters: ReviewQueuePageFilters) {
  const params = buildSharedSearchParams(filters);
  if (filters.createdFrom) {
    params.set("created_from", `${filters.createdFrom}T00:00:00Z`);
  }
  if (filters.createdTo) {
    params.set("created_to", `${filters.createdTo}T23:59:59.999Z`);
  }
  params.set("page", String(filters.page));
  params.set("page_size", String(filters.pageSize));
  return params;
}

export function parseReviewQueueReturnFilters(value: string | undefined) {
  if (!value) {
    return null;
  }

  try {
    const url = new URL(value, RETURN_ORIGIN);
    if (url.origin !== RETURN_ORIGIN || url.pathname !== "/admin/reviews") {
      return null;
    }
    return parseReviewQueueFilters(url.searchParams);
  } catch {
    return null;
  }
}

function buildSharedSearchParams(filters: ReviewQueuePageFilters) {
  const params = new URLSearchParams();
  if (filters.q) {
    params.set("q", filters.q);
  }
  for (const state of filters.states) {
    if (REVIEW_STATES.has(state)) {
      params.append("state", state);
    }
  }
  if (filters.bankCode) {
    params.set("bank_code", filters.bankCode);
  }
  if (filters.productType) {
    params.set("product_type", filters.productType);
  }
  if (filters.validationStatus) {
    params.set("validation_status", filters.validationStatus);
  }
  params.set("sort_by", SORT_FIELDS.has(filters.sortBy) ? filters.sortBy : "priority");
  params.set("sort_order", filters.sortOrder === "asc" ? "asc" : "desc");
  return params;
}

function firstValue(source: SearchParamRecord | URLSearchParams, name: string) {
  if (source instanceof URLSearchParams) {
    return source.get(name)?.trim() ?? "";
  }
  const value = source[name];
  return (Array.isArray(value) ? value[0] : value)?.trim() ?? "";
}

function valuesFor(source: SearchParamRecord | URLSearchParams, name: string) {
  if (source instanceof URLSearchParams) {
    return source.getAll(name).map((value) => value.trim()).filter(Boolean);
  }
  const value = source[name];
  const values = Array.isArray(value) ? value : typeof value === "string" ? [value] : [];
  return values.map((item) => item.trim()).filter(Boolean);
}

function normalizeDate(value: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return "";
  }
  const parsed = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(parsed.valueOf()) || parsed.toISOString().slice(0, 10) !== value ? "" : value;
}

function positiveInteger(value: string) {
  if (!/^\d+$/.test(value)) {
    return null;
  }
  const parsed = Number.parseInt(value, 10);
  return Number.isSafeInteger(parsed) && parsed >= 1 ? parsed : null;
}
