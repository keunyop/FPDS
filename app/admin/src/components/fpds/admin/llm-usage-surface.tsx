"use client";

import { Coins, Database, Gauge, TriangleAlert } from "lucide-react";
import Link from "next/link";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { AdminTableAutoRefresh } from "@/components/fpds/admin/admin-table-auto-refresh";
import { AdminStatStrip } from "@/components/fpds/admin/admin-stat-strip";
import { Button } from "@/components/ui/button";
import type { LlmUsageDashboardResponse } from "@/lib/admin-api";
import {
  buildAdminHref,
  formatAdminDateTimeValue,
  getAdminIntlLocale,
  type AdminLocale,
} from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

export type LlmUsagePageFilters = {
  search: string;
  from: string;
  to: string;
  runId: string;
  agentName: string;
  modelName: string;
  providerName: string;
  stage: string;
};

type LlmUsageSurfaceProps = {
  filters: LlmUsagePageFilters;
  locale: AdminLocale;
  usage: LlmUsageDashboardResponse;
};

type UsageRow = Record<string, unknown>;

const USAGE_COPY = {
  en: {
    path: ["Observability", "Usage"],
    title: "LLM usage",
    description: "Trace spend pressure, errors, concentration, and movement before opening run-level evidence.",
    records: "Usage records",
    recordsNote: "Rows in scope",
    tokens: "Total tokens",
    tokensNote: "Prompt + completion",
    average: "Average tokens / row",
    averageNote: "Density in scope",
    zeroRows: "Zero-token rows",
    zeroRowsNote: "Instrumentation check",
    attention: "Operational signals",
    attentionDescription: "The current cost window, outliers, concentration, and latest movement in decision order.",
    estimatedCost: "Estimated cost",
    estimatedSpend: "Current scoped spend",
    anomalyCandidates: "Anomaly candidates",
    investigateOutliers: "Rows requiring inspection",
    topModel: "Top model concentration",
    noModelRows: "No model rows",
    latestTrend: "Latest trend signal",
    noTrendRows: "No trend rows",
    noSignal: "No signal",
    filters: "Scope controls",
    filtersDescription: "Narrow the evidence window without changing usage records.",
    resetScope: "Reset scope",
    search: "Search",
    searchPlaceholder: "usage id, request id, product, review, bank",
    from: "From",
    to: "To",
    runId: "Run ID",
    runIdPlaceholder: "run id",
    agentName: "Agent name",
    modelName: "Model name",
    provider: "Provider",
    stage: "Stage",
    quickScopes: "Quick scopes",
    extraction: "Extraction",
    normalization: "Normalization",
    validation: "Validation",
    apply: "Apply",
    clear: "Clear",
    active: "Active",
    currentWindow: "Current window",
    start: "Start",
    now: "Now",
    promptTokens: "Prompt tokens",
    completionTokens: "Completion tokens",
    totalTokens: "Total tokens",
    avgTokens: "Avg tokens / row",
    trend: "Trend",
    trendTitle: "Cost and volume movement",
    trendDescription: "Daily buckets expose movement and instrumentation gaps before concentration drilldown.",
    latestBucket: "Latest bucket",
    latestCost: "Latest cost",
    latestSignal: "Latest signal",
    noTrendTitle: "No trend evidence",
    noTrendCopy: "Expand the date range or clear filters to recover the usage timeline.",
    anomalies: "Anomalies",
    anomalyTitle: "Outliers to investigate",
    anomalyDescription: "Start with unusual spend or token rows, then open the linked review or run evidence.",
    noAnomalyTitle: "No anomaly candidates",
    noAnomalyCopy: "The current scope did not return unusual usage rows.",
    signal: "Signal",
    context: "Context",
    observed: "Observed",
    reviewContext: "Review context",
    action: "Action",
    bucket: "Bucket",
    volume: "Volume",
    cost: "Cost",
    scope: "Scope",
    recordsColumn: "Records",
    delta: "Delta",
    model: "Model",
    agent: "Agent",
    run: "Run",
    lastSeen: "Last seen",
    concentration: "Concentration",
    modelTitle: "Model concentration",
    modelDescription: "Compare model share to find a dominant cost source.",
    agentTitle: "Agent concentration",
    agentDescription: "Locate the orchestration layer creating token and cost pressure.",
    runTitle: "Run-linked spend",
    runDescription: "Move from a high-cost execution window to its diagnostic evidence.",
    noModelTitle: "No model aggregation",
    noModelCopy: "Broaden the date range or clear the model filter.",
    noAgentTitle: "No agent aggregation",
    noAgentCopy: "Broaden the scope to recover agent context.",
    noRunTitle: "No run aggregation",
    noRunCopy: "Widen the scope or clear the run filter.",
    focusModel: "Focus model",
    focusAgent: "Focus agent",
    openRun: "Open run",
    openReview: "Open review",
    noDrilldown: "No linked evidence",
    rows: "rows",
    runs: "runs",
    candidates: "candidates",
    score: "Score",
    tokenDelta: "tokens",
    costDelta: "cost",
    runType: "Run type",
    noStage: "No stage context",
    noModel: "No model context",
    noProduct: "No product context",
    noReviewState: "No linked review state",
    noValidation: "No validation context",
    noQueueReason: "No queue reason",
    noTrendNote: "No trend note stored.",
    noAnomalyReason: "No anomaly reason stored.",
    missing: "n/a",
  },
  ko: {
    path: ["관찰 가능성", "사용량"],
    title: "LLM 사용량",
    description: "실행 근거를 열기 전에 비용 압력, 오류, 집중도와 추세를 추적합니다.",
    records: "사용 기록",
    recordsNote: "현재 범위의 행",
    tokens: "총 토큰",
    tokensNote: "프롬프트 + 완료",
    average: "행당 평균 토큰",
    averageNote: "현재 범위 밀도",
    zeroRows: "토큰 0인 행",
    zeroRowsNote: "계측 상태 확인",
    attention: "운영 신호",
    attentionDescription: "비용, 이상치, 집중도, 최신 추세 순으로 현재 범위를 점검합니다.",
    estimatedCost: "예상 비용",
    estimatedSpend: "현재 범위의 예상 지출",
    anomalyCandidates: "이상 후보",
    investigateOutliers: "확인이 필요한 행",
    topModel: "최상위 모델 집중도",
    noModelRows: "모델 데이터 없음",
    latestTrend: "최신 추세 신호",
    noTrendRows: "추세 데이터 없음",
    noSignal: "신호 없음",
    filters: "범위 설정",
    filtersDescription: "사용 기록을 변경하지 않고 조회할 근거 범위를 좁힙니다.",
    resetScope: "범위 초기화",
    search: "검색",
    searchPlaceholder: "사용 ID, 요청 ID, 상품, 검토, 은행",
    from: "시작일",
    to: "종료일",
    runId: "실행 ID",
    runIdPlaceholder: "실행 ID",
    agentName: "에이전트명",
    modelName: "모델명",
    provider: "제공자",
    stage: "단계",
    quickScopes: "빠른 범위",
    extraction: "추출",
    normalization: "정규화",
    validation: "검증",
    apply: "적용",
    clear: "지우기",
    active: "적용됨",
    currentWindow: "현재 범위",
    start: "시작",
    now: "현재",
    promptTokens: "프롬프트 토큰",
    completionTokens: "완료 토큰",
    totalTokens: "총 토큰",
    avgTokens: "행당 평균 토큰",
    trend: "추세",
    trendTitle: "비용 및 사용량 추세",
    trendDescription: "일별 변화와 계측 공백을 먼저 확인한 뒤 집중도를 진단합니다.",
    latestBucket: "최신 구간",
    latestCost: "최신 비용",
    latestSignal: "최신 신호",
    noTrendTitle: "추세 근거 없음",
    noTrendCopy: "날짜 범위를 넓히거나 필터를 지워 사용량 타임라인을 확인하세요.",
    anomalies: "이상치",
    anomalyTitle: "조사할 이상치",
    anomalyDescription: "비정상 비용 또는 토큰 행부터 확인한 뒤 연결된 검토나 실행 근거를 엽니다.",
    noAnomalyTitle: "이상 후보 없음",
    noAnomalyCopy: "현재 범위에서 비정상 사용 행이 발견되지 않았습니다.",
    signal: "신호",
    context: "맥락",
    observed: "관측값",
    reviewContext: "검토 맥락",
    action: "작업",
    bucket: "구간",
    volume: "사용량",
    cost: "비용",
    scope: "범위",
    recordsColumn: "기록",
    delta: "변화",
    model: "모델",
    agent: "에이전트",
    run: "실행",
    lastSeen: "최근 관측",
    concentration: "집중도",
    modelTitle: "모델 집중도",
    modelDescription: "모델별 비중을 비교해 지배적인 비용 원인을 찾습니다.",
    agentTitle: "에이전트 집중도",
    agentDescription: "토큰과 비용 압력을 만드는 오케스트레이션 계층을 찾습니다.",
    runTitle: "실행별 비용",
    runDescription: "고비용 실행 구간에서 진단 근거로 바로 이동합니다.",
    noModelTitle: "모델 집계 없음",
    noModelCopy: "날짜 범위를 넓히거나 모델 필터를 지우세요.",
    noAgentTitle: "에이전트 집계 없음",
    noAgentCopy: "범위를 넓혀 에이전트 맥락을 확인하세요.",
    noRunTitle: "실행 집계 없음",
    noRunCopy: "범위를 넓히거나 실행 필터를 지우세요.",
    focusModel: "모델로 좁히기",
    focusAgent: "에이전트로 좁히기",
    openRun: "실행 열기",
    openReview: "검토 열기",
    noDrilldown: "연결된 근거 없음",
    rows: "행",
    runs: "실행",
    candidates: "후보",
    score: "점수",
    tokenDelta: "토큰",
    costDelta: "비용",
    runType: "실행 유형",
    noStage: "단계 맥락 없음",
    noModel: "모델 맥락 없음",
    noProduct: "상품 맥락 없음",
    noReviewState: "연결된 검토 상태 없음",
    noValidation: "검증 맥락 없음",
    noQueueReason: "대기열 사유 없음",
    noTrendNote: "저장된 추세 메모가 없습니다.",
    noAnomalyReason: "저장된 이상 사유가 없습니다.",
    missing: "없음",
  },
  ja: {
    path: ["オブザーバビリティ", "使用量"],
    title: "LLM 使用量",
    description: "実行証跡を開く前に、コスト圧力、異常、集中度、推移を追跡します。",
    records: "使用記録",
    recordsNote: "現在の範囲の行",
    tokens: "総トークン",
    tokensNote: "プロンプト + 完了",
    average: "行あたり平均トークン",
    averageNote: "現在範囲の密度",
    zeroRows: "ゼロトークン行",
    zeroRowsNote: "計測状態の確認",
    attention: "運用シグナル",
    attentionDescription: "コスト、異常、集中度、最新推移の順で現在範囲を確認します。",
    estimatedCost: "推定コスト",
    estimatedSpend: "現在範囲の推定支出",
    anomalyCandidates: "異常候補",
    investigateOutliers: "確認が必要な行",
    topModel: "上位モデル集中度",
    noModelRows: "モデルデータなし",
    latestTrend: "最新の推移シグナル",
    noTrendRows: "推移データなし",
    noSignal: "シグナルなし",
    filters: "範囲設定",
    filtersDescription: "使用記録を変更せず、確認する証跡の範囲を絞ります。",
    resetScope: "範囲をリセット",
    search: "検索",
    searchPlaceholder: "使用 ID、リクエスト ID、商品、レビュー、銀行",
    from: "開始日",
    to: "終了日",
    runId: "実行 ID",
    runIdPlaceholder: "実行 ID",
    agentName: "エージェント名",
    modelName: "モデル名",
    provider: "プロバイダー",
    stage: "ステージ",
    quickScopes: "クイック範囲",
    extraction: "抽出",
    normalization: "正規化",
    validation: "検証",
    apply: "適用",
    clear: "クリア",
    active: "適用中",
    currentWindow: "現在の範囲",
    start: "開始",
    now: "現在",
    promptTokens: "プロンプトトークン",
    completionTokens: "完了トークン",
    totalTokens: "総トークン",
    avgTokens: "行あたり平均トークン",
    trend: "推移",
    trendTitle: "コストと使用量の推移",
    trendDescription: "日次変化と計測の欠落を先に確認してから集中度を診断します。",
    latestBucket: "最新区間",
    latestCost: "最新コスト",
    latestSignal: "最新シグナル",
    noTrendTitle: "推移の証跡なし",
    noTrendCopy: "日付範囲を広げるかフィルターを解除してタイムラインを確認してください。",
    anomalies: "異常",
    anomalyTitle: "調査する異常",
    anomalyDescription: "異常なコストまたはトークン行から確認し、関連レビューや実行証跡を開きます。",
    noAnomalyTitle: "異常候補なし",
    noAnomalyCopy: "現在の範囲では異常な使用行は見つかりませんでした。",
    signal: "シグナル",
    context: "コンテキスト",
    observed: "観測値",
    reviewContext: "レビュー情報",
    action: "操作",
    bucket: "区間",
    volume: "使用量",
    cost: "コスト",
    scope: "範囲",
    recordsColumn: "記録",
    delta: "変化",
    model: "モデル",
    agent: "エージェント",
    run: "実行",
    lastSeen: "最終観測",
    concentration: "集中度",
    modelTitle: "モデル集中度",
    modelDescription: "モデル別の比率を比較し、主要なコスト要因を特定します。",
    agentTitle: "エージェント集中度",
    agentDescription: "トークンとコスト圧力を生むオーケストレーション層を特定します。",
    runTitle: "実行別コスト",
    runDescription: "高コストの実行区間から診断証跡へ直接移動します。",
    noModelTitle: "モデル集計なし",
    noModelCopy: "日付範囲を広げるかモデルフィルターを解除してください。",
    noAgentTitle: "エージェント集計なし",
    noAgentCopy: "範囲を広げてエージェント情報を確認してください。",
    noRunTitle: "実行集計なし",
    noRunCopy: "範囲を広げるか実行フィルターを解除してください。",
    focusModel: "モデルに絞る",
    focusAgent: "エージェントに絞る",
    openRun: "実行を開く",
    openReview: "レビューを開く",
    noDrilldown: "関連証跡なし",
    rows: "行",
    runs: "実行",
    candidates: "候補",
    score: "スコア",
    tokenDelta: "トークン",
    costDelta: "コスト",
    runType: "実行タイプ",
    noStage: "ステージ情報なし",
    noModel: "モデル情報なし",
    noProduct: "商品情報なし",
    noReviewState: "関連レビュー状態なし",
    noValidation: "検証情報なし",
    noQueueReason: "キュー理由なし",
    noTrendNote: "保存された推移メモはありません。",
    noAnomalyReason: "保存された異常理由はありません。",
    missing: "なし",
  },
} satisfies Record<AdminLocale, Record<string, string | readonly string[]>>;

