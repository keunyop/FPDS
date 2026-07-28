"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import type { BankDetailResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

type BankDetailSurfaceProps = {
  detail: BankDetailResponse;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
};

const BANK_DETAIL_COPY = {
  en: {
    back: "Back to banks", catalog: "View source catalog", description: "Bank profile and source coverage.",
    path: ["Operations", "Banks", "Bank Detail"], updateFailed: "Bank could not be updated.",
    updateApiFailed: "Bank could not be updated. Check the admin API and try again.", updated: "Bank profile was updated.",
    bankCode: "Bank code", country: "Country", bankName: "Bank name", homepage: "Homepage URL", logo: "Logo URL",
    language: "Language", status: "Status", reason: "Change reason", saving: "Saving...", save: "Save bank",
    coverage: "Catalog coverage", empty: "No source catalog item exists for this bank yet.",
    generated: (count: number) => `${count} generated source${count === 1 ? "" : "s"}`,
  },
  ko: {
    back: "은행 목록", catalog: "소스 카탈로그 보기", description: "은행 프로필과 소스 커버리지입니다.",
    path: ["운영", "은행", "은행 상세"], updateFailed: "은행 정보를 업데이트할 수 없습니다.",
    updateApiFailed: "은행 정보를 업데이트할 수 없습니다. Admin API를 확인한 뒤 다시 시도하세요.", updated: "은행 프로필을 업데이트했습니다.",
    bankCode: "은행 코드", country: "국가", bankName: "은행명", homepage: "홈페이지 URL", logo: "로고 URL",
    language: "언어", status: "상태", reason: "변경 사유", saving: "저장 중...", save: "은행 저장",
    coverage: "카탈로그 커버리지", empty: "이 은행의 소스 카탈로그 항목이 아직 없습니다.",
    generated: (count: number) => `생성 소스 ${count}개`,
  },
  ja: {
    back: "銀行一覧", catalog: "ソースカタログを見る", description: "銀行プロフィールとソースカバレッジです。",
    path: ["運用", "銀行", "銀行詳細"], updateFailed: "銀行情報を更新できませんでした。",
    updateApiFailed: "銀行情報を更新できませんでした。Admin APIを確認して再試行してください。", updated: "銀行プロフィールを更新しました。",
    bankCode: "銀行コード", country: "国", bankName: "銀行名", homepage: "ホームページ URL", logo: "ロゴ URL",
    language: "言語", status: "状態", reason: "変更理由", saving: "保存中...", save: "銀行を保存",
    coverage: "カタログカバレッジ", empty: "この銀行のソースカタログ項目はまだありません。",
    generated: (count: number) => `生成ソース ${count} 件`,
  },
} as const;

const LANGUAGE_OPTIONS: Record<AdminLocale, ReadonlyArray<{ label: string; value: string }>> = {
  en: [{ label: "English", value: "en" }, { label: "Korean", value: "ko" }, { label: "Japanese", value: "ja" }],
  ko: [{ label: "영어", value: "en" }, { label: "한국어", value: "ko" }, { label: "일본어", value: "ja" }],
  ja: [{ label: "英語", value: "en" }, { label: "韓国語", value: "ko" }, { label: "日本語", value: "ja" }],
};

