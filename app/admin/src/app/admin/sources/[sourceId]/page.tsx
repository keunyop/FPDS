import { notFound, redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { SourceDetailSurface } from "@/components/fpds/admin/source-detail-surface";
import { fetchAdminSession, fetchSourceRegistryDetail, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

import { LogoutButton } from "../../LogoutButton";

type SourceDetailPageProps = {
  params: Promise<{ sourceId: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function SourceDetailPage({ params, searchParams }: SourceDetailPageProps) {
  const { sourceId } = await params;
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let detail: Awaited<ReturnType<typeof fetchSourceRegistryDetail>> = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) {
      detail = await fetchSourceRegistryDetail(sourceId);
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref(`/admin/sources/${sourceId}`, new URLSearchParams(), locale))}`);
  }

  if (!session || apiUnavailable) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center px-4 py-8 md:px-6">
        <section className="w-full rounded-[1.75rem] border border-destructive/20 bg-card/95 p-6 shadow-sm md:p-8">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-destructive">Admin API unavailable</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
              Source detail could not load because the admin API is not reachable.
            </h1>
          </div>
        </section>
      </main>
    );
  }

  if (!detail) {
    notFound();
  }

  return (
    <ApplicationShell5
      environmentLabel={process.env.NODE_ENV === "production" ? "Prod" : "Dev"}
      locale={locale}
      headerActions={<LogoutButton apiOrigin={getAdminApiOrigin()} />}
      user={{
        name: session.user.display_name,
        email: session.user.email,
        role: session.user.role,
      }}
    >
      <SourceDetailSurface detail={detail} locale={locale} />
    </ApplicationShell5>
  );
}
