import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { AdminApiUnavailable } from "@/components/fpds/admin/admin-api-unavailable";
import { HealthDashboardSurface } from "@/components/fpds/admin/health-dashboard-surface";
import { fetchAdminSession, fetchDashboardHealth, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type DashboardHealthPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function DashboardHealthPage({ searchParams }: DashboardHealthPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let health: Awaited<ReturnType<typeof fetchDashboardHealth>> = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) {
      health = await fetchDashboardHealth();
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/health/dashboard", new URLSearchParams(), locale))}`);
  }

  if (session && !health && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/health/dashboard", new URLSearchParams(), locale))}`);
  }

  if (!session || !health || apiUnavailable) {
    return <AdminApiUnavailable title="Dashboard health could not load." />;
  }

  const envLabel = process.env.NODE_ENV === "production" ? "Prod" : "Dev";

  return (
    <ApplicationShell5
      environmentLabel={envLabel}
      locale={locale}
      logoutApiOrigin={getAdminApiOrigin()}
      user={{
        name: session.user.display_name,
        loginId: session.user.login_id,
        role: session.user.role,
      }}
    >
      <HealthDashboardSurface csrfToken={session.csrf_token} health={health} />
    </ApplicationShell5>
  );
}
