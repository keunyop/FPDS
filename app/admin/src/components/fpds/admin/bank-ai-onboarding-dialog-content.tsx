"use client";

import { ExternalLink, Landmark, Loader2, SearchCheck, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo, useState, type FormEvent } from "react";

import { BankLogoMark } from "@/components/fpds/admin/bank-logo-mark";
import { Button } from "@/components/ui/button";
import type {
  BankAiOnboardingResponse,
  ProductTypeItem,
} from "@/lib/admin-api";
import type { AdminLocale } from "@/lib/admin-i18n";
import {
  buildAdminProductTypeLabelMap,
  formatAdminProductType,
} from "@/lib/admin-product-types";

type BankAiOnboardingDialogContentProps = {
  countryCode: string;
  csrfToken: string | null | undefined;
  locale: AdminLocale;
  productTypes: ProductTypeItem[];
  onCompleted: (result: BankAiOnboardingResponse) => void;
  onClose: () => void;
};

const AI_BANK_COPY = {
  en: {
    currentCountry: "Working country",
    count: "Banks to add",
    help: "FPDS researches the largest missing banks in this country, verifies each official site, and adds only Product Type coverage supported by current official pages.",
    excludes: "Banks already registered in this country are excluded automatically.",
    evidence: "Current web sources are required for bank size, homepage, and coverage. If the requested count cannot be fully verified, no banks are added.",
    submit: "Research and add banks",
    pending: "Researching banks...",
    pendingHelp: "This can take up to a minute while official sources are checked.",
    failed: "Banks could not be added.",
    unavailable: "AI bank onboarding is not configured for this environment.",
    schemaNotReady: "AI bank onboarding is awaiting the required database migration.",
    insufficient: "There were not enough fully sourced, non-duplicate banks. Nothing was added.",
    productTypesRequired: "Add at least one active Product Type before using this action.",
    added: (count: number) => `${count} ${count === 1 ? "bank" : "banks"} added`,
    coverageAdded: (count: number) => `${count} coverage ${count === 1 ? "item" : "items"}`,
    rankingBasis: "Ranking basis",
    nationalRank: (rank: number) => `Country rank #${rank}`,
    officialHomepage: "Official homepage",
    evidenceLink: "Evidence",
    coverage: "Coverage",
    noCoverage: "No coverage",
    close: "Done",
    addMore: "Add more",
  },
  ko: {
    currentCountry: "작업 국가",
    count: "추가할 은행 수",
    help: "FPDS가 이 국가에서 아직 등록되지 않은 큰 은행을 조사하고 공식 사이트를 검증한 뒤, 현재 공식 페이지로 확인되는 상품유형 coverage만 함께 추가합니다.",
    excludes: "이 국가에 이미 등록된 은행은 자동으로 제외됩니다.",
    evidence: "은행 규모, 홈페이지, coverage는 현재 웹 출처로 확인되어야 합니다. 선택한 수량 전체를 검증하지 못하면 어떤 은행도 추가하지 않습니다.",
    submit: "은행 조사 후 추가",
    pending: "은행 조사 중...",
    pendingHelp: "공식 출처를 확인하는 동안 최대 1분 정도 걸릴 수 있습니다.",
    failed: "은행을 추가할 수 없습니다.",
    unavailable: "이 환경에는 AI 은행 추가가 설정되어 있지 않습니다.",
    schemaNotReady: "AI 은행 추가에 필요한 데이터베이스 마이그레이션이 아직 적용되지 않았습니다.",
    insufficient: "출처가 충분하고 중복되지 않은 은행을 요청 수만큼 확인하지 못했습니다. 추가된 은행은 없습니다.",
    productTypesRequired: "이 기능을 사용하기 전에 활성 상품유형을 하나 이상 추가하세요.",
    added: (count: number) => `은행 ${count}개 추가`,
    coverageAdded: (count: number) => `coverage ${count}개 추가`,
    rankingBasis: "순위 기준",
    nationalRank: (rank: number) => `국가 순위 #${rank}`,
    officialHomepage: "공식 홈페이지",
    evidenceLink: "근거",
    coverage: "Coverage",
    noCoverage: "Coverage 없음",
    close: "완료",
    addMore: "더 추가",
  },
  ja: {
    currentCountry: "作業対象国",
    count: "追加する銀行数",
    help: "FPDS がこの国で未登録の大規模銀行を調査し、公式サイトを確認したうえで、現在の公式ページで確認できる商品タイプの coverage のみを追加します。",
    excludes: "この国ですでに登録されている銀行は自動的に除外されます。",
    evidence: "銀行規模、ホームページ、coverage には現在の Web 出典が必要です。選択した件数をすべて確認できない場合、銀行は追加されません。",
    submit: "銀行を調査して追加",
    pending: "銀行を調査中...",
    pendingHelp: "公式情報の確認には最大1分ほどかかる場合があります。",
    failed: "銀行を追加できませんでした。",
    unavailable: "この環境では AI 銀行追加が設定されていません。",
    schemaNotReady: "AI 銀行追加に必要なデータベース移行がまだ適用されていません。",
    insufficient: "出典が十分で重複しない銀行を指定件数まで確認できませんでした。銀行は追加されていません。",
    productTypesRequired: "この操作の前に、有効な商品タイプを1件以上追加してください。",
    added: (count: number) => `${count}件の銀行を追加`,
    coverageAdded: (count: number) => `${count}件の coverage を追加`,
    rankingBasis: "ランキング基準",
    nationalRank: (rank: number) => `国内順位 #${rank}`,
    officialHomepage: "公式ホームページ",
    evidenceLink: "根拠",
    coverage: "Coverage",
    noCoverage: "Coverage なし",
    close: "完了",
    addMore: "さらに追加",
  },
} as const;

