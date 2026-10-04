"use client";

import { LockKeyhole, Search } from "lucide-react";
import { useId, useState } from "react";

import { Input } from "@/components/ui/input";
import { collectionFieldLabel, collectionFieldMode, changeCollectionField, collectionFieldSelectionError, canChangeCollectionFieldSelection,
  type CollectionFieldConfiguration, type CollectionFieldSelection, type CollectionFieldMode } from "@/lib/admin-collection-fields";
import type { AdminLocale } from "@/lib/admin-i18n";

const COPY = {
  "en": {
    "title": "Collection information",
    "required": "Required information",
    "optional": "Optional information",
    "additional": "Optional & additional information",
    "extraRequired": "Additional required information",
    "protected": "Protected",
    "omit": "Not selected",
    "fieldLimit": "Choose up to 60 collection fields.",
    "search": "Find a field",
    "empty": "No matching fields.",
    "rule": "Core requirements stay protected. Alternatives and conditions apply.",
    "limited_transactions": "When the transaction allowance is limited",
    "early_access_not_prohibited": "When early withdrawal is not prohibited",
    "unavailable": "Collection settings are unavailable. Reload after the Admin API is updated."
  },
  "ko": {
    "title": "수집 정보",
    "required": "필수 수집 정보",
    "optional": "선택 수집 정보",
    "additional": "선택 및 추가 수집 정보",
    "extraRequired": "추가 필수 수집 정보",
    "protected": "보호됨",
    "omit": "수집 대상 제외",
    "fieldLimit": "수집 항목은 최대 60개까지 선택할 수 있습니다.",
    "search": "항목 찾기",
    "empty": "일치하는 항목이 없습니다.",
    "rule": "기본 필수 요건은 보호됩니다. 대체 항목과 적용 조건을 따릅니다.",
    "limited_transactions": "포함 거래 횟수가 제한된 경우",
    "early_access_not_prohibited": "중도 인출이 금지되지 않은 경우",
    "unavailable": "수집 설정을 불러올 수 없습니다. Admin API 업데이트 후 새로고침하세요."
  },
  "ja": {
    "title": "収集情報",
    "required": "必須の収集情報",
    "optional": "任意の収集情報",
    "additional": "任意・追加の収集情報",
    "extraRequired": "追加の必須収集情報",
    "protected": "保護対象",
    "omit": "収集対象外",
    "fieldLimit": "収集項目は60個まで選択できます。",
    "search": "項目を検索",
    "empty": "一致する項目がありません。",
    "rule": "基本要件は保護されます。代替項目と適用条件に従います。",
    "limited_transactions": "無料取引回数に上限がある場合",
    "early_access_not_prohibited": "中途解約が禁止されていない場合",
    "unavailable": "収集設定を読み込めません。Admin APIの更新後に再読み込みしてください。"
  }
} as const;

const REQUIREMENT_LABELS: Record<string, [string, string, string]> = {
  "ongoing_rate": [
    "Ongoing annual rate",
    "일반 연이율",
    "通常年利"
  ],
  "ongoing_apy": [
    "Ongoing annual yield",
    "일반 연수익률",
    "通常年利回り"
  ],
  "rate": [
    "Rate",
    "금리",
    "金利"
  ],
  "qualified_rate_or_apr": [
    "Rate or qualified APR",
    "금리 또는 조건이 명시된 APR",
    "金利・条件付きAPR"
  ],
  "apr_or_rate_range": [
    "APR or rate range",
    "APR 또는 금리 범위",
    "APR・金利範囲"
  ],
  "term": [
    "Term",
    "기간",
    "期間"
  ],
  "term_range": [
    "Term or term range",
    "기간 또는 기간 범위",
    "期間・期間範囲"
  ],
  "transaction_structure": [
    "Transaction cost structure",
    "거래 비용 구조",
    "取引費用の体系"
  ],
  "excess_transaction_cost": [
    "Excess transaction cost",
    "초과 거래 비용",
    "超過取引費用"
  ],
  "withdrawal_access": [
    "Early withdrawal access",
    "중도 인출 가능 여부",
    "中途解約の可否"
  ],
  "withdrawal_consequences": [
    "Early withdrawal consequences",
    "중도 인출 시 불이익",
    "中途解約の条件・負担"
  ],
  "security": [
    "Security requirements",
    "담보 요건",
    "担保要件"
  ]
};