export function LlmUsageSurface({ filters, locale, usage }: LlmUsageSurfaceProps) {
  const copy = USAGE_COPY[locale];
  const modelRows = usage.by_model ?? [];
  const agentRows = usage.by_agent ?? [];
  const runRows = usage.by_run ?? [];
  const trendRows = usage.usage_trend ?? usage.trend ?? [];
  const anomalyRows = usage.anomaly_candidates ?? [];
  const totals = usage.totals ?? {};
  const totalTokens = readNumber(totals, ["total_tokens", "token_total", "tokens"]) ?? 0;
  const totalCost = readNumber(totals, ["estimated_cost", "cost_total", "total_cost"]) ?? 0;
  const topModel = topUsageRow(modelRows);
  const latestTrend = trendRows.at(-1) ?? null;
  const maxTokenVolume = maxTokens(trendRows);
  const activeFilters = Object.values(filters).filter(Boolean).length;

  const statItems = [
    {
      label: copy.records as string,
      value: formatCount(locale, readNumber(totals, ["usage_record_count", "record_count", "count"])),
      note: copy.recordsNote as string,
      tone: "info" as const,
      icon: Database,
    },
    {
      label: copy.tokens as string,
      value: formatTokens(locale, totalTokens),
      note: copy.tokensNote as string,
      tone: "success" as const,
      icon: Gauge,
    },
    {
      label: copy.average as string,
      value: formatTokens(locale, readNumber(totals, ["average_tokens_per_record"])),
      note: copy.averageNote as string,
      tone: "neutral" as const,
      icon: Coins,
    },
    {
      label: copy.zeroRows as string,
      value: formatCount(locale, readNumber(totals, ["zero_token_records"])),
      note: copy.zeroRowsNote as string,
      tone: "warning" as const,
      icon: TriangleAlert,
    },
  ];

  return (
    <section className="grid min-w-0 gap-6">
      <AdminTableAutoRefresh locale={locale} />

      <AdminPageHeader
        description={copy.description as string}
        path={[...(copy.path as readonly string[])]}
        title={copy.title as string}
      />

      <section aria-labelledby="usage-attention-title" className="overflow-hidden rounded-lg border border-border bg-card">
        <div className="flex flex-col gap-1 border-b border-border px-4 py-3 sm:px-5">
          <h2 className="text-base font-semibold text-foreground" id="usage-attention-title">{copy.attention}</h2>
          <p className="text-sm text-muted-foreground">{copy.attentionDescription}</p>
        </div>
        <div className="grid divide-y divide-border lg:grid-cols-4 lg:divide-x lg:divide-y-0">
          <SignalItem
            label={copy.estimatedCost as string}
            note={copy.estimatedSpend as string}
            tone="warning"
            value={formatCost(locale, totalCost)}
          />
          <SignalItem
            label={copy.anomalyCandidates as string}
            note={copy.investigateOutliers as string}
            tone={anomalyRows.length > 0 ? "danger" : "neutral"}
            value={formatCount(locale, readNumber(totals, ["anomaly_candidate_count", "anomaly_count"]), anomalyRows.length)}
          />
          <SignalItem
            label={copy.topModel as string}
            note={topModel ? rowLabel(topModel, "model_name", copy.model as string) : copy.noModelRows as string}
            tone="neutral"
            value={topModel ? formatPercent(locale, readNumber(topModel, ["cost_share_percent"])) : copy.missing as string}
          />
          <SignalItem
            label={copy.latestTrend as string}
            note={latestTrend ? formatTimestamp(readText(latestTrend, ["interval_start", "bucket_date", "date"])) : copy.noTrendRows as string}
            tone={latestTrend ? signalTone(latestTrend) : "neutral"}
            value={latestTrend ? rowSignal(latestTrend, copy.noSignal as string) : copy.missing as string}
          />
        </div>
      </section>

      <AdminStatStrip framed={false} items={statItems} />

      <section className="rounded-lg border border-border bg-card p-4 sm:p-5">
        <div className="flex flex-col gap-3 border-b border-border pb-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-base font-semibold text-foreground">{copy.filters}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{copy.filtersDescription}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {activeFilters > 0 ? (
              <span className="rounded-md bg-info-soft px-2.5 py-1 text-xs font-medium text-info">
                {copy.active} · {formatCount(locale, activeFilters)}
              </span>
            ) : null}
            <Button asChild size="sm" variant="outline">
              <Link href={usageHref(locale, filters, emptyFilters())}>{copy.resetScope}</Link>
            </Button>
          </div>
        </div>

        <form action="/admin/usage" className="mt-4 grid min-w-0 gap-4">
          {locale !== "en" ? <input name="locale" type="hidden" value={locale} /> : null}
          <div className="grid min-w-0 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <FilterField label={copy.search as string}>
              <input className={inputClasses} defaultValue={filters.search} name="q" placeholder={copy.searchPlaceholder as string} type="search" />
            </FilterField>
            <FilterField label={copy.from as string}>
              <input className={inputClasses} defaultValue={filters.from} name="from" type="date" />
            </FilterField>
            <FilterField label={copy.to as string}>
              <input className={inputClasses} defaultValue={filters.to} name="to" type="date" />
            </FilterField>
            <FilterField label={copy.runId as string}>
              <input className={inputClasses} defaultValue={filters.runId} name="run_id" placeholder={copy.runIdPlaceholder as string} type="text" />
            </FilterField>
            <FilterField label={copy.agentName as string}>
              <input className={inputClasses} defaultValue={filters.agentName} name="agent_name" placeholder="extraction-agent" type="text" />
            </FilterField>
            <FilterField label={copy.modelName as string}>
              <input className={inputClasses} defaultValue={filters.modelName} name="model_name" placeholder="gpt-4.1-mini" type="text" />
            </FilterField>
            <FilterField label={copy.provider as string}>
              <input className={inputClasses} defaultValue={filters.providerName} name="provider_name" placeholder="openai" type="text" />
            </FilterField>
            <FilterField label={copy.stage as string}>
              <input className={inputClasses} defaultValue={filters.stage} name="stage" placeholder="validation_routing" type="text" />
            </FilterField>
          </div>
          <div className="flex flex-col gap-3 border-t border-border pt-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-medium text-muted-foreground">{copy.quickScopes}</span>
              <Button asChild size="sm" variant="outline">
                <Link href={usageHref(locale, filters, { stage: "extraction" })}>{copy.extraction}</Link>
              </Button>
              <Button asChild size="sm" variant="outline">
                <Link href={usageHref(locale, filters, { stage: "normalization" })}>{copy.normalization}</Link>
              </Button>
              <Button asChild size="sm" variant="outline">
                <Link href={usageHref(locale, filters, { stage: "validation_routing" })}>{copy.validation}</Link>
              </Button>
            </div>
            <div className="flex gap-2">
              <Button type="submit">{copy.apply}</Button>
              <Button asChild variant="outline">
                <Link href={usageHref(locale, filters, emptyFilters())}>{copy.clear}</Link>
              </Button>
            </div>
          </div>
        </form>
      </section>

      <section aria-labelledby="usage-window-title" className="overflow-hidden rounded-lg border border-border bg-card">
        <div className="flex flex-col gap-2 border-b border-border px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5">
          <h2 className="text-base font-semibold text-foreground" id="usage-window-title">{copy.currentWindow}</h2>
          {filters.from || filters.to ? (
            <span className="w-fit rounded-md bg-warning-soft px-2.5 py-1 text-xs font-medium text-warning">
              {filters.from || copy.start} — {filters.to || copy.now}
            </span>
          ) : null}
        </div>
        <dl className="grid divide-y divide-border sm:grid-cols-2 sm:divide-x sm:divide-y-0 lg:grid-cols-4">
          <Metric label={copy.promptTokens as string} value={formatTokens(locale, readNumber(totals, ["prompt_tokens"]))} />
          <Metric label={copy.completionTokens as string} value={formatTokens(locale, readNumber(totals, ["completion_tokens"]))} />
          <Metric label={copy.totalTokens as string} value={formatTokens(locale, totalTokens)} />
          <Metric label={copy.avgTokens as string} value={formatTokens(locale, readNumber(totals, ["average_tokens_per_record"]))} />
        </dl>
      </section>

      <div className="grid min-w-0 gap-6 xl:grid-cols-[1.08fr_0.92fr]">
        <DataSection
          description={copy.trendDescription as string}
          eyebrow={copy.trend as string}
          title={copy.trendTitle as string}
        >
          {trendRows.length === 0 ? (
            <EmptySection copy={copy.noTrendCopy as string} title={copy.noTrendTitle as string} />
          ) : (
            <div className="max-w-full overflow-x-auto">
              <table aria-label={copy.trendTitle as string} className="min-w-[880px] table-fixed">
                <thead>
                  <tr>
                    <TableHead>{copy.bucket}</TableHead>
                    <TableHead>{copy.volume}</TableHead>
                    <TableHead>{copy.cost}</TableHead>
                    <TableHead>{copy.recordsColumn}</TableHead>
                    <TableHead>{copy.delta}</TableHead>
                    <TableHead>{copy.signal}</TableHead>
                  </tr>
                </thead>
                <tbody>
                  {trendRows.map((row, index) => {
                    const tokens = readNumber(row, ["total_tokens", "tokens", "token_total"]);
                    const width = maxTokenVolume > 0 && tokens !== null ? Math.max(5, Math.round((tokens / maxTokenVolume) * 100)) : 0;
                    return (
                      <tr className="align-top" key={rowKey(row, index, ["period", "bucket_date", "date"])}>
                        <TableCell>
                          <p className="font-medium text-foreground">{rowText(row, ["period", "bucket_date"], copy.bucket as string)}</p>
                          <p className="mt-1 text-xs text-muted-foreground">{formatTimestamp(readText(row, ["interval_start", "bucket_date", "date"]))}</p>
                        </TableCell>
                        <TableCell>
                          <div className="h-1.5 rounded-full bg-muted"><div className="h-1.5 rounded-full bg-primary" style={{ width: `${width}%` }} /></div>
                          <p className="mt-2 font-mono text-xs font-semibold text-foreground">{formatTokens(locale, tokens)}</p>
                        </TableCell>
                        <TableCell><span className="font-mono text-xs font-semibold">{formatCost(locale, readNumber(row, ["estimated_cost", "cost", "total_cost"]))}</span></TableCell>
                        <TableCell>
                          <p>{formatCount(locale, readNumber(row, ["record_count", "usage_record_count", "count"]))} {copy.rows}</p>
                          <p className="mt-1 text-xs text-muted-foreground">{formatCount(locale, readNumber(row, ["run_count"]))} {copy.runs}</p>
                        </TableCell>
                        <TableCell>
                          <p>{formatSignedPercent(locale, readNumber(row, ["token_delta_percent"]))} {copy.tokenDelta}</p>
                          <p className="mt-1 text-xs text-muted-foreground">{formatSignedPercent(locale, readNumber(row, ["cost_delta_percent"]))} {copy.costDelta}</p>
                        </TableCell>
                        <TableCell>
                          <StatusBadge row={row} />
                          <p className="mt-2 max-w-48 text-xs text-muted-foreground">{rowSummary(row, copy.noTrendNote as string)}</p>
                        </TableCell>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </DataSection>

        <DataSection
          description={copy.anomalyDescription as string}
          eyebrow={copy.anomalies as string}
          title={copy.anomalyTitle as string}
        >
          {anomalyRows.length === 0 ? (
            <EmptySection copy={copy.noAnomalyCopy as string} title={copy.noAnomalyTitle as string} />
          ) : (
            <div className="max-w-full overflow-x-auto">
              <table aria-label={copy.anomalyTitle as string} className="min-w-[760px] table-fixed">
                <thead>
                  <tr>
                    <TableHead>{copy.signal}</TableHead>
                    <TableHead>{copy.context}</TableHead>
                    <TableHead>{copy.observed}</TableHead>
                    <TableHead>{copy.action}</TableHead>
                  </tr>
                </thead>
                <tbody>
                  {anomalyRows.map((row, index) => (
                    <tr className="align-top" key={rowKey(row, index, ["signal", "reason", "run_id"])}>
                      <TableCell>
                        <StatusBadge row={row} />
                        <p className="mt-2 text-sm text-foreground">{rowSummary(row, copy.noAnomalyReason as string)}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{copy.score} {formatCount(locale, readNumber(row, ["anomaly_score"]))}</p>
                      </TableCell>
                      <TableCell>
                        <p className="font-mono text-xs font-semibold text-foreground">{rowLabel(row, "run_id", copy.run as string)}</p>
                        <p className="mt-1">{rowText(row, ["agent_name", "agent_names"], copy.agent as string)}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{rowText(row, ["product_name"], copy.noProduct as string)}</p>
                      </TableCell>
                      <TableCell>
                        <p className="font-mono text-xs font-semibold">{formatTokens(locale, readNumber(row, ["total_tokens", "observed_total_tokens", "tokens"]))}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{formatCost(locale, readNumber(row, ["estimated_cost", "observed_cost", "cost"]))}</p>
                        <p className="mt-2 text-xs text-muted-foreground">{rowText(row, ["validation_status"], copy.noValidation as string)}</p>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-2">
                          {rowLinkToReview(row, locale) ? <Button asChild size="sm" variant="outline"><Link href={rowLinkToReview(row, locale)!}>{copy.openReview}</Link></Button> : null}
                          {rowLinkToRun(row, locale) ? <Button asChild size="sm" variant="outline"><Link href={rowLinkToRun(row, locale)!}>{copy.openRun}</Link></Button> : null}
                          {!rowLinkToReview(row, locale) && !rowLinkToRun(row, locale) ? <span className="text-xs text-muted-foreground">{copy.noDrilldown}</span> : null}
                        </div>
                      </TableCell>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </DataSection>
      </div>

      <DataSection
        description={copy.modelDescription as string}
        eyebrow={copy.concentration as string}
        title={copy.modelTitle as string}
      >
        {modelRows.length === 0 ? (
          <EmptySection copy={copy.noModelCopy as string} title={copy.noModelTitle as string} />
        ) : (
          <ConcentrationTable
            copy={copy}
            filters={filters}
            locale={locale}
            rows={modelRows}
            totalCost={totalCost}
            totalTokens={totalTokens}
            type="model"
          />
        )}
      </DataSection>

      <div className="grid min-w-0 gap-6 xl:grid-cols-2">
        <DataSection
          description={copy.agentDescription as string}
          eyebrow={copy.concentration as string}
          title={copy.agentTitle as string}
        >
          {agentRows.length === 0 ? (
            <EmptySection copy={copy.noAgentCopy as string} title={copy.noAgentTitle as string} />
          ) : (
            <ConcentrationTable copy={copy} filters={filters} locale={locale} rows={agentRows} totalCost={totalCost} totalTokens={totalTokens} type="agent" />
          )}
        </DataSection>
        <DataSection
          description={copy.runDescription as string}
          eyebrow={copy.concentration as string}
          title={copy.runTitle as string}
        >
          {runRows.length === 0 ? (
            <EmptySection copy={copy.noRunCopy as string} title={copy.noRunTitle as string} />
          ) : (
            <ConcentrationTable copy={copy} filters={filters} locale={locale} rows={runRows} totalCost={totalCost} totalTokens={totalTokens} type="run" />
          )}
        </DataSection>
      </div>
    </section>
  );
}

type UsageCopy = (typeof USAGE_COPY)[AdminLocale];

function ConcentrationTable({
  copy,
  filters,
  locale,
  rows,
  totalCost,
  totalTokens,
  type,
}: {
  copy: UsageCopy;
  filters: LlmUsagePageFilters;
  locale: AdminLocale;
  rows: UsageRow[];
  totalCost: number;
  totalTokens: number;
  type: "model" | "agent" | "run";
}) {
  const label = type === "model" ? copy.model : type === "agent" ? copy.agent : copy.run;
  return (
    <div className="max-w-full overflow-x-auto">
      <table aria-label={label as string} className="min-w-[760px] table-fixed">
        <thead><tr><TableHead>{label}</TableHead><TableHead>{copy.scope}</TableHead><TableHead>{copy.tokens}</TableHead><TableHead>{copy.cost}</TableHead><TableHead>{copy.action}</TableHead></tr></thead>
        <tbody>
          {rows.map((row, index) => {
            const identityKey = type === "model" ? "model_name" : type === "agent" ? "agent_name" : "run_id";
            const identity = rowLabel(row, identityKey, label as string);
            const href = type === "run"
              ? rowLinkToRun(row, locale)
              : usageHref(locale, filters, type === "model" ? { modelName: readText(row, ["model_name"]), runId: "", search: "" } : { agentName: readText(row, ["agent_name"]), runId: "", search: "" });
            return (
              <tr className="align-top" key={rowKey(row, index, [identityKey, "name"])}>
                <TableCell>
                  {type === "run" && href ? <Link className="font-mono text-xs font-semibold text-foreground underline-offset-4 hover:text-primary hover:underline" href={href}>{identity}</Link> : <p className="font-medium text-foreground">{identity}</p>}
                  <p className="mt-1 text-xs text-muted-foreground">
                    {type === "model"
                      ? rowText(row, ["provider_name"], copy.provider as string)
                      : type === "agent"
                        ? rowText(row, ["stage_names"], copy.noStage as string)
                        : rowText(row, ["run_type", "run_state"], copy.runType as string)}
                  </p>
                </TableCell>
                <TableCell>
                  <p>{formatCount(locale, readNumber(row, ["usage_record_count", "record_count", "count"]))} {copy.rows}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{formatCount(locale, readNumber(row, ["run_count", "run_total"]))} {copy.runs}</p>
                </TableCell>
                <TableCell><ShareCell locale={locale} share={readNumber(row, ["token_share_percent"]) ?? safeShare(readNumber(row, ["total_tokens"]), totalTokens)} value={formatTokens(locale, readNumber(row, ["total_tokens", "tokens", "token_total"]))} /></TableCell>
                <TableCell><ShareCell locale={locale} share={readNumber(row, ["cost_share_percent"]) ?? safeShare(readNumber(row, ["estimated_cost"]), totalCost)} tone="warning" value={formatCost(locale, readNumber(row, ["estimated_cost", "cost", "total_cost"]))} /></TableCell>
                <TableCell>{href ? <Button asChild size="sm" variant="outline"><Link href={href}>{type === "model" ? copy.focusModel : type === "agent" ? copy.focusAgent : copy.openRun}</Link></Button> : <span className="text-xs text-muted-foreground">{copy.noDrilldown}</span>}</TableCell>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

const inputClasses = "h-10 min-w-0 rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none placeholder:text-muted-foreground focus:border-ring focus:ring-2 focus:ring-ring/30";

function FilterField({ children, label }: { children: React.ReactNode; label: string }) {
  return <label className="grid min-w-0 gap-1.5 text-sm"><span className="font-medium text-foreground">{label}</span>{children}</label>;
}

function SignalItem({ label, note, tone, value }: { label: string; note: string; tone: "neutral" | "warning" | "danger"; value: string }) {
  return (
    <div className="min-w-0 px-4 py-4 sm:px-5">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className={cn("mt-2 truncate font-mono text-lg font-semibold", tone === "danger" ? "text-destructive" : tone === "warning" ? "text-warning" : "text-foreground")}>{value}</p>
      <p className="mt-1 truncate text-xs text-muted-foreground">{note}</p>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="px-4 py-4 sm:px-5"><dt className="text-xs font-medium text-muted-foreground">{label}</dt><dd className="mt-2 font-mono text-sm font-semibold text-foreground">{value}</dd></div>;
}

function DataSection({ children, description, eyebrow, title }: { children: React.ReactNode; description: string; eyebrow: string; title: string }) {
  return (
    <section className="min-w-0 overflow-hidden rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-4 sm:px-5">
        <p className="text-xs font-medium text-muted-foreground">{eyebrow}</p>
        <h2 className="mt-1 text-base font-semibold text-foreground">{title}</h2>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">{description}</p>
      </div>
      {children}
    </section>
  );
}

function EmptySection({ copy, title }: { copy: string; title: string }) {
  return <div className="px-4 py-8 sm:px-5"><p className="text-sm font-medium text-foreground">{title}</p><p className="mt-2 max-w-2xl text-sm text-muted-foreground">{copy}</p></div>;
}

function TableHead({ children }: { children: React.ReactNode }) {
  return <th className="border-b border-border px-4 py-3 text-left text-xs font-semibold text-muted-foreground">{children}</th>;
}

function TableCell({ children }: { children: React.ReactNode }) {
  return <td className="border-b border-border/70 px-4 py-3 text-sm text-foreground">{children}</td>;
}

function ShareCell({ locale, share, tone = "primary", value }: { locale: AdminLocale; share: number; tone?: "primary" | "warning"; value: string }) {
  const width = Math.max(0, Math.min(100, share));
  return (
    <div>
      <div className="h-1.5 rounded-full bg-muted"><div className={cn("h-1.5 rounded-full", tone === "warning" ? "bg-warning" : "bg-primary")} style={{ width: `${width}%` }} /></div>
      <p className="mt-2 font-mono text-xs font-semibold">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{formatPercent(locale, share)}</p>
    </div>
  );
}

function StatusBadge({ row }: { row: UsageRow }) {
  return <span className={cn("inline-flex rounded-md px-2 py-1 text-xs font-medium", statusBadgeClasses(row))}>{rowSignal(row, "Signal")}</span>;
}

function usageHref(locale: AdminLocale, filters: LlmUsagePageFilters, overrides: Partial<LlmUsagePageFilters>) {
  const next = { ...filters, ...overrides };
  const params = new URLSearchParams();
  if (next.search) params.set("q", next.search);
  if (next.from) params.set("from", next.from);
  if (next.to) params.set("to", next.to);
  if (next.runId) params.set("run_id", next.runId);
  if (next.agentName) params.set("agent_name", next.agentName);
  if (next.modelName) params.set("model_name", next.modelName);
  if (next.providerName) params.set("provider_name", next.providerName);
  if (next.stage) params.set("stage", next.stage);
  return buildAdminHref("/admin/usage", params, locale);
}

function emptyFilters(): LlmUsagePageFilters {
  return { search: "", from: "", to: "", runId: "", agentName: "", modelName: "", providerName: "", stage: "" };
}

function rowLinkToRun(row: UsageRow, locale: AdminLocale) {
  const runId = readText(row, ["run_id"]);
  return runId ? buildAdminHref(`/admin/runs/${encodeURIComponent(runId)}`, new URLSearchParams(), locale) : "";
}

function rowLinkToReview(row: UsageRow, locale: AdminLocale) {
  const reviewTaskId = readText(row, ["review_task_id"]);
  return reviewTaskId ? buildAdminHref(`/admin/reviews/${encodeURIComponent(reviewTaskId)}`, new URLSearchParams(), locale) : "";
}

function topUsageRow(rows: UsageRow[]) {
  return [...rows].sort((left, right) => {
    const costDelta = (readNumber(right, ["estimated_cost", "cost", "total_cost"]) ?? 0) - (readNumber(left, ["estimated_cost", "cost", "total_cost"]) ?? 0);
    return costDelta || (readNumber(right, ["total_tokens", "tokens", "token_total"]) ?? 0) - (readNumber(left, ["total_tokens", "tokens", "token_total"]) ?? 0);
  })[0];
}

function readNumber(row: Record<string, unknown>, keys: string[]) {
  for (const key of keys) {
    const value = row[key];
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string" && value.trim() && Number.isFinite(Number(value))) return Number(value);
  }
  return null;
}

function readText(row: Record<string, unknown>, keys: string[]) {
  for (const key of keys) {
    const value = row[key];
    if (typeof value === "string" && value.trim()) return value.trim();
    if (Array.isArray(value)) {
      const values = value.filter((item): item is string => typeof item === "string" && Boolean(item.trim())).map((item) => item.trim());
      if (values.length) return values.join(", ");
    }
  }
  return "";
}

function rowLabel(row: UsageRow, key: string, fallback: string) {
  return readText(row, [key]) || fallback;
}

function rowText(row: UsageRow, keys: string[], fallback: string) {
  return readText(row, keys) || fallback;
}

function rowSummary(row: UsageRow, fallback: string) {
  return readText(row, ["reason", "summary", "note", "message", "signal_reason", "anomaly_reasons"]) || fallback;
}

function rowSignal(row: UsageRow, fallback: string) {
  return readText(row, ["signal", "severity", "trend_state", "anomaly_type", "reason_code"]) || fallback;
}

function rowKey(row: UsageRow, index: number, keys: string[]) {
  return keys.map((key) => readText(row, [key])).find(Boolean) || String(index);
}

function statusBadgeClasses(row: UsageRow) {
  const value = readText(row, ["trend_state", "signal", "severity", "status"]).toLowerCase();
  if (["critical", "high", "spike", "failed", "error"].includes(value)) return "bg-destructive/10 text-destructive";
  if (["warning", "elevated", "medium"].includes(value)) return "bg-warning-soft text-warning";
  if (["stable", "normal", "baseline", "low", "info"].includes(value)) return "bg-success-soft text-success";
  return "bg-muted text-muted-foreground";
}

function signalTone(row: UsageRow): "neutral" | "warning" | "danger" {
  const value = readText(row, ["trend_state", "signal", "severity", "status"]).toLowerCase();
  if (["critical", "high", "spike", "failed", "error"].includes(value)) return "danger";
  if (["warning", "elevated", "medium"].includes(value)) return "warning";
  return "neutral";
}

function formatCount(locale: AdminLocale, value: number | null, fallback?: number) {
  return (value ?? fallback ?? 0).toLocaleString(getAdminIntlLocale(locale));
}

function formatTokens(locale: AdminLocale, value: number | null) {
  if (value === null) return USAGE_COPY[locale].missing as string;
  return value.toLocaleString(getAdminIntlLocale(locale), { maximumFractionDigits: value % 1 === 0 ? 0 : 2 });
}

function formatCost(locale: AdminLocale, value: number | null) {
  if (value === null) return USAGE_COPY[locale].missing as string;
  return value.toLocaleString(getAdminIntlLocale(locale), { currency: "USD", maximumFractionDigits: 6, minimumFractionDigits: 2, style: "currency" });
}

function formatPercent(locale: AdminLocale, value: number | null) {
  if (value === null) return USAGE_COPY[locale].missing as string;
  return `${value.toLocaleString(getAdminIntlLocale(locale), { maximumFractionDigits: 2, minimumFractionDigits: 2 })}%`;
}

function formatSignedPercent(locale: AdminLocale, value: number | null) {
  if (value === null) return USAGE_COPY[locale].missing as string;
  return `${value >= 0 ? "+" : ""}${value.toLocaleString(getAdminIntlLocale(locale), { maximumFractionDigits: 2, minimumFractionDigits: 2 })}%`;
}

function formatTimestamp(value: string) {
  return formatAdminDateTimeValue(value);
}

function maxTokens(rows: UsageRow[]) {
  return rows.reduce((max, row) => Math.max(max, readNumber(row, ["total_tokens", "tokens", "token_total"]) ?? 0), 0);
}

function safeShare(value: number | null, total: number) {
  return value === null || total <= 0 ? 0 : Number(((value / total) * 100).toFixed(2));
}
