import { notFound, redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { ReviewDetailSurface } from "@/components/fpds/admin/review-detail-surface";
import { fetchAdminSession, fetchReviewTaskDetail, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

import { LogoutButton } from "../../LogoutButton";

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
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center px-4 py-8 md:px-6">
        <section className="w-full rounded-[1.75rem] border border-destructive/20 bg-card/95 p-6 shadow-sm md:p-8">
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-destructive">Admin API unavailable</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
            Review detail could not load because the admin API is not reachable.
          </h1>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            Start the FastAPI admin service and refresh this page. The review detail route now depends on the protected
            review-task detail and decision endpoints.
          </p>
        </section>
      </main>
    );
  }

  if (!detail) {
    notFound();
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
      <ReviewDetailSurface csrfToken={session.csrf_token} detail={detail} />
    </ApplicationShell5>
  );
}
