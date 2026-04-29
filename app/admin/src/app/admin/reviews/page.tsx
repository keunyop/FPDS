import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { AdminApiUnavailable } from "@/components/fpds/admin/admin-api-unavailable";
import { ReviewQueueSurface, type ReviewQueuePageFilters } from "@/components/fpds/admin/review-queue-surface";
import { fetchAdminSession, fetchProductTypeList, fetchReviewQueue, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type ReviewQueuePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

const DEFAULT_STATES = ["queued", "deferred"];

export default async function ReviewQueuePage({ searchParams }: ReviewQueuePageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  const filters = parsePageFilters(resolvedSearchParams);
  const apiSearchParams = buildApiSearchParams(filters);

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let queue: Awaited<ReturnType<typeof fetchReviewQueue>> = null;
  let productTypeList: Awaited<ReturnType<typeof fetchProductTypeList>> | null = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) {
      [queue, productTypeList] = await Promise.all([
        fetchReviewQueue(apiSearchParams),
        fetchProductTypeList(),
      ]);
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/reviews", new URLSearchParams(), locale))}`);
  }

  if (session && !queue && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/reviews", new URLSearchParams(), locale))}`);
  }

  if (!session || !queue || !productTypeList || apiUnavailable) {
    return <AdminApiUnavailable locale={locale} title="Review queue could not load." />;
  }

  const envLabel = process.env.NODE_ENV === "production" ? "Prod" : "Dev";
  return (
    <ApplicationShell5
      environmentLabel={envLabel}
      locale={locale}
      logoutApiOrigin={getAdminApiOrigin()}
      user={{
        name: session.user.display_name,
        loginId: session.user.login_id,
        role: session.user.role,
      }}
    >
      <ReviewQueueSurface filters={filters} locale={locale} productTypes={productTypeList.items} queue={queue} />
    </ApplicationShell5>
  );
}

function parsePageFilters(searchParams: Record<string, string | string[] | undefined>): ReviewQueuePageFilters {
  return {
    q: firstValue(searchParams.q),
    states: multiValue(searchParams.state, DEFAULT_STATES),
    bankCode: firstValue(searchParams.bank_code).toUpperCase(),
    productType: firstValue(searchParams.product_type).toLowerCase(),
    validationStatus: firstValue(searchParams.validation_status).toLowerCase(),
    createdFrom: firstValue(searchParams.created_from),
    createdTo: firstValue(searchParams.created_to),
    sortBy: firstValue(searchParams.sort_by) || "priority",
    sortOrder: firstValue(searchParams.sort_order) === "asc" ? "asc" : "desc",
    page: positiveInteger(firstValue(searchParams.page)) ?? 1,
  };
}

function buildApiSearchParams(filters: ReviewQueuePageFilters) {
  const params = new URLSearchParams();
  for (const state of filters.states) {
    params.append("state", state);
  }
  if (filters.q) {
    params.set("q", filters.q);
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
  if (filters.createdFrom) {
    params.set("created_from", `${filters.createdFrom}T00:00:00Z`);
  }
  if (filters.createdTo) {
    params.set("created_to", `${filters.createdTo}T23:59:59.999Z`);
  }
  params.set("sort_by", filters.sortBy);
  params.set("sort_order", filters.sortOrder);
  params.set("page", String(filters.page));
  return params;
}

function firstValue(value: string | string[] | undefined) {
  if (Array.isArray(value)) {
    return value[0]?.trim() ?? "";
  }
  return value?.trim() ?? "";
}

function multiValue(value: string | string[] | undefined, fallback: string[]) {
  if (Array.isArray(value)) {
    const normalized = value.map((item) => item.trim().toLowerCase()).filter(Boolean);
    return normalized.length ? normalized : fallback;
  }
  if (typeof value === "string" && value.trim()) {
    return [value.trim().toLowerCase()];
  }
  return fallback;
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
