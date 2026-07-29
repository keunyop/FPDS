import { notFound, redirect } from "next/navigation";

import { AdminShell } from "@/components/fpds/admin/admin-shell";
import { AdminApiUnavailable } from "@/components/fpds/admin/admin-api-unavailable";
import { ReviewDetailSurface } from "@/components/fpds/admin/review-detail-surface";
import { fetchAdminSession, fetchReviewTaskDetail, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type ReviewDetailPageProps = {
  params: Promise<{
    reviewTaskId: string;
  }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function ReviewDetailPage({ params, searchParams }: ReviewDetailPageProps) {
  const { reviewTaskId } = await params;
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let detail: Awaited<ReturnType<typeof fetchReviewTaskDetail>> = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) {
      detail = await fetchReviewTaskDetail(reviewTaskId);
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref(`/admin/reviews/${reviewTaskId}`, new URLSearchParams(), locale))}`);
  }

  if (!session || apiUnavailable) {
    const unavailableTitle = {
      en: "Review detail could not load.",
      ko: "검토 상세를 불러오지 못했습니다.",
      ja: "レビュー詳細を読み込めませんでした。",
    }[locale];
    return <AdminApiUnavailable title={unavailableTitle} />;
  }

  if (!detail) {
    notFound();
  }

  const envLabel = process.env.NODE_ENV === "production" ? "Prod" : "Dev";
  return (
    <AdminShell
      environmentLabel={envLabel}
      locale={locale}
      logoutApiOrigin={getAdminApiOrigin()}
      user={{
        name: session.user.display_name,
        loginId: session.user.login_id,
        role: session.user.role,
      }}
    >
      <ReviewDetailSurface csrfToken={session.csrf_token} detail={detail} locale={locale} />
    </AdminShell>
  );
}
