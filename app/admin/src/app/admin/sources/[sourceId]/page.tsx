import { notFound, redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { AdminApiUnavailable } from "@/components/fpds/admin/admin-api-unavailable";
import { SourceDetailSurface } from "@/components/fpds/admin/source-detail-surface";
import { fetchAdminSession, fetchSourceRegistryDetail, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

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
    return <AdminApiUnavailable title="Source detail could not load." />;
  }

  if (!detail) {
    notFound();
  }

  return (
    <ApplicationShell5
      environmentLabel={process.env.NODE_ENV === "production" ? "Prod" : "Dev"}
      locale={locale}
      logoutApiOrigin={getAdminApiOrigin()}
      user={{
        name: session.user.display_name,
        loginId: session.user.login_id,
        role: session.user.role,
      }}
    >
      <SourceDetailSurface csrfToken={session.csrf_token} detail={detail} locale={locale} userRole={session.user.role} />
    </ApplicationShell5>
  );
}