export function ProductTypeCollectionFields({ configuration, selection, disabled, locale, onChange }: {
  configuration: CollectionFieldConfiguration | undefined;
  selection: CollectionFieldSelection | undefined;
  disabled: boolean;
  locale: AdminLocale;
  onChange: (selection: CollectionFieldSelection) => void;
}) {
  const copy = COPY[locale];
  const id = useId();
  const [query, setQuery] = useState("");
  const [limitError, setLimitError] = useState(false);
  if (!configuration || !selection) return <p role="status" className="text-sm text-muted-foreground">{copy.unavailable}</p>;
  const protectedKeys = new Set(configuration.locked_required_fields);
  const groupedKeys = new Set(configuration.requirements.flatMap(requirement => requirement.alternatives));
  const identityKeys = configuration.locked_required_fields.filter(key => !groupedKeys.has(key));
  const additionalRequired = selection.required_fields.filter(key => !protectedKeys.has(key));
  const needle = query.trim().toLocaleLowerCase();
  const fields = configuration.field_catalog.filter(field => !protectedKeys.has(field.field_key) &&
    (!needle || `${collectionFieldLabel(field.field_key, locale)} ${field.field_key}`.toLocaleLowerCase().includes(needle)));

  return (
    <section aria-labelledby={`${id}-title`} className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-foreground" id={`${id}-title`}>{copy.title} <span className="ml-1 text-xs font-normal text-muted-foreground">{configuration.country_code}</span></h2>
        <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <span>{copy.required}: <strong className="font-mono text-foreground">{selection.required_fields.length}</strong></span>
          <span>{copy.optional}: <strong className="font-mono text-foreground">{selection.optional_fields.length}</strong></span>
        </div>
      </div>
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-sm font-medium text-foreground">
          <LockKeyhole aria-hidden="true" className="size-4 text-muted-foreground" />
          <h3>{copy.required}</h3>
          <span className="text-xs font-normal text-muted-foreground">{copy.protected}</span>
        </div>
        <p className="text-xs text-muted-foreground">{copy.rule}</p>
        <dl className="divide-y divide-border border-y border-border">
          {identityKeys.map(key => <div className="py-2 text-sm text-foreground" key={key}><dt>{collectionFieldLabel(key, locale)}</dt><dd className="sr-only">{copy.protected}</dd></div>)}
          {configuration.requirements.map(requirement => (
            <div className="grid gap-1 py-2 text-sm sm:grid-cols-[minmax(0,1fr)_minmax(0,1.35fr)] sm:gap-4" key={requirement.key}>
              <dt className="font-medium text-foreground">
                {requirementLabel(requirement.key, locale)}
                {requirement.required_when !== "always" ? <span className="mt-0.5 block text-xs font-normal text-muted-foreground">{conditionLabel(requirement.required_when, locale)}</span> : null}
              </dt>
              {requirement.alternatives.length === 1 && requirement.alternatives[0] === requirement.key
                ? <dd className="sr-only">{copy.protected}</dd>
                : <dd className="break-words text-muted-foreground">{requirement.alternatives.map(key => collectionFieldLabel(key, locale)).join(" / ")}</dd>}
            </div>
          ))}
        </dl>
      </div>
      {additionalRequired.length > 0 ? <div className="space-y-1 text-sm">
        <h3 className="font-medium text-foreground">{copy.extraRequired}</h3>
        <p className="text-muted-foreground">{additionalRequired.map(key => collectionFieldLabel(key, locale)).join(", ")}</p>
      </div> : null}
      <details className="group border-b border-border pb-2">
        <summary className="min-h-10 cursor-pointer py-2 text-sm font-medium text-foreground">{copy.additional}</summary>
        <div className="relative mt-2">
          <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-3 size-4 text-muted-foreground" />
          <Input aria-label={copy.search} className="min-h-10 pl-9" onChange={event => setQuery(event.target.value)} placeholder={copy.search} type="search" value={query} />
        </div>
        {limitError ? <p className="mt-2 text-sm text-destructive" role="alert">{copy.fieldLimit}</p> : null}
        <div className="mt-3 divide-y divide-border">
          {fields.length === 0 ? <p className="py-4 text-sm text-muted-foreground">{copy.empty}</p> : fields.map(field => {
            const fieldId = `${id}-${field.field_key}`;
            return (
              <div className="grid min-w-0 gap-2 py-3 sm:grid-cols-[minmax(0,1fr)_11rem] sm:items-center sm:gap-4" key={field.field_key}>
                <div className="min-w-0">
                  <label className="text-sm font-medium text-foreground" htmlFor={fieldId}>{collectionFieldLabel(field.field_key, locale)}</label>
                  <p className="mt-0.5 break-words font-mono text-xs text-muted-foreground" id={`${fieldId}-type`}>{field.field_key} · {field.value_type}{field.unit ? ` · ${field.unit}` : ""}</p>
                </div>
                <select aria-describedby={`${fieldId}-type`} className="h-10 w-full min-w-0 rounded-md border border-input bg-background px-3 text-sm text-foreground disabled:cursor-not-allowed disabled:opacity-60" disabled={disabled} id={fieldId} onChange={event => {
                    const next = changeCollectionField(configuration, selection, field.field_key, event.target.value as CollectionFieldMode);
                    const invalid = collectionFieldSelectionError(next) !== null;
                    setLimitError(invalid);
                    if (canChangeCollectionFieldSelection(selection, next)) onChange(next);
                  }} value={collectionFieldMode(selection, field.field_key)}>
                  <option value="required">{copy.required}</option>
                  <option value="optional">{copy.optional}</option>
                  <option value="omit">{copy.omit}</option>
                </select>
              </div>
            );
          })}
        </div>
      </details>
    </section>
  );
}

function requirementLabel(key: string, locale: AdminLocale): string {
  const known = REQUIREMENT_LABELS[key];
  return known ? known[locale === "ko" ? 1 : locale === "ja" ? 2 : 0] : collectionFieldLabel(key, locale);
}

function conditionLabel(key: string, locale: AdminLocale): string {
  if (key === "limited_transactions" || key === "early_access_not_prohibited") return COPY[locale][key];
  return collectionFieldLabel(key, locale);
}
