import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { SourceRegistrySurface, type SourceRegistryPageFilters } from "@/components/fpds/admin/source-registry-surface";
import { fetchAdminSession, fetchSourceRegistryList, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

import { LogoutButton } from "../LogoutButton";

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
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center px-4 py-8 md:px-6">
        <section className="w-full rounded-[1.75rem] border border-destructive/20 bg-card/95 p-6 shadow-sm md:p-8">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-destructive">Admin API unavailable</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
              Source registry could not load because the admin API is not reachable.
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">
              Start the FastAPI service and refresh this page. The source registry route depends on the protected admin
              API before it can render live source management or collection actions.
            </p>
          </div>
        </section>
      </main>
    );
  }

  return (
    <ApplicationShell5
      environmentLabel={process.env.NODE_ENV === "production" ? "Prod" : "Dev"}
      locale={locale}
      headerActions={<LogoutButton apiOrigin={getAdminApiOrigin()} />}
      user={{
        name: session.user.display_name,
        email: session.user.email ?? session.user.login_id,
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
