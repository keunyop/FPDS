import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { SourceCatalogSurface, type SourceCatalogPageFilters } from "@/components/fpds/admin/source-catalog-surface";
import { fetchAdminSession, fetchSourceCatalogDetail, fetchSourceCatalogList, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

import { LogoutButton } from "../LogoutButton";

type SourceCatalogPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function SourceCatalogPage({ searchParams }: SourceCatalogPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  const filters = parsePageFilters(resolvedSearchParams);
  const apiSearchParams = buildApiSearchParams(filters);
  const activeCatalogItemId = firstValue(resolvedSearchParams.catalog) || null;
  const addModalOpen = firstValue(resolvedSearchParams.modal).toLowerCase() === "add";

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let catalog: Awaited<ReturnType<typeof fetchSourceCatalogList>> = null;
  let activeCatalogDetail: Awaited<ReturnType<typeof fetchSourceCatalogDetail>> = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) {
      catalog = await fetchSourceCatalogList(apiSearchParams);
      if (activeCatalogItemId) {
        activeCatalogDetail = await fetchSourceCatalogDetail(activeCatalogItemId);
      }
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/source-catalog", new URLSearchParams(), locale))}`);
  }

  if (!session || !catalog || apiUnavailable) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center px-4 py-8 md:px-6">
        <section className="w-full rounded-[1.75rem] border border-destructive/20 bg-card/95 p-6 shadow-sm md:p-8">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-destructive">Admin API unavailable</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
              Source catalog could not load because the admin API is not reachable.
            </h1>
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
        email: session.user.email,
        role: session.user.role,
      }}
    >
      <SourceCatalogSurface
        activeCatalogDetail={activeCatalogDetail}
        activeCatalogItemId={activeCatalogItemId}
        addModalOpen={addModalOpen}
        catalog={catalog}
        csrfToken={session.csrf_token}
        filters={filters}
        locale={locale}
      />
    </ApplicationShell5>
  );
}

function parsePageFilters(searchParams: Record<string, string | string[] | undefined>): SourceCatalogPageFilters {
  return {
    q: firstValue(searchParams.q),
    bankCode: firstValue(searchParams.bank_code).toUpperCase(),
    productType: firstValue(searchParams.product_type).toLowerCase(),
    status: firstValue(searchParams.status).toLowerCase(),
  };
}

function buildApiSearchParams(filters: SourceCatalogPageFilters) {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.bankCode) params.set("bank_code", filters.bankCode);
  if (filters.productType) params.set("product_type", filters.productType);
  if (filters.status) params.set("status", filters.status);
  return params;
}

function firstValue(value: string | string[] | undefined) {
  if (Array.isArray(value)) {
    return value[0]?.trim() ?? "";
  }
  return value?.trim() ?? "";
}
