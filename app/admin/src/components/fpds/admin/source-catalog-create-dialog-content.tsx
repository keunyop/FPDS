"use client";

import { FileText, Layers3 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { InputGroup, InputGroupAddon, InputGroupTextarea } from "@/components/ui/input-group";
import type { SourceCatalogItem } from "@/lib/admin-api";
import type { AdminLocale } from "@/lib/admin-i18n";

type SourceCatalogCreateDialogContentProps = {
  bankOptions: Array<{ bank_code: string; bank_name: string }>;
  csrfToken: string | null | undefined;
  locale: AdminLocale;
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

const CREATE_CATALOG_COPY = {
  en: {
    bank: "Bank",
    productType: "Product type",
    status: "Status",
    changeReason: "Change reason",
    placeholder: "Why is this coverage being added?",
    adding: "Adding...",
    addCoverage: "Add coverage",
    createFailed: "Source catalog item could not be created.",
    createApiFailed: "Source catalog item could not be created. Check the admin API and try again.",
    active: "Active",
    inactive: "Inactive",
  },
  ko: {
    bank: "은행",
    productType: "상품 유형",
    status: "상태",
    changeReason: "변경 사유",
    placeholder: "이 coverage를 추가하는 이유",
    adding: "추가 중...",
    addCoverage: "Coverage 추가",
    createFailed: "Source catalog 항목을 생성할 수 없습니다.",
    createApiFailed: "Source catalog 항목을 생성할 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    active: "활성",
    inactive: "비활성",
  },
  ja: {
    bank: "銀行",
    productType: "商品タイプ",
    status: "状態",
    changeReason: "変更理由",
    placeholder: "この coverage を追加する理由",
    adding: "追加中...",
    addCoverage: "Coverage を追加",
    createFailed: "Source catalog 項目を作成できません。",
    createApiFailed: "Source catalog 項目を作成できません。Admin APIを確認してから再試行してください。",
    active: "有効",
    inactive: "無効",
  },
} as const;

export function SourceCatalogCreateDialogContent({
  bankOptions,
  csrfToken,
  locale,
  onCreated,
}: SourceCatalogCreateDialogContentProps) {
  const copy = CREATE_CATALOG_COPY[locale];
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
        setError(payload.error?.message ?? copy.createFailed);
        return;
      }

      onCreated(payload.data?.catalog_item ?? null);
      router.refresh();
    } catch {
      setError(copy.createApiFailed);
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
            label={copy.bank}
            options={bankOptions.map((option) => ({ label: option.bank_name, value: option.bank_code }))}
            value={form.bank_code}
            onChange={(value) => setForm((current) => ({ ...current, bank_code: value }))}
          />
          <SelectField
            label={copy.productType}
            options={PRODUCT_TYPE_OPTIONS}
            value={form.product_type}
            onChange={(value) => setForm((current) => ({ ...current, product_type: value }))}
          />
          <SelectField
            label={copy.status}
            options={STATUS_OPTIONS.map((option) => ({ ...option, label: formatStatus(locale, option.value) }))}
            value={form.status}
            onChange={(value) => setForm((current) => ({ ...current, status: value }))}
          />
        </div>

        <Field data-invalid={Boolean(error)}>
          <FieldLabel>{copy.changeReason}</FieldLabel>
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
              placeholder={copy.placeholder}
              rows={3}
              value={form.change_reason}
            />
          </InputGroup>
          {error ? <FieldError>{error}</FieldError> : null}
        </Field>

        <div className="flex justify-end">
          <Button disabled={pending || !form.bank_code} type="submit">
            {pending ? copy.adding : copy.addCoverage}
          </Button>
        </div>
      </form>
    </div>
  );
}

function formatStatus(locale: AdminLocale, value: string) {
  if (value === "active") {
    return CREATE_CATALOG_COPY[locale].active;
  }
  if (value === "inactive") {
    return CREATE_CATALOG_COPY[locale].inactive;
  }
  return value;
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