export function BankDetailSurface({ detail, locale, csrfToken }: BankDetailSurfaceProps) {
  const copy = BANK_DETAIL_COPY[locale];
  const router = useRouter();
  const [form, setForm] = useState({
    bank_name: detail.bank.bank_name,
    homepage_url: detail.bank.homepage_url ?? "",
    logo_url: detail.bank.logo_url ?? "",
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
    document.body.dataset.adminMutationPending = "true";
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
      setMessage(copy.updated);
      router.refresh();
    } catch {
      setError(copy.updateApiFailed);
    } finally {
      setPending(false);
      delete document.body.dataset.adminMutationPending;
    }
  }

  return (
    <section aria-busy={pending} className="grid gap-5">
      <AdminPageHeader
        actions={
          <>
            <Link className="inline-flex h-10 items-center justify-center rounded-md border border-border px-4 text-sm font-semibold text-foreground transition-colors hover:border-primary hover:text-primary" href={buildAdminHref("/admin/banks", new URLSearchParams(), locale)}>
              {copy.back}
            </Link>
            <Link className="inline-flex h-10 items-center justify-center rounded-md border border-border px-4 text-sm font-semibold text-foreground transition-colors hover:border-primary hover:text-primary" href={buildAdminHref("/admin/source-catalog", new URLSearchParams(`bank_code=${detail.bank.bank_code}`), locale)}>
              {copy.catalog}
            </Link>
          </>
        }
        badges={
          <>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{detail.bank.bank_code}</span>
            <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{detail.bank.status}</span>
          </>
        }
        description={copy.description}
        path={copy.path}
        title={detail.bank.bank_name}
      />

      <article className="border border-border bg-card p-5">
        {message ? <p aria-live="polite" className="mb-4 border-l-4 border-success bg-success-soft px-4 py-3 text-sm text-success" role="status">{message}</p> : null}
        {error ? <p aria-live="assertive" className="mb-4 border-l-4 border-destructive bg-destructive/10 px-4 py-3 text-sm text-destructive" role="alert">{error}</p> : null}
        <form className="grid gap-4" data-admin-dirty="true" onSubmit={handleSave}>
          <div className="grid gap-4 lg:grid-cols-2">
            <ReadonlyField label={copy.bankCode} value={detail.bank.bank_code} />
            <ReadonlyField label={copy.country} value={detail.bank.country_code} />
            <TextField label={copy.bankName} value={form.bank_name} onChange={(value) => setForm((current) => ({ ...current, bank_name: value }))} />
            <TextField label={copy.homepage} value={form.homepage_url} onChange={(value) => setForm((current) => ({ ...current, homepage_url: value }))} />
            <TextField label={copy.logo} value={form.logo_url} onChange={(value) => setForm((current) => ({ ...current, logo_url: value }))} />
            <SelectField label={copy.language} options={LANGUAGE_OPTIONS[locale]} value={form.source_language} onChange={(value) => setForm((current) => ({ ...current, source_language: value }))} />
            <SelectField label={copy.status} options={["active", "inactive"]} value={form.status} onChange={(value) => setForm((current) => ({ ...current, status: value }))} />
          </div>
          <TextField label={copy.reason} value={form.change_reason} onChange={(value) => setForm((current) => ({ ...current, change_reason: value }))} />
          <div className="flex justify-end">
            <button className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70" disabled={pending} type="submit">
              {pending ? copy.saving : copy.save}
            </button>
          </div>
        </form>
      </article>

      <article className="border border-border bg-card p-5">
        <h2 className="text-lg font-semibold text-foreground">{copy.coverage}</h2>
        {detail.catalog_items.length === 0 ? (
          <p className="mt-4 text-sm leading-6 text-muted-foreground">{copy.empty}</p>
        ) : (
          <div className="mt-4 divide-y divide-border border-y border-border">
            {detail.catalog_items.map((item) => (
              <div className="py-4" key={item.catalog_item_id}>
                <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <Link className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" href={buildAdminHref(`/admin/source-catalog/${item.catalog_item_id}`, new URLSearchParams(), locale)}>
                      {item.product_type}
                    </Link>
                    <p className="mt-1 text-sm text-muted-foreground">{copy.generated(item.generated_source_count)}</p>
                  </div>
                  <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{item.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </article>
    </section>
  );
}

function ReadonlyField({ label, value }: { label: string; value: string }) {
  return (
    <article className="border border-border bg-background p-4">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 font-mono text-sm text-foreground">{value}</p>
    </article>
  );
}

function SelectField({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: ReadonlyArray<string> | ReadonlyArray<{ label: string; value: string }>;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <select className="h-10 rounded-md border border-input bg-background px-3 text-sm text-foreground" onChange={(event) => onChange(event.target.value)} value={value}>
        {options.map((option) => (
          <option key={typeof option === "string" ? option : option.value} value={typeof option === "string" ? option : option.value}>
            {typeof option === "string" ? option : option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function TextField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <input className="h-10 rounded-md border border-input bg-background px-3 text-sm" onChange={(event) => onChange(event.target.value)} value={value} />
    </label>
  );
}
