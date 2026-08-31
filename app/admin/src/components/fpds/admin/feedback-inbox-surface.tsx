"use client";

import Link from "next/link";
import { AlertTriangle, Globe2, Inbox, MessageSquareText } from "lucide-react";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { AdminStatStrip } from "@/components/fpds/admin/admin-stat-strip";
import { AdminTableAutoRefresh } from "@/components/fpds/admin/admin-table-auto-refresh";
import { Button } from "@/components/ui/button";
import type { PublicFeedbackListResponse } from "@/lib/admin-api";
import { buildAdminHref, formatAdminDateTime, type AdminLocale } from "@/lib/admin-i18n";

export type FeedbackInboxPageFilters = {
  category: string;
  page: number;
  q: string;
  submissionType: string;
};

type FeedbackInboxSurfaceProps = {
  feedback: PublicFeedbackListResponse;
  filters: FeedbackInboxPageFilters;
  locale: AdminLocale;
};

const CATEGORIES = [
  "incorrect_rate_or_fee",
  "incorrect_product_details",
  "outdated_information",
  "missing_information",
  "broken_link",
  "content_issue",
  "usability_issue",
  "feature_suggestion",
  "accessibility_issue",
  "other",
] as const;

const COPY = {
  en: {
    allCategories: "All categories",
    allTypes: "All types",
    category: "Category",
    clear: "Clear",
    description: "Country-scoped product error reports and site feedback submitted through FPDS Public.",
    details: "Details",
    emptyBody: "Change or clear the filters to review other submissions.",
    emptyTitle: "No feedback matches these filters",
    feedback: "Feedback",
    filters: "Filter submissions",
    generalSite: "General site feedback",
    locale: "Submitted locale",
    noDetails: "No additional details",
    next: "Next",
    pageItems: "On this page",
    path: ["More tools", "Feedback"],
    previous: "Previous",
    product: "Product context",
    productErrors: "Product errors",
    reference: "Reference",
    results: "Feedback inbox",
    search: "Search",
    searchPlaceholder: "Details, product, bank, category, or ID",
    siteFeedback: "Site feedback",
    submissionType: "Type",
    submitted: "Submitted",
    total: "Total submissions",
    typeProduct: "Product error",
    typeSite: "Site feedback",
    showing: (start: number, end: number, total: number) => "Showing " + start + "–" + end + " of " + total,
  },
  ko: {
    allCategories: "전체 분류",
    allTypes: "전체 유형",
    category: "분류",
    clear: "초기화",
    description: "FPDS Public에서 접수된 국가별 상품 오류 신고와 사이트 피드백입니다.",
    details: "상세 내용",
    emptyBody: "필터를 변경하거나 초기화해 다른 접수 내용을 확인하세요.",
    emptyTitle: "조건에 맞는 피드백이 없습니다",
    feedback: "피드백",
    filters: "접수 내용 필터",
    generalSite: "사이트 일반 피드백",
    locale: "접수 언어",
    noDetails: "추가 상세 내용 없음",
    next: "다음",
    pageItems: "현재 페이지",
    path: ["기타 도구", "피드백"],
    previous: "이전",
    product: "상품 정보",
    productErrors: "상품 오류",
    reference: "참조",
    results: "피드백함",
    search: "검색",
    searchPlaceholder: "상세 내용, 상품, 은행, 분류 또는 ID",
    siteFeedback: "사이트 피드백",
    submissionType: "유형",
    submitted: "접수 일시",
    total: "전체 접수",
    typeProduct: "상품 오류",
    typeSite: "사이트 피드백",
    showing: (start: number, end: number, total: number) => "전체 " + total + "건 중 " + start + "–" + end + "건",
  },
  ja: {
    allCategories: "すべての分類",
    allTypes: "すべての種類",
    category: "分類",
    clear: "リセット",
    description: "FPDS Publicから送信された国別の商品情報の誤りとサイトへのフィードバックです。",
    details: "詳細",
    emptyBody: "フィルターを変更またはリセットして、他の送信内容をご確認ください。",
    emptyTitle: "条件に一致するフィードバックはありません",
    feedback: "フィードバック",
    filters: "送信内容を絞り込む",
    generalSite: "サイト全般のフィードバック",
    locale: "送信言語",
    noDetails: "追加の詳細なし",
    next: "次へ",
    pageItems: "このページ",
    path: ["その他のツール", "フィードバック"],
    previous: "前へ",
    product: "商品情報",
    productErrors: "商品情報の誤り",
    reference: "参照",
    results: "フィードバック受信箱",
    search: "検索",
    searchPlaceholder: "詳細、商品、銀行、分類、ID",
    siteFeedback: "サイトへのフィードバック",
    submissionType: "種類",
    submitted: "送信日時",
    total: "総送信数",
    typeProduct: "商品情報の誤り",
    typeSite: "サイトへのフィードバック",
    showing: (start: number, end: number, total: number) => "全" + total + "件中 " + start + "–" + end + "件",
  },
};

