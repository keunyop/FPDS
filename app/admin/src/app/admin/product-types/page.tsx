import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import {
  ProductTypeRegistrySurface,
  type ProductTypePageFilters,
} from "@/components/fpds/admin/product-type-registry-surface";
import { fetchAdminSession, fetchProductTypeDetail, fetchProductTypeList, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

import { LogoutButton } from "../LogoutButton";

type ProductTypePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function ProductTypePage({ searchParams }: ProductTypePageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  const filters = parsePageFilters(resolvedSearchParams);
  const apiSearchParams = buildApiSearchParams(filters);
  const addModalOpen = firstValue(resolvedSearchParams.modal).toLowerCase() === "add";
  const activeProductTypeCode = firstValue(resolvedSearchParams.productType);

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let productTypes: Awaited<ReturnType<typeof fetchProductTypeList>> = null;
  let activeProductType: Awaited<ReturnType<typeof fetchProductTypeDetail>> = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) {
      productTypes = await fetchProductTypeList(apiSearchParams);
      if (activeProductTypeCode) {
        activeProductType = await fetchProductTypeDetail(activeProductTypeCode);
      }
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/product-types", new URLSearchParams(), locale))}`);
  }

  if (!session || !productTypes || apiUnavailable) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center px-4 py-8 md:px-6">
        <section className="w-full rounded-[1.75rem] border border-destructive/20 bg-card/95 p-6 shadow-sm md:p-8">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-destructive">Admin API unavailable</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
              Product type registry could not load because the admin API is not reachable.
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
      <ProductTypeRegistrySurface
        activeProductType={activeProductType}
        activeProductTypeCode={activeProductTypeCode || null}
        addModalOpen={addModalOpen}
        csrfToken={session.csrf_token}
        filters={filters}
        locale={locale}
        productTypes={productTypes}
      />
    </ApplicationShell5>
  );
}

function parsePageFilters(searchParams: Record<string, string | string[] | undefined>): ProductTypePageFilters {
  return {
    q: firstValue(searchParams.q),
    status: firstValue(searchParams.status).toLowerCase(),
  };
}

function buildApiSearchParams(filters: ProductTypePageFilters) {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.status) params.set("status", filters.status);
  return params;
}

function firstValue(value: string | string[] | undefined) {
  if (Array.isArray(value)) {
    return value[0]?.trim() ?? "";
  }
  return value?.trim() ?? "";
}
