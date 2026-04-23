import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { BankRegistrySurface, type BankRegistryPageFilters } from "@/components/fpds/admin/bank-registry-surface";
import { fetchAdminSession, fetchBankDetail, fetchBankList, fetchProductTypeList, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

import { LogoutButton } from "../LogoutButton";

type BankRegistryPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function BankRegistryPage({ searchParams }: BankRegistryPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  const filters = parsePageFilters(resolvedSearchParams);
  const apiSearchParams = buildApiSearchParams(filters);
  const activeBankCode = firstValue(resolvedSearchParams.bank) || null;
  const addModalOpen = firstValue(resolvedSearchParams.modal).toLowerCase() === "add";

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let banks: Awaited<ReturnType<typeof fetchBankList>> = null;
  let activeBankDetail: Awaited<ReturnType<typeof fetchBankDetail>> = null;
  let productTypes: Awaited<ReturnType<typeof fetchProductTypeList>> = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) {
      banks = await fetchBankList(apiSearchParams);
      productTypes = await fetchProductTypeList();
      if (activeBankCode) {
        activeBankDetail = await fetchBankDetail(activeBankCode);
      }
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/banks", new URLSearchParams(), locale))}`);
  }

  if (!session || !banks || !productTypes || apiUnavailable) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center px-4 py-8 md:px-6">
        <section className="w-full rounded-[1.75rem] border border-destructive/20 bg-card/95 p-6 shadow-sm md:p-8">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-destructive">Admin API unavailable</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
              Bank registry could not load because the admin API is not reachable.
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
        email: session.user.email ?? session.user.login_id,
        role: session.user.role,
      }}
    >
      <BankRegistrySurface
        activeBankCode={activeBankCode}
        activeBankDetail={activeBankDetail}
        addModalOpen={addModalOpen}
        banks={banks}
        csrfToken={session.csrf_token}
        filters={filters}
        locale={locale}
        productTypes={productTypes.items}
      />
    </ApplicationShell5>
  );
}

function parsePageFilters(searchParams: Record<string, string | string[] | undefined>): BankRegistryPageFilters {
  return {
    q: firstValue(searchParams.q),
    status: firstValue(searchParams.status).toLowerCase(),
  };
}

function buildApiSearchParams(filters: BankRegistryPageFilters) {
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
