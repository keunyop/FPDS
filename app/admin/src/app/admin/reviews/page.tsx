import { redirect } from "next/navigation";

import { AdminShell } from "@/components/fpds/admin/admin-shell";
import { AdminApiUnavailable } from "@/components/fpds/admin/admin-api-unavailable";
import { ReviewQueueSurface } from "@/components/fpds/admin/review-queue-surface";
import { fetchAdminSession, fetchBankList, fetchProductTypeList, fetchReviewQueue, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";
import { buildReviewQueueApiSearchParams, parseReviewQueueFilters } from "@/lib/review-queue-query";

type ReviewQueuePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function ReviewQueuePage({ searchParams }: ReviewQueuePageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  const filters = parseReviewQueueFilters(resolvedSearchParams);
  const apiSearchParams = buildReviewQueueApiSearchParams(filters);

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let queue: Awaited<ReturnType<typeof fetchReviewQueue>> = null;
  let productTypeList: Awaited<ReturnType<typeof fetchProductTypeList>> | null = null;
  let bankList: Awaited<ReturnType<typeof fetchBankList>> | null = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) {
      const bankSearchParams = new URLSearchParams({ status: "active" });
      [queue, productTypeList, bankList] = await Promise.all([
        fetchReviewQueue(apiSearchParams),
        fetchProductTypeList(),
        fetchBankList(bankSearchParams),
      ]);
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/reviews", new URLSearchParams(), locale))}`);
  }

  if (session && !queue && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/reviews", new URLSearchParams(), locale))}`);
  }

  if (!session || !queue || !productTypeList || !bankList || apiUnavailable) {
    return <AdminApiUnavailable locale={locale} title={locale === "ko" ? "검토 대기열을 불러올 수 없습니다." : locale === "ja" ? "レビューキューを読み込めません。" : "Review queue could not load."} />;
  }

  const envLabel = process.env.NODE_ENV === "production" ? "Prod" : "Dev";
  return (
    <AdminShell
      countryCode={session.country_code}
      csrfToken={session.csrf_token}
      environmentLabel={envLabel}
      locale={locale}
      logoutApiOrigin={getAdminApiOrigin()}
      user={{
        name: session.user.display_name,
        loginId: session.user.login_id,
        role: session.user.role,
      }}
    >
      <ReviewQueueSurface
        banks={bankList.items}
        csrfToken={session.csrf_token}
        filters={filters}
        locale={locale}
        productTypes={productTypeList.items}
        queue={queue}
      />
    </AdminShell>
  );
}
