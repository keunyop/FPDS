import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { AdminApiUnavailable } from "@/components/fpds/admin/admin-api-unavailable";
import { LlmUsageSurface, type LlmUsagePageFilters } from "@/components/fpds/admin/llm-usage-surface";
import { fetchAdminSession, fetchLlmUsage, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type LlmUsagePageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function LlmUsagePage({ searchParams }: LlmUsagePageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
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
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/usage", new URLSearchParams(), locale))}`);
  }

  if (session && !usage && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/usage", new URLSearchParams(), locale))}`);
  }

  if (!session || !usage || apiUnavailable) {
    return <AdminApiUnavailable title="LLM usage visibility could not load." />;
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
