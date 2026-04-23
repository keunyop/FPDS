import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { HealthDashboardSurface } from "@/components/fpds/admin/health-dashboard-surface";
import { fetchAdminSession, fetchDashboardHealth, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

import { LogoutButton } from "../../LogoutButton";

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
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center px-4 py-8 md:px-6">
        <section className="w-full rounded-[1.75rem] border border-destructive/20 bg-card/95 p-6 shadow-sm md:p-8">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-destructive">Admin API unavailable</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
              Dashboard health could not load because the admin API is not reachable.
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">
              Start the FastAPI service and refresh this page. The health route depends on the protected session
              contract and the `/api/admin/dashboard-health` endpoint.
            </p>
          </div>
        </section>
      </main>
    );
  }

  const envLabel = process.env.NODE_ENV === "production" ? "Prod" : "Dev";

  return (
    <ApplicationShell5
      environmentLabel={envLabel}
      locale={locale}
      headerActions={<LogoutButton apiOrigin={getAdminApiOrigin()} />}
      user={{
        name: session.user.display_name,
        email: session.user.email ?? session.user.login_id,
        role: session.user.role,
      }}
    >
      <HealthDashboardSurface csrfToken={session.csrf_token} health={health} />
    </ApplicationShell5>
  );
}
