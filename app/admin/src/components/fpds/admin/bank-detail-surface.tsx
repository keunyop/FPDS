"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import type { BankDetailResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

type BankDetailSurfaceProps = {
  detail: BankDetailResponse;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
};

const LANGUAGE_OPTIONS = [
  { label: "English", value: "en" },
  { label: "Korean", value: "ko" },
  { label: "Japanese", value: "ja" },
] as const;

export function BankDetailSurface({ detail, locale, csrfToken }: BankDetailSurfaceProps) {
  const router = useRouter();
  const [form, setForm] = useState({
    bank_name: detail.bank.bank_name,
    homepage_url: detail.bank.homepage_url ?? "",
    source_language: detail.bank.source_language,
    status: detail.bank.status,
    change_reason: detail.bank.change_reason ?? "",
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
      const response = await fetch(`/admin/banks/${detail.bank.bank_code}/update`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify(form),
      });
      const payload = (await response.json()) as { error?: { message?: string } };
      if (!response.ok) {
        setError(payload.error?.message ?? "Bank could not be updated.");
        return;
      }
      setMessage("Bank profile was updated.");
      router.refresh();
    } catch {
      setError("Bank could not be updated. Check the admin API and try again.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="grid gap-6">
      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Bank detail</p>
            <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
              {detail.bank.bank_name}
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
              Bank code is system-generated and read-only. Edit only the visible bank profile and reuse it across
              source catalog items.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{detail.bank.bank_code}</span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{detail.bank.status}</span>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/banks", new URLSearchParams(), locale)}>
            Back to banks
          </Link>
          <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/source-catalog", new URLSearchParams(`bank_code=${detail.bank.bank_code}`), locale)}>
            View source catalog
          </Link>
        </div>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        {message ? <p className="mb-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="mb-4 rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p> : null}
        <form className="grid gap-4" onSubmit={handleSave}>
          <div className="grid gap-4 lg:grid-cols-2">
            <ReadonlyField label="Bank code" value={detail.bank.bank_code} />
            <ReadonlyField label="Country" value={detail.bank.country_code} />
            <TextField label="Bank name" value={form.bank_name} onChange={(value) => setForm((current) => ({ ...current, bank_name: value }))} />
            <TextField label="Homepage URL" value={form.homepage_url} onChange={(value) => setForm((current) => ({ ...current, homepage_url: value }))} />
            <SelectField label="Language" options={LANGUAGE_OPTIONS} value={form.source_language} onChange={(value) => setForm((current) => ({ ...current, source_language: value }))} />
            <SelectField label="Status" options={["active", "inactive"]} value={form.status} onChange={(value) => setForm((current) => ({ ...current, status: value }))} />
          </div>
          <TextField label="Change reason" value={form.change_reason} onChange={(value) => setForm((current) => ({ ...current, change_reason: value }))} />
          <div className="flex justify-end">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70" disabled={pending} type="submit">
              {pending ? "Saving..." : "Save bank"}
            </button>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Catalog coverage</p>
        {detail.catalog_items.length === 0 ? (
          <p className="mt-4 text-sm leading-6 text-muted-foreground">No source catalog item exists for this bank yet.</p>
        ) : (
          <div className="mt-4 grid gap-3">
            {detail.catalog_items.map((item) => (
              <div className="rounded-2xl border border-border/80 bg-background p-4" key={item.catalog_item_id}>
                <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <Link className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/source-catalog/${item.catalog_item_id}`, new URLSearchParams(), locale)}>
                      {item.product_type}
                    </Link>
                    <p className="mt-1 text-sm text-muted-foreground">{item.generated_source_count} generated source(s)</p>
                  </div>
                  <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{item.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </article>
    </section>
  );
}

function ReadonlyField({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-[1.5rem] border border-border/80 bg-background p-5">
      <p className="text-sm font-medium uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-3 text-sm text-foreground">{value}</p>
    </article>
  );
}

function SelectField({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: ReadonlyArray<string> | ReadonlyArray<{ label: string; value: string }>;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <select className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground" onChange={(event) => onChange(event.target.value)} value={value}>
        {options.map((option) => (
          <option key={typeof option === "string" ? option : option.value} value={typeof option === "string" ? option : option.value}>
            {typeof option === "string" ? option : option.label}
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