const CATEGORY_LABELS: Record<AdminLocale, Record<string, string>> = {
  en: {
    accessibility_issue: "Accessibility issue",
    broken_link: "Official link does not work",
    content_issue: "Content issue",
    feature_suggestion: "Feature suggestion",
    incorrect_product_details: "Incorrect product details or eligibility",
    incorrect_rate_or_fee: "Incorrect rate or fee",
    missing_information: "Missing information",
    other: "Other",
    outdated_information: "Outdated information",
    usability_issue: "Site usability issue",
  },
  ko: {
    accessibility_issue: "접근성 문제",
    broken_link: "공식 링크가 작동하지 않음",
    content_issue: "콘텐츠 문제",
    feature_suggestion: "기능 제안",
    incorrect_product_details: "상품 정보 또는 가입 조건 오류",
    incorrect_rate_or_fee: "금리 또는 수수료 오류",
    missing_information: "중요 정보 누락",
    other: "기타",
    outdated_information: "오래된 정보",
    usability_issue: "사이트 이용 불편",
  },
  ja: {
    accessibility_issue: "アクセシビリティの問題",
    broken_link: "公式リンクが機能しない",
    content_issue: "コンテンツの問題",
    feature_suggestion: "機能の提案",
    incorrect_product_details: "商品情報または申込条件の誤り",
    incorrect_rate_or_fee: "金利または手数料の誤り",
    missing_information: "重要な情報の不足",
    other: "その他",
    outdated_information: "古い情報",
    usability_issue: "サイトが使いにくい",
  },
};

const fieldClass = "h-10 min-w-0 rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none transition-colors focus:border-ring focus:ring-2 focus:ring-ring/25";

