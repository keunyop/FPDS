import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { RunStatusSurface, type RunStatusPageFilters } from "@/components/fpds/admin/run-status-surface";
import { fetchAdminSession, fetchRunStatusList, getAdminApiOrigin } from "@/lib/admin-api";

import { LogoutButton } from "../LogoutButton";

type RunStatusPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

const DEFAULT_STATES = ["started", "completed", "failed"];

export default async function RunStatusPage({ searchParams }: RunStatusPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parsePageFilters(resolvedSearchParams);
  const apiSearchParams = buildApiSearchParams(filters);

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let runs: Awaited<ReturnType<typeof fetchRunStatusList>> = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) {
      runs = await fetchRunStatusList(apiSearchParams);
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect("/admin/login?next=/admin/runs");
  }

  if (session && !runs && !apiUnavailable) {
    redirect("/admin/login?next=/admin/runs");
  }

  if (!session || !runs || apiUnavailable) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center px-4 py-8 md:px-6">
        <section className="w-full rounded-[1.75rem] border border-destructive/20 bg-card/95 p-6 shadow-sm md:p-8">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-destructive">Admin API unavailable</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
              Run diagnostics could not load because the admin API is not reachable.
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">
              Start the FastAPI service and refresh this page. The runs route now depends on the protected session
              contract and the new `/api/admin/runs` endpoint.
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
      headerActions={<LogoutButton apiOrigin={getAdminApiOrigin()} />}
      user={{
        name: session.user.display_name,
        email: session.user.email,
        role: session.user.role,
      }}
    >
      <RunStatusSurface filters={filters} runs={runs} />
    </ApplicationShell5>
  );
}

function parsePageFilters(searchParams: Record<string, string | string[] | undefined>): RunStatusPageFilters {
  return {
    q: firstValue(searchParams.q),
    states: multiValue(searchParams.state, DEFAULT_STATES),
    runType: firstValue(searchParams.run_type).toLowerCase(),
    partialOnly: firstValue(searchParams.partial_only).toLowerCase() === "true",
    startedFrom: firstValue(searchParams.started_from),
    startedTo: firstValue(searchParams.started_to),
    sortBy: firstValue(searchParams.sort_by) || "started_at",
    sortOrder: firstValue(searchParams.sort_order) === "asc" ? "asc" : "desc",
    page: positiveInteger(firstValue(searchParams.page)) ?? 1,
  };
}

function buildApiSearchParams(filters: RunStatusPageFilters) {
  const params = new URLSearchParams();
  for (const state of filters.states) {
    params.append("state", state);
  }
  if (filters.q) {
    params.set("q", filters.q);
  }
  if (filters.runType) {
    params.set("run_type", filters.runType);
  }
  if (filters.partialOnly) {
    params.set("partial_only", "true");
  }
  if (filters.startedFrom) {
    params.set("started_from", `${filters.startedFrom}T00:00:00Z`);
  }
  if (filters.startedTo) {
    params.set("started_to", `${filters.startedTo}T23:59:59.999Z`);
  }
  params.set("sort_by", filters.sortBy);
  params.set("sort_order", filters.sortOrder);
  params.set("page", String(filters.page));
  return params;
}

function firstValue(value: string | string[] | undefined) {
  if (Array.isArray(value)) {
    return value[0]?.trim() ?? "";
  }
  return value?.trim() ?? "";
}

function multiValue(value: string | string[] | undefined, fallback: string[]) {
  if (Array.isArray(value)) {
    const normalized = value.map((item) => item.trim().toLowerCase()).filter(Boolean);
    return normalized.length ? normalized : fallback;
  }
  if (typeof value === "string" && value.trim()) {
    return [value.trim().toLowerCase()];
  }
  return fallback;
}

function positiveInteger(value: string) {
  if (!value) {
    return null;
  }
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed < 1) {
    return null;
  }
  return parsed;
}
