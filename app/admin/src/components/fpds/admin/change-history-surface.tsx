"use client";

import Link from "next/link";

import { AdminTableAutoRefresh } from "@/components/fpds/admin/admin-table-auto-refresh";
import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { Stats5 } from "@/components/stats5";
import { Button } from "@/components/ui/button";
import type { ChangeHistoryListResponse, ProductTypeItem } from "@/lib/admin-api";
import { buildAdminHref, formatAdminDateTimeValue, type AdminLocale } from "@/lib/admin-i18n";
import { buildAdminProductTypeLabelMap, buildAdminProductTypeOptions, formatAdminProductType } from "@/lib/admin-product-types";
import { cn } from "@/lib/utils";

const BANK_OPTIONS = ["TD", "RBC", "BMO", "SCOTIA", "CIBC"] as const;
const CHANGE_TYPE_OPTIONS = ["New", "Updated", "Discontinued", "Reclassified", "ManualOverride"] as const;

export type ChangeHistoryPageFilters = {
  q: string;
  bankCode: string;
  productType: string;
  changeType: string;
  changedFrom: string;
  changedTo: string;
  sortBy: string;
  sortOrder: "asc" | "desc";
  page: number;
};

type ChangeHistorySurfaceProps = {
  filters: ChangeHistoryPageFilters;
  changes: ChangeHistoryListResponse;
  locale: AdminLocale;
  productTypes: ProductTypeItem[];
};

