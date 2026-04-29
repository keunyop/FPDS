import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { AdminApiUnavailable } from "@/components/fpds/admin/admin-api-unavailable";
import {
  ChangeHistorySurface,
  type ChangeHistoryPageFilters,
} from "@/components/fpds/admin/change-history-surface";
import { fetchAdminSession, fetchChangeHistoryList, fetchProductTypeList, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type ChangeHistoryPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function ChangeHistoryPage({ searchParams }: ChangeHistoryPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  const filters = parsePageFilters(resolvedSearchParams);
  const apiSearchParams = buildApiSearchParams(filters);

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let changes: Awaited<ReturnType<typeof fetchChangeHistoryList>> = null;
  let productTypeList: Awaited<ReturnType<typeof fetchProductTypeList>> | null = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) {
      [changes, productTypeList] = await Promise.all([
        fetchChangeHistoryList(apiSearchParams),
        fetchProductTypeList(),
      ]);
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/changes", new URLSearchParams(), locale))}`);
  }

  if (session && !changes && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/changes", new URLSearchParams(), locale))}`);
  }

  if (!session || !changes || !productTypeList || apiUnavailable) {
    return <AdminApiUnavailable locale={locale} title="Change history could not load." />;
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
      <ChangeHistorySurface changes={changes} filters={filters} locale={locale} productTypes={productTypeList.items} />
    </ApplicationShell5>
  );
}

function parsePageFilters(searchParams: Record<string, string | string[] | undefined>): ChangeHistoryPageFilters {
  return {
    q: firstValue(searchParams.q),
    bankCode: firstValue(searchParams.bank_code).toUpperCase(),
    productType: firstValue(searchParams.product_type).toLowerCase(),
    changeType: firstValue(searchParams.change_type),
    changedFrom: firstValue(searchParams.changed_from),
    changedTo: firstValue(searchParams.changed_to),
    sortBy: firstValue(searchParams.sort_by) || "detected_at",
    sortOrder: firstValue(searchParams.sort_order) === "asc" ? "asc" : "desc",
    page: positiveInteger(firstValue(searchParams.page)) ?? 1,
  };
}

function buildApiSearchParams(filters: ChangeHistoryPageFilters) {
  const params = new URLSearchParams();
  if (filters.q) {
    params.set("q", filters.q);
  }
  if (filters.bankCode) {
    params.set("bank_code", filters.bankCode);
  }
  if (filters.productType) {
    params.set("product_type", filters.productType);
  }
  if (filters.changeType) {
    params.set("change_type", filters.changeType);
  }
  if (filters.changedFrom) {
    params.set("changed_from", `${filters.changedFrom}T00:00:00Z`);
  }
  if (filters.changedTo) {
    params.set("changed_to", `${filters.changedTo}T23:59:59.999Z`);
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
