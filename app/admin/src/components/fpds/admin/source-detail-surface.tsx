"use client";

import { Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { DestructiveConfirmDialog } from "@/components/fpds/admin/destructive-confirm-dialog";
import { Button } from "@/components/ui/button";
import type { SourceRegistryDetailResponse } from "@/lib/admin-api";
import { buildAdminHref, formatAdminDateTimeValue, type AdminLocale } from "@/lib/admin-i18n";

type SourceDetailSurfaceProps = {
  detail: SourceRegistryDetailResponse;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
  userRole: string;
};

const SOURCE_DETAIL_EN_COPY = {
  back: "Back to sources",
  openUrl: "Open source URL",
  description: "Generated source metadata and collection history.",
  path: ["Operations", "Sources", "Source Detail"],
  bank: "Bank",
  country: "Country",
  productType: "Product type",
  productKey: "Product key",
  sourceName: "Source name",
  sourceType: "Source type",
  role: "Role",
  status: "Status",
  language: "Language",
  purpose: "Purpose",
  candidateProducing: "Candidate-producing",
  sourceUrl: "Source URL",
  normalizedUrl: "Normalized URL",
  discoveryExplainability: "Discovery explainability",
  promotedTitle: "Why this source was promoted",
  promotedDescription: "Bounded discovery scoring and selection signals.",
  selectionPathMissing: "selection path n/a",
  confidenceMissing: "confidence n/a",
  noMetadata: "No discovery explainability metadata was persisted for this source.",
  aiPredictedRole: "AI predicted role",
  aiConfidenceBand: "AI confidence band",
  pageTitle: "Page title",
  aiRationale: "AI rationale",
  recentHistory: "Recent collection history",
  noRecentRuns: "No recent collection runs were linked to this source yet.",
  started: "started",
  candidates: (count: number) => `${count} candidates`,
  reviewQueued: (count: number) => `${count} review queued`,
  yes: "yes",
  no: "no",
  missing: "n/a",
  deleting: "Removing...",
  removeSource: "Remove source",
  removeFailed: "Source detail could not be removed.",
  removeApiFailed: "Source detail could not be removed. Check the admin API and try again.",
  removeDescription: "This marks the source as removed, keeps the audit trail, and prevents the row from being selected for collection. It does not delete historical run or candidate records.",
  removeTitle: (sourceId: string) => `Remove ${sourceId}?`,
} as const;

const SOURCE_DETAIL_COPY: Record<AdminLocale, typeof SOURCE_DETAIL_EN_COPY> = {
  en: SOURCE_DETAIL_EN_COPY,
  ko: SOURCE_DETAIL_EN_COPY,
  ja: SOURCE_DETAIL_EN_COPY,
};

export function SourceDetailSurface({ detail, locale, csrfToken, userRole }: SourceDetailSurfaceProps) {
  const copy = SOURCE_DETAIL_COPY[locale];
  const router = useRouter();
  const discoveryMetadata = detail.source.discovery_metadata ?? {};
  const [pendingDelete, setPendingDelete] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const canDelete = userRole.toLowerCase() === "admin" && detail.source.status !== "removed";

  async function handleDelete() {
    setPendingDelete(true);
    setError(null);

    try {
      const response = await fetch(`/admin/sources/${encodeURIComponent(detail.source.source_id)}/delete`, {
        method: "DELETE",
        headers: {
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
      });
      const payload = (await response.json()) as { error?: { message?: string } };
      if (!response.ok) {
        setError(payload.error?.message ?? copy.removeFailed);
        setDeleteDialogOpen(false);
        return;
      }
      setDeleteDialogOpen(false);
      router.push(buildAdminHref("/admin/sources", new URLSearchParams(), locale), { scroll: false });
      router.refresh();
    } catch {
      setError(copy.removeApiFailed);
      setDeleteDialogOpen(false);
    } finally {
      setPendingDelete(false);
    }
  }

  return (
    <section className="grid gap-6">
      <AdminPageHeader
        actions={
          <>
            {canDelete ? (
              <Button disabled={pendingDelete} onClick={() => setDeleteDialogOpen(true)} type="button" variant="destructive">
                <Trash2 className="size-4" />
                {pendingDelete ? copy.deleting : copy.removeSource}
              </Button>
            ) : null}
            <Button asChild variant="outline">
              <Link href={buildAdminHref("/admin/sources", new URLSearchParams(), locale)}>{copy.back}</Link>
            </Button>
            <Button asChild>
              <a href={detail.source.source_url} rel="noreferrer" target="_blank">
                {copy.openUrl}
              </a>
            </Button>
          </>
        }
        badges={
          <>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{detail.source.discovery_role}</span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{detail.source.status}</span>
          </>
        }
        description={copy.description}
        path={copy.path}
        title={detail.source.source_id}
      />

      {error ? <p className="rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p> : null}

      <article className="grid gap-4 lg:grid-cols-2">
        <ReadonlyField label={copy.bank} value={detail.source.bank_code} />
        <ReadonlyField label={copy.country} value={detail.source.country_code} />
        <ReadonlyField label={copy.productType} value={detail.source.product_type} />
        <ReadonlyField label={copy.sourceName} value={detail.source.source_name} />
        <ReadonlyField label={copy.sourceType} value={detail.source.source_type} />
        <ReadonlyField label={copy.role} value={detail.source.discovery_role} />
        <ReadonlyField label={copy.status} value={detail.source.status} />
        <ReadonlyField label={copy.language} value={detail.source.source_language} />
        <ReadonlyField label={copy.purpose} value={detail.source.purpose || copy.missing} />
        <ReadonlyField label={copy.candidateProducing} value={detail.source.candidate_producing_flag ? copy.yes : copy.no} />
        <ReadonlyField label={fieldLabel(locale, "lastVerified")} value={formatSourceDateTime(detail.source.last_verified_at, copy.missing)} />
        <ReadonlyField label={fieldLabel(locale, "lastSeen")} value={formatSourceDateTime(detail.source.last_seen_at, copy.missing)} />
        <ReadonlyField label={copy.productKey} value={detail.source.product_key ?? copy.missing} />
        <ReadonlyField label={fieldLabel(locale, "updated")} value={formatSourceDateTime(detail.source.updated_at, copy.missing)} />
        <ReadonlyField className="lg:col-span-2" label={copy.sourceUrl} value={detail.source.source_url} />
        <ReadonlyField className="lg:col-span-2" label={copy.normalizedUrl} value={detail.source.normalized_url} />
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.discoveryExplainability}</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{copy.promotedTitle}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy.promotedDescription}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              {asString(discoveryMetadata.selection_path) ?? copy.selectionPathMissing}
            </span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
              {asString(discoveryMetadata.selection_confidence) ?? copy.confidenceMissing}
            </span>
          </div>
        </div>

        {Object.keys(discoveryMetadata).length === 0 ? (
          <p className="mt-6 text-sm leading-6 text-muted-foreground">{copy.noMetadata}</p>
        ) : (
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <ReadonlyField label={copy.aiPredictedRole} value={asString(discoveryMetadata.ai_predicted_role) ?? copy.missing} />
            <ReadonlyField label={copy.aiConfidenceBand} value={asString(discoveryMetadata.ai_confidence_band) ?? copy.missing} />
            <ReadonlyField className="lg:col-span-2" label={copy.pageTitle} value={asString(discoveryMetadata.page_title) ?? asString(discoveryMetadata.primary_heading) ?? copy.missing} />
            <ReadonlyField className="lg:col-span-2" label={copy.aiRationale} value={asString(discoveryMetadata.ai_short_rationale) ?? copy.missing} />
          </div>
        )}
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.recentHistory}</p>
        {detail.recent_runs.length === 0 ? (
          <p className="mt-4 text-sm leading-6 text-muted-foreground">{copy.noRecentRuns}</p>
        ) : (
          <div className="mt-4 grid gap-3">
            {detail.recent_runs.map((item) => (
              <div className="rounded-2xl border border-border/80 bg-background p-4" key={item.run_id}>
                <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <Link className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/runs/${item.run_id}`, new URLSearchParams(), locale)}>
                      {item.run_id}
                    </Link>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {item.pipeline_stage || item.trigger_type} {copy.started} {formatSourceDateTime(item.started_at, copy.missing)}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{item.run_status}</span>
                    <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{copy.candidates(item.candidate_count)}</span>
                    <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{copy.reviewQueued(item.review_queued_count)}</span>
                  </div>
                </div>
                {item.error_summary ? <p className="mt-3 text-sm leading-6 text-destructive">{item.error_summary}</p> : null}
              </div>
            ))}
          </div>
        )}
      </article>

      <DestructiveConfirmDialog
        confirmLabel={copy.removeSource}
        description={copy.removeDescription}
        onConfirm={handleDelete}
        onOpenChange={setDeleteDialogOpen}
        open={deleteDialogOpen}
        pending={pendingDelete}
        pendingLabel={copy.deleting}
        title={copy.removeTitle(detail.source.source_id)}
      />
    </section>
  );
}

function ReadonlyField({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <article className={`rounded-[1.5rem] border border-border/80 bg-card/95 p-5 shadow-sm ${className ?? ""}`}>
      <p className="text-sm font-medium uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-3 break-words text-sm leading-6 text-foreground">{value}</p>
    </article>
  );
}

function asString(value: unknown) {
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim();
  return normalized.length > 0 ? normalized : null;
}

function fieldLabel(_locale: AdminLocale, key: "lastVerified" | "lastSeen" | "updated") {
  const labels = {
    lastVerified: "Last verified",
    lastSeen: "Last seen",
    updated: "Updated",
  };
  return labels[key];
}

function formatSourceDateTime(value: string | null, missing: string) {
  return formatAdminDateTimeValue(value, missing, { seconds: true });
}
