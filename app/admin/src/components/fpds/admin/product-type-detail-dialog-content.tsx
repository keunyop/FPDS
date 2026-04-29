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
import { formatAdminBoolean, localizedMissing, type AdminLocale } from "@/lib/admin-i18n";

type ProductTypeDetailDialogContentProps = {
  productType: ProductTypeItem;
  csrfToken: string | null | undefined;
  locale: AdminLocale;
  onDeleted?: () => void;
  onUpdated?: (productType: ProductTypeItem) => void;
};

type ProductTypeFormState = {
  product_type_code: string;
  display_name: string;
  description: string;
  status: string;
};

const DETAIL_COPY = {
  en: {
    code: "Code",
    family: "Family",
    status: "Status",
    managed: "Managed",
    active: "active",
    inactive: "inactive",
    profileEyebrow: "Product type profile",
    profileTitle: "Operator-managed onboarding definition",
    profileDescription: "Product type definitions feed homepage-first discovery and the generic AI fallback path.",
    displayName: "Display name",
    description: "Description",
    discoveryKeywords: "Discovery keywords",
    fallbackPolicy: "Fallback policy",
    deleting: "Deleting...",
    deleteProductType: "Delete product type",
    saving: "Saving...",
    saveProductType: "Save product type",
    keepProductType: "Keep product type",
    updateFailed: "Product type could not be updated.",
    updateApiFailed: "Product type could not be updated. Check the admin API and try again.",
    deleteFailed: "Product type could not be deleted.",
    deleteApiFailed: "Product type could not be deleted. Check the admin API and try again.",
    updated: (name: string) => `${name} was updated.`,
    deleteDescription: (name: string) =>
      `Delete ${name} from the registry. Bank coverage or generated sources that still reference it will block this action.`,
    deleteTitle: (name: string) => `Delete ${name}?`,
  },
  ko: {
    code: "코드",
    family: "Family",
    status: "상태",
    managed: "관리 대상",
    active: "활성",
    inactive: "비활성",
    profileEyebrow: "상품 유형 프로필",
    profileTitle: "운영자 관리 onboarding 정의",
    profileDescription: "상품 유형 정의는 홈페이지 우선 discovery와 generic AI fallback 경로에 사용됩니다.",
    displayName: "표시 이름",
    description: "설명",
    discoveryKeywords: "Discovery keywords",
    fallbackPolicy: "Fallback policy",
    deleting: "삭제 중...",
    deleteProductType: "상품 유형 삭제",
    saving: "저장 중...",
    saveProductType: "상품 유형 저장",
    keepProductType: "상품 유형 유지",
    updateFailed: "상품 유형을 수정할 수 없습니다.",
    updateApiFailed: "상품 유형을 수정할 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    deleteFailed: "상품 유형을 삭제할 수 없습니다.",
    deleteApiFailed: "상품 유형을 삭제할 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.",
    updated: (name: string) => `${name}이(가) 수정되었습니다.`,
    deleteDescription: (name: string) =>
      `${name}을(를) registry에서 삭제합니다. 아직 참조 중인 bank coverage 또는 generated source가 있으면 이 작업은 차단됩니다.`,
    deleteTitle: (name: string) => `${name}을(를) 삭제할까요?`,
  },
  ja: {
    code: "コード",
    family: "Family",
    status: "状態",
    managed: "管理対象",
    active: "有効",
    inactive: "無効",
    profileEyebrow: "商品タイププロファイル",
    profileTitle: "運用者管理の onboarding 定義",
    profileDescription: "商品タイプ定義はホームページ優先 discovery と generic AI fallback 経路で使用されます。",
    displayName: "表示名",
    description: "説明",
    discoveryKeywords: "Discovery keywords",
    fallbackPolicy: "Fallback policy",
    deleting: "削除中...",
    deleteProductType: "商品タイプを削除",
    saving: "保存中...",
    saveProductType: "商品タイプを保存",
    keepProductType: "商品タイプを保持",
    updateFailed: "商品タイプを更新できません。",
    updateApiFailed: "商品タイプを更新できません。Admin APIを確認してから再試行してください。",
    deleteFailed: "商品タイプを削除できません。",
    deleteApiFailed: "商品タイプを削除できません。Admin APIを確認してから再試行してください。",
    updated: (name: string) => `${name}を更新しました。`,
    deleteDescription: (name: string) =>
      `${name}を registry から削除します。参照中の bank coverage または generated source がある場合、この操作はブロックされます。`,
    deleteTitle: (name: string) => `${name}を削除しますか？`,
  },
} as const;

