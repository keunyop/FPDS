import { redirect } from "next/navigation";

import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type BankDetailPageProps = {
  params: Promise<{ bankCode: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function BankDetailPage({ params, searchParams }: BankDetailPageProps) {
  const { bankCode } = await params;
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  const redirectParams = new URLSearchParams();

  redirectParams.set("bank", bankCode);
  redirect(buildAdminHref("/admin/banks", redirectParams, locale));
}
