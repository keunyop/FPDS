export type PublicFreshness = {
  snapshot_id: string | null;
  refreshed_at: string | null;
  source_change_cutoff_at: string | null;
  cache_ttl_sec: number;
  status: "fresh" | "stale" | "unavailable";
  latest_attempted_at?: string | null;
  latest_error_summary?: string | null;
};

export type PublicProduct = {
  product_id: string;
  bank_code: string;
  bank_name: string;
  country_code: string;
  product_family: string;
  product_type: string;
  product_type_label: string;
  subtype_code: string | null;
  subtype_label: string | null;
  product_name: string;
  source_language: string;
  currency: string;
  status: string;
  public_display_rate: number | null;
  public_display_fee: number | null;
  minimum_balance: number | null;
  minimum_deposit: number | null;
  term_length_days: number | null;
  product_highlight_badge_code: string | null;
  product_highlight_badge_label: string | null;
  target_customer_tags: string[];
  target_customer_tag_labels: string[];
  last_verified_at: string | null;
  last_changed_at: string | null;
};

export type PublicProductsResponse = {
  items: PublicProduct[];
  applied_filters: Record<string, unknown>;
  sort: {
    sort_by: string;
    sort_order: "asc" | "desc";
  };
  freshness: PublicFreshness;
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next_page: boolean;
};

export type PublicFilterOption = {
  value: string;
  label: string;
  count: number;
  productType?: string;
};

export type PublicFiltersResponse = {
  banks: PublicFilterOption[];
  product_types: PublicFilterOption[];
  subtypes: PublicFilterOption[];
  target_customer_tags: PublicFilterOption[];
  fee_buckets: PublicFilterOption[];
  minimum_balance_buckets: PublicFilterOption[];
  minimum_deposit_buckets: PublicFilterOption[];
  term_buckets: PublicFilterOption[];
  applied_filters: Record<string, unknown>;
  freshness: PublicFreshness;
};

export type PublicDashboardMetric = {
  metric_key: string;
  label: string;
  value: number | null;
  unit: string;
  scope_note: string | null;
};

export type PublicDashboardBreakdownItem = {
  count: number;
  share_percent: number;
};

export type PublicDashboardSummaryResponse = {
  metrics: PublicDashboardMetric[];
  breakdowns: {
    products_by_bank: Array<
      PublicDashboardBreakdownItem & {
        bank_code: string;
        bank_name: string;
      }
    >;
    products_by_product_type: Array<
      PublicDashboardBreakdownItem & {
        product_type: string;
        product_type_label: string;
      }
    >;
  };
  applied_filters: Record<string, unknown>;
  freshness: PublicFreshness;
};

export type PublicDashboardRankingRow = {
  rank: number;
  product_id: string;
  bank_code: string;
  bank_name: string;
  product_name: string;
  product_type: string;
  metric_value: number | null;
  metric_unit: string;
  last_changed_at: string | null;
};

export type PublicDashboardRankingWidget = {
  ranking_key: string;
  title: string;
  metric_label: string;
  items: PublicDashboardRankingRow[];
  window_days?: number;
};

export type PublicDashboardRankingsResponse = {
  widgets: PublicDashboardRankingWidget[];
  availability_status: string;
  insufficiency_note: string | null;
  applied_filters: Record<string, unknown>;
  freshness: PublicFreshness;
};

export type PublicDashboardScatterAxis = {
  key: string;
  label: string;
  unit: string;
};

export type PublicDashboardScatterPoint = {
  product_id: string;
  bank_code: string;
  bank_name: string;
  product_name: string;
  product_type: string;
  x_value: number;
  y_value: number;
  highlight_badge_code: string | null;
};

export type PublicDashboardScatterResponse = {
  chart_key: string | null;
  title: string | null;
  x_axis: PublicDashboardScatterAxis | null;
  y_axis: PublicDashboardScatterAxis | null;
  points: PublicDashboardScatterPoint[];
  availability_status: string;
  insufficiency_note: string | null;
  methodology_note: string | null;
  applied_filters: Record<string, unknown>;
  freshness: PublicFreshness;
};

type PublicApiEnvelope<T> = {
  data: T;
};

export function getPublicApiOrigin() {
  return process.env.FPDS_PUBLIC_API_ORIGIN ?? "http://localhost:4000";
}

export async function fetchPublicProducts(searchParams: URLSearchParams): Promise<PublicProductsResponse> {
  return fetchPublicData<PublicProductsResponse>("/api/public/products", searchParams);
}

export async function fetchPublicFilters(searchParams: URLSearchParams): Promise<PublicFiltersResponse> {
  const payload = await fetchPublicData<{
    banks: Array<{ code: string; label: string; count: number }>;
    product_types: Array<{ code: string; label: string; count: number }>;
    subtypes: Array<{ code: string; label: string; count: number; product_type: string }>;
    target_customer_tags: Array<{ code: string; label: string; count: number }>;
    fee_buckets: Array<{ code: string; label: string; count: number }>;
    minimum_balance_buckets: Array<{ code: string; label: string; count: number }>;
    minimum_deposit_buckets: Array<{ code: string; label: string; count: number }>;
    term_buckets: Array<{ code: string; label: string; count: number }>;
    applied_filters: Record<string, unknown>;
    freshness: PublicFreshness;
  }>("/api/public/filters", searchParams);

  return {
    banks: payload.banks.map((option) => normalizeFilterOption(option)),
    product_types: payload.product_types.map((option) => normalizeFilterOption(option)),
    subtypes: payload.subtypes.map((option) => normalizeFilterOption(option, option.product_type)),
    target_customer_tags: payload.target_customer_tags.map((option) => normalizeFilterOption(option)),
    fee_buckets: payload.fee_buckets.map((option) => normalizeFilterOption(option)),
    minimum_balance_buckets: payload.minimum_balance_buckets.map((option) => normalizeFilterOption(option)),
    minimum_deposit_buckets: payload.minimum_deposit_buckets.map((option) => normalizeFilterOption(option)),
    term_buckets: payload.term_buckets.map((option) => normalizeFilterOption(option)),
    applied_filters: payload.applied_filters,
    freshness: payload.freshness
  };
}

export async function fetchPublicDashboardSummary(searchParams: URLSearchParams): Promise<PublicDashboardSummaryResponse> {
  return fetchPublicData<PublicDashboardSummaryResponse>("/api/public/dashboard-summary", searchParams);
}

export async function fetchPublicDashboardRankings(searchParams: URLSearchParams): Promise<PublicDashboardRankingsResponse> {
  return fetchPublicData<PublicDashboardRankingsResponse>("/api/public/dashboard-rankings", searchParams);
}

export async function fetchPublicDashboardScatter(searchParams: URLSearchParams): Promise<PublicDashboardScatterResponse> {
  return fetchPublicData<PublicDashboardScatterResponse>("/api/public/dashboard-scatter", searchParams);
}

async function fetchPublicData<T>(path: string, searchParams?: URLSearchParams): Promise<T> {
  const url = new URL(path, getPublicApiOrigin());
  if (searchParams) {
    url.search = searchParams.toString();
  }

  const response = await fetch(url, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Failed to load public data from ${path}.`);
  }

  const payload = (await response.json()) as PublicApiEnvelope<T>;
  return payload.data;
}

function normalizeFilterOption(
  option: { code: string; label: string; count: number },
  productType?: string
): PublicFilterOption {
  return {
    value: option.code,
    label: option.label,
    count: option.count,
    productType
  };
}