export function ProductTypeDetailDialogContent({
  productType,
  csrfToken,
  locale,
  onDeleted,
  onUpdated,
}: ProductTypeDetailDialogContentProps) {
  const copy = DETAIL_COPY[locale];
  const router = useRouter();
  const [form, setForm] = useState<ProductTypeFormState>({
    product_type_code: productType.product_type_code,
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
      const response = await fetch(`/admin/product-types/${encodeURIComponent(productType.product_type_code)}/update`, {
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
        setError(payload.error?.message ?? copy.updateFailed);
        return;
      }
      const updatedProductType = payload.data?.product_type;
      setMessage(copy.updated(updatedProductType?.display_name ?? productType.product_type_code));
      if (updatedProductType) {
        onUpdated?.(updatedProductType);
      }
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
    let deleted = false;

    try {
      const response = await fetch(`/admin/product-types/${encodeURIComponent(productType.product_type_code)}/delete`, {
        method: "DELETE",
        headers: {
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
      });
      const payload = (await response.json()) as {
        error?: { message?: string };
      };
      if (!response.ok) {
        setError(payload.error?.message ?? copy.deleteFailed);
        setDeleteDialogOpen(false);
        return;
      }
      setDeleteDialogOpen(false);
      deleted = true;
      onDeleted?.();
      router.refresh();
    } catch {
      setError(copy.deleteApiFailed);
      setDeleteDialogOpen(false);
    } finally {
      if (!deleted) {
        setPendingDelete(false);
      }
    }
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <ReadonlySummary label={copy.code} value={productType.product_type_code} />
        <ReadonlySummary label={copy.family} value={productType.product_family} />
        <ReadonlySummary label={copy.status} value={formatStatus(locale, productType.status)} />
        <ReadonlySummary label={copy.managed} value={formatAdminBoolean(locale, productType.managed_flag)} />
      </div>

      {message ? <p className="rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p> : null}

      <section className="rounded-[1.5rem] border border-border/80 bg-card/95 p-5 shadow-sm">
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">{copy.profileEyebrow}</p>
          <h2 className="text-xl font-semibold tracking-tight text-foreground">{copy.profileTitle}</h2>
          <p className="text-sm leading-6 text-muted-foreground">
            {copy.profileDescription}
          </p>
        </div>

        <form className="mt-5 space-y-4" onSubmit={handleSave}>
          <InputField
            icon={<Search className="size-4" />}
            label={copy.code}
            onChange={(value) => setForm((current) => ({ ...current, product_type_code: value }))}
            value={form.product_type_code}
          />
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
            icon={<Sparkles className="size-4" />}
            label={copy.status}
            locale={locale}
            onChange={(value) => setForm((current) => ({ ...current, status: value }))}
            value={form.status}
          />
          <ReadonlyBlock
            label={copy.discoveryKeywords}
            value={productType.discovery_keywords.join(", ") || localizedMissing(locale)}
          />
          <ReadonlyBlock
            label={copy.fallbackPolicy}
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
              {pendingDelete ? copy.deleting : copy.deleteProductType}
            </Button>
            <Button disabled={pendingSave} type="submit">
              {pendingSave ? copy.saving : copy.saveProductType}
            </Button>
          </div>
        </form>
      </section>

      <DestructiveConfirmDialog
        cancelLabel={copy.keepProductType}
        confirmLabel={copy.deleteProductType}
        description={copy.deleteDescription(productType.display_name)}
        onConfirm={handleDelete}
        onOpenChange={setDeleteDialogOpen}
        open={deleteDialogOpen}
        pending={pendingDelete}
        pendingLabel={copy.deleting}
        title={copy.deleteTitle(productType.display_name)}
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
  locale,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  icon: ReactNode;
  disabled?: boolean;
  locale: AdminLocale;
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
          <option value="active">{DETAIL_COPY[locale].active}</option>
          <option value="inactive">{DETAIL_COPY[locale].inactive}</option>
        </select>
      </div>
    </label>
  );
}

function formatStatus(locale: AdminLocale, value: string) {
  if (value === "active") {
    return DETAIL_COPY[locale].active;
  }
  if (value === "inactive") {
    return DETAIL_COPY[locale].inactive;
  }
  return value;
}
