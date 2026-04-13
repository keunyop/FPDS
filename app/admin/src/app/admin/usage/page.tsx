import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { LlmUsageSurface, type LlmUsagePageFilters } from "@/components/fpds/admin/llm-usage-surface";
import { fetchAdminSession, fetchLlmUsage, getAdminApiOrigin } from "@/lib/admin-api";

import { LogoutButton } from "../LogoutButton";

type LlmUsagePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function LlmUsagePage({ searchParams }: LlmUsagePageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parsePageFilters(resolvedSearchParams);
  const apiSearchParams = buildApiSearchParams(filters);

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let usage: Awaited<ReturnType<typeof fetchLlmUsage>> = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) {
      usage = await fetchLlmUsage(apiSearchParams);
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect("/admin/login?next=/admin/usage");
  }

  if (session && !usage && !apiUnavailable) {
    redirect("/admin/login?next=/admin/usage");
  }

  if (!session || !usage || apiUnavailable) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center px-4 py-8 md:px-6">
        <section className="w-full rounded-[1.75rem] border border-destructive/20 bg-card/95 p-6 shadow-sm md:p-8">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-destructive">Admin API unavailable</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
              LLM usage visibility could not load because the admin API is not reachable.
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">
              Start the FastAPI service and refresh this page. The usage route depends on the protected session
              contract and the `/api/admin/llm-usage` endpoint.
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
      <LlmUsageSurface filters={filters} usage={usage} />
    </ApplicationShell5>
  );
}

function parsePageFilters(searchParams: Record<string, string | string[] | undefined>): LlmUsagePageFilters {
  return {
    search: firstValue(searchParams.q),
    from: firstValue(searchParams.from),
    to: firstValue(searchParams.to),
    runId: firstValue(searchParams.run_id),
    agentName: firstValue(searchParams.agent_name),
    modelName: firstValue(searchParams.model_name),
    providerName: firstValue(searchParams.provider_name),
    stage: firstValue(searchParams.stage),
  };
}

function buildApiSearchParams(filters: LlmUsagePageFilters) {
  const params = new URLSearchParams();
  if (filters.from) {
    params.set("from", `${filters.from}T00:00:00Z`);
  }
  if (filters.to) {
    params.set("to", `${filters.to}T23:59:59.999Z`);
  }
  if (filters.runId) {
    params.set("run_id", filters.runId);
  }
  if (filters.search) {
    params.set("search", filters.search);
  }
  if (filters.agentName) {
    params.set("agent_name", filters.agentName);
  }
  if (filters.modelName) {
    params.set("model_name", filters.modelName);
  }
  if (filters.providerName) {
    params.set("provider_name", filters.providerName);
  }
  if (filters.stage) {
    params.set("stage", filters.stage);
  }
  return params;
}

function firstValue(value: string | string[] | undefined) {
  if (Array.isArray(value)) {
    return value[0]?.trim() ?? "";
  }
  return value?.trim() ?? "";
}