const CHANGE_COPY = {
  en: {
    description: "Canonical changes with review, run, and audit context.",
    path: ["Operations", "Change History"],
    title: "Change History",
    visibleChanges: "Visible changes",
    currentFilters: "Current filters.",
    affectedProducts: "Affected products",
    inThisView: "In this view.",
    manualOverrides: "Manual overrides",
    operatorEdits: "Operator edits.",
    reclassified: "Reclassified",
    taxonomyChanges: "Taxonomy changes.",
    snapshot: "Change Snapshot",
    filtersSort: "Filters and sort",
    controls: "Change Controls",
    latestChanges: "Latest changes",
    search: "Search",
    searchPlaceholder: "product, change id, run, or review task",
    bank: "Bank",
    allBanks: "All banks",
    productType: "Product type",
    allTypes: "All types",
    changeType: "Change type",
    allChanges: "All changes",
    sortBy: "Sort by",
    detectedTime: "Detected time",
    productName: "Product name",
    bankCode: "Bank code",
    changedFrom: "Changed from",
    changedTo: "Changed to",
    order: "Order",
    descending: "Descending",
    ascending: "Ascending",
    applyFilters: "Search",
    reset: "Reset",
    results: "Results",
    table: "Change table",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `Page ${page} of ${totalPages} with ${totalItems} matching change${totalItems === 1 ? "" : "s"}.`,
    start: "Start",
    now: "Now",
    noMatching: "No matching changes",
    noMatchingTitle: "The current filter set returned no canonical change events.",
    noMatchingDescription:
      "Widen the date range, remove the change-type filter, or clear the search term. Change history stays separate from current product state, so this route only shows persisted canonical events.",
    resetFilters: "Reset change filters",
    change: "Change",
    product: "Product",
    detected: "Detected",
    changedFields: "Changed fields",
    reviewContext: "Review context",
    runContext: "Run context",
    auditContext: "Audit context",
    action: "Action",
    previousVersion: "Previous version",
    noFieldDiff: "No field-level diff was stored for this event.",
    noReviewerNote: "No reviewer note stored.",
    noLinkedReview: "No linked review task is stored for this event.",
    correlation: "Correlation",
    noCorrelation: "No correlation id stored.",
    noRun: "No producing run is linked to this event.",
    manualOverrideAudit: "Manual override audit",
    operator: "Operator",
    auditDiffMissing: "Audit diff summary not stored.",
    userLinked: "User-linked",
    systemLinked: "System-linked",
    noActor: "No explicit actor snapshot stored.",
    reviewDetail: "Review detail",
    runDetail: "Run detail",
    noDrilldown: "No related drilldown is available.",
    showing: (start: number, end: number, total: number) => `Showing ${start}-${end} of ${total}`,
    previous: "Previous",
    next: "Next",
    missing: "n/a",
  },
  ko: {
    description: "Review, run, audit context가 연결된 canonical 변경 이력입니다.",
    path: ["운영", "변경 이력"],
    title: "변경 이력",
    visibleChanges: "표시된 변경",
    currentFilters: "현재 필터.",
    affectedProducts: "영향 상품",
    inThisView: "현재 보기 기준.",
    manualOverrides: "수동 override",
    operatorEdits: "운영자 편집.",
    reclassified: "재분류",
    taxonomyChanges: "Taxonomy 변경.",
    snapshot: "변경 Snapshot",
    filtersSort: "필터 및 정렬",
    controls: "변경 제어",
    latestChanges: "최근 변경",
    search: "검색",
    searchPlaceholder: "상품, change id, run 또는 review task",
    bank: "은행",
    allBanks: "전체 은행",
    productType: "상품 유형",
    allTypes: "전체 유형",
    changeType: "변경 유형",
    allChanges: "전체 변경",
    sortBy: "정렬 기준",
    detectedTime: "감지 시각",
    productName: "상품명",
    bankCode: "은행 코드",
    changedFrom: "변경 시작",
    changedTo: "변경 종료",
    order: "순서",
    descending: "내림차순",
    ascending: "오름차순",
    applyFilters: "Search",
    reset: "초기화",
    results: "결과",
    table: "변경 테이블",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `${page} / ${totalPages} 페이지, 일치하는 변경 ${totalItems}개.`,
    start: "시작",
    now: "현재",
    noMatching: "일치하는 변경 없음",
    noMatchingTitle: "현재 필터에 맞는 canonical change event가 없습니다.",
    noMatchingDescription:
      "기간을 넓히거나, 변경 유형 필터를 제거하거나, 검색어를 지우세요. 변경 이력은 현재 상품 상태와 분리되어 있어 저장된 canonical event만 표시합니다.",
    resetFilters: "변경 필터 초기화",
    change: "변경",
    product: "상품",
    detected: "감지",
    changedFields: "변경 필드",
    reviewContext: "Review context",
    runContext: "Run context",
    auditContext: "Audit context",
    action: "작업",
    previousVersion: "이전 버전",
    noFieldDiff: "이 event에는 field-level diff가 저장되지 않았습니다.",
    noReviewerNote: "저장된 reviewer note가 없습니다.",
    noLinkedReview: "이 event에 연결된 review task가 없습니다.",
    correlation: "Correlation",
    noCorrelation: "저장된 correlation id가 없습니다.",
    noRun: "이 event에 연결된 producing run이 없습니다.",
    manualOverrideAudit: "수동 override audit",
    operator: "운영자",
    auditDiffMissing: "Audit diff summary가 저장되지 않았습니다.",
    userLinked: "User-linked",
    systemLinked: "System-linked",
    noActor: "명시적인 actor snapshot이 저장되지 않았습니다.",
    reviewDetail: "Review 상세",
    runDetail: "Run 상세",
    noDrilldown: "연결된 drilldown이 없습니다.",
    showing: (start: number, end: number, total: number) => `${start}-${end} / ${total} 표시`,
    previous: "이전",
    next: "다음",
    missing: "없음",
  },
  ja: {
    description: "Review、run、audit context 付きの canonical 変更履歴です。",
    path: ["運用", "変更履歴"],
    title: "変更履歴",
    visibleChanges: "表示中の変更",
    currentFilters: "現在のフィルター.",
    affectedProducts: "影響商品",
    inThisView: "このビュー内.",
    manualOverrides: "手動 override",
    operatorEdits: "オペレーター編集.",
    reclassified: "再分類",
    taxonomyChanges: "Taxonomy 変更.",
    snapshot: "変更 Snapshot",
    filtersSort: "フィルターと並び替え",
    controls: "変更コントロール",
    latestChanges: "最新変更",
    search: "検索",
    searchPlaceholder: "商品、change id、run、review task",
    bank: "銀行",
    allBanks: "すべての銀行",
    productType: "商品タイプ",
    allTypes: "すべてのタイプ",
    changeType: "変更タイプ",
    allChanges: "すべての変更",
    sortBy: "並び替え",
    detectedTime: "検出時刻",
    productName: "商品名",
    bankCode: "銀行コード",
    changedFrom: "変更開始",
    changedTo: "変更終了",
    order: "順序",
    descending: "降順",
    ascending: "昇順",
    applyFilters: "Search",
    reset: "リセット",
    results: "結果",
    table: "変更テーブル",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `${page} / ${totalPages} ページ、該当する変更 ${totalItems} 件。`,
    start: "開始",
    now: "現在",
    noMatching: "該当する変更なし",
    noMatchingTitle: "現在のフィルターに該当する canonical change event はありません。",
    noMatchingDescription:
      "期間を広げる、変更タイプフィルターを外す、または検索語を消してください。変更履歴は現在の商品状態とは別で、保存済み canonical event のみ表示します。",
    resetFilters: "変更フィルターをリセット",
    change: "変更",
    product: "商品",
    detected: "検出",
    changedFields: "変更フィールド",
    reviewContext: "Review context",
    runContext: "Run context",
    auditContext: "Audit context",
    action: "操作",
    previousVersion: "前バージョン",
    noFieldDiff: "この event には field-level diff が保存されていません。",
    noReviewerNote: "保存された reviewer note はありません。",
    noLinkedReview: "この event に紐づく review task はありません。",
    correlation: "Correlation",
    noCorrelation: "保存された correlation id はありません。",
    noRun: "この event に紐づく producing run はありません。",
    manualOverrideAudit: "手動 override audit",
    operator: "オペレーター",
    auditDiffMissing: "Audit diff summary は保存されていません。",
    userLinked: "User-linked",
    systemLinked: "System-linked",
    noActor: "明示的な actor snapshot は保存されていません。",
    reviewDetail: "Review 詳細",
    runDetail: "Run 詳細",
    noDrilldown: "関連する drilldown はありません。",
    showing: (start: number, end: number, total: number) => `${start}-${end} / ${total} 表示`,
    previous: "前へ",
    next: "次へ",
    missing: "なし",
  },
} as const;

