import { notFound, redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { AdminApiUnavailable } from "@/components/fpds/admin/admin-api-unavailable";
import { RunDetailSurface } from "@/components/fpds/admin/run-detail-surface";
import { fetchAdminSession, fetchRunStatusDetail, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type RunDetailPageProps = {
  params: Promise<{
    runId: string;
  }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function RunDetailPage({ params, searchParams }: RunDetailPageProps) {
  const { runId } = await params;
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let detail: Awaited<ReturnType<typeof fetchRunStatusDetail>> = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) {
      detail = await fetchRunStatusDetail(runId);
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref(`/admin/runs/${runId}`, new URLSearchParams(), locale))}`);
  }

  if (!session || apiUnavailable) {
    return <AdminApiUnavailable locale={locale} title={locale === "ko" ? "실행 상세를 불러올 수 없습니다." : locale === "ja" ? "実行詳細を読み込めません。" : "Run detail could not load."} />;
  }

  if (!detail) {
    notFound();
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
      <RunDetailSurface csrfToken={session.csrf_token} detail={detail} locale={locale} />
    </ApplicationShell5>
  );
}
