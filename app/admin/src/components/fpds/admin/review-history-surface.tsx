import Link from "next/link";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { Button } from "@/components/ui/button";
import type { ReviewTaskDetailResponse } from "@/lib/admin-api";
import { buildAdminHref, formatAdminDateTime, translateReviewAction, translateReviewState, type AdminLocale } from "@/lib/admin-i18n";

const COPY = {
  en: { title: "Review history", description: "Historical record. New collections automatically accept verified facts or exclude the candidate.", back: "Back to history", run: "Open run", facts: "Recorded facts", evidence: "Source evidence", decisions: "Past decisions", none: "No recorded decisions", missing: "Not recorded" },
  ko: { title: "과거 검토 기록", description: "과거 기록입니다. 새 수집은 검증된 정보만 자동 반영하고 불확실한 후보는 제외합니다.", back: "기록 목록", run: "실행 보기", facts: "기록된 정보", evidence: "원문 근거", decisions: "과거 결정", none: "기록된 결정이 없습니다", missing: "기록 없음" },
  ja: { title: "過去の審査記録", description: "過去の記録です。新しい収集は確認できた情報を自動反映し、不確かな候補を除外します。", back: "記録一覧", run: "実行を見る", facts: "記録された情報", evidence: "原文の根拠", decisions: "過去の判断", none: "判断の記録はありません", missing: "記録なし" },
} as const;

export function ReviewHistorySurface({ detail, locale, returnTo }: { detail: ReviewTaskDetailResponse; locale: AdminLocale; returnTo: string }) {
  const copy = COPY[locale];
  return (
    <div className="grid min-w-0 gap-5">
      <AdminPageHeader path={[copy.title]} title={detail.candidate.product_name} description={copy.description}
        actions={<><Button asChild variant="outline"><Link href={returnTo}>{copy.back}</Link></Button><Button asChild variant="outline"><Link href={buildAdminHref(`/admin/runs/${detail.review_task.run_id}`, new URLSearchParams(), locale)}>{copy.run}</Link></Button></>}
        badges={<span className="text-sm text-muted-foreground">{detail.candidate.bank_name} · {detail.candidate.currency} · {translateReviewState(locale, detail.review_task.review_state)}</span>}
      />
      <section className="min-w-0 rounded-lg border border-border bg-card p-4">
        <h2 className="text-base font-semibold">{copy.facts}</h2>
        <dl className="mt-3 divide-y divide-border">
          {detail.proposed_fields.map((field) => <div className="grid min-w-0 gap-1 py-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] sm:gap-4" key={field.field_name}>
            <dt className="text-sm text-muted-foreground">{field.label}</dt>
            <dd className="min-w-0 whitespace-pre-wrap break-words text-sm [overflow-wrap:anywhere]">{displayValue(field.value, copy.missing)}</dd>
          </div>)}
        </dl>
      </section>
      <details className="min-w-0 rounded-lg border border-border bg-card p-4">
        <summary className="cursor-pointer text-sm font-medium">{copy.evidence} ({detail.evidence_links.length})</summary>
        <div className="mt-3 grid min-w-0 gap-3">
          {detail.evidence_links.map((item, index) => <blockquote className="min-w-0 whitespace-pre-wrap break-words border-l-2 border-border pl-3 text-sm text-muted-foreground [overflow-wrap:anywhere]" key={index}>{displayValue(item.evidence_excerpt, copy.missing)}</blockquote>)}
        </div>
      </details>
      <section className="min-w-0 rounded-lg border border-border bg-card p-4">
        <h2 className="text-base font-semibold">{copy.decisions}</h2>
        {detail.decision_history.length === 0 ? <p className="mt-3 text-sm text-muted-foreground">{copy.none}</p> : <ul className="mt-3 grid gap-3">
          {detail.decision_history.map((item, index) => <li className="min-w-0 break-words text-sm" key={index}>{translateReviewAction(locale, item.action_type)} · {formatAdminDateTime(locale, item.decided_at)}</li>)}
        </ul>}
      </section>
    </div>
  );
}

function displayValue(value: unknown, missing: string): string {
  if (value === null || value === undefined || value === "") return missing;
  return typeof value === "object" ? JSON.stringify(value, null, 2) : String(value);
}
