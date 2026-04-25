"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import type { BankItem, SourceCatalogDetailResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

const PRODUCT_TYPE_OPTIONS = ["chequing", "savings", "gic"];

type SourceCatalogDetailSurfaceProps = {
  bankOptions: BankItem[];
  detail: SourceCatalogDetailResponse;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
};

export function SourceCatalogDetailSurface({ bankOptions, detail, locale, csrfToken }: SourceCatalogDetailSurfaceProps) {
  const router = useRouter();
  const [form, setForm] = useState({
    bank_code: detail.catalog_item.bank_code,
    product_type: detail.catalog_item.product_type,
    status: detail.catalog_item.status,
    change_reason: detail.catalog_item.change_reason ?? "",
  });
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch(`/admin/source-catalog/${detail.catalog_item.catalog_item_id}/update`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify(form),
      });
      const payload = (await response.json()) as { error?: { message?: string } };
      if (!response.ok) {
        setError(payload.error?.message ?? "Source catalog item could not be updated.");
        return;
      }
      setMessage("Source catalog item was updated.");
      router.refresh();
    } catch {
      setError("Source catalog item could not be updated. Check the admin API and try again.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="grid gap-6">
      <AdminPageHeader
        actions={
          <>
            <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/source-catalog", new URLSearchParams(), locale)}>
              Back to source catalog
            </Link>
            <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/sources", new URLSearchParams(`bank_code=${detail.catalog_item.bank_code}&product_type=${detail.catalog_item.product_type}`), locale)}>
              View generated sources
            </Link>
          </>
        }
        badges={
          <>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{detail.catalog_item.catalog_item_id}</span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{detail.catalog_item.status}</span>
          </>
        }
        description="Coverage detail and recent collection history."
        path={["Operations", "Source Catalog", "Coverage Detail"]}
        title={`${detail.catalog_item.bank_name} ${detail.catalog_item.product_type}`}
      />

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        {message ? <p className="mb-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="mb-4 rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p> : null}
        <form className="grid gap-4" onSubmit={handleSave}>
          <div className="grid gap-4 lg:grid-cols-3">
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Bank</span>
              <select className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground" onChange={(event) => setForm((current) => ({ ...current, bank_code: event.target.value }))} value={form.bank_code}>
                {bankOptions.map((option) => (
                  <option key={option.bank_code} value={option.bank_code}>
                    {option.bank_name}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Product type</span>
              <select className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground" onChange={(event) => setForm((current) => ({ ...current, product_type: event.target.value }))} value={form.product_type}>
                {PRODUCT_TYPE_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">Status</span>
              <select className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground" onChange={(event) => setForm((current) => ({ ...current, status: event.target.value }))} value={form.status}>
                <option value="active">active</option>
                <option value="inactive">inactive</option>
              </select>
            </label>
          </div>
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">Change reason</span>
            <input className="h-10 rounded-xl border border-border bg-background px-3 text-sm" onChange={(event) => setForm((current) => ({ ...current, change_reason: event.target.value }))} value={form.change_reason} />
          </label>
          <div className="flex justify-end">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70" disabled={pending} type="submit">
              {pending ? "Saving..." : "Save source catalog item"}
            </button>
          </div>
        </form>
      </article>

      <article className="grid gap-4 lg:grid-cols-2">
        <ReadonlyField label="Homepage URL" value={detail.catalog_item.homepage_url ?? "n/a"} />
        <ReadonlyField label="Generated source count" value={String(detail.catalog_item.generated_source_count)} />
        <ReadonlyField className="lg:col-span-2" label="Sample generated source ids" value={detail.sample_source_ids.join(", ") || "No generated sources yet"} />
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Recent collection history</p>
        {detail.recent_runs.length === 0 ? (
          <p className="mt-4 text-sm leading-6 text-muted-foreground">No collection runs were linked to this catalog item yet.</p>
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
