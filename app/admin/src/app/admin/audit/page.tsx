import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { AdminApiUnavailable } from "@/components/fpds/admin/admin-api-unavailable";
import { AuditLogSurface, type AuditLogPageFilters } from "@/components/fpds/admin/audit-log-surface";
import { fetchAdminSession, fetchAuditLogList, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale } from "@/lib/admin-i18n";

type AuditLogPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function AuditLogPage({ searchParams }: AuditLogPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  const filters = parsePageFilters(resolvedSearchParams);
  const apiSearchParams = buildApiSearchParams(filters);

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let auditLog: Awaited<ReturnType<typeof fetchAuditLogList>> = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
    if (session) {
      auditLog = await fetchAuditLogList(apiSearchParams);
    }
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/audit", new URLSearchParams(), locale))}`);
  }

  if (session && !auditLog && !apiUnavailable) {
    redirect(`/admin/login?next=${encodeURIComponent(buildAdminHref("/admin/audit", new URLSearchParams(), locale))}`);
  }

  if (!session || !auditLog || apiUnavailable) {
    return <AdminApiUnavailable locale={locale} title="Audit history could not load." />;
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
      <AuditLogSurface auditLog={auditLog} filters={filters} locale={locale} />
    </ApplicationShell5>
  );
}

function parsePageFilters(searchParams: Record<string, string | string[] | undefined>): AuditLogPageFilters {
  return {
    q: firstValue(searchParams.q),
    eventCategory: firstValue(searchParams.event_category).toLowerCase(),
    eventType: firstValue(searchParams.event_type),
    actorType: firstValue(searchParams.actor_type).toLowerCase(),
    targetType: firstValue(searchParams.target_type).toLowerCase(),
    occurredFrom: firstValue(searchParams.occurred_from),
    occurredTo: firstValue(searchParams.occurred_to),
    sortBy: firstValue(searchParams.sort_by) || "occurred_at",
    sortOrder: firstValue(searchParams.sort_order) === "asc" ? "asc" : "desc",
    page: positiveInteger(firstValue(searchParams.page)) ?? 1,
  };
}

function buildApiSearchParams(filters: AuditLogPageFilters) {
  const params = new URLSearchParams();
  if (filters.q) {
    params.set("q", filters.q);
  }
  if (filters.eventCategory) {
    params.set("event_category", filters.eventCategory);
  }
  if (filters.eventType) {
    params.set("event_type", filters.eventType);
  }
  if (filters.actorType) {
    params.set("actor_type", filters.actorType);
  }
  if (filters.targetType) {
    params.set("target_type", filters.targetType);
  }
  if (filters.occurredFrom) {
    params.set("occurred_from", `${filters.occurredFrom}T00:00:00Z`);
  }
  if (filters.occurredTo) {
    params.set("occurred_to", `${filters.occurredTo}T23:59:59.999Z`);
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
