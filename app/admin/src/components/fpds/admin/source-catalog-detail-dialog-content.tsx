"use client";

import Link from "next/link";
import { FileText } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { InputGroup, InputGroupAddon, InputGroupTextarea } from "@/components/ui/input-group";
import type { SourceCatalogDetailResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

type SourceCatalogDetailDialogContentProps = {
  bankOptions: Array<{ bank_code: string; bank_name: string }>;
  detail: SourceCatalogDetailResponse;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
};

const PRODUCT_TYPE_OPTIONS = [
  { label: "chequing", value: "chequing" },
  { label: "savings", value: "savings" },
  { label: "gic", value: "gic" },
] as const;

const STATUS_OPTIONS = [
  { label: "active", value: "active" },
  { label: "inactive", value: "inactive" },
] as const;

export function SourceCatalogDetailDialogContent({
  bankOptions,
  detail,
  locale,
  csrfToken,
}: SourceCatalogDetailDialogContentProps) {
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
    <div className="space-y-4 lg:grid lg:grid-cols-[minmax(0,1.15fr)_minmax(18rem,0.85fr)] lg:gap-5 lg:space-y-0">
      <div className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <ReadonlySummary label="Catalog item id" value={detail.catalog_item.catalog_item_id} />
          <ReadonlySummary label="Generated sources" value={String(detail.catalog_item.generated_source_count)} />
          <ReadonlySummary label="Homepage URL" value={detail.catalog_item.homepage_url ?? "n/a"} />
          <ReadonlySummary label="Sample source ids" value={detail.sample_source_ids.join(", ") || "No generated sources yet"} />
        </div>

        {message ? <p className="rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p> : null}

        <form className="space-y-4" onSubmit={handleSave}>
          <div className="grid gap-4 lg:grid-cols-3">
            <SelectField
              label="Bank"
              options={bankOptions.map((option) => ({ label: option.bank_name, value: option.bank_code }))}
              value={form.bank_code}
              onChange={(value) => setForm((current) => ({ ...current, bank_code: value }))}
            />
            <SelectField
              label="Product type"
              options={PRODUCT_TYPE_OPTIONS}
              value={form.product_type}
              onChange={(value) => setForm((current) => ({ ...current, product_type: value }))}
            />
            <SelectField
              label="Status"
              options={STATUS_OPTIONS}
              value={form.status}
              onChange={(value) => setForm((current) => ({ ...current, status: value }))}
            />
          </div>

          <Field data-invalid={Boolean(error)}>
            <FieldLabel>Change reason</FieldLabel>
            <InputGroup className="min-h-20 items-start">
              <InputGroupAddon align="block-start">
                <FileText className="size-4" />
              </InputGroupAddon>
              <InputGroupTextarea
                aria-invalid={Boolean(error)}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    change_reason: event.target.value,
                  }))
                }
                placeholder="Why was this coverage updated?"
                rows={2}
                value={form.change_reason}
              />
            </InputGroup>
            {error ? <FieldError>{error}</FieldError> : null}
          </Field>

          <div className="flex flex-col gap-3 sm:flex-row sm:justify-between">
            <Link
              className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary"
              href={buildAdminHref("/admin/sources", new URLSearchParams(`bank_code=${detail.catalog_item.bank_code}&product_type=${detail.catalog_item.product_type}`), locale)}
            >
              View generated sources
            </Link>
            <Button disabled={pending} type="submit">
              {pending ? "Saving..." : "Save coverage"}
            </Button>
          </div>
        </form>
      </div>

      <div className="space-y-3 rounded-[1.5rem] border border-border/80 bg-muted/20 p-4">
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Recent collection history</p>
        {detail.recent_runs.length === 0 ? (
          <p className="text-sm leading-6 text-muted-foreground">No collection runs were linked to this coverage yet.</p>
        ) : (
          <div className="grid gap-3">
            {detail.recent_runs.slice(0, 3).map((item) => (
              <div className="rounded-2xl border border-border/80 bg-background px-4 py-3" key={item.run_id}>
                <div className="flex flex-col gap-2">
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
        {detail.recent_runs.length > 3 ? (
          <p className="text-xs leading-5 text-muted-foreground">
            Showing the latest 3 runs here. Open a run detail to inspect older collection history.
          </p>
        ) : null}
      </div>
    </div>
  );
}

function ReadonlySummary({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/80 bg-muted/35 px-4 py-3">
      <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-2 break-words text-sm font-medium leading-6 text-foreground">{value}</p>
    </div>
  );
}

function SelectField({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: ReadonlyArray<{ label: string; value: string }>;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <select className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground" onChange={(event) => onChange(event.target.value)} value={value}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
