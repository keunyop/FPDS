"use client";

import type { ReactNode } from "react";
import { FileText, Search, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { InputGroup, InputGroupAddon, InputGroupInput, InputGroupTextarea } from "@/components/ui/input-group";
import type { ProductTypeItem } from "@/lib/admin-api";

type ProductTypeCreateDialogContentProps = {
  csrfToken: string | null | undefined;
  onCreated: (productType: ProductTypeItem | null) => void;
};

type ProductTypeFormState = {
  display_name: string;
  description: string;
  status: string;
};

const DEFAULT_FORM: ProductTypeFormState = {
  display_name: "",
  description: "",
  status: "active",
};

export function ProductTypeCreateDialogContent({
  csrfToken,
  onCreated,
}: ProductTypeCreateDialogContentProps) {
  const router = useRouter();
  const [form, setForm] = useState<ProductTypeFormState>(DEFAULT_FORM);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);

    try {
      const response = await fetch("/admin/product-types/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify(form),
      });
      const payload = (await response.json()) as {
        data?: { product_type?: ProductTypeItem };
        error?: { message?: string };
      };
      if (!response.ok) {
        setError(payload.error?.message ?? "Product type could not be created.");
        return;
      }

      setForm(DEFAULT_FORM);
      onCreated(payload.data?.product_type ?? null);
      router.refresh();
    } catch {
      setError("Product type could not be created. Check the admin API and try again.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="space-y-5">
      {error ? <p className="rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p> : null}

      <form className="space-y-4" onSubmit={handleCreate}>
        <InputField
          icon={<Search className="size-4" />}
          label="Display name"
          onChange={(value) => setForm((current) => ({ ...current, display_name: value }))}
          value={form.display_name}
        />
        <TextareaField
          icon={<FileText className="size-4" />}
          label="Description"
          onChange={(value) => setForm((current) => ({ ...current, description: value }))}
          value={form.description}
        />
        <SelectField
          icon={<Sparkles className="size-4" />}
          label="Status"
          onChange={(value) => setForm((current) => ({ ...current, status: value }))}
          value={form.status}
        />
        {error ? <FieldError>{error}</FieldError> : null}
        <div className="flex justify-end">
          <Button disabled={pending} type="submit">
            {pending ? "Creating..." : "Create product type"}
          </Button>
        </div>
      </form>
    </div>
  );
}

function InputField({
  label,
  value,
  onChange,
  icon,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  icon: ReactNode;
}) {
  return (
    <Field>
      <FieldLabel>{label}</FieldLabel>
      <InputGroup>
        <InputGroupAddon align="inline-start">{icon}</InputGroupAddon>
        <InputGroupInput onChange={(event) => onChange(event.target.value)} value={value} />
      </InputGroup>
    </Field>
  );
}

function TextareaField({
  label,
  value,
  onChange,
  icon,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  icon: ReactNode;
}) {
  return (
    <Field>
      <FieldLabel>{label}</FieldLabel>
      <InputGroup className="min-h-24 items-start">
        <InputGroupAddon align="block-start">{icon}</InputGroupAddon>
        <InputGroupTextarea onChange={(event) => onChange(event.target.value)} rows={4} value={value} />
      </InputGroup>
    </Field>
  );
}

function SelectField({
  label,
  value,
  onChange,
  icon,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  icon: ReactNode;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <div className="flex h-10 items-center rounded-xl border border-input bg-background px-3">
        <div className="mr-2 text-muted-foreground">{icon}</div>
        <select className="w-full bg-transparent text-sm text-foreground outline-none" onChange={(event) => onChange(event.target.value)} value={value}>
          <option value="active">active</option>
          <option value="inactive">inactive</option>
        </select>
      </div>
    </label>
  );
}
