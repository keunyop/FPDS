"use client";

import Link from "next/link";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import type { SourceRegistryListResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

export type SourceRegistryPageFilters = {
  q: string;
  bankCode: string;
  countryCode: string;
  productType: string;
  status: string;
  discoveryRole: string;
};

type SourceRegistrySurfaceProps = {
  filters: SourceRegistryPageFilters;
  registry: SourceRegistryListResponse;
  locale: AdminLocale;
};

export function SourceRegistrySurface({ filters, registry, locale }: SourceRegistrySurfaceProps) {
  return (
    <section className="grid gap-6">
      <AdminPageHeader
        actions={
          <>
            <Link className="rounded-full border border-border px-4 py-2 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/banks", new URLSearchParams(), locale)}>
              Manage banks
            </Link>
          </>
        }
        description="Generated source rows for inspection."
        path={["Operations", "Sources"]}
        title="Sources"
      />

      <article className="grid gap-4 md:grid-cols-4">
        <StatCard label="Visible sources" value={String(registry.summary.total_items)} />
        <StatCard label="Candidate-producing" value={String(registry.summary.candidate_producing_items)} />
        <StatCard label="Active" value={String(registry.summary.status_counts.active ?? 0)} />
        <StatCard label="Detail role" value={String(registry.summary.role_counts.detail ?? 0)} />
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <form action={buildAdminHref("/admin/sources", new URLSearchParams(), locale)} className="grid gap-4 lg:grid-cols-[1.4fr_repeat(5,minmax(0,1fr))_auto]">
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">Search</span>
            <input className="h-10 rounded-xl border border-border bg-background px-3 text-sm" defaultValue={filters.q} name="q" placeholder="source id, name, or URL" type="search" />
          </label>
          <FilterSelect defaultValue={filters.bankCode} label="Bank" name="bank_code" options={registry.facets.bank_codes} />
          <FilterSelect defaultValue={filters.countryCode} label="Country" name="country_code" options={["CA"]} />
          <FilterSelect defaultValue={filters.productType} label="Product type" name="product_type" options={registry.facets.product_types} />
          <FilterSelect defaultValue={filters.status} label="Status" name="status" options={registry.facets.statuses} />
          <FilterSelect defaultValue={filters.discoveryRole} label="Role" name="discovery_role" options={registry.facets.discovery_roles} />
          <div className="flex items-end gap-2">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" type="submit">
              Apply
            </button>
            <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/sources", new URLSearchParams(), locale)}>
              Reset
            </Link>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="border-b border-border/80 px-6 py-5">
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Generated source detail</p>
        </div>

        <div className="overflow-x-auto px-6 py-5">
          <table className="min-w-[1080px] table-fixed border-separate border-spacing-0">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                <th className="border-b border-border px-3 py-3 font-medium">Source</th>
                <th className="border-b border-border px-3 py-3 font-medium">Bank</th>
                <th className="border-b border-border px-3 py-3 font-medium">Product</th>
                <th className="border-b border-border px-3 py-3 font-medium">Role</th>
                <th className="border-b border-border px-3 py-3 font-medium">Status</th>
                <th className="border-b border-border px-3 py-3 font-medium">Type</th>
                <th className="border-b border-border px-3 py-3 font-medium">URL</th>
                <th className="border-b border-border px-3 py-3 font-medium">Updated</th>
              </tr>
            </thead>
            <tbody>
              {registry.items.length === 0 ? (
                <tr>
                  <td className="px-3 py-8 text-sm text-muted-foreground" colSpan={8}>
                    No source rows matched the current filter set.
                  </td>
                </tr>
              ) : (
                registry.items.map((item) => (
                  <tr className="align-top text-sm" key={item.source_id}>
                    <td className="border-b border-border/70 px-3 py-4">
                      <Link className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/sources/${item.source_id}`, new URLSearchParams(), locale)}>
                        {item.source_id}
                      </Link>
                      <p className="mt-1 text-sm text-muted-foreground">{item.source_name}</p>
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.bank_code}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.product_type}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.discovery_role}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.status}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.source_type}</td>
                    <td className="border-b border-border/70 px-3 py-4">
                      <a className="line-clamp-2 text-primary underline-offset-4 hover:underline" href={item.source_url} rel="noreferrer" target="_blank">
                        {item.source_url}
                      </a>
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-muted-foreground">{item.updated_at ?? "n/a"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}

function FilterSelect({
  defaultValue,
  label,
  name,
  options,
}: {
  defaultValue: string;
  label: string;
  name: string;
  options: string[];
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <select className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground" defaultValue={defaultValue} name={name}>
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-lg border border-border/80 bg-background p-4">
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{value}</p>
    </article>
  );
}
