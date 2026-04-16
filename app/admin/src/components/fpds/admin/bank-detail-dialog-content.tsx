"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { Globe, Landmark, Languages, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
  InputGroupTextarea,
} from "@/components/ui/input-group";
import type { BankDetailResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

type BankDetailDialogContentProps = {
  detail: BankDetailResponse;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
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

export function BankDetailDialogContent({
  detail,
  locale,
  csrfToken,
}: BankDetailDialogContentProps) {
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
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2">
        <ReadonlySummary label="Bank code" value={detail.bank.bank_code} />
        <ReadonlySummary label="Country" value={detail.bank.country_code} />
      </div>

      {message ? (
        <p className="rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <form className="space-y-4" onSubmit={handleSave}>
        <FieldGroup className="lg:grid lg:grid-cols-2 lg:gap-4">
          <InputField
            icon={<Landmark className="size-4" />}
            label="Bank name"
            onChange={(value) =>
              setForm((current) => ({ ...current, bank_name: value }))
            }
            value={form.bank_name}
          />
          <InputField
            icon={<Globe className="size-4" />}
            label="Homepage URL"
            onChange={(value) =>
              setForm((current) => ({ ...current, homepage_url: value }))
            }
            value={form.homepage_url}
          />
        </FieldGroup>

        <div className="grid gap-4 sm:grid-cols-2">
          <SelectField
            icon={<Languages className="size-4" />}
            label="Language"
            onChange={(value) =>
              setForm((current) => ({ ...current, source_language: value }))
            }
            options={LANGUAGE_OPTIONS}
            value={form.source_language}
          />
          <SelectField
            icon={<ShieldCheck className="size-4" />}
            label="Status"
            onChange={(value) =>
              setForm((current) => ({ ...current, status: value }))
            }
            options={STATUS_OPTIONS}
            value={form.status}
          />
        </div>

        <Field data-invalid={Boolean(error)}>
          <FieldLabel>Change reason</FieldLabel>
          <InputGroup className="min-h-24 items-start">
            <InputGroupTextarea
              aria-invalid={Boolean(error)}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  change_reason: event.target.value,
                }))
              }
              placeholder="Why was this bank profile updated?"
              rows={3}
              value={form.change_reason}
            />
          </InputGroup>
          {error ? <FieldError>{error}</FieldError> : null}
        </Field>

        <div className="flex flex-col gap-3 sm:flex-row sm:justify-between">
          <Link
            className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary"
            href={buildAdminHref(
              "/admin/source-catalog",
              new URLSearchParams(`bank_code=${detail.bank.bank_code}`),
              locale,
            )}
          >
            View source catalog
          </Link>
          <Button disabled={pending} type="submit">
            {pending ? "Saving..." : "Save bank"}
          </Button>
        </div>
      </form>
    </div>
  );
}

function ReadonlySummary({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/80 bg-muted/35 px-4 py-3">
      <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-2 text-sm font-medium text-foreground">{value}</p>
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
