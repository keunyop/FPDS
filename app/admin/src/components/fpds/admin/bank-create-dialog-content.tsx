"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import type { BankItem } from "@/lib/admin-api";

type BankCreateDialogContentProps = {
  csrfToken: string | null | undefined;
  onCreated: (bank: BankItem | null) => void;
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

export function BankCreateDialogContent({ csrfToken, onCreated }: BankCreateDialogContentProps) {
  const router = useRouter();
  const [createForm, setCreateForm] = useState<CreateBankFormState>(DEFAULT_CREATE_FORM);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    <div className="grid gap-5 p-6 pt-0">
      {error ? <p className="rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p> : null}

      <form className="grid gap-4" onSubmit={handleCreate}>
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
            {pending ? "Adding..." : "Add bank"}
          </button>
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
