import { redirect } from "next/navigation";

import { AdminApiUnavailable } from "@/components/fpds/admin/admin-api-unavailable";
import { AdminShell } from "@/components/fpds/admin/admin-shell";
import { CountryRegistrySurface } from "@/components/fpds/admin/country-registry-surface";
import { fetchAdminSession, fetchCountryRegistry, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type CountriesPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function CountriesPage({ searchParams }: CountriesPageProps) {
  const locale = resolveAdminLocale((await searchParams) ?? {});
  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let countryRegistry: Awaited<ReturnType<typeof fetchCountryRegistry>> = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session?.user.role.toLowerCase() === "admin") {
      countryRegistry = await fetchCountryRegistry();
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/countries", new URLSearchParams(), locale))}`);
  }
  if (session && session.user.role.toLowerCase() !== "admin") {
    redirect(buildAdminHref("/admin", new URLSearchParams(), locale));
  }
  if (!session || !countryRegistry || apiUnavailable) {
    const title = locale === "ko"
      ? "\uAD6D\uAC00 \uC124\uC815\uC744 \uBD88\uB7EC\uC624\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4."
      : locale === "ja"
        ? "\u56FD\u306E\u8A2D\u5B9A\u3092\u8AAD\u307F\u8FBC\u3081\u307E\u305B\u3093\u3067\u3057\u305F\u3002"
        : "Country settings could not load.";
    return <AdminApiUnavailable locale={locale} title={title} />;
  }

  return (
    <AdminShell
      countryCode={session.country_code}
      csrfToken={session.csrf_token}
      environmentLabel={process.env.NODE_ENV === "production" ? "Prod" : "Dev"}
      locale={locale}
      logoutApiOrigin={getAdminApiOrigin()}
      user={{
        name: session.user.display_name,
        loginId: session.user.login_id,
        role: session.user.role,
      }}
    >
      <CountryRegistrySurface
        countryRegistry={countryRegistry}
        csrfToken={session.csrf_token}
        currentCountryCode={session.country_code}
        locale={locale}
      />
    </AdminShell>
  );
}
