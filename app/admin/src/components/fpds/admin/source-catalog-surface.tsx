"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import type { SourceCatalogCollectionLaunchResponse, SourceCatalogItem, SourceCatalogListResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

export type SourceCatalogPageFilters = {
  q: string;
  bankCode: string;
  productType: string;
  status: string;
};

type SourceCatalogSurfaceProps = {
  catalog: SourceCatalogListResponse;
  filters: SourceCatalogPageFilters;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
};

type CreateCatalogFormState = {
  bank_code: string;
  product_type: string;
  status: string;
  change_reason: string;
};

const PRODUCT_TYPE_OPTIONS = ["chequing", "savings", "gic"];

export function SourceCatalogSurface({ catalog, filters, locale, csrfToken }: SourceCatalogSurfaceProps) {
  const router = useRouter();
  const [selectedCatalogItemIds, setSelectedCatalogItemIds] = useState<string[]>([]);
  const [createForm, setCreateForm] = useState<CreateCatalogFormState>({
    bank_code: catalog.facets.bank_options[0]?.bank_code ?? "",
    product_type: "savings",
    status: "active",
    change_reason: "",
  });
  const [collectPending, setCollectPending] = useState(false);
  const [createPending, setCreatePending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreatePending(true);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch("/admin/source-catalog/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify(createForm),
      });
      const payload = (await response.json()) as { data?: { catalog_item?: SourceCatalogItem }; error?: { message?: string } };
      if (!response.ok) {
        setError(payload.error?.message ?? "Source catalog item could not be created.");
        return;
      }
      setMessage(`Source catalog item ${payload.data?.catalog_item?.catalog_item_id ?? ""} was created.`);
      setCreateForm((current) => ({ ...current, change_reason: "" }));
      router.refresh();
    } catch {
      setError("Source catalog item could not be created. Check the admin API and try again.");
    } finally {
      setCreatePending(false);
    }
  }

  async function handleCollect() {
    if (selectedCatalogItemIds.length === 0) {
      setError("Select at least one source catalog item before starting collection.");
      setMessage(null);
      return;
    }

    setCollectPending(true);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch("/admin/source-catalog/collect", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify({ catalog_item_ids: selectedCatalogItemIds }),
      });
      const payload = (await response.json()) as { data?: SourceCatalogCollectionLaunchResponse; error?: { message?: string } };
      if (!response.ok) {
        setError(payload.error?.message ?? "Collection could not be launched.");
        return;
      }
      const generatedSourceCount = payload.data?.materialized_items.reduce((sum, item) => sum + item.generated_source_ids.length, 0) ?? 0;
      setMessage(`Collection launched for ${selectedCatalogItemIds.length} catalog item(s). Materialized ${generatedSourceCount} source row(s).`);
      setSelectedCatalogItemIds([]);
      router.refresh();
    } catch {
      setError("Collection could not be launched. Check the admin API and try again.");
    } finally {
      setCollectPending(false);
    }
  }

  function toggleCatalogItem(catalogItemId: string, checked: boolean) {
    setSelectedCatalogItemIds((current) => {
      if (checked) {
        return [...current, catalogItemId];
      }
      return current.filter((item) => item !== catalogItemId);
    });
  }

  return (
    <section className="grid gap-6">
      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Source catalog</p>
            <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
              Choose the bank and product type, then let collection generate source detail.
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
              This is the only place operators add or edit product coverage. Bank and product type are selected from
              controlled dropdowns, and generated source rows stay read-only afterwards.
            </p>
          </div>
          <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/sources", new URLSearchParams(), locale)}>
            View generated sources
          </Link>
        </div>
      </article>

      <article className="grid gap-4 md:grid-cols-4">
        <StatCard label="Catalog items" note="Current list scope" value={String(catalog.summary.total_items)} />
        <StatCard label="Generated sources" note="Already materialized" value={String(catalog.summary.generated_source_count)} />
        <StatCard label="Active" note="Ready for collection" value={String(catalog.summary.status_counts.active ?? 0)} />
        <StatCard label="Selected" note="Ready to collect" value={String(selectedCatalogItemIds.length)} />
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <form action={buildAdminHref("/admin/source-catalog", new URLSearchParams(), locale)} className="grid gap-4 lg:grid-cols-[1.4fr_repeat(3,minmax(0,1fr))_auto]">
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">Search</span>
            <input className="h-10 rounded-xl border border-border bg-background px-3 text-sm" defaultValue={filters.q} name="q" placeholder="bank or catalog item id" type="search" />
          </label>
          <BankSelect defaultValue={filters.bankCode} label="Bank" name="bank_code" options={catalog.facets.bank_options} />
          <SelectField label="Product type" options={catalog.facets.product_types} defaultValue={filters.productType} name="product_type" />
          <SelectField label="Status" options={catalog.facets.statuses} defaultValue={filters.status} name="status" />
          <div className="flex items-end gap-2">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" type="submit">
              Apply
            </button>
            <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/source-catalog", new URLSearchParams(), locale)}>
              Reset
            </Link>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <div className="flex flex-col gap-3 border-b border-border/80 pb-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Create coverage</p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Pick an existing bank and a supported product type. Collection will fill source detail automatically.
            </p>
          </div>
          <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70" disabled={collectPending || selectedCatalogItemIds.length === 0} onClick={handleCollect} type="button">
            {collectPending ? "Launching..." : `Collect selected (${selectedCatalogItemIds.length})`}
          </button>
        </div>

        {message ? <p className="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="mt-4 rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p> : null}

        <form className="mt-6 grid gap-4" onSubmit={handleCreate}>
          <div className="grid gap-4 lg:grid-cols-4">
            <BankSelectClient label="Bank" options={catalog.facets.bank_options} value={createForm.bank_code} onChange={(value) => setCreateForm((current) => ({ ...current, bank_code: value }))} />
            <SelectFieldClient label="Product type" options={PRODUCT_TYPE_OPTIONS} value={createForm.product_type} onChange={(value) => setCreateForm((current) => ({ ...current, product_type: value }))} />
            <SelectFieldClient label="Status" options={["active", "inactive"]} value={createForm.status} onChange={(value) => setCreateForm((current) => ({ ...current, status: value }))} />
            <TextField label="Change reason" value={createForm.change_reason} onChange={(value) => setCreateForm((current) => ({ ...current, change_reason: value }))} />
          </div>
          <div className="flex justify-end">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70" disabled={createPending} type="submit">
              {createPending ? "Creating..." : "Create source catalog item"}
            </button>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="overflow-x-auto px-6 py-5">
          <table className="min-w-[1040px] table-fixed border-separate border-spacing-0">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                <th className="border-b border-border px-3 py-3 font-medium">Select</th>
                <th className="border-b border-border px-3 py-3 font-medium">Bank</th>
                <th className="border-b border-border px-3 py-3 font-medium">Product type</th>
                <th className="border-b border-border px-3 py-3 font-medium">Status</th>
                <th className="border-b border-border px-3 py-3 font-medium">Homepage</th>
                <th className="border-b border-border px-3 py-3 font-medium">Generated sources</th>
                <th className="border-b border-border px-3 py-3 font-medium">Updated</th>
              </tr>
            </thead>
            <tbody>
              {catalog.items.length === 0 ? (
                <tr>
                  <td className="px-3 py-8 text-sm text-muted-foreground" colSpan={7}>
                    No source catalog items matched the current filter set.
                  </td>
                </tr>
              ) : (
                catalog.items.map((item) => (
                  <tr className="align-top text-sm" key={item.catalog_item_id}>
                    <td className="border-b border-border/70 px-3 py-4">
                      <input checked={selectedCatalogItemIds.includes(item.catalog_item_id)} className="h-4 w-4 rounded border-border text-primary focus:ring-primary" onChange={(event) => toggleCatalogItem(item.catalog_item_id, event.target.checked)} type="checkbox" />
                    </td>
                    <td className="border-b border-border/70 px-3 py-4">
                      <Link className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/source-catalog/${item.catalog_item_id}`, new URLSearchParams(), locale)}>
                        {item.bank_name}
                      </Link>
                      <p className="mt-1 text-sm text-muted-foreground">{item.bank_code}</p>
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.product_type}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.status}</td>
                    <td className="border-b border-border/70 px-3 py-4">
                      {item.homepage_url ? (
                        <a className="text-primary underline-offset-4 hover:underline" href={item.homepage_url} rel="noreferrer" target="_blank">
                          {item.homepage_url}
                        </a>
                      ) : (
                        <span className="text-muted-foreground">n/a</span>
                      )}
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.generated_source_count}</td>
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

function StatCard({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <article className="rounded-[1.5rem] border border-border/80 bg-card/95 p-5 shadow-sm">
      <p className="text-sm font-medium uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-foreground">{value}</p>
      <p className="mt-2 text-sm text-muted-foreground">{note}</p>
    </article>
  );
}

function BankSelect({
  defaultValue,
  label,
  name,
  options,
}: {
  defaultValue: string;
  label: string;
  name: string;
  options: Array<{ bank_code: string; bank_name: string }>;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <select className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground" defaultValue={defaultValue} name={name}>
        <option value="">All</option>
        {options.map((option) => (
          <option key={option.bank_code} value={option.bank_code}>
            {option.bank_name}
          </option>
        ))}
      </select>
    </label>
  );
}

function BankSelectClient({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: Array<{ bank_code: string; bank_name: string }>;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <select className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground" onChange={(event) => onChange(event.target.value)} value={value}>
        {options.map((option) => (
          <option key={option.bank_code} value={option.bank_code}>
            {option.bank_name}
          </option>
        ))}
      </select>
    </label>
  );
}

function SelectField({
  label,
  options,
  defaultValue,
  name,
}: {
  label: string;
  options: string[];
  defaultValue: string;
  name: string;
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

function SelectFieldClient({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: string[];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <select className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground" onChange={(event) => onChange(event.target.value)} value={value}>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function TextField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <input className="h-10 rounded-xl border border-border bg-background px-3 text-sm" onChange={(event) => onChange(event.target.value)} value={value} />
    </label>
  );
}
