import type { SourceCatalogCollectionLaunchResponse } from "./admin-api";
import type { AdminLocale } from "./admin-i18n";

const REASONS: Record<AdminLocale, Record<string, string>> = {
  en: {
    review_deferred: "previously deferred review",
    review_rejected: "previously rejected review",
    unresolved_product_boundary: "unresolved product identity",
    terminal_source_failure: "unresolved access or document error",
    source_not_found: "source no longer found",
    structural_zero_detail_requires_rediscovery: "no eligible product detail found previously",
    unknown: "source needs revalidation",
  },
  ko: {
    review_deferred: "이전 review 보류",
    review_rejected: "이전 review 반려",
    unresolved_product_boundary: "단일 상품 식별 불가",
    terminal_source_failure: "미해결 접근·문서 오류",
    source_not_found: "원문 페이지 없음",
    structural_zero_detail_requires_rediscovery: "이전 탐색에서 수집 가능한 상세 페이지 없음",
    unknown: "근거 재확인 필요",
  },
  ja: {
    review_deferred: "以前のレビュー保留",
    review_rejected: "以前のレビュー却下",
    unresolved_product_boundary: "単一商品の識別が未解決",
    terminal_source_failure: "アクセス・文書エラーが未解決",
    source_not_found: "参照ページが見つからない",
    structural_zero_detail_requires_rediscovery: "前回の探索で収集可能な商品詳細なし",
    unknown: "根拠の再確認が必要",
  },
};

export function collectionPreflightMessage(
  locale: AdminLocale,
  payload: SourceCatalogCollectionLaunchResponse | undefined,
): string | null {
  const skipped = payload?.skipped_items ?? [];
  if (!skipped.length) return null;
  const banks = [...new Set(skipped.map((item) => item.bank_code))];
  const bankSummary = banks.slice(0, 4).join(", ") + (banks.length > 4 ? " …" : "");
  const reasons = [...new Set(skipped.flatMap((item) => item.reason_codes))]
    .map((reason) => REASONS[locale][reason] ?? REASONS[locale].unknown).join("; ");
  const runs = payload?.run_ids.length ?? 0;
  if (locale === "ko") {
    return `${skipped.length}개 수집 범위(${bankSummary})를 건너뛰었습니다: ${reasons}. 생성 run ${runs}개. 근거를 확인한 뒤 정밀 재탐색으로 다시 시도할 수 있습니다.`;
  }
  if (locale === "ja") {
    return `${skipped.length}件の収集範囲（${bankSummary}）をスキップしました: ${reasons}。作成した run は${runs}件です。根拠を確認後、精密再探索で再試行できます。`;
  }
  return `Skipped ${skipped.length} collection scope(s) (${bankSummary}): ${reasons}. Created ${runs} run(s). Check the sources, then use precision rediscovery to try again.`;
}
