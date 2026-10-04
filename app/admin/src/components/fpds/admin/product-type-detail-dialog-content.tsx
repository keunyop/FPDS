"use client";

import type { ReactNode } from "react";
import { FileText, Search, Sparkles, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useId, useState, type FormEvent } from "react";

import { DestructiveConfirmDialog } from "@/components/fpds/admin/destructive-confirm-dialog";
import { Button } from "@/components/ui/button";
import { ProductTypeCollectionFields } from "@/components/fpds/admin/product-type-collection-fields";
import { collectionFieldSelection, sameCollectionFieldSelection, collectionFieldSelectionError, type CollectionFieldSelection } from "@/lib/admin-collection-fields";
import { Field, FieldLabel } from "@/components/ui/field";
import { InputGroup, InputGroupAddon, InputGroupInput, InputGroupTextarea } from "@/components/ui/input-group";
import type { ProductTypeItem } from "@/lib/admin-api";
import { formatAdminBoolean, localizedMissing, type AdminLocale } from "@/lib/admin-i18n";

type ProductTypeDetailDialogContentProps = {
  productType: ProductTypeItem;
  csrfToken: string | null | undefined;
  canManage: boolean;
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
    profileTitle: "Profile",
    displayName: "Display name",
    description: "Description",
    discoveryKeywords: "Discovery keywords",
    metadata: "Discovery settings",
    fallbackPolicy: "Fallback policy",
    deleting: "Deleting...",
    deleteProductType: "Delete product type",
    saving: "Saving...",
    saveProductType: "Save product type",
    keepProductType: "Keep product type",
    updateFailed: "Product type could not be updated.",
    fieldLimit: "Choose up to 60 collection fields.",
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
    family: "상품군",
    status: "상태",
    managed: "관리 대상",
    active: "활성",
    inactive: "비활성",
    profileTitle: "프로필",
    displayName: "표시 이름",
    description: "설명",
    discoveryKeywords: "검색 키워드",
    metadata: "검색 설정",
    fallbackPolicy: "수집 방식",
    deleting: "삭제 중...",
    deleteProductType: "상품 유형 삭제",
    saving: "저장 중...",
    saveProductType: "상품 유형 저장",
    keepProductType: "상품 유형 유지",
    updateFailed: "상품 유형을 수정할 수 없습니다.",
    fieldLimit: "수집 항목은 최대 60개까지 선택할 수 있습니다.",
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
    family: "商品群",
    status: "状態",
    managed: "管理対象",
    active: "有効",
    inactive: "無効",
    profileTitle: "プロファイル",
    displayName: "表示名",
    description: "説明",
    discoveryKeywords: "検索キーワード",
    metadata: "検索設定",
    fallbackPolicy: "収集方式",
    deleting: "削除中...",
    deleteProductType: "商品タイプを削除",
    saving: "保存中...",
    saveProductType: "商品タイプを保存",
    keepProductType: "商品タイプを保持",
    updateFailed: "商品タイプを更新できません。",
    fieldLimit: "収集項目は60個まで選択できます。",
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
  canManage,
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
  const [selection, setSelection] = useState<CollectionFieldSelection | undefined>(
    productType.collection_fields ? collectionFieldSelection(productType.collection_fields) : undefined,
  );
  const [pendingSave, setPendingSave] = useState(false);
  const [pendingDelete, setPendingDelete] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const busy = pendingSave || pendingDelete;
  const initialForm = {
    product_type_code: productType.product_type_code,
    display_name: productType.display_name,
    description: productType.description,
    status: productType.status,
  };
  const dirty = JSON.stringify(form) !== JSON.stringify(initialForm) || Boolean(
    selection && productType.collection_fields && !sameCollectionFieldSelection(selection, productType.collection_fields),
  );

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canManage || busy || !dirty) return;
    if (selection && collectionFieldSelectionError(selection)) { setError(copy.fieldLimit); return; }
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
        body: JSON.stringify({ ...form, ...(selection ? { collection_fields: selection } : {}) }),
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
        setForm({ product_type_code: updatedProductType.product_type_code, display_name: updatedProductType.display_name,
          description: updatedProductType.description, status: updatedProductType.status });
        setSelection(updatedProductType.collection_fields ? collectionFieldSelection(updatedProductType.collection_fields) : undefined);
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
    if (!canManage || busy) return;
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
    <div aria-busy={busy} className="min-w-0 space-y-5" data-admin-dirty={dirty} data-admin-mutation-pending={busy}>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-3 border-y border-border py-3 sm:grid-cols-4">
        <ReadonlySummary label={copy.code} value={productType.product_type_code} />
        <ReadonlySummary label={copy.family} value={productType.product_family} />
        <ReadonlySummary label={copy.status} value={formatStatus(locale, productType.status)} />
        <ReadonlySummary label={copy.managed} value={formatAdminBoolean(locale, productType.managed_flag)} />
      </dl>

      {message ? <p aria-live="polite" className="border-l-4 border-success bg-success-soft px-4 py-3 text-sm text-success" role="status">{message}</p> : null}
      {error ? <p className="border-l-4 border-destructive bg-destructive/10 px-4 py-3 text-sm text-destructive" role="alert">{error}</p> : null}

      <form className="space-y-5" onSubmit={handleSave}>
        <ProductTypeCollectionFields configuration={productType.collection_fields} disabled={!canManage || busy} locale={locale} onChange={setSelection} selection={selection} />

        <details className="space-y-4 border-b border-border pb-3">
          <summary className="min-h-10 cursor-pointer py-2 text-sm font-medium text-foreground">{copy.profileTitle}</summary>
          <div className="grid min-w-0 gap-4 sm:grid-cols-2">
            <InputField disabled={!canManage || busy} icon={<Search aria-hidden="true" className="size-4" />} label={copy.code} onChange={value => setForm(current => ({ ...current, product_type_code: value }))} value={form.product_type_code} />
            <InputField disabled={!canManage || busy} icon={<Search aria-hidden="true" className="size-4" />} label={copy.displayName} onChange={value => setForm(current => ({ ...current, display_name: value }))} value={form.display_name} />
          </div>
          <TextareaField disabled={!canManage || busy} icon={<FileText aria-hidden="true" className="size-4" />} label={copy.description} onChange={value => setForm(current => ({ ...current, description: value }))} value={form.description} />
          <SelectField disabled={!canManage || busy} icon={<Sparkles aria-hidden="true" className="size-4" />} label={copy.status} locale={locale} onChange={value => setForm(current => ({ ...current, status: value }))} value={form.status} />
        </details>

        <details className="border-b border-border pb-2">
          <summary className="min-h-10 cursor-pointer py-2 text-sm font-medium text-foreground">{copy.metadata}</summary>
          <dl className="grid gap-3 py-2 sm:grid-cols-2">
            <ReadonlySummary label={copy.discoveryKeywords} value={productType.discovery_keywords.join(", ") || localizedMissing(locale)} />
            <ReadonlySummary label={copy.fallbackPolicy} value={productType.fallback_policy} />
          </dl>
        </details>

        {canManage ? <div className="flex flex-col-reverse gap-2 border-t border-border pt-4 sm:flex-row sm:justify-between sm:gap-3">
          <Button className="min-h-10" disabled={busy} onClick={() => setDeleteDialogOpen(true)} type="button" variant="outline">
            <Trash2 aria-hidden="true" className="size-4" />
            {pendingDelete ? copy.deleting : copy.deleteProductType}
          </Button>
          <Button className="min-h-10" disabled={busy || !dirty} type="submit">{pendingSave ? copy.saving : copy.saveProductType}</Button>
        </div> : null}
      </form>

      {canManage ? <DestructiveConfirmDialog cancelLabel={copy.keepProductType} confirmLabel={copy.deleteProductType} description={copy.deleteDescription(productType.display_name)} onConfirm={handleDelete} onOpenChange={setDeleteDialogOpen} open={deleteDialogOpen} pending={pendingDelete} pendingLabel={copy.deleting} title={copy.deleteTitle(productType.display_name)} /> : null}
    </div>
  );
}

function ReadonlySummary({ label, value }: { label: string; value: string }) {
  return <div className="min-w-0"><dt className="text-xs text-muted-foreground">{label}</dt><dd className="mt-1 break-words text-sm font-medium text-foreground">{value}</dd></div>;
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
  const id = useId();
  return (
    <Field>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <InputGroup>
        <InputGroupAddon align="inline-start">{icon}</InputGroupAddon>
        <InputGroupInput id={id} required disabled={disabled} onChange={(event) => onChange(event.target.value)} value={value} />
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
  const id = useId();
  return (
    <Field>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <InputGroup className="min-h-24 items-start">
        <InputGroupAddon align="block-start">{icon}</InputGroupAddon>
        <InputGroupTextarea id={id} disabled={disabled} onChange={(event) => onChange(event.target.value)} rows={4} value={value} />
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
      <div className="flex h-10 items-center rounded-md border border-input bg-background px-3 focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/30">
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