export function ChangeHistorySurface({ filters, changes, locale, productTypes }: ChangeHistorySurfaceProps) {
  const copy = CHANGE_COPY[locale];
  const productTypeOptions = buildAdminProductTypeOptions(productTypes);
  const productTypeLabelMap = buildAdminProductTypeLabelMap(productTypes);
  const changeTypeCounts = changes.summary.change_type_counts;
  const statItems = [
    {
      label: copy.visibleChanges,
      value: String(changes.summary.total_items),
      note: copy.currentFilters,
      tone: "info" as const,
    },
    {
      label: copy.affectedProducts,
      value: String(changes.summary.affected_product_count),
      note: copy.inThisView,
      tone: "success" as const,
    },
    {
      label: copy.manualOverrides,
      value: String(changes.summary.manual_override_items),
      note: copy.operatorEdits,
      tone: "warning" as const,
    },
    {
      label: copy.reclassified,
      value: String(changeTypeCounts.Reclassified ?? 0),
      note: copy.taxonomyChanges,
      tone: "neutral" as const,
    },
  ];

  return (
    <section className="grid min-w-0 gap-6">
      <AdminTableAutoRefresh />

      <AdminPageHeader
        description={copy.description}
        path={copy.path}
        title={copy.title}
      />

      <Stats5
        framed={false}
        items={statItems}
        title={copy.snapshot}
      />

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <div className="flex flex-col gap-4 border-b border-border/80 pb-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.filtersSort}</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{copy.controls}</h2>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button asChild size="sm" variant="outline">
              <Link href={buildAdminHref("/admin/changes", new URLSearchParams(), locale)}>{copy.latestChanges}</Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href={buildChangeHref(locale, filters, { changeType: "ManualOverride", page: 1 })}>{copy.manualOverrides}</Link>
            </Button>
          </div>
        </div>

        <form action={buildAdminHref("/admin/changes", new URLSearchParams(), locale)} className="mt-6 grid gap-5">
          <div className="grid gap-4 xl:grid-cols-[1.6fr_repeat(4,minmax(0,1fr))]">
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.search}</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.q}
                name="q"
                placeholder={copy.searchPlaceholder}
                type="search"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.bank}</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.bankCode}
                name="bank_code"
              >
                <option value="">{copy.allBanks}</option>
                {BANK_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.productType}</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.productType}
                name="product_type"
              >
                <option value="">{copy.allTypes}</option>
                {productTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.changeType}</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.changeType}
                name="change_type"
              >
                <option value="">{copy.allChanges}</option>
                {CHANGE_TYPE_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option === "ManualOverride" ? "Manual override" : option}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.sortBy}</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.sortBy}
                name="sort_by"
              >
                <option value="detected_at">{copy.detectedTime}</option>
                <option value="change_type">{copy.changeType}</option>
                <option value="product_name">{copy.productName}</option>
                <option value="bank_code">{copy.bankCode}</option>
              </select>
            </label>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1fr_1fr_1fr_auto]">
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.changedFrom}</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.changedFrom}
                name="changed_from"
                type="date"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.changedTo}</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.changedTo}
                name="changed_to"
                type="date"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.order}</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.sortOrder}
                name="sort_order"
              >
                <option value="desc">{copy.descending}</option>
                <option value="asc">{copy.ascending}</option>
              </select>
            </label>

            <div className="flex items-end gap-2">
              <Button type="submit">{copy.applyFilters}</Button>
              <Button asChild variant="outline">
                <Link href={buildAdminHref("/admin/changes", new URLSearchParams(), locale)}>{copy.reset}</Link>
              </Button>
            </div>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="flex flex-col gap-3 border-b border-border/80 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.results}</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{copy.table}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {copy.pageSummary(changes.page, Math.max(changes.total_pages, 1), changes.total_items)}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {filters.bankCode ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {filters.bankCode}
              </span>
            ) : null}
            {filters.productType ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {formatAdminProductType(filters.productType, productTypeLabelMap)}
              </span>
            ) : null}
            {filters.changeType ? (
              <span className={cn("rounded-full px-3 py-1 text-xs font-medium", changeTypeBadgeClasses(filters.changeType))}>
                {formatChangeType(filters.changeType)}
              </span>
            ) : null}
            {filters.changedFrom || filters.changedTo ? (
              <span className="rounded-full bg-info-soft px-3 py-1 text-xs font-medium text-info">
                {filters.changedFrom || copy.start} to {filters.changedTo || copy.now}
              </span>
            ) : null}
          </div>
        </div>

        {changes.items.length === 0 ? (
          <div className="px-6 py-10">
            <div className="rounded-[1.5rem] border border-dashed border-border bg-background px-6 py-8">
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.noMatching}</p>
              <h3 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
                {copy.noMatchingTitle}
              </h3>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
                {copy.noMatchingDescription}
              </p>
              <div className="mt-6">
                <Button asChild variant="outline">
                  <Link href={buildAdminHref("/admin/changes", new URLSearchParams(), locale)}>{copy.resetFilters}</Link>
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto px-6 py-5">
              <table className="min-w-[1560px] table-fixed border-separate border-spacing-0">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.change}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.product}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.detected}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.changedFields}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.reviewContext}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.runContext}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.auditContext}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.action}</th>
                  </tr>
                </thead>
                <tbody>
                  {changes.items.map((item) => (
                    <tr className="align-top" key={item.change_event_id}>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <span className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", changeTypeBadgeClasses(item.change_type))}>
                            {formatChangeType(item.change_type)}
                          </span>
                          <p className="text-sm font-medium leading-6 text-foreground">{item.change_summary}</p>
                          <span className="text-xs text-muted-foreground">{item.change_event_id}</span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1">
                          <p className="font-medium text-foreground">{item.product_name}</p>
                          <p className="text-sm text-muted-foreground">
                            {item.bank_name} · {formatAdminProductType(item.product_type, productTypeLabelMap)}
                            {item.subtype_code ? ` · ${item.subtype_code}` : ""}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Product {item.canonical_product_id}
                            {item.version_info.current_version_no ? ` · v${item.version_info.current_version_no}` : ""}
                          </p>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-1 text-sm">
                          <span className="font-medium text-foreground">{formatTimestamp(item.detected_at)}</span>
                          <span className="text-muted-foreground">
                            {copy.previousVersion} {item.version_info.previous_version_no ?? copy.missing}
                          </span>
                        </div>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        {item.changed_fields.length === 0 ? (
                          <p className="text-sm leading-6 text-muted-foreground">{copy.noFieldDiff}</p>
                        ) : (
                          <div className="flex flex-wrap gap-2">
                            {item.changed_fields.map((field) => (
                              <span
                                className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground"
                                key={`${item.change_event_id}-${field}`}
                              >
                                {field}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        {item.review_context.review_task_id ? (
                          <div className="grid gap-2 text-sm">
                            <Link
                              className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline"
                              href={buildAdminHref(`/admin/reviews/${item.review_context.review_task_id}`, new URLSearchParams(), locale)}
                            >
                              {item.review_context.review_task_id}
                            </Link>
                            <span className="text-muted-foreground">
                              {toTitleCase(item.review_context.review_state ?? "unknown")}
                              {item.review_context.action_type ? ` · ${toTitleCase(item.review_context.action_type)}` : ""}
                            </span>
                            <span className="text-muted-foreground">
                              {item.review_context.diff_summary ?? item.review_context.reason_text ?? copy.noReviewerNote}
                            </span>
                          </div>
                        ) : (
                          <p className="text-sm leading-6 text-muted-foreground">{copy.noLinkedReview}</p>
                        )}
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        {item.run_context.run_id ? (
                          <div className="grid gap-2 text-sm">
                            <Link
                              className="font-medium text-foreground underline-offset-4 hover:text-primary hover:underline"
                              href={buildAdminHref(`/admin/runs/${item.run_context.run_id}`, new URLSearchParams(), locale)}
                            >
                              {item.run_context.run_id}
                            </Link>
                            <span className="text-muted-foreground">
                              {toTitleCase(item.run_context.run_type ?? "unknown")} · {toTitleCase(item.run_context.run_status ?? "unknown")}
                            </span>
                            <span className="text-muted-foreground">
                              {item.run_context.correlation_id ? `${copy.correlation} ${item.run_context.correlation_id}` : copy.noCorrelation}
                            </span>
                          </div>
                        ) : (
                          <p className="text-sm leading-6 text-muted-foreground">{copy.noRun}</p>
                        )}
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        {item.audit_context ? (
                          <div className="grid gap-2 text-sm">
                            <span className="inline-flex w-fit rounded-full bg-warning-soft px-2.5 py-1 text-xs font-medium text-warning">
                              {copy.manualOverrideAudit}
                            </span>
                            <span className="font-medium text-foreground">
                              {item.audit_context.actor.display_name ?? item.actor.display_name ?? copy.operator}
                            </span>
                            <span className="text-muted-foreground">
                              {item.audit_context.diff_summary ?? copy.auditDiffMissing}
                            </span>
                            <span className="text-muted-foreground">{formatTimestamp(item.audit_context.occurred_at)}</span>
                          </div>
                        ) : (
                          <div className="grid gap-1 text-sm">
                            <span className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", actorTypeBadgeClasses(item.actor_type))}>
                              {item.actor_type === "user" ? copy.userLinked : copy.systemLinked}
                            </span>
                            <span className="text-muted-foreground">
                              {item.actor.display_name ?? item.actor.email ?? copy.noActor}
                            </span>
                          </div>
                        )}
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="flex flex-col gap-2">
                          {item.review_context.review_task_id ? (
                            <Button asChild size="sm" variant="outline">
                              <Link href={buildAdminHref(`/admin/reviews/${item.review_context.review_task_id}`, new URLSearchParams(), locale)}>{copy.reviewDetail}</Link>
                            </Button>
                          ) : null}
                          {item.run_context.run_id ? (
                            <Button asChild size="sm" variant="outline">
                              <Link href={buildAdminHref(`/admin/runs/${item.run_context.run_id}`, new URLSearchParams(), locale)}>{copy.runDetail}</Link>
                            </Button>
                          ) : null}
                          {!item.review_context.review_task_id && !item.run_context.run_id ? (
                            <span className="text-xs text-muted-foreground">{copy.noDrilldown}</span>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-col gap-3 border-t border-border/80 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-muted-foreground">
                {copy.showing((changes.page - 1) * changes.page_size + 1, Math.min(changes.page * changes.page_size, changes.total_items), changes.total_items)}
              </p>
              <div className="flex items-center gap-2">
                {changes.page > 1 ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildChangeHref(locale, filters, { page: Math.max(1, changes.page - 1) })}>{copy.previous}</Link>
                  </Button>
                ) : (
                  <span className="inline-flex h-7 items-center rounded-[min(var(--radius-md),12px)] border border-border bg-muted px-2.5 text-[0.8rem] text-muted-foreground opacity-60">
                    {copy.previous}
                  </span>
                )}
                {changes.has_next_page ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildChangeHref(locale, filters, { page: changes.page + 1 })}>{copy.next}</Link>
                  </Button>
                ) : (
                  <span className="inline-flex h-7 items-center rounded-[min(var(--radius-md),12px)] border border-border bg-muted px-2.5 text-[0.8rem] text-muted-foreground opacity-60">
                    {copy.next}
                  </span>
                )}
              </div>
            </div>
          </>
        )}
      </article>
    </section>
  );
}

function buildChangeHref(locale: AdminLocale, filters: ChangeHistoryPageFilters, overrides: Partial<ChangeHistoryPageFilters>) {
  const next = {
    ...filters,
    ...overrides,
  };
  const params = new URLSearchParams();
  if (next.q) {
    params.set("q", next.q);
  }
  if (next.bankCode) {
    params.set("bank_code", next.bankCode);
  }
  if (next.productType) {
    params.set("product_type", next.productType);
  }
  if (next.changeType) {
    params.set("change_type", next.changeType);
  }
  if (next.changedFrom) {
    params.set("changed_from", next.changedFrom);
  }
  if (next.changedTo) {
    params.set("changed_to", next.changedTo);
  }
  if (next.sortBy) {
    params.set("sort_by", next.sortBy);
  }
  if (next.sortOrder) {
    params.set("sort_order", next.sortOrder);
  }
  if (next.page > 1) {
    params.set("page", String(next.page));
  }

  return buildAdminHref("/admin/changes", params, locale);
}

function formatTimestamp(value: string | null) {
  return formatAdminDateTimeValue(value);
}

function toTitleCase(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatChangeType(value: string) {
  return value === "ManualOverride" ? "Manual override" : value;
}

function changeTypeBadgeClasses(changeType: string) {
  switch (changeType) {
    case "New":
      return "bg-success-soft text-success";
    case "Updated":
      return "bg-info-soft text-info";
    case "Discontinued":
      return "bg-destructive/10 text-destructive";
    case "Reclassified":
      return "bg-warning-soft text-warning";
    case "ManualOverride":
      return "bg-warning-soft text-warning";
    default:
      return "bg-muted text-muted-foreground";
  }
}

function actorTypeBadgeClasses(actorType: string) {
  return actorType === "user" ? "bg-info-soft text-info" : "bg-muted text-muted-foreground";
}
