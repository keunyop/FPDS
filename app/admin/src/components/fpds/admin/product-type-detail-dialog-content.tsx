"use client";

import type { ReactNode } from "react";
import { FileText, Search, Sparkles, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { DestructiveConfirmDialog } from "@/components/fpds/admin/destructive-confirm-dialog";
import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { InputGroup, InputGroupAddon, InputGroupInput, InputGroupTextarea } from "@/components/ui/input-group";
import type { ProductTypeItem } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

type ProductTypeDetailDialogContentProps = {
  productType: ProductTypeItem;
  csrfToken: string | null | undefined;
  locale: AdminLocale;
};

type ProductTypeFormState = {
  display_name: string;
  description: string;
  status: string;
};

export function ProductTypeDetailDialogContent({
  productType,
  csrfToken,
  locale,
}: ProductTypeDetailDialogContentProps) {
  const router = useRouter();
  const [form, setForm] = useState<ProductTypeFormState>({
    display_name: productType.display_name,
    description: productType.description,
    status: productType.status,
  });
  const [pendingSave, setPendingSave] = useState(false);
  const [pendingDelete, setPendingDelete] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPendingSave(true);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch(`/admin/product-types/${productType.product_type_code}/update`, {
        method: "PATCH",
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
        setError(payload.error?.message ?? "Product type could not be updated.");
        return;
      }
      setMessage(`${payload.data?.product_type?.display_name ?? productType.product_type_code} was updated.`);
      router.refresh();
    } catch {
      setError("Product type could not be updated. Check the admin API and try again.");
    } finally {
      setPendingSave(false);
    }
  }

  async function handleDelete() {
    setPendingDelete(true);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch(`/admin/product-types/${productType.product_type_code}/delete`, {
        method: "DELETE",
        headers: {
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
      });
      const payload = (await response.json()) as {
        error?: { message?: string };
      };
      if (!response.ok) {
        setError(payload.error?.message ?? "Product type could not be deleted.");
        setDeleteDialogOpen(false);
        return;
      }
      setDeleteDialogOpen(false);
      router.push(buildAdminHref("/admin/product-types", new URLSearchParams(), locale), { scroll: false });
      router.refresh();
    } catch {
      setError("Product type could not be deleted. Check the admin API and try again.");
      setDeleteDialogOpen(false);
    } finally {
      setPendingDelete(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <ReadonlySummary label="Code" value={productType.product_type_code} />
        <ReadonlySummary label="Family" value={productType.product_family} />
        <ReadonlySummary label="Status" value={productType.status} />
        <ReadonlySummary label="Managed" value={productType.managed_flag ? "Yes" : "No"} />
      </div>

      {message ? <p className="rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p> : null}

      <section className="rounded-[1.5rem] border border-border/80 bg-card/95 p-5 shadow-sm">
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Product type profile</p>
          <h2 className="text-xl font-semibold tracking-tight text-foreground">Operator-managed onboarding definition</h2>
          <p className="text-sm leading-6 text-muted-foreground">
            Product type definitions feed homepage-first discovery and the generic AI fallback path.
          </p>
        </div>

        <form className="mt-5 space-y-4" onSubmit={handleSave}>
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
          <ReadonlyBlock
            label="Discovery keywords"
            value={productType.discovery_keywords.join(", ") || "n/a"}
          />
          <ReadonlyBlock
            label="Fallback policy"
            value={productType.fallback_policy}
          />
          {error ? <FieldError>{error}</FieldError> : null}
          <div className="flex justify-between gap-3">
            <Button
              disabled={pendingDelete}
              onClick={() => setDeleteDialogOpen(true)}
              type="button"
              variant="destructive"
            >
              <Trash2 className="size-4" />
              {pendingDelete ? "Deleting..." : "Delete product type"}
            </Button>
            <Button disabled={pendingSave} type="submit">
              {pendingSave ? "Saving..." : "Save product type"}
            </Button>
          </div>
        </form>
      </section>

      <DestructiveConfirmDialog
        cancelLabel="Keep product type"
        confirmLabel="Delete product type"
        description={`Delete ${productType.display_name} from the registry. Bank coverage or generated sources that still reference it will block this action.`}
        onConfirm={handleDelete}
        onOpenChange={setDeleteDialogOpen}
        open={deleteDialogOpen}
        pending={pendingDelete}
        title={`Delete ${productType.display_name}?`}
      />
    </div>
  );
}

function ReadonlySummary({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/80 bg-muted/35 px-4 py-3">
      <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}

function ReadonlyBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/80 bg-muted/20 px-4 py-4">
      <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-sm leading-6 text-foreground">{value}</p>
    </div>
  );
}

function InputField({
  label,
  value,
  onChange,
  icon,
  disabled = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  icon: ReactNode;
  disabled?: boolean;
}) {
  return (
    <Field>
      <FieldLabel>{label}</FieldLabel>
      <InputGroup>
        <InputGroupAddon align="inline-start">{icon}</InputGroupAddon>
        <InputGroupInput disabled={disabled} onChange={(event) => onChange(event.target.value)} value={value} />
      </InputGroup>
    </Field>
  );
}

function TextareaField({
  label,
  value,
  onChange,
  icon,
  disabled = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  icon: ReactNode;
  disabled?: boolean;
}) {
  return (
    <Field>
      <FieldLabel>{label}</FieldLabel>
      <InputGroup className="min-h-24 items-start">
        <InputGroupAddon align="block-start">{icon}</InputGroupAddon>
        <InputGroupTextarea disabled={disabled} onChange={(event) => onChange(event.target.value)} rows={4} value={value} />
      </InputGroup>
    </Field>
  );
}

function SelectField({
  label,
  value,
  onChange,
  icon,
  disabled = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  icon: ReactNode;
  disabled?: boolean;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <div className="flex h-10 items-center rounded-xl border border-input bg-background px-3">
        <div className="mr-2 text-muted-foreground">{icon}</div>
        <select
          className="w-full bg-transparent text-sm text-foreground outline-none disabled:cursor-not-allowed disabled:opacity-70"
          disabled={disabled}
          onChange={(event) => onChange(event.target.value)}
          value={value}
        >
          <option value="active">active</option>
          <option value="inactive">inactive</option>
        </select>
      </div>
    </label>
  );
}
