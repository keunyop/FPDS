import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { AdminApiUnavailable } from "@/components/fpds/admin/admin-api-unavailable";
import { BankRegistrySurface, type BankRegistryPageFilters } from "@/components/fpds/admin/bank-registry-surface";
import { fetchAdminSession, fetchBankDetail, fetchBankList, fetchProductTypeList, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

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
    return <AdminApiUnavailable title="Bank registry could not load." />;
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
