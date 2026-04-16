"use client";

import Link from "next/link";

import type { SourceRegistryDetailResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

type SourceDetailSurfaceProps = {
  detail: SourceRegistryDetailResponse;
  locale: AdminLocale;
};

export function SourceDetailSurface({ detail, locale }: SourceDetailSurfaceProps) {
  return (
    <section className="grid gap-6">
      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Source detail</p>
            <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
              {detail.source.source_id}
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
              This page is read-only. Generated source metadata is filled automatically after collection from the bank
              and source catalog configuration.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{detail.source.discovery_role}</span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{detail.source.status}</span>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/sources", new URLSearchParams(), locale)}>
            Back to sources
          </Link>
          <a className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" href={detail.source.source_url} rel="noreferrer" target="_blank">
            Open source URL
          </a>
        </div>
      </article>

      <article className="grid gap-4 lg:grid-cols-2">
        <ReadonlyField label="Bank" value={detail.source.bank_code} />
        <ReadonlyField label="Country" value={detail.source.country_code} />
        <ReadonlyField label="Product type" value={detail.source.product_type} />
        <ReadonlyField label="Product key" value={detail.source.product_key ?? "n/a"} />
        <ReadonlyField label="Source name" value={detail.source.source_name} />
        <ReadonlyField label="Source type" value={detail.source.source_type} />
        <ReadonlyField label="Role" value={detail.source.discovery_role} />
        <ReadonlyField label="Status" value={detail.source.status} />
        <ReadonlyField label="Priority" value={detail.source.priority} />
        <ReadonlyField label="Language" value={detail.source.source_language} />
        <ReadonlyField label="Purpose" value={detail.source.purpose || "n/a"} />
        <ReadonlyField label="Candidate-producing" value={detail.source.candidate_producing_flag ? "yes" : "no"} />
        <ReadonlyField className="lg:col-span-2" label="Source URL" value={detail.source.source_url} />
        <ReadonlyField className="lg:col-span-2" label="Normalized URL" value={detail.source.normalized_url} />
        <ReadonlyField className="lg:col-span-2" label="Expected fields" value={detail.source.expected_fields.join(", ") || "n/a"} />
        <ReadonlyField className="lg:col-span-2" label="Alias URLs" value={detail.source.alias_urls.join(", ") || "n/a"} />
        <ReadonlyField className="lg:col-span-2" label="Redirect target URL" value={detail.source.redirect_target_url ?? "n/a"} />
        <ReadonlyField className="lg:col-span-2" label="Change reason" value={detail.source.change_reason ?? "n/a"} />
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Recent collection history</p>
        {detail.recent_runs.length === 0 ? (
          <p className="mt-4 text-sm leading-6 text-muted-foreground">No recent collection runs were linked to this source yet.</p>
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
                      {item.pipeline_stage || item.trigger_type} started {item.started_at ?? "n/a"}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{item.run_status}</span>
                    <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{item.candidate_count} candidates</span>
                    <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{item.review_queued_count} review queued</span>
                  </div>
                </div>
                {item.error_summary ? <p className="mt-3 text-sm leading-6 text-destructive">{item.error_summary}</p> : null}
              </div>
            ))}
          </div>
        )}
      </article>
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
