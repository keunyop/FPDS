"use client";

import type { ReactNode } from "react";
import { FileText, Search, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { InputGroup, InputGroupAddon, InputGroupInput, InputGroupTextarea } from "@/components/ui/input-group";
import type { ProductTypeItem } from "@/lib/admin-api";
import type { AdminLocale } from "@/lib/admin-i18n";

type ProductTypeCreateDialogContentProps = {
  csrfToken: string | null | undefined;
  locale: AdminLocale;
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

const CREATE_COPY = {
  en: {
    displayName: "Display name",
    description: "Description",
    status: "Status",
    active: "active",
    inactive: "inactive",
    create: "Create product type",
    creating: "Creating...",
    createFailed: "Product type could not be created.",
    apiFailed: "Product type could not be created. Check the admin API and try again.",
  },
  ko: {
    displayName: "표시 이름",
    description: "설명",
    status: "상태",
    active: "활성",
    inactive: "비활성",
    create: "상품 유형 생성",
    creating: "생성 중...",
    createFailed: "상품 유형을 생성할 수 없습니다.",
    apiFailed: "상품 유형을 생성할 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
  },
  ja: {
    displayName: "表示名",
    description: "説明",
    status: "状態",
    active: "有効",
    inactive: "無効",
    create: "商品タイプを作成",
    creating: "作成中...",
    createFailed: "商品タイプを作成できません。",
    apiFailed: "商品タイプを作成できません。Admin APIを確認してから再試行してください。",
  },
} as const;

export function ProductTypeCreateDialogContent({
  csrfToken,
  locale,
  onCreated,
}: ProductTypeCreateDialogContentProps) {
  const copy = CREATE_COPY[locale];
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
        setError(payload.error?.message ?? copy.createFailed);
        return;
      }

      setForm(DEFAULT_FORM);
      onCreated(payload.data?.product_type ?? null);
      router.refresh();
    } catch {
      setError(copy.apiFailed);
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
          label={copy.displayName}
          onChange={(value) => setForm((current) => ({ ...current, display_name: value }))}
          value={form.display_name}
        />
        <TextareaField
          icon={<FileText className="size-4" />}
          label={copy.description}
          onChange={(value) => setForm((current) => ({ ...current, description: value }))}
          value={form.description}
        />
        <SelectField
          copy={copy}
          icon={<Sparkles className="size-4" />}
          label={copy.status}
          onChange={(value) => setForm((current) => ({ ...current, status: value }))}
          value={form.status}
        />
        {error ? <FieldError>{error}</FieldError> : null}
        <div className="flex justify-end">
          <Button disabled={pending} type="submit">
            {pending ? copy.creating : copy.create}
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
  copy,
  label,
  value,
  onChange,
  icon,
}: {
  copy: typeof CREATE_COPY[AdminLocale];
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
          <option value="active">{copy.active}</option>
          <option value="inactive">{copy.inactive}</option>
        </select>
      </div>
    </label>
  );
}
