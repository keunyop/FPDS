"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import type { BankItem, BankListResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

export type BankRegistryPageFilters = {
  q: string;
  status: string;
};

type BankRegistrySurfaceProps = {
  banks: BankListResponse;
  filters: BankRegistryPageFilters;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
};

type CreateBankFormState = {
  bank_name: string;
  homepage_url: string;
  source_language: string;
  status: string;
  change_reason: string;
};

const DEFAULT_CREATE_FORM: CreateBankFormState = {
  bank_name: "",
  homepage_url: "",
  source_language: "en",
  status: "active",
  change_reason: "",
};

export function BankRegistrySurface({ banks, filters, locale, csrfToken }: BankRegistrySurfaceProps) {
  const router = useRouter();
  const [createForm, setCreateForm] = useState<CreateBankFormState>(DEFAULT_CREATE_FORM);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch("/admin/banks/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify(createForm),
      });
      const payload = (await response.json()) as { data?: { bank?: BankItem }; error?: { message?: string } };
      if (!response.ok) {
        setError(payload.error?.message ?? "Bank could not be created.");
        return;
      }
      const createdBank = payload.data?.bank;
      setMessage(`Bank ${createdBank?.bank_name ?? createForm.bank_name} was created with code ${createdBank?.bank_code ?? "auto"}.`);
      setCreateForm(DEFAULT_CREATE_FORM);
      router.refresh();
    } catch {
      setError("Bank could not be created. Check the admin API and try again.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="grid gap-6">
      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Banks</p>
            <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
              Manage the bank list once, then reuse it in source catalog coverage.
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
              Bank code is generated automatically. Operators only need the visible bank name, homepage URL, and basic
              status metadata here.
            </p>
          </div>
          <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/source-catalog", new URLSearchParams(), locale)}>
            Go to source catalog
          </Link>
        </div>
      </article>

      <article className="grid gap-4 md:grid-cols-3">
        <StatCard label="Banks" note="Current list scope" value={String(banks.summary.total_items)} />
        <StatCard label="Active" note="Available for catalog coverage" value={String(banks.summary.status_counts.active ?? 0)} />
        <StatCard label="Managed" note="Created or edited from admin" value={String(banks.items.filter((item) => item.managed_flag).length)} />
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <form action={buildAdminHref("/admin/banks", new URLSearchParams(), locale)} className="grid gap-4 lg:grid-cols-[1.4fr_minmax(0,220px)_auto]">
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">Search</span>
            <input className="h-10 rounded-xl border border-border bg-background px-3 text-sm" defaultValue={filters.q} name="q" placeholder="bank name or homepage URL" type="search" />
          </label>
          <FilterSelect defaultValue={filters.status} label="Status" name="status" options={banks.facets.statuses} />
          <div className="flex items-end gap-2">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" type="submit">
              Apply
            </button>
            <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/banks", new URLSearchParams(), locale)}>
              Reset
            </Link>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <div className="border-b border-border/80 pb-5">
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Create bank</p>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            Add the public bank profile once. The system generates the bank code and uses the homepage as the starting
            point for source discovery later.
          </p>
        </div>

        {message ? <p className="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="mt-4 rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p> : null}

        <form className="mt-6 grid gap-4" onSubmit={handleCreate}>
          <div className="grid gap-4 lg:grid-cols-2">
            <TextField label="Bank name" value={createForm.bank_name} onChange={(value) => setCreateForm((current) => ({ ...current, bank_name: value }))} />
            <TextField label="Homepage URL" value={createForm.homepage_url} onChange={(value) => setCreateForm((current) => ({ ...current, homepage_url: value }))} />
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            <SelectField label="Language" options={["en", "fr"]} value={createForm.source_language} onChange={(value) => setCreateForm((current) => ({ ...current, source_language: value }))} />
            <SelectField label="Status" options={["active", "inactive"]} value={createForm.status} onChange={(value) => setCreateForm((current) => ({ ...current, status: value }))} />
            <TextField label="Change reason" value={createForm.change_reason} onChange={(value) => setCreateForm((current) => ({ ...current, change_reason: value }))} />
          </div>
          <div className="flex justify-end">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70" disabled={pending} type="submit">
              {pending ? "Creating..." : "Create bank"}
            </button>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="overflow-x-auto px-6 py-5">
          <table className="min-w-[980px] table-fixed border-separate border-spacing-0">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                <th className="border-b border-border px-3 py-3 font-medium">Bank</th>
                <th className="border-b border-border px-3 py-3 font-medium">Code</th>
                <th className="border-b border-border px-3 py-3 font-medium">Homepage</th>
                <th className="border-b border-border px-3 py-3 font-medium">Status</th>
                <th className="border-b border-border px-3 py-3 font-medium">Catalog items</th>
                <th className="border-b border-border px-3 py-3 font-medium">Generated sources</th>
                <th className="border-b border-border px-3 py-3 font-medium">Updated</th>
              </tr>
            </thead>
            <tbody>
              {banks.items.length === 0 ? (
                <tr>
                  <td className="px-3 py-8 text-sm text-muted-foreground" colSpan={7}>
                    No banks matched the current filter set.
                  </td>
                </tr>
              ) : (
                banks.items.map((item) => (
                  <tr className="align-top text-sm" key={item.bank_code}>
                    <td className="border-b border-border/70 px-3 py-4">
                      <Link className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/banks/${item.bank_code}`, new URLSearchParams(), locale)}>
                        {item.bank_name}
                      </Link>
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.bank_code}</td>
                    <td className="border-b border-border/70 px-3 py-4">
                      {item.homepage_url ? (
                        <a className="text-primary underline-offset-4 hover:underline" href={item.homepage_url} rel="noreferrer" target="_blank">
                          {item.homepage_url}
                        </a>
                      ) : (
                        <span className="text-muted-foreground">n/a</span>
                      )}
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.status}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.catalog_item_count}</td>
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

function SelectField({
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

function TextField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <input className="h-10 rounded-xl border border-border bg-background px-3 text-sm" onChange={(event) => onChange(event.target.value)} value={value} />
    </label>
  );
}
