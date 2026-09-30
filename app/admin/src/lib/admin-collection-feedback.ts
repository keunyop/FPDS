import type { CollectionPreparation, SourceCatalogCollectionLaunchResponse } from "./admin-api";
import type { AdminLocale } from "./admin-i18n";

const REASONS: Record<AdminLocale, Record<string, string>> = {
  en: {
    collection_preparation_in_progress: "eligibility check already in progress",
    preparation_requires_rediscovery: "previous eligibility check needs revalidation",
    no_eligible_detail: "no eligible product detail",
    source_temporarily_unavailable: "source temporarily unavailable",
    preparation_unavailable: "eligibility check interrupted",
    coverage_changed: "coverage changed during the check",
    product_not_currently_offered: "no current official offering verified",
    review_deferred: "previously deferred review",
    review_rejected: "previously rejected review",
    unresolved_product_boundary: "unresolved product identity",
    terminal_source_failure: "unresolved access or document error",
    source_not_found: "source no longer found",
    structural_zero_detail_requires_rediscovery: "no eligible product detail found previously",
    unknown: "source needs revalidation",
  },
  ko: {
    collection_preparation_in_progress: "수집 가능 여부 확인 중",
    preparation_requires_rediscovery: "이전 검사 결과 재확인 필요",
    no_eligible_detail: "수집 가능한 단일 상품 상세 페이지 없음",
    source_temporarily_unavailable: "원문에 일시적으로 접근할 수 없음",
    preparation_unavailable: "사전 검사 중단",
    coverage_changed: "검사 도중 수집 범위 변경",
    product_not_currently_offered: "현재 공식 상품 제공 근거 없음",
    review_deferred: "이전 review 보류",
    review_rejected: "이전 review 반려",
    unresolved_product_boundary: "단일 상품 식별 불가",
    terminal_source_failure: "미해결 접근·문서 오류",
    source_not_found: "원문 페이지 없음",
    structural_zero_detail_requires_rediscovery: "이전 탐색에서 수집 가능한 상세 페이지 없음",
    unknown: "근거 재확인 필요",
  },
  ja: {
    collection_preparation_in_progress: "収集可否を確認中",
    preparation_requires_rediscovery: "前回の確認結果の再検証が必要",
    no_eligible_detail: "収集可能な単一商品の詳細なし",
    source_temporarily_unavailable: "参照ページに一時的にアクセス不可",
    preparation_unavailable: "事前確認が中断",
    coverage_changed: "確認中に収集範囲が変更",
    product_not_currently_offered: "現在の公式商品提供を確認できず",
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
  if (payload?.workflow_state === "preparing") {
    const checking = collectionPreparationMessage(locale, { status: "queued" });
    if (!skipped.length) return checking;
    return `${checking} ${collectionPreflightMessage(locale, { ...payload, workflow_state: "skipped" })}`;
  }
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

export function collectionPreparationMessage(
  locale: AdminLocale,
  state: CollectionPreparation | undefined,
): string | null {
  if (!state?.status) return null;
  const pending = state.status === "queued" || state.status === "checking";
  const interrupted = pending && state.updated_at
    && Date.now() - new Date(state.updated_at).getTime() > 2 * 60 * 60 * 1000;
  const reasons = (state.reason_codes ?? []).map((reason) => REASONS[locale][reason] ?? REASONS[locale].unknown).join("; ");
  const hasRun = Boolean(state.run_id);
  if (locale === "ko") {
    if (interrupted) return "사전 검사가 지연됐거나 중단됐습니다. 다시 수집을 요청할 수 있습니다.";
    if (pending) return "수집 가능 여부 확인 중입니다. 상품 상세 페이지와 접근 검사를 통과하면 run을 생성합니다. 결과는 은행 목록과 coverage에서 확인할 수 있습니다.";
    if (hasRun) return `수집 run을 생성했습니다.${state.excluded_sources?.length ? ` 접근할 수 없는 소스 ${state.excluded_sources.length}개는 제외했습니다.` : ""}`;
    return `수집을 시작하지 않았습니다: ${reasons || REASONS.ko.unknown}. ${state.retryable ? "다시 수집을 요청할 수 있습니다." : "근거를 확인한 뒤 정밀 재탐색으로 재검사할 수 있습니다."}`;
  }
  if (locale === "ja") {
    if (interrupted) return "事前確認が遅延または中断しました。収集を再度要求できます。";
    if (pending) return "収集可否を確認中です。商品詳細とアクセスの確認後に run を作成します。結果は銀行一覧と coverage で確認できます。";
    if (hasRun) return `収集 run を作成しました。${state.excluded_sources?.length ? `アクセスできない参照元${state.excluded_sources.length}件を除外しました。` : ""}`;
    return `収集を開始しませんでした: ${reasons || REASONS.ja.unknown}。${state.retryable ? "収集を再度要求できます。" : "根拠を確認し、精密再探索で再検証できます。"}`;
  }
  if (interrupted) return "The eligibility check was delayed or interrupted. You can request collection again.";
  if (pending) return "Checking collection eligibility. A run is created after product detail and source access checks pass. See results in the bank list and coverage.";
  if (hasRun) return `Collection run created.${state.excluded_sources?.length ? ` Excluded ${state.excluded_sources.length} unavailable source(s).` : ""}`;
  return `Collection did not start: ${reasons || REASONS.en.unknown}. ${state.retryable ? "You can request collection again." : "Check the evidence, then use precision rediscovery to revalidate."}`;
}