export function BankAiOnboardingDialogContent({
  countryCode,
  csrfToken,
  locale,
  productTypes,
  onCompleted,
  onClose,
}: BankAiOnboardingDialogContentProps) {
  const copy = AI_BANK_COPY[locale];
  const router = useRouter();
  const [count, setCount] = useState("3");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BankAiOnboardingResponse | null>(null);
  const productTypeLabelMap = useMemo(
    () => buildAdminProductTypeLabelMap(productTypes),
    [productTypes],
  );
  const countryName = useMemo(
    () => formatCountryName(countryCode, locale),
    [countryCode, locale],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);
    document.body.dataset.adminMutationPending = "true";

    try {
      const response = await fetch("/admin/banks/ai-onboard", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify({ count: Number(count) }),
      });
      const payload = (await response.json()) as {
        data?: BankAiOnboardingResponse;
        error?: { code?: string; message?: string };
      };
      if (!response.ok || !payload.data) {
        setError(localizeError(payload.error?.code, payload.error?.message, copy));
        return;
      }
      setResult(payload.data);
      onCompleted(payload.data);
      router.refresh();
    } catch {
      setError(copy.failed);
    } finally {
      setPending(false);
      delete document.body.dataset.adminMutationPending;
    }
  }

  if (result) {
    return (
      <div className="space-y-5">
        <section className="border-l-4 border-success bg-success-soft px-4 py-3" role="status">
          <p className="font-semibold text-success">{copy.added(result.added_count)}</p>
          <p className="mt-1 text-sm text-success">{copy.coverageAdded(result.coverage_item_count)}</p>
        </section>

        <section className="border-y border-border py-4">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            {copy.rankingBasis}
          </p>
          <p className="mt-2 text-sm font-semibold text-foreground">
            {result.ranking_basis.metric} · {result.ranking_basis.as_of_date}
          </p>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            {result.ranking_basis.summary}
          </p>
        </section>

        <div className="divide-y divide-border border-y border-border">
          {result.banks.map((item) => (
            <article className="grid gap-3 py-4" key={item.bank.bank_code}>
              <div className="flex min-w-0 items-start gap-3">
                <BankLogoMark
                  alt={item.bank.logo_alt_text ?? `${item.bank.bank_name} logo`}
                  bankCode={item.bank.bank_code}
                  bankName={item.bank.bank_name}
                  logoUrl={item.bank.logo_url}
                />
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-foreground">{item.bank.bank_name}</h3>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {copy.nationalRank(item.rank)} · {item.size_metric_label}: {item.size_metric_value} ({item.size_metric_as_of})
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm">
                <a
                  className="inline-flex items-center gap-1 font-medium text-primary underline-offset-4 hover:underline"
                  href={item.bank.homepage_url ?? item.homepage_source_url}
                  rel="noreferrer"
                  target="_blank"
                >
                  {copy.officialHomepage}
                  <ExternalLink aria-hidden="true" className="size-3.5" />
                </a>
                <a
                  className="inline-flex items-center gap-1 text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
                  href={item.ranking_source_url}
                  rel="noreferrer"
                  target="_blank"
                >
                  {copy.evidenceLink}
                  <ExternalLink aria-hidden="true" className="size-3.5" />
                </a>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground">{copy.coverage}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {item.coverage.length > 0 ? (
                    item.coverage.map((coverage) => (
                      <a
                        className="inline-flex min-h-9 items-center gap-1 rounded-md border border-border bg-background px-3 text-xs font-medium text-foreground hover:border-primary hover:text-primary"
                        href={coverage.source_url}
                        key={coverage.product_type}
                        rel="noreferrer"
                        target="_blank"
                      >
                        {formatAdminProductType(coverage.product_type, productTypeLabelMap)}
                        <ExternalLink aria-hidden="true" className="size-3" />
                      </a>
                    ))
                  ) : (
                    <span className="text-sm text-muted-foreground">{copy.noCoverage}</span>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>

        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button onClick={() => setResult(null)} variant="outline">
            {copy.addMore}
          </Button>
          <Button onClick={onClose}>{copy.close}</Button>
        </div>
      </div>
    );
  }

  return (
    <form aria-busy={pending} className="space-y-5" onSubmit={handleSubmit}>
      <section className="grid gap-4 border-y border-border py-4 sm:grid-cols-[minmax(0,1fr)_10rem] sm:items-end">
        <div className="flex gap-3">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
            <SearchCheck aria-hidden="true" className="size-5" />
          </span>
          <div>
            <p className="text-xs font-medium text-muted-foreground">{copy.currentCountry}</p>
            <p className="mt-1 font-semibold text-foreground">{countryName} · {countryCode}</p>
          </div>
        </div>
        <label className="grid gap-2 text-sm">
          <span className="font-medium text-foreground">{copy.count}</span>
          <select
            className="h-10 rounded-md border border-input bg-background px-3 text-sm text-foreground"
            disabled={pending}
            onChange={(event) => setCount(event.target.value)}
            value={count}
          >
            {Array.from({ length: 10 }, (_, index) => index + 1).map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
      </section>

      <div className="space-y-3 text-sm leading-6">
        <p className="text-foreground">{copy.help}</p>
        <p className="flex gap-2 text-muted-foreground">
          <Landmark aria-hidden="true" className="mt-1 size-4 shrink-0" />
          <span>{copy.excludes}</span>
        </p>
        <p className="flex gap-2 text-muted-foreground">
          <Sparkles aria-hidden="true" className="mt-1 size-4 shrink-0" />
          <span>{copy.evidence}</span>
        </p>
      </div>

      {pending ? (
        <p className="flex items-start gap-2 border-l-4 border-info bg-info-soft px-4 py-3 text-sm text-info" role="status">
          <Loader2 aria-hidden="true" className="mt-0.5 size-4 shrink-0 animate-spin" />
          <span>
            <strong className="block">{copy.pending}</strong>
            <span className="mt-1 block">{copy.pendingHelp}</span>
          </span>
        </p>
      ) : null}

      {error ? (
        <p aria-live="assertive" className="border-l-4 border-destructive bg-destructive/10 px-4 py-3 text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}

      <div className="flex justify-end">
        <Button disabled={pending} type="submit">
          {pending ? <Loader2 aria-hidden="true" className="animate-spin" /> : <Sparkles aria-hidden="true" />}
          {pending ? copy.pending : copy.submit}
        </Button>
      </div>
    </form>
  );
}

function formatCountryName(countryCode: string, locale: AdminLocale) {
  try {
    return new Intl.DisplayNames([locale], { type: "region" }).of(countryCode) ?? countryCode;
  } catch {
    return countryCode;
  }
}

function localizeError(
  code: string | undefined,
  fallback: string | undefined,
  copy: (typeof AI_BANK_COPY)[AdminLocale],
) {
  if (code === "ai_provider_unavailable") {
    return copy.unavailable;
  }
  if (code === "bank_ai_schema_not_ready") {
    return copy.schemaNotReady;
  }
  if (code === "bank_ai_results_insufficient") {
    return copy.insufficient;
  }
  if (code === "active_product_types_required") {
    return copy.productTypesRequired;
  }
  return fallback || copy.failed;
}
