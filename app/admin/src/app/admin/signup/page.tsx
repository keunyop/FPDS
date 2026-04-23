import { redirect } from "next/navigation";

import { SignupRequestForm } from "@/components/signup-request-form";
import { fetchAdminSession, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type SignupPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function SignupPage({ searchParams }: SignupPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;

  try {
    session = await fetchAdminSession();
  } catch {
    session = null;
  }

  if (session) {
    redirect(buildAdminHref("/admin", new URLSearchParams(), locale));
  }

  return <SignupRequestForm apiOrigin={getAdminApiOrigin()} locale={locale} />;
}
