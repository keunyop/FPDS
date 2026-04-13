import { notFound, redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { RunDetailSurface } from "@/components/fpds/admin/run-detail-surface";
import { fetchAdminSession, fetchRunStatusDetail, getAdminApiOrigin } from "@/lib/admin-api";

import { LogoutButton } from "../../LogoutButton";

type RunDetailPageProps = {
  params: Promise<{
    runId: string;
  }>;
};

export default async function RunDetailPage({ params }: RunDetailPageProps) {
  const { runId } = await params;

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
    redirect(`/admin/login?next=/admin/runs/${runId}`);
  }

  if (!session || apiUnavailable) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center px-4 py-8 md:px-6">
        <section className="w-full rounded-[1.75rem] border border-destructive/20 bg-card/95 p-6 shadow-sm md:p-8">
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-destructive">Admin API unavailable</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
            Run detail could not load because the admin API is not reachable.
          </h1>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            Start the FastAPI admin service and refresh this page. The run detail route now depends on the protected
            runs endpoints.
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
      headerActions={<LogoutButton apiOrigin={getAdminApiOrigin()} />}
      user={{
        name: session.user.display_name,
        email: session.user.email,
        role: session.user.role,
      }}
    >
      <RunDetailSurface detail={detail} />
    </ApplicationShell5>
  );
}
