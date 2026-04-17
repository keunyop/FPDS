import { redirect } from "next/navigation";

import { fetchSourceCatalogDetail } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type SourceCatalogDetailPageProps = {
  params: Promise<{ catalogItemId: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function SourceCatalogDetailPage({
  params,
  searchParams,
}: SourceCatalogDetailPageProps) {
  const { catalogItemId } = await params;
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  let detail: Awaited<ReturnType<typeof fetchSourceCatalogDetail>> = null;
  try {
    detail = await fetchSourceCatalogDetail(catalogItemId);
  } catch {
    detail = null;
  }
  const redirectParams = new URLSearchParams();

  if (detail?.catalog_item.bank_code) {
    redirectParams.set("bank", detail.catalog_item.bank_code);
  }

  redirect(buildAdminHref("/admin/banks", redirectParams, locale));
}
