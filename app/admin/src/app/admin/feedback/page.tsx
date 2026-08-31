import { redirect } from "next/navigation";

import { AdminApiUnavailable } from "@/components/fpds/admin/admin-api-unavailable";
import { AdminShell } from "@/components/fpds/admin/admin-shell";
import {
  FeedbackInboxSurface,
  type FeedbackInboxPageFilters,
} from "@/components/fpds/admin/feedback-inbox-surface";
import {
  fetchAdminSession,
  fetchPublicFeedbackList,
  getAdminApiOrigin,
} from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type FeedbackPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

const SUBMISSION_TYPES = new Set(["product_error", "site_feedback"]);
const CATEGORIES = new Set([
  "accessibility_issue",
  "broken_link",
  "content_issue",
  "feature_suggestion",
  "incorrect_product_details",
  "incorrect_rate_or_fee",
  "missing_information",
  "other",
  "outdated_information",
  "usability_issue",
]);

export default async function FeedbackPage({ searchParams }: FeedbackPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  const filters = parsePageFilters(resolvedSearchParams);
  const apiSearchParams = buildApiSearchParams(filters);
  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let feedback: Awaited<ReturnType<typeof fetchPublicFeedbackList>> = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) feedback = await fetchPublicFeedbackList(apiSearchParams);
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect("/admin/login?next=" + encodeURIComponent(buildAdminHref("/admin/feedback", new URLSearchParams(), locale)));
  }

  if (session && !feedback && !apiUnavailable) {
    redirect("/admin/login?next=" + encodeURIComponent(buildAdminHref("/admin/feedback", new URLSearchParams(), locale)));
  }

  if (!session || !feedback || apiUnavailable) {
    const title = locale === "ko"
      ? "피드백을 불러올 수 없습니다."
      : locale === "ja"
        ? "フィードバックを読み込めません。"
        : "Feedback could not load.";
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
      <FeedbackInboxSurface feedback={feedback} filters={filters} locale={locale} />
    </AdminShell>
  );
}

function parsePageFilters(searchParams: Record<string, string | string[] | undefined>): FeedbackInboxPageFilters {
  const submissionType = firstValue(searchParams.submission_type).toLowerCase();
  const category = firstValue(searchParams.category).toLowerCase();
  return {
    category: CATEGORIES.has(category) ? category : "",
    page: positiveInteger(firstValue(searchParams.page)) ?? 1,
    q: firstValue(searchParams.q),
    submissionType: SUBMISSION_TYPES.has(submissionType) ? submissionType : "",
  };
}

function buildApiSearchParams(filters: FeedbackInboxPageFilters) {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.submissionType) params.set("submission_type", filters.submissionType);
  if (filters.category) params.set("category", filters.category);
  params.set("page", String(filters.page));
  params.set("page_size", "50");
  return params;
}

function firstValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0]?.trim() ?? "" : value?.trim() ?? "";
}

function positiveInteger(value: string) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed >= 1 ? parsed : null;
}
