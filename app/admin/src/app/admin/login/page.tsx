import { redirect } from "next/navigation";

import { Login2 } from "@/components/login2";
import { fetchAdminSession, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type LoginPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const nextParam = Array.isArray(resolvedSearchParams.next)
    ? resolvedSearchParams.next[0]
    : resolvedSearchParams.next;
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

  return <Login2 apiOrigin={getAdminApiOrigin()} locale={locale} nextPath={nextParam ?? buildAdminHref("/admin", new URLSearchParams(), locale)} />;
}
