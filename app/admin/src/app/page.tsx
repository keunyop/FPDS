import { redirect } from "next/navigation";

import { resolveAdminLocale } from "@/lib/admin-i18n";

type HomePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function HomePage({ searchParams }: HomePageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  redirect(locale === "en" ? "/admin" : `/admin?locale=${locale}`);
}
