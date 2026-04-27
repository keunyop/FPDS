"use client";

import type { ReactNode } from "react";
import { Globe, Landmark, Languages, ShieldCheck, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { BankCoverageSection } from "@/components/fpds/admin/bank-coverage-section";
import { DestructiveConfirmDialog } from "@/components/fpds/admin/destructive-confirm-dialog";
import { Button } from "@/components/ui/button";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/components/ui/input-group";
import type { BankDetailResponse, ProductTypeItem } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

type BankDetailDialogContentProps = {
  detail: BankDetailResponse;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
  productTypes: ProductTypeItem[];
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

const BANK_DETAIL_COPY = {
  en: {
    bankCode: "Bank code",
    coverage: "Coverage",
    productTypeCount: (count: number) => `${count} product type(s)`,
    bankProfile: "Bank profile",
    profileTitle: "Operator-supplied bank information",
    bankName: "Bank name",
    homepageUrl: "Homepage URL",
    language: "Language",
    status: "Status",
    active: "active",
    inactive: "inactive",
    deleting: "Deleting...",
    deleteBank: "Delete bank",
    saving: "Saving...",
    saveBank: "Save bank",
    keepBank: "Keep bank",
    updateSuccess: "Bank profile was updated.",
    updateFailed: "Bank could not be updated.",
    updateApiFailed: "Bank could not be updated. Check the admin API and try again.",
    deleteFailed: "Bank could not be deleted.",
    deleteApiFailed: "Bank could not be deleted. Check the admin API and try again.",
    deleteDescription: (name: string) =>
      `Delete ${name} from the bank registry. Admin-managed coverage and generated source rows will be removed, but collected runtime data or published history will block this action.`,
    deleteTitle: (name: string) => `Delete ${name}?`,
  },
  ko: {
    bankCode: "은행 코드",
    coverage: "Coverage",
    productTypeCount: (count: number) => `${count}개 상품 유형`,
    bankProfile: "은행 프로필",
    profileTitle: "운영자가 입력한 은행 정보",
    bankName: "은행명",
    homepageUrl: "홈페이지 URL",
    language: "언어",
    status: "상태",
    active: "활성",
    inactive: "비활성",
    deleting: "삭제 중...",
    deleteBank: "은행 삭제",
    saving: "저장 중...",
    saveBank: "은행 저장",
    keepBank: "은행 유지",
    updateSuccess: "은행 프로필이 수정되었습니다.",
    updateFailed: "은행을 수정할 수 없습니다.",
    updateApiFailed: "은행을 수정할 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    deleteFailed: "은행을 삭제할 수 없습니다.",
    deleteApiFailed: "은행을 삭제할 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    deleteDescription: (name: string) =>
      `${name}을(를) bank registry에서 삭제합니다. Admin 관리 coverage와 generated source row는 제거되지만, 수집된 runtime data 또는 publish history가 있으면 작업이 차단됩니다.`,
    deleteTitle: (name: string) => `${name}을(를) 삭제할까요?`,
  },
  ja: {
    bankCode: "銀行コード",
    coverage: "Coverage",
    productTypeCount: (count: number) => `${count}件の商品タイプ`,
    bankProfile: "銀行プロファイル",
    profileTitle: "運用者が入力した銀行情報",
    bankName: "銀行名",
    homepageUrl: "ホームページURL",
    language: "言語",
    status: "状態",
    active: "有効",
    inactive: "無効",
    deleting: "削除中...",
    deleteBank: "銀行を削除",
    saving: "保存中...",
    saveBank: "銀行を保存",
    keepBank: "銀行を保持",
    updateSuccess: "銀行プロファイルを更新しました。",
    updateFailed: "銀行を更新できません。",
    updateApiFailed: "銀行を更新できません。Admin APIを確認してから再試行してください。",
    deleteFailed: "銀行を削除できません。",
    deleteApiFailed: "銀行を削除できません。Admin APIを確認してから再試行してください。",
    deleteDescription: (name: string) =>
      `${name}を bank registry から削除します。Admin 管理の coverage と generated source row は削除されますが、収集済み runtime data または publish history がある場合はブロックされます。`,
    deleteTitle: (name: string) => `${name}を削除しますか？`,
  },
} as const;

export function BankDetailDialogContent({
  detail,
  locale,
  csrfToken,
  productTypes,
}: BankDetailDialogContentProps) {
  const copy = BANK_DETAIL_COPY[locale];
  const router = useRouter();
  const [form, setForm] = useState({
    bank_name: detail.bank.bank_name,
    homepage_url: detail.bank.homepage_url ?? "",
    source_language: detail.bank.source_language,
    status: detail.bank.status,
    change_reason: detail.bank.change_reason ?? "",
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
        setError(payload.error?.message ?? copy.updateFailed);
        return;
      }
      setMessage(copy.updateSuccess);
      router.refresh();
    } catch {
      setError(copy.updateApiFailed);
    } finally {
      setPendingSave(false);
    }
  }

  async function handleDelete() {
    setPendingDelete(true);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch(`/admin/banks/${detail.bank.bank_code}/delete`, {
        method: "DELETE",
        headers: {
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
      });
      const payload = (await response.json()) as { error?: { message?: string } };
      if (!response.ok) {
        setError(payload.error?.message ?? copy.deleteFailed);
        setDeleteDialogOpen(false);
        return;
      }
      setDeleteDialogOpen(false);
      router.push(buildAdminHref("/admin/banks", new URLSearchParams(), locale), { scroll: false });
      router.refresh();
    } catch {
      setError(copy.deleteApiFailed);
      setDeleteDialogOpen(false);
    } finally {
      setPendingDelete(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2">
        <ReadonlySummary label={copy.bankCode} value={detail.bank.bank_code} />
        <ReadonlySummary
          label={copy.coverage}
          value={copy.productTypeCount(detail.catalog_items.length)}
        />
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

      <div className="grid gap-5 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
        <section className="rounded-[1.5rem] border border-border/80 bg-card/95 p-5 shadow-sm">
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              {copy.bankProfile}
            </p>
            <h2 className="text-xl font-semibold tracking-tight text-foreground">
              {copy.profileTitle}
            </h2>
          </div>

          <form className="mt-5 space-y-4" onSubmit={handleSave}>
            <FieldGroup className="lg:grid lg:grid-cols-2 lg:gap-4">
              <InputField
                icon={<Landmark className="size-4" />}
                label={copy.bankName}
                onChange={(value) =>
                  setForm((current) => ({ ...current, bank_name: value }))
                }
                value={form.bank_name}
              />
              <InputField
                icon={<Globe className="size-4" />}
                label={copy.homepageUrl}
                onChange={(value) =>
                  setForm((current) => ({ ...current, homepage_url: value }))
                }
                value={form.homepage_url}
              />
            </FieldGroup>

            <div className="grid gap-4 sm:grid-cols-2">
              <SelectField
                icon={<Languages className="size-4" />}
                label={copy.language}
                onChange={(value) =>
                  setForm((current) => ({ ...current, source_language: value }))
                }
                options={LANGUAGE_OPTIONS}
                value={form.source_language}
              />
              <SelectField
                icon={<ShieldCheck className="size-4" />}
                label={copy.status}
                locale={locale}
                onChange={(value) =>
                  setForm((current) => ({ ...current, status: value }))
                }
                options={STATUS_OPTIONS}
                value={form.status}
              />
            </div>

            <div className="flex justify-between gap-3">
              <Button disabled={pendingDelete} onClick={() => setDeleteDialogOpen(true)} type="button" variant="destructive">
                <Trash2 className="size-4" />
                {pendingDelete ? copy.deleting : copy.deleteBank}
              </Button>
              <Button disabled={pendingSave} type="submit">
                {pendingSave ? copy.saving : copy.saveBank}
              </Button>
            </div>
          </form>
        </section>

        <BankCoverageSection
          bankCode={detail.bank.bank_code}
          catalogItems={detail.catalog_items}
          csrfToken={csrfToken}
          locale={locale}
          productTypes={productTypes}
        />
      </div>

      <DestructiveConfirmDialog
        cancelLabel={copy.keepBank}
        confirmLabel={copy.deleteBank}
        description={copy.deleteDescription(detail.bank.bank_name)}
        onConfirm={handleDelete}
        onOpenChange={setDeleteDialogOpen}
        open={deleteDialogOpen}
        pending={pendingDelete}
        pendingLabel={copy.deleting}
        title={copy.deleteTitle(detail.bank.bank_name)}
      />
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
              {locale && (option.value === "active" || option.value === "inactive") ? BANK_DETAIL_COPY[locale][option.value] : option.label}
            </option>
          ))}
        </select>
      </div>
    </label>
  );
}
