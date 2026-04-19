"use client";

import type { ReactNode } from "react";
import { FileText, Globe, Landmark, Languages, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
  InputGroupTextarea,
} from "@/components/ui/input-group";
import type { BankItem, ProductTypeItem } from "@/lib/admin-api";
import { buildAdminProductTypeOptions, formatAdminProductType } from "@/lib/admin-product-types";

type BankCreateDialogContentProps = {
  csrfToken: string | null | undefined;
  productTypes: ProductTypeItem[];
  onCreated: (bank: BankItem | null) => void;
};

type CreateBankFormState = {
  bank_name: string;
  homepage_url: string;
  source_language: string;
  status: string;
  change_reason: string;
  initial_coverage_product_types: string[];
};

const LANGUAGE_OPTIONS = [
  { label: "English", value: "en" },
  { label: "Korean", value: "ko" },
  { label: "Japanese", value: "ja" },
] as const;

const STATUS_OPTIONS = [
  { label: "active", value: "active" },
  { label: "inactive", value: "inactive" },
] as const;

const DEFAULT_CREATE_FORM: CreateBankFormState = {
  bank_name: "",
  homepage_url: "",
  source_language: "en",
  status: "active",
  change_reason: "",
  initial_coverage_product_types: [],
};

export function BankCreateDialogContent({ csrfToken, productTypes, onCreated }: BankCreateDialogContentProps) {
  const router = useRouter();
  const [createForm, setCreateForm] = useState<CreateBankFormState>(DEFAULT_CREATE_FORM);
  const [coverageSearch, setCoverageSearch] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const productTypeOptions = useMemo(() => buildAdminProductTypeOptions(productTypes.filter((item) => item.status === "active")), [productTypes]);
  const productTypeLabelMap = useMemo(
    () => Object.fromEntries(productTypeOptions.map((item) => [item.value, item.label])),
    [productTypeOptions],
  );
  const filteredOptions = useMemo(() => {
    const needle = coverageSearch.trim().toLowerCase();
    if (!needle) {
      return productTypeOptions;
    }
    return productTypeOptions.filter((option) =>
      `${option.label} ${option.value} ${option.description}`.toLowerCase().includes(needle),
    );
  }, [coverageSearch, productTypeOptions]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
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

      const createdBank = payload.data?.bank ?? null;
      setCreateForm(DEFAULT_CREATE_FORM);
      onCreated(createdBank);
      router.refresh();
    } catch {
      setError("Bank could not be created. Check the admin API and try again.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="space-y-5">
      {error ? <p className="rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p> : null}

      <form className="space-y-4" onSubmit={handleCreate}>
        <FieldGroup className="lg:grid lg:grid-cols-2 lg:gap-4">
          <InputField
            icon={<Landmark className="size-4" />}
            label="Bank name"
            onChange={(value) =>
              setCreateForm((current) => ({ ...current, bank_name: value }))
            }
            value={createForm.bank_name}
          />
          <InputField
            icon={<Globe className="size-4" />}
            label="Homepage URL"
            onChange={(value) =>
              setCreateForm((current) => ({ ...current, homepage_url: value }))
            }
            value={createForm.homepage_url}
          />
        </FieldGroup>
        <div className="grid gap-4 sm:grid-cols-2">
          <SelectField
            icon={<Languages className="size-4" />}
            label="Language"
            options={LANGUAGE_OPTIONS}
            value={createForm.source_language}
            onChange={(value) =>
              setCreateForm((current) => ({
                ...current,
                source_language: value,
              }))
            }
          />
          <SelectField
            icon={<ShieldCheck className="size-4" />}
            label="Status"
            options={STATUS_OPTIONS}
            value={createForm.status}
            onChange={(value) =>
              setCreateForm((current) => ({ ...current, status: value }))
            }
          />
        </div>
        <Field>
          <FieldLabel>Initial coverage</FieldLabel>
          <div className="grid gap-3 rounded-2xl border border-border/80 bg-muted/20 p-4">
            <p className="text-sm leading-6 text-muted-foreground">
              Search and pick any product families you already want this bank to cover. You can add more later in the bank detail modal.
            </p>
            <input
              className="h-10 rounded-xl border border-border bg-background px-3 text-sm"
              onChange={(event) => setCoverageSearch(event.target.value)}
              placeholder="Search product types"
              type="search"
              value={coverageSearch}
            />
            <div className="flex flex-wrap gap-2">
              {filteredOptions.map((option) => {
                const selected = createForm.initial_coverage_product_types.includes(option.value);
                return (
                  <button
                    className={`inline-flex h-10 items-center justify-center rounded-xl border px-4 text-sm font-medium transition ${
                      selected
                        ? "border-primary bg-primary text-primary-foreground"
                        : "border-border bg-background text-foreground hover:border-primary hover:text-primary"
                    }`}
                    key={option.value}
                    onClick={() =>
                      setCreateForm((current) => ({
                        ...current,
                        initial_coverage_product_types: selected
                          ? current.initial_coverage_product_types.filter((item) => item !== option.value)
                          : [...current.initial_coverage_product_types, option.value],
                      }))
                    }
                    type="button"
                  >
                    {formatAdminProductType(option.value, productTypeLabelMap)}
                  </button>
                );
              })}
            </div>
            {filteredOptions.length === 0 ? (
              <p className="text-sm text-muted-foreground">No product types matched the current search.</p>
            ) : null}
          </div>
        </Field>
        <Field data-invalid={Boolean(error)}>
          <FieldLabel>Change reason</FieldLabel>
          <InputGroup className="min-h-24 items-start">
            <InputGroupAddon align="block-start">
              <FileText className="size-4" />
            </InputGroupAddon>
            <InputGroupTextarea
              aria-invalid={Boolean(error)}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  change_reason: event.target.value,
                }))
              }
              placeholder="Why is this bank being added?"
              rows={3}
              value={createForm.change_reason}
            />
          </InputGroup>
          {error ? <FieldError>{error}</FieldError> : null}
        </Field>
        <div className="flex justify-end">
          <Button disabled={pending} type="submit">
            {pending ? "Adding..." : "Add bank"}
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
        <InputGroupInput
          onChange={(event) => onChange(event.target.value)}
          value={value}
        />
      </InputGroup>
    </Field>
  );
}

function SelectField({
  label,
  options,
  value,
  onChange,
  icon,
}: {
  label: string;
  options: ReadonlyArray<{ label: string; value: string }>;
  value: string;
  onChange: (value: string) => void;
  icon: ReactNode;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <div className="flex h-10 items-center rounded-xl border border-input bg-background px-3">
        <div className="mr-2 text-muted-foreground">{icon}</div>
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
