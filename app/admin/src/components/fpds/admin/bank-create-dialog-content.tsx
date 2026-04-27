"use client";

import type { ReactNode } from "react";
import { Globe, Landmark, Languages, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/components/ui/input-group";
import type { BankItem, ProductTypeItem } from "@/lib/admin-api";
import type { AdminLocale } from "@/lib/admin-i18n";
import { buildAdminProductTypeOptions, formatAdminProductType } from "@/lib/admin-product-types";

type BankCreateDialogContentProps = {
  csrfToken: string | null | undefined;
  locale: AdminLocale;
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

const CREATE_BANK_COPY = {
  en: {
    bankName: "Bank name",
    homepageUrl: "Homepage URL",
    language: "Language",
    status: "Status",
    active: "active",
    inactive: "inactive",
    initialCoverage: "Initial coverage",
    coverageHelp: "Search and pick any product families you already want this bank to cover. You can add more later in the bank detail modal.",
    searchProductTypes: "Search product types",
    noProductTypes: "No product types matched the current search.",
    adding: "Adding...",
    addBank: "Add bank",
    createFailed: "Bank could not be created.",
    createApiFailed: "Bank could not be created. Check the admin API and try again.",
  },
  ko: {
    bankName: "은행명",
    homepageUrl: "홈페이지 URL",
    language: "언어",
    status: "상태",
    active: "활성",
    inactive: "비활성",
    initialCoverage: "초기 coverage",
    coverageHelp: "이 은행에서 바로 cover할 상품군을 검색해 선택하세요. 나중에 은행 상세 modal에서 더 추가할 수 있습니다.",
    searchProductTypes: "상품 유형 검색",
    noProductTypes: "현재 검색에 맞는 상품 유형이 없습니다.",
    adding: "추가 중...",
    addBank: "은행 추가",
    createFailed: "은행을 생성할 수 없습니다.",
    createApiFailed: "은행을 생성할 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
  },
  ja: {
    bankName: "銀行名",
    homepageUrl: "ホームページURL",
    language: "言語",
    status: "状態",
    active: "有効",
    inactive: "無効",
    initialCoverage: "初期 coverage",
    coverageHelp: "この銀行で最初に cover する商品群を検索して選択してください。後から銀行詳細 modal で追加できます。",
    searchProductTypes: "商品タイプを検索",
    noProductTypes: "現在の検索に該当する商品タイプはありません。",
    adding: "追加中...",
    addBank: "銀行を追加",
    createFailed: "銀行を作成できません。",
    createApiFailed: "銀行を作成できません。Admin APIを確認してから再試行してください。",
  },
} as const;

const DEFAULT_CREATE_FORM: CreateBankFormState = {
  bank_name: "",
  homepage_url: "",
  source_language: "en",
  status: "active",
  change_reason: "",
  initial_coverage_product_types: [],
};

export function BankCreateDialogContent({ csrfToken, locale, productTypes, onCreated }: BankCreateDialogContentProps) {
  const copy = CREATE_BANK_COPY[locale];
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
        setError(payload.error?.message ?? copy.createFailed);
        return;
      }

      const createdBank = payload.data?.bank ?? null;
      setCreateForm(DEFAULT_CREATE_FORM);
      onCreated(createdBank);
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
        <FieldGroup className="lg:grid lg:grid-cols-2 lg:gap-4">
          <InputField
            icon={<Landmark className="size-4" />}
            label={copy.bankName}
            onChange={(value) =>
              setCreateForm((current) => ({ ...current, bank_name: value }))
            }
            value={createForm.bank_name}
          />
          <InputField
            icon={<Globe className="size-4" />}
            label={copy.homepageUrl}
            onChange={(value) =>
              setCreateForm((current) => ({ ...current, homepage_url: value }))
            }
            value={createForm.homepage_url}
          />
        </FieldGroup>
        <div className="grid gap-4 sm:grid-cols-2">
          <SelectField
            icon={<Languages className="size-4" />}
            label={copy.language}
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
            label={copy.status}
            locale={locale}
            options={STATUS_OPTIONS}
            value={createForm.status}
            onChange={(value) =>
              setCreateForm((current) => ({ ...current, status: value }))
            }
          />
        </div>
        <Field>
          <FieldLabel>{copy.initialCoverage}</FieldLabel>
          <div className="grid gap-3 rounded-2xl border border-border/80 bg-muted/20 p-4">
            <p className="text-sm leading-6 text-muted-foreground">
              {copy.coverageHelp}
            </p>
            <input
              className="h-10 rounded-xl border border-border bg-background px-3 text-sm"
              onChange={(event) => setCoverageSearch(event.target.value)}
              placeholder={copy.searchProductTypes}
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
              <p className="text-sm text-muted-foreground">{copy.noProductTypes}</p>
            ) : null}
          </div>
        </Field>
        <div className="flex justify-end">
          <Button disabled={pending} type="submit">
            {pending ? copy.adding : copy.addBank}
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
  locale,
}: {
  label: string;
  options: ReadonlyArray<{ label: string; value: string }>;
  value: string;
  onChange: (value: string) => void;
  icon: ReactNode;
  locale?: AdminLocale;
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
              {locale && (option.value === "active" || option.value === "inactive") ? CREATE_BANK_COPY[locale][option.value] : option.label}
            </option>
          ))}
        </select>
      </div>
    </label>
  );
}
