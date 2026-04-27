"use client";

import Link from "next/link";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { Stats5 } from "@/components/stats5";
import { Button } from "@/components/ui/button";
import type { AuditLogListResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

const CATEGORY_OPTIONS = ["review", "run", "publish", "auth", "config", "usage"] as const;
const ACTOR_TYPE_OPTIONS = ["user", "system", "service", "scheduler"] as const;

export type AuditLogPageFilters = {
  q: string;
  eventCategory: string;
  eventType: string;
  actorType: string;
  targetType: string;
  occurredFrom: string;
  occurredTo: string;
  sortBy: string;
  sortOrder: "asc" | "desc";
  page: number;
};

type AuditLogSurfaceProps = {
  auditLog: AuditLogListResponse;
  filters: AuditLogPageFilters;
  locale: AdminLocale;
};

const AUDIT_COPY = {
  en: {
    description: "Append-only events by actor, target, request, and linked workflow.",
    path: ["Operations", "Audit Log"],
    title: "Audit Log",
    visibleEvents: "Visible events",
    currentFilters: "Current filters.",
    reviewEvents: "Review events",
    reviewActions: "Review actions.",
    authEvents: "Auth events",
    loginActivity: "Login activity.",
    userActors: "User actors",
    humanActivity: "Human activity.",
    snapshot: "Audit Snapshot",
    filtersSort: "Filters and sort",
    controls: "Audit Controls",
    latestEvents: "Latest events",
    traceViews: "Trace views",
    search: "Search",
    searchPlaceholder: "audit id, request id, actor, run, review task",
    category: "Category",
    allCategories: "All categories",
    eventType: "Event type",
    actorType: "Actor type",
    allActors: "All actors",
    targetType: "Target type",
    sortBy: "Sort by",
    occurredTime: "Occurred time",
    occurredFrom: "Occurred from",
    occurredTo: "Occurred to",
    order: "Order",
    descending: "Descending",
    ascending: "Ascending",
    applyFilters: "Apply filters",
    reset: "Reset",
    results: "Results",
    table: "Audit table",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `Page ${page} of ${totalPages} with ${totalItems} matching audit${totalItems === 1 ? " event" : " events"}.`,
    start: "Start",
    now: "Now",
    noMatching: "No matching audit events",
    noMatchingTitle: "The current filter set returned no append-only audit history.",
    noMatchingDescription:
      "Widen the time range, remove the category filter, or search more broadly. This route only shows persisted audit events, so future publish and usage history will appear here as those writer paths land.",
    resetFilters: "Reset audit filters",
    event: "Event",
    actor: "Actor",
    target: "Target",
    reasonDiff: "Reason and diff",
    linkedContext: "Linked context",
    request: "Request",
    action: "Action",
    systemActor: "System actor",
    roleSnapshot: "Role snapshot",
    noRoleSnapshot: "No role snapshot stored.",
    unknown: "unknown",
    noState: "No state transition was stored for this event.",
    noReason: "No explicit reason was stored.",
    noDiff: "No diff summary was stored for this event.",
    sourceRef: "Source ref",
    noProductContext: "No product context stored.",
    noBankContext: "No bank context stored.",
    review: "Review",
    run: "Run",
    noLinkedContext: "No linked run or review task.",
    noRequestId: "No request id stored.",
    noIp: "No IP stored.",
    retention: "Retention",
    reviewDetail: "Review detail",
    runDetail: "Run detail",
    noDrilldown: "No related drilldown is available.",
    showing: (start: number, end: number, total: number) => `Showing ${start}-${end} of ${total}`,
    previous: "Previous",
    next: "Next",
  },
  ko: {
    description: "Actor, target, request, 연결 workflow 기준 append-only event입니다.",
    path: ["운영", "Audit Log"],
    title: "Audit Log",
    visibleEvents: "표시된 이벤트",
    currentFilters: "현재 필터.",
    reviewEvents: "Review 이벤트",
    reviewActions: "Review 작업.",
    authEvents: "Auth 이벤트",
    loginActivity: "로그인 활동.",
    userActors: "User actor",
    humanActivity: "사람 활동.",
    snapshot: "Audit Snapshot",
    filtersSort: "필터 및 정렬",
    controls: "Audit 제어",
    latestEvents: "최근 이벤트",
    traceViews: "Trace view",
    search: "검색",
    searchPlaceholder: "audit id, request id, actor, run, review task",
    category: "Category",
    allCategories: "전체 category",
    eventType: "Event type",
    actorType: "Actor type",
    allActors: "전체 actor",
    targetType: "Target type",
    sortBy: "정렬 기준",
    occurredTime: "발생 시각",
    occurredFrom: "발생 시작",
    occurredTo: "발생 종료",
    order: "순서",
    descending: "내림차순",
    ascending: "오름차순",
    applyFilters: "필터 적용",
    reset: "초기화",
    results: "결과",
    table: "Audit 테이블",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `${page} / ${totalPages} 페이지, 일치하는 audit event ${totalItems}개.`,
    start: "시작",
    now: "현재",
    noMatching: "일치하는 audit event 없음",
    noMatchingTitle: "현재 필터에 맞는 append-only audit 이력이 없습니다.",
    noMatchingDescription:
      "기간을 넓히거나 category 필터를 제거하거나 더 넓게 검색하세요. 이 화면은 저장된 audit event만 표시하므로 publish/usage writer 경로가 추가되면 해당 이력이 여기에 표시됩니다.",
    resetFilters: "Audit 필터 초기화",
    event: "이벤트",
    actor: "Actor",
    target: "Target",
    reasonDiff: "사유 및 diff",
    linkedContext: "연결 context",
    request: "Request",
    action: "작업",
    systemActor: "System actor",
    roleSnapshot: "Role snapshot",
    noRoleSnapshot: "저장된 role snapshot이 없습니다.",
    unknown: "unknown",
    noState: "이 event에는 state transition이 저장되지 않았습니다.",
    noReason: "명시적인 사유가 저장되지 않았습니다.",
    noDiff: "이 event에는 diff summary가 저장되지 않았습니다.",
    sourceRef: "Source ref",
    noProductContext: "저장된 product context가 없습니다.",
    noBankContext: "저장된 bank context가 없습니다.",
    review: "Review",
    run: "Run",
    noLinkedContext: "연결된 run 또는 review task가 없습니다.",
    noRequestId: "저장된 request id가 없습니다.",
    noIp: "저장된 IP가 없습니다.",
    retention: "Retention",
    reviewDetail: "Review 상세",
    runDetail: "Run 상세",
    noDrilldown: "연결된 drilldown이 없습니다.",
    showing: (start: number, end: number, total: number) => `${start}-${end} / ${total} 표시`,
    previous: "이전",
    next: "다음",
  },
  ja: {
    description: "Actor、target、request、連携 workflow 別の append-only event です。",
    path: ["運用", "Audit Log"],
    title: "Audit Log",
    visibleEvents: "表示中のイベント",
    currentFilters: "現在のフィルター.",
    reviewEvents: "Review イベント",
    reviewActions: "Review 操作.",
    authEvents: "Auth イベント",
    loginActivity: "ログイン活動.",
    userActors: "User actor",
    humanActivity: "人の活動.",
    snapshot: "Audit Snapshot",
    filtersSort: "フィルターと並び替え",
    controls: "Audit コントロール",
    latestEvents: "最新イベント",
    traceViews: "Trace view",
    search: "検索",
    searchPlaceholder: "audit id、request id、actor、run、review task",
    category: "Category",
    allCategories: "すべての category",
    eventType: "Event type",
    actorType: "Actor type",
    allActors: "すべての actor",
    targetType: "Target type",
    sortBy: "並び替え",
    occurredTime: "発生時刻",
    occurredFrom: "発生開始",
    occurredTo: "発生終了",
    order: "順序",
    descending: "降順",
    ascending: "昇順",
    applyFilters: "フィルター適用",
    reset: "リセット",
    results: "結果",
    table: "Audit テーブル",
    pageSummary: (page: number, totalPages: number, totalItems: number) =>
      `${page} / ${totalPages} ページ、該当する audit event ${totalItems} 件。`,
    start: "開始",
    now: "現在",
    noMatching: "該当する audit event なし",
    noMatchingTitle: "現在のフィルターに該当する append-only audit 履歴はありません。",
    noMatchingDescription:
      "期間を広げる、category フィルターを外す、またはより広く検索してください。この画面は保存済み audit event のみ表示するため、publish/usage writer 経路が追加されるとその履歴がここに表示されます。",
    resetFilters: "Audit フィルターをリセット",
    event: "イベント",
    actor: "Actor",
    target: "Target",
    reasonDiff: "理由と diff",
    linkedContext: "連携 context",
    request: "Request",
    action: "操作",
    systemActor: "System actor",
    roleSnapshot: "Role snapshot",
    noRoleSnapshot: "保存された role snapshot はありません。",
    unknown: "unknown",
    noState: "この event には state transition が保存されていません。",
    noReason: "明示的な理由は保存されていません。",
    noDiff: "この event には diff summary が保存されていません。",
    sourceRef: "Source ref",
    noProductContext: "保存された product context はありません。",
    noBankContext: "保存された bank context はありません。",
    review: "Review",
    run: "Run",
    noLinkedContext: "連携 run または review task はありません。",
    noRequestId: "保存された request id はありません。",
    noIp: "保存された IP はありません。",
    retention: "Retention",
    reviewDetail: "Review 詳細",
    runDetail: "Run 詳細",
    noDrilldown: "関連する drilldown はありません。",
    showing: (start: number, end: number, total: number) => `${start}-${end} / ${total} 表示`,
    previous: "前へ",
    next: "次へ",
  },
} as const;

export function AuditLogSurface({ auditLog, filters, locale }: AuditLogSurfaceProps) {
  const copy = AUDIT_COPY[locale];
  const categoryCounts = auditLog.summary.category_counts;
  const statItems = [
    {
      label: copy.visibleEvents,
      value: String(auditLog.summary.total_items),
      note: copy.currentFilters,
      tone: "info" as const,
    },
    {
      label: copy.reviewEvents,
      value: String(categoryCounts.review ?? 0),
      note: copy.reviewActions,
      tone: "success" as const,
    },
    {
      label: copy.authEvents,
      value: String(categoryCounts.auth ?? 0),
      note: copy.loginActivity,
      tone: "warning" as const,
    },
    {
      label: copy.userActors,
      value: String(auditLog.summary.user_actor_items),
      note: copy.humanActivity,
      tone: "neutral" as const,
    },
  ];

  return (
    <section className="grid gap-6">
      <AdminPageHeader
        description={copy.description}
        path={copy.path}
        title={copy.title}
      />

      <Stats5
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
              <Link href={buildAdminHref("/admin/audit", new URLSearchParams(), locale)}>{copy.latestEvents}</Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href={buildAuditHref(locale, filters, { eventCategory: "auth", page: 1 })}>{copy.authEvents}</Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href={buildAuditHref(locale, filters, { eventType: "evidence_trace_viewed", page: 1 })}>{copy.traceViews}</Link>
            </Button>
          </div>
        </div>

        <form action={buildAdminHref("/admin/audit", new URLSearchParams(), locale)} className="mt-6 grid gap-5">
          <div className="grid gap-4 xl:grid-cols-[1.4fr_repeat(5,minmax(0,1fr))]">
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
              <span className="font-medium text-foreground">{copy.category}</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.eventCategory}
                name="event_category"
              >
                <option value="">{copy.allCategories}</option>
                {CATEGORY_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {toTitleCase(option)}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.eventType}</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.eventType}
                name="event_type"
                placeholder="review_task_edited"
                type="text"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.actorType}</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.actorType}
                name="actor_type"
              >
                <option value="">{copy.allActors}</option>
                {ACTOR_TYPE_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {toTitleCase(option)}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.targetType}</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.targetType}
                name="target_type"
                placeholder="review_task"
                type="text"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.sortBy}</span>
              <select
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.sortBy}
                name="sort_by"
              >
                <option value="occurred_at">{copy.occurredTime}</option>
                <option value="event_category">{copy.category}</option>
                <option value="event_type">{copy.eventType}</option>
                <option value="target_type">{copy.targetType}</option>
              </select>
            </label>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1fr_1fr_1fr_auto]">
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.occurredFrom}</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.occurredFrom}
                name="occurred_from"
                type="date"
              />
            </label>

            <label className="grid gap-2 text-sm">
              <span className="font-medium text-foreground">{copy.occurredTo}</span>
              <input
                className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-3 focus:ring-ring/40"
                defaultValue={filters.occurredTo}
                name="occurred_to"
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
                <Link href={buildAdminHref("/admin/audit", new URLSearchParams(), locale)}>{copy.reset}</Link>
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
              {copy.pageSummary(auditLog.page, Math.max(auditLog.total_pages, 1), auditLog.total_items)}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {filters.eventCategory ? (
              <span className={cn("rounded-full px-3 py-1 text-xs font-medium", categoryBadgeClasses(filters.eventCategory))}>
                {toTitleCase(filters.eventCategory)}
              </span>
            ) : null}
            {filters.actorType ? (
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {toTitleCase(filters.actorType)}
              </span>
            ) : null}
            {filters.eventType ? (
              <span className="rounded-full bg-info-soft px-3 py-1 text-xs font-medium text-info">{filters.eventType}</span>
            ) : null}
            {filters.occurredFrom || filters.occurredTo ? (
              <span className="rounded-full bg-warning-soft px-3 py-1 text-xs font-medium text-warning">
                {filters.occurredFrom || copy.start} to {filters.occurredTo || copy.now}
              </span>
            ) : null}
          </div>
        </div>

        {auditLog.items.length === 0 ? (
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
                  <Link href={buildAdminHref("/admin/audit", new URLSearchParams(), locale)}>{copy.resetFilters}</Link>
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto px-6 py-5">
              <table className="min-w-[1640px] table-fixed border-separate border-spacing-0">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.event}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.actor}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.target}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.reasonDiff}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.linkedContext}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.request}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.action}</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLog.items.map((item) => (
                    <tr className="align-top" key={item.audit_event_id}>
                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className={cn("inline-flex rounded-full px-2.5 py-1 text-xs font-medium", categoryBadgeClasses(item.event_category))}>
                              {toTitleCase(item.event_category)}
                            </span>
                            <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
                              {formatEventType(item.event_type)}
                            </span>
                          </div>
                          <p className="text-sm font-medium leading-6 text-foreground">{formatTimestamp(item.occurred_at)}</p>
                          <span className="text-xs text-muted-foreground">{item.audit_event_id}</span>
                        </div>
                      </td>

                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2 text-sm">
                          <span className={cn("inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-medium", actorTypeBadgeClasses(item.actor_type))}>
                            {toTitleCase(item.actor_type)}
                          </span>
                          <span className="font-medium text-foreground">
                            {item.actor.display_name ?? item.actor.email ?? item.actor.actor_id ?? copy.systemActor}
                          </span>
                          <span className="text-muted-foreground">
                            {item.actor.role_snapshot
                              ? `${copy.roleSnapshot}: ${item.actor.role_snapshot}`
                              : copy.noRoleSnapshot}
                          </span>
                        </div>
                      </td>

                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2 text-sm">
                          <span className="font-medium text-foreground">{item.target.display_name ?? item.target.target_id}</span>
                          <span className="text-muted-foreground">
                            {toTitleCase(item.target.target_type)} / {item.target.target_id}
                          </span>
                          {item.state_transition.previous_state || item.state_transition.new_state ? (
                            <span className="text-muted-foreground">
                              {item.state_transition.previous_state ?? copy.unknown}
                              {" -> "}
                              {item.state_transition.new_state ?? copy.unknown}
                            </span>
                          ) : (
                            <span className="text-muted-foreground">{copy.noState}</span>
                          )}
                        </div>
                      </td>

                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2 text-sm">
                          <span className="font-medium text-foreground">
                            {item.reason.reason_text ?? item.reason.reason_code ?? copy.noReason}
                          </span>
                          <span className="text-muted-foreground">
                            {item.diff_summary ?? copy.noDiff}
                          </span>
                          {item.source_ref ? <span className="text-muted-foreground">{copy.sourceRef}: {item.source_ref}</span> : null}
                        </div>
                      </td>

                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2 text-sm">
                          <span className="font-medium text-foreground">
                            {item.related_context.product_name ?? item.related_context.bank_name ?? copy.noProductContext}
                          </span>
                          <span className="text-muted-foreground">
                            {item.related_context.bank_name
                              ? `${item.related_context.bank_name}${item.related_context.bank_code ? ` (${item.related_context.bank_code})` : ""}`
                              : copy.noBankContext}
                          </span>
                          <span className="text-muted-foreground">
                            {item.related_context.review_task_id
                              ? `${copy.review} ${item.related_context.review_task_id}`
                              : item.related_context.run_id
                                ? `${copy.run} ${item.related_context.run_id}`
                                : copy.noLinkedContext}
                          </span>
                        </div>
                      </td>

                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="grid gap-2 text-sm">
                          <span className="font-medium text-foreground">{item.request_context.request_id ?? copy.noRequestId}</span>
                          <span className="text-muted-foreground">
                            {item.request_context.ip_address ?? copy.noIp}
                          </span>
                          <span className="text-muted-foreground">
                            {copy.retention} {item.retention_class}
                          </span>
                        </div>
                      </td>

                      <td className="border-b border-border/70 px-3 py-4">
                        <div className="flex flex-col gap-2">
                          {item.related_context.review_task_id ? (
                            <Button asChild size="sm" variant="outline">
                              <Link href={buildAdminHref(`/admin/reviews/${item.related_context.review_task_id}`, new URLSearchParams(), locale)}>{copy.reviewDetail}</Link>
                            </Button>
                          ) : null}
                          {item.related_context.run_id ? (
                            <Button asChild size="sm" variant="outline">
                              <Link href={buildAdminHref(`/admin/runs/${item.related_context.run_id}`, new URLSearchParams(), locale)}>{copy.runDetail}</Link>
                            </Button>
                          ) : null}
                          {!item.related_context.review_task_id && !item.related_context.run_id ? (
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
                {copy.showing((auditLog.page - 1) * auditLog.page_size + 1, Math.min(auditLog.page * auditLog.page_size, auditLog.total_items), auditLog.total_items)}
              </p>
              <div className="flex items-center gap-2">
                {auditLog.page > 1 ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildAuditHref(locale, filters, { page: Math.max(1, auditLog.page - 1) })}>{copy.previous}</Link>
                  </Button>
                ) : (
                  <span className="inline-flex h-7 items-center rounded-[min(var(--radius-md),12px)] border border-border bg-muted px-2.5 text-[0.8rem] text-muted-foreground opacity-60">
                    {copy.previous}
                  </span>
                )}
                {auditLog.has_next_page ? (
                  <Button asChild size="sm" variant="outline">
                    <Link href={buildAuditHref(locale, filters, { page: auditLog.page + 1 })}>{copy.next}</Link>
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

function buildAuditHref(locale: AdminLocale, filters: AuditLogPageFilters, overrides: Partial<AuditLogPageFilters>) {
  const next = {
    ...filters,
    ...overrides,
  };
  const params = new URLSearchParams();
  if (next.q) {
    params.set("q", next.q);
  }
  if (next.eventCategory) {
    params.set("event_category", next.eventCategory);
  }
  if (next.eventType) {
    params.set("event_type", next.eventType);
  }
  if (next.actorType) {
    params.set("actor_type", next.actorType);
  }
  if (next.targetType) {
    params.set("target_type", next.targetType);
  }
  if (next.occurredFrom) {
    params.set("occurred_from", next.occurredFrom);
  }
  if (next.occurredTo) {
    params.set("occurred_to", next.occurredTo);
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

  return buildAdminHref("/admin/audit", params, locale);
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return "n/a";
  }
  return new Intl.DateTimeFormat("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatEventType(value: string) {
  return toTitleCase(value);
}

function toTitleCase(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function categoryBadgeClasses(category: string) {
  switch (category) {
    case "review":
      return "bg-info-soft text-info";
    case "auth":
      return "bg-warning-soft text-warning";
    case "publish":
      return "bg-success-soft text-success";
    case "run":
      return "bg-muted text-foreground";
    case "config":
      return "bg-muted text-muted-foreground";
    case "usage":
      return "bg-primary/10 text-primary";
    default:
      return "bg-muted text-muted-foreground";
  }
}

function actorTypeBadgeClasses(actorType: string) {
  switch (actorType) {
    case "user":
      return "bg-info-soft text-info";
    case "system":
      return "bg-muted text-muted-foreground";
    case "service":
      return "bg-success-soft text-success";
    case "scheduler":
      return "bg-warning-soft text-warning";
    default:
      return "bg-muted text-muted-foreground";
  }
}
