import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { AdminApiUnavailable } from "@/components/fpds/admin/admin-api-unavailable";
import { SourceRegistrySurface, type SourceRegistryPageFilters } from "@/components/fpds/admin/source-registry-surface";
import { fetchAdminSession, fetchSourceRegistryList, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type SourceRegistryPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function SourceRegistryPage({ searchParams }: SourceRegistryPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  const filters = parsePageFilters(resolvedSearchParams);
  const apiSearchParams = buildApiSearchParams(filters);

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let registry: Awaited<ReturnType<typeof fetchSourceRegistryList>> = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) {
      registry = await fetchSourceRegistryList(apiSearchParams);
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/sources", new URLSearchParams(), locale))}`);
  }

  if (session && !registry && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/sources", new URLSearchParams(), locale))}`);
  }

  if (!session || !registry || apiUnavailable) {
    return <AdminApiUnavailable locale={locale} title="Source registry could not load." />;
  }

  return (
    <ApplicationShell5
      environmentLabel={process.env.NODE_ENV === "production" ? "Prod" : "Dev"}
      locale={locale}
      logoutApiOrigin={getAdminApiOrigin()}
      user={{
        name: session.user.display_name,
        loginId: session.user.login_id,
        role: session.user.role,
      }}
    >
      <SourceRegistrySurface filters={filters} locale={locale} registry={registry} />
    </ApplicationShell5>
  );
}

function parsePageFilters(searchParams: Record<string, string | string[] | undefined>): SourceRegistryPageFilters {
  return {
    q: firstValue(searchParams.q),
    bankCode: firstValue(searchParams.bank_code).toUpperCase(),
    countryCode: firstValue(searchParams.country_code).toUpperCase(),
    productType: firstValue(searchParams.product_type).toLowerCase(),
    status: firstValue(searchParams.status).toLowerCase(),
    discoveryRole: firstValue(searchParams.discovery_role).toLowerCase(),
  };
}

function buildApiSearchParams(filters: SourceRegistryPageFilters) {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.bankCode) params.set("bank_code", filters.bankCode);
  if (filters.countryCode) params.set("country_code", filters.countryCode);
  if (filters.productType) params.set("product_type", filters.productType);
  if (filters.status) params.set("status", filters.status);
  if (filters.discoveryRole) params.set("discovery_role", filters.discoveryRole);
  return params;
}

function firstValue(value: string | string[] | undefined) {
  if (Array.isArray(value)) {
    return value[0]?.trim() ?? "";
  }
  return value?.trim() ?? "";
}
