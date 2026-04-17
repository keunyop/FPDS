"use client";

import { FileText, Layers3 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { InputGroup, InputGroupAddon, InputGroupTextarea } from "@/components/ui/input-group";
import type { SourceCatalogItem } from "@/lib/admin-api";

type SourceCatalogCreateDialogContentProps = {
  bankOptions: Array<{ bank_code: string; bank_name: string }>;
  csrfToken: string | null | undefined;
  onCreated: (item: SourceCatalogItem | null) => void;
};

type CreateCatalogFormState = {
  bank_code: string;
  product_type: string;
  status: string;
  change_reason: string;
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

export function SourceCatalogCreateDialogContent({
  bankOptions,
  csrfToken,
  onCreated,
}: SourceCatalogCreateDialogContentProps) {
  const router = useRouter();
  const [form, setForm] = useState<CreateCatalogFormState>({
    bank_code: bankOptions[0]?.bank_code ?? "",
    product_type: "savings",
    status: "active",
    change_reason: "",
  });
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);

    try {
      const response = await fetch("/admin/source-catalog/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify(form),
      });
      const payload = (await response.json()) as {
        data?: { catalog_item?: SourceCatalogItem };
        error?: { message?: string };
      };
      if (!response.ok) {
        setError(payload.error?.message ?? "Source catalog item could not be created.");
        return;
      }

      onCreated(payload.data?.catalog_item ?? null);
      router.refresh();
    } catch {
      setError("Source catalog item could not be created. Check the admin API and try again.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="space-y-5">
      {error ? <p className="rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p> : null}

      <form className="space-y-4" onSubmit={handleCreate}>
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
          <InputGroup className="min-h-24 items-start">
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
              placeholder="Why is this coverage being added?"
              rows={3}
              value={form.change_reason}
            />
          </InputGroup>
          {error ? <FieldError>{error}</FieldError> : null}
        </Field>

        <div className="flex justify-end">
          <Button disabled={pending || !form.bank_code} type="submit">
            {pending ? "Adding..." : "Add coverage"}
          </Button>
        </div>
      </form>
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
      <div className="flex h-10 items-center rounded-xl border border-input bg-background px-3">
        <div className="mr-2 text-muted-foreground">
          <Layers3 className="size-4" />
        </div>
        <select
          className="w-full bg-transparent text-sm text-foreground outline-none"
          onChange={(event) => onChange(event.target.value)}
          value={value}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    </label>
  );
}
