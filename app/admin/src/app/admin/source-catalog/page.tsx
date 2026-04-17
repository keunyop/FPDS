import { redirect } from "next/navigation";

import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type SourceCatalogPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function SourceCatalogPage({ searchParams }: SourceCatalogPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  const bankCode = firstValue(resolvedSearchParams.bank_code).toUpperCase();
  const params = new URLSearchParams();

  if (bankCode) {
    params.set("bank", bankCode);
  }

  redirect(buildAdminHref("/admin/banks", params, locale));
}

function firstValue(value: string | string[] | undefined) {
  if (Array.isArray(value)) {
    return value[0]?.trim() ?? "";
  }
  return value?.trim() ?? "";
}