export function FeedbackInboxSurface({ feedback, filters, locale }: FeedbackInboxSurfaceProps) {
  const copy = COPY[locale];
  const firstItem = feedback.total_items === 0 ? 0 : (feedback.page - 1) * feedback.page_size + 1;
  const lastItem = Math.min(feedback.page * feedback.page_size, feedback.total_items);
  const statItems = [
    { icon: Inbox, label: copy.total, note: copy.results, tone: "neutral" as const, value: String(feedback.summary.total_items) },
    { icon: AlertTriangle, label: copy.productErrors, note: copy.typeProduct, tone: "warning" as const, value: String(feedback.summary.product_error_items) },
    { icon: Globe2, label: copy.siteFeedback, note: copy.typeSite, tone: "info" as const, value: String(feedback.summary.site_feedback_items) },
    { icon: MessageSquareText, label: copy.pageItems, note: copy.results, tone: "neutral" as const, value: String(feedback.items.length) },
  ];

  return (
    <section className="grid min-w-0 gap-6">
      <AdminTableAutoRefresh locale={locale} />
      <AdminPageHeader description={copy.description} path={copy.path} title={copy.feedback} />
      <AdminStatStrip framed={false} items={statItems} />

      <article className="min-w-0 rounded-lg border border-border bg-card p-4">
        <h2 className="text-base font-semibold text-foreground">{copy.filters}</h2>
        <form action={buildAdminHref("/admin/feedback", new URLSearchParams(), locale)} className="mt-4 grid gap-3 lg:grid-cols-[minmax(14rem,1.6fr)_minmax(10rem,0.7fr)_minmax(13rem,1fr)_auto] lg:items-end">
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">{copy.search}</span>
            <input className={fieldClass} defaultValue={filters.q} name="q" placeholder={copy.searchPlaceholder} type="search" />
          </label>
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">{copy.submissionType}</span>
            <select className={fieldClass} defaultValue={filters.submissionType} name="submission_type">
              <option value="">{copy.allTypes}</option>
              <option value="product_error">{copy.typeProduct}</option>
              <option value="site_feedback">{copy.typeSite}</option>
            </select>
          </label>
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">{copy.category}</span>
            <select className={fieldClass} defaultValue={filters.category} name="category">
              <option value="">{copy.allCategories}</option>
              {CATEGORIES.map((category) => <option key={category} value={category}>{CATEGORY_LABELS[locale][category]}</option>)}
            </select>
          </label>
          <div className="flex gap-2">
            <Button type="submit">{copy.search}</Button>
            <Button asChild variant="outline"><Link href={buildAdminHref("/admin/feedback", new URLSearchParams(), locale)}>{copy.clear}</Link></Button>
          </div>
        </form>
      </article>

      <article className="min-w-0 overflow-hidden border border-border bg-card">
        <div className="border-b border-border px-4 py-4">
          <h2 className="text-lg font-semibold text-foreground">{copy.results}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{copy.showing(firstItem, lastItem, feedback.total_items)}</p>
        </div>

        {feedback.items.length === 0 ? (
          <div className="px-6 py-10">
            <div className="border border-dashed border-border bg-background px-5 py-6">
              <h3 className="text-lg font-semibold text-foreground">{copy.emptyTitle}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{copy.emptyBody}</p>
              <Button asChild className="mt-5" variant="outline"><Link href={buildAdminHref("/admin/feedback", new URLSearchParams(), locale)}>{copy.clear}</Link></Button>
            </div>
          </div>
        ) : (
          <>
            <div aria-label={copy.results} className="max-w-full overflow-x-auto px-4 py-3" role="region" tabIndex={0}>
              <table className="min-w-[1040px] table-fixed border-separate border-spacing-0">
                <thead>
                  <tr className="text-left text-xs text-muted-foreground">
                    <th className="w-44 border-b border-border px-3 py-3 font-medium">{copy.submitted}</th>
                    <th className="w-56 border-b border-border px-3 py-3 font-medium">{copy.submissionType} / {copy.category}</th>
                    <th className="w-72 border-b border-border px-3 py-3 font-medium">{copy.product}</th>
                    <th className="border-b border-border px-3 py-3 font-medium">{copy.details}</th>
                    <th className="w-52 border-b border-border px-3 py-3 font-medium">{copy.reference}</th>
                  </tr>
                </thead>
                <tbody>
                  {feedback.items.map((item) => (
                    <tr className="align-top" key={item.submission_id}>
                      <td className="border-b border-border/70 px-3 py-4 text-sm">
                        <p className="font-medium text-foreground">{formatAdminDateTime(locale, item.submitted_at, { seconds: true })}</p>
                        <p className="mt-2 text-xs text-muted-foreground">{item.country_code}</p>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <span className={item.submission_type === "product_error" ? "inline-flex rounded-full bg-warning-soft px-2.5 py-1 text-xs font-medium text-warning" : "inline-flex rounded-full bg-info-soft px-2.5 py-1 text-xs font-medium text-info"}>
                          {item.submission_type === "product_error" ? copy.typeProduct : copy.typeSite}
                        </span>
                        <p className="mt-2 text-sm font-medium leading-5 text-foreground">{CATEGORY_LABELS[locale][item.category] ?? item.category}</p>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        {item.product ? (
                          <div className="grid gap-1 text-sm">
                            <p className="font-medium text-foreground">{item.product.bank_name} · {item.product.product_name}</p>
                            <p className="text-xs text-muted-foreground">{titleCase(item.product.product_type)} · {item.product.bank_code}</p>
                            <p className="break-all font-mono text-[11px] text-muted-foreground">{item.product.product_id}</p>
                          </div>
                        ) : <p className="text-sm text-muted-foreground">{copy.generalSite}</p>}
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <p className="max-w-xl whitespace-pre-wrap break-words text-sm leading-6 text-foreground">{item.details || copy.noDetails}</p>
                      </td>
                      <td className="border-b border-border/70 px-3 py-4">
                        <p className="break-all font-mono text-[11px] text-foreground">{item.submission_id}</p>
                        <p className="mt-2 text-xs text-muted-foreground">{copy.locale}: {item.locale.toUpperCase()}</p>
                        {item.snapshot_id ? <p className="mt-1 break-all font-mono text-[10px] text-muted-foreground">{item.snapshot_id}</p> : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex flex-col gap-3 border-t border-border px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-muted-foreground">{copy.showing(firstItem, lastItem, feedback.total_items)}</p>
              <div className="flex gap-2">
                <Button asChild={feedback.page > 1} disabled={feedback.page <= 1} size="sm" variant="outline">
                  {feedback.page > 1 ? <Link href={buildFeedbackHref(filters, feedback.page - 1, locale)}>{copy.previous}</Link> : <span>{copy.previous}</span>}
                </Button>
                <Button asChild={feedback.has_next_page} disabled={!feedback.has_next_page} size="sm" variant="outline">
                  {feedback.has_next_page ? <Link href={buildFeedbackHref(filters, feedback.page + 1, locale)}>{copy.next}</Link> : <span>{copy.next}</span>}
                </Button>
              </div>
            </div>
          </>
        )}
      </article>
    </section>
  );
}

function buildFeedbackHref(filters: FeedbackInboxPageFilters, page: number, locale: AdminLocale) {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.submissionType) params.set("submission_type", filters.submissionType);
  if (filters.category) params.set("category", filters.category);
  if (page > 1) params.set("page", String(page));
  return buildAdminHref("/admin/feedback", params, locale);
}

function titleCase(value: string) {
  return value.replace(/[-_]/g, " ").replace(/\b\w/g, (character) => character.toUpperCase());
}
