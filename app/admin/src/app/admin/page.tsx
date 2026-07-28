import Link from "next/link";
import { redirect } from "next/navigation";
import { Activity, ArrowUpRight, Gauge, ShieldCheck, UserCheck } from "lucide-react";

import { ApplicationShell5 } from "@/components/application-shell5";
import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { SignupRequestReviewPanel } from "@/components/fpds/admin/signup-request-review-panel";
import {
  fetchAdminSession,
  fetchDashboardHealth,
  fetchReviewQueue,
  fetchRunStatusList,
  fetchSignupRequests,
  getAdminApiOrigin,
} from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale, type AdminLocale } from "@/lib/admin-i18n";

const OVERVIEW_COPY = {
  en: {
    apiUnavailableTitle: "Admin API unavailable",
    apiUnavailableHeading: "The admin web shell is up, but the auth service is not reachable.",
    apiUnavailableBody:
      "Start the FastAPI service and refresh this page. The protected admin shell depends on `/api/admin/auth/session`.",
    apiUnavailableBlocked: "Protected navigation, operator context, and authenticated workflow surfaces.",
    breadcrumb: ["Overview", "Dashboard"],
    greetingFallback: "there",
    briefingTitle: "Operations briefing",
    signedInAs: "Signed in as",
    subtitle: "Review the items that need attention, then jump to the owning surface.",
    controlFlow: "Operational attention",
    controlFlowDescription: "Signals follow the operating path from execution and review to public serving.",
    attentionSignals: "attention signals",
    openSurface: "Open surface",
    clear: "Clear",
    unavailableState: "Unavailable",
    blocked: "Blocked",
    reviewQueue: "Review queue",
    reviewQueueHint: "Queued or deferred",
    runAttention: "Run attention",
    runAttentionHint: "Failed or partial",
    dashboardHealth: "Dashboard health",
    dashboardHealthHint: "Stale, failed, or empty",
    signupRequests: "Signup requests",
    signupRequestsHint: "Pending approval",
    role: "Role",
    roleHint: "Current access",
    unavailable: "n/a",
    healthy: "Healthy",
    needsAttention: "Needs attention",
  },
  ko: {
    apiUnavailableTitle: "Admin API unavailable",
    apiUnavailableHeading: "Admin web shell은 열렸지만 auth service에 연결할 수 없습니다.",
    apiUnavailableBody:
      "FastAPI service를 시작한 뒤 페이지를 새로고침해주세요. 보호된 admin shell은 `/api/admin/auth/session`에 의존합니다.",
    apiUnavailableBlocked: "보호된 navigation, operator context, 인증된 workflow 화면.",
    breadcrumb: ["개요", "Dashboard"],
    greetingFallback: "운영자",
    briefingTitle: "운영 브리핑",
    signedInAs: "로그인",
    subtitle: "주의가 필요한 항목만 확인하고 담당 화면으로 이동하세요.",
    controlFlow: "운영 주의 항목",
    controlFlowDescription: "실행과 검토에서 공개 제공 상태까지 운영 흐름 순서로 신호를 보여줍니다.",
    attentionSignals: "개 주의 신호",
    openSurface: "화면 열기",
    clear: "정상",
    unavailableState: "확인 불가",
    blocked: "차단됨",
    reviewQueue: "검토 대기열",
    reviewQueueHint: "대기 또는 보류",
    runAttention: "실행 확인 필요",
    runAttentionHint: "실패 또는 부분 완료",
    dashboardHealth: "Dashboard 상태",
    dashboardHealthHint: "오래됨, 실패, 또는 비어 있음",
    signupRequests: "가입 요청",
    signupRequestsHint: "승인 대기",
    role: "권한",
    roleHint: "현재 접근 권한",
    unavailable: "없음",
    healthy: "정상",
    needsAttention: "확인 필요",
  },
  ja: {
    apiUnavailableTitle: "Admin API unavailable",
    apiUnavailableHeading: "Admin web shell は開いていますが、auth service に接続できません。",
    apiUnavailableBody:
      "FastAPI service を起動してからページを更新してください。保護された admin shell は `/api/admin/auth/session` に依存します。",
    apiUnavailableBlocked: "保護された navigation、operator context、認証済み workflow 画面。",
    breadcrumb: ["概要", "Dashboard"],
    greetingFallback: "operator",
    briefingTitle: "運用ブリーフィング",
    signedInAs: "ログイン",
    subtitle: "対応が必要な項目を確認し、担当画面へ移動してください。",
    controlFlow: "運用上の注意",
    controlFlowDescription: "実行と審査から公開提供まで、運用フローに沿ってシグナルを表示します。",
    attentionSignals: "件の注意シグナル",
    openSurface: "画面を開く",
    clear: "正常",
    unavailableState: "確認不可",
    blocked: "ブロック中",
    reviewQueue: "審査キュー",
    reviewQueueHint: "待機または保留",
    runAttention: "実行の確認",
    runAttentionHint: "失敗または部分完了",
    dashboardHealth: "Dashboard 健全性",
    dashboardHealthHint: "古い、失敗、または空",
    signupRequests: "登録申請",
    signupRequestsHint: "承認待ち",
    role: "ロール",
    roleHint: "現在のアクセス権",
    unavailable: "なし",
    healthy: "正常",
    needsAttention: "確認が必要",
  },
} as const satisfies Record<
  AdminLocale,
  {
    apiUnavailableTitle: string;
    apiUnavailableHeading: string;
    apiUnavailableBody: string;
    apiUnavailableBlocked: string;
    breadcrumb: readonly [string, string];
    greetingFallback: string;
    briefingTitle: string;
    signedInAs: string;
    subtitle: string;
    controlFlow: string;
    controlFlowDescription: string;
    attentionSignals: string;
    openSurface: string;
    clear: string;
    unavailableState: string;
    blocked: string;
    reviewQueue: string;
    reviewQueueHint: string;
    runAttention: string;
    runAttentionHint: string;
    dashboardHealth: string;
    dashboardHealthHint: string;
    signupRequests: string;
    signupRequestsHint: string;
    role: string;
    roleHint: string;
    unavailable: string;
    healthy: string;
    needsAttention: string;
  }
>;

type AdminOverviewPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function AdminOverviewPage({ searchParams }: AdminOverviewPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = resolveAdminLocale(resolvedSearchParams);
  const copy = OVERVIEW_COPY[locale];

  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let apiUnavailable = false;

  try {
    session = await fetchAdminSession();
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect(buildAdminHref("/admin/login", new URLSearchParams([["next", buildAdminHref("/admin", new URLSearchParams(), locale)]]), locale));
  }

  if (apiUnavailable) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center px-4 py-8 md:px-6">
        <section className="w-full rounded-xl border border-destructive/20 bg-card p-6 shadow-sm md:p-8">
          <div className="max-w-3xl">
            <p className="text-sm font-medium text-destructive">{copy.apiUnavailableTitle}</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">{copy.apiUnavailableHeading}</h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">{copy.apiUnavailableBody}</p>
          </div>
          <div className="mt-6 rounded-lg border border-destructive/20 bg-critical-soft px-4 py-3 text-sm text-destructive">
            <strong className="block font-medium">{copy.blocked}</strong>
            <span className="mt-1 block leading-6">{copy.apiUnavailableBlocked}</span>
          </div>
        </section>
      </main>
    );
  }

  const activeSession = session!;
  const [signupRequests, reviewQueue, runs, dashboardHealth] = await Promise.all([
    activeSession.user.role === "admin" ? fetchOptional(fetchSignupRequests()) : Promise.resolve(null),
    fetchOptional(fetchReviewQueue(buildReviewQueueParams())),
    fetchOptional(fetchRunStatusList(buildRunStatusParams())),
    fetchOptional(fetchDashboardHealth()),
  ]);

  const envLabel = process.env.NODE_ENV === "production" ? "Prod" : "Dev";
  const displayName = activeSession.user.display_name.trim() || activeSession.user.login_id || copy.greetingFallback;
  const reviewCount = reviewQueue?.summary.active_items ?? null;
  const runAttentionCount = runs ? (runs.summary.state_counts.failed ?? 0) + runs.summary.partial_items : null;
  const dashboardIssueCount = dashboardHealth
    ? dashboardHealth.summary.failed_domains + dashboardHealth.summary.stale_domains + dashboardHealth.summary.empty_domains
    : null;
  const pendingSignupCount = activeSession.user.role === "admin" ? (signupRequests?.summary.pending_items ?? null) : null;

  const attentionItems = [
    {
      label: copy.runAttention,
      value: formatCount(runAttentionCount, copy.unavailable),
      hint: copy.runAttentionHint,
      needsAttention: runAttentionCount !== null && runAttentionCount > 0,
      available: runAttentionCount !== null,
      icon: Activity,
      href: buildAdminHref("/admin/runs", runLinkParams(), locale),
    },
    {
      label: copy.reviewQueue,
      value: formatCount(reviewCount, copy.unavailable),
      hint: copy.reviewQueueHint,
      needsAttention: reviewCount !== null && reviewCount > 0,
      available: reviewCount !== null,
      icon: UserCheck,
      href: buildAdminHref("/admin/reviews", reviewQueueLinkParams(), locale),
    },
    {
      label: copy.dashboardHealth,
      value: dashboardIssueCount === null ? copy.unavailable : dashboardIssueCount === 0 ? copy.healthy : copy.needsAttention,
      hint: copy.dashboardHealthHint,
      needsAttention: dashboardIssueCount !== null && dashboardIssueCount > 0,
      available: dashboardIssueCount !== null,
      icon: Gauge,
      href: buildAdminHref("/admin/health/dashboard", new URLSearchParams(), locale),
    },
    {
      label: activeSession.user.role === "admin" ? copy.signupRequests : copy.role,
      value: activeSession.user.role === "admin" ? formatCount(pendingSignupCount, copy.unavailable) : activeSession.user.role,
      hint: activeSession.user.role === "admin" ? copy.signupRequestsHint : copy.roleHint,
      needsAttention: activeSession.user.role === "admin" && pendingSignupCount !== null && pendingSignupCount > 0,
      available: activeSession.user.role !== "admin" || pendingSignupCount !== null,
      icon: ShieldCheck,
      href: buildAdminHref("/admin", new URLSearchParams(), locale),
    },
  ] as const;
  const attentionSignalCount = attentionItems.filter((item) => item.needsAttention).length;

  return (
    <ApplicationShell5
      environmentLabel={envLabel}
      locale={locale}
      logoutApiOrigin={getAdminApiOrigin()}
      user={{
        name: activeSession.user.display_name,
        loginId: activeSession.user.login_id,
        role: activeSession.user.role,
      }}
    >
      <div className="mx-auto grid w-full max-w-7xl gap-6">
        <AdminPageHeader
          badges={
            <span className="inline-flex min-h-8 items-center gap-2 border border-border bg-card px-2.5 text-xs font-semibold text-muted-foreground">
              <ShieldCheck className="h-3.5 w-3.5 text-success" aria-hidden="true" />
              {copy.signedInAs} {displayName} · {activeSession.user.role}
            </span>
          }
          description={copy.subtitle}
          path={copy.breadcrumb}
          title={copy.briefingTitle}
        />

        <section aria-labelledby="operational-attention-title">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 className="text-lg font-semibold tracking-[-0.01em] text-foreground" id="operational-attention-title">
                {copy.controlFlow}
              </h2>
              <p className="mt-1 max-w-3xl text-sm leading-5 text-muted-foreground">{copy.controlFlowDescription}</p>
            </div>
            <p className="font-mono text-xs font-semibold text-muted-foreground">
              {attentionSignalCount} {copy.attentionSignals}
            </p>
          </div>

          <div className="mt-4 grid overflow-hidden rounded-lg border border-border bg-card md:grid-cols-2 xl:grid-cols-4">
            {attentionItems.map((item) => {
              const Icon = item.icon;
              const stateLabel = !item.available
                ? copy.unavailableState
                : item.needsAttention
                  ? copy.needsAttention
                  : copy.clear;

              return (
                <Link
                  className="group min-w-0 border-b border-border p-4 transition-colors last:border-b-0 hover:bg-accent/45 md:border-r md:even:border-r-0 xl:border-b-0 xl:even:border-r xl:last:border-r-0"
                  href={item.href}
                  key={item.label}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex min-w-0 items-center gap-2">
                      <Icon
                        className={
                          !item.available
                            ? "h-4 w-4 text-muted-foreground"
                            : item.needsAttention
                              ? "h-4 w-4 text-warning"
                              : "h-4 w-4 text-success"
                        }
                        aria-hidden="true"
                      />
                      <p className="truncate text-xs font-semibold text-muted-foreground">{item.label}</p>
                    </div>
                    <ArrowUpRight className="h-4 w-4 text-muted-foreground transition-colors group-hover:text-primary" aria-hidden="true" />
                  </div>
                  <p className="mt-4 break-words font-mono text-xl font-semibold tracking-[-0.02em] text-foreground">{item.value}</p>
                  <div className="mt-3 flex items-center justify-between gap-3 text-xs">
                    <span className="text-muted-foreground">{item.hint}</span>
                    <span
                      className={
                        !item.available
                          ? "font-semibold text-muted-foreground"
                          : item.needsAttention
                            ? "font-semibold text-warning"
                            : "font-semibold text-success"
                      }
                    >
                      {stateLabel}
                    </span>
                  </div>
                  <span className="sr-only">{copy.openSurface}</span>
                </Link>
              );
            })}
          </div>
        </section>

        {activeSession.user.role === "admin" && signupRequests && signupRequests.items.length > 0 ? (
          <SignupRequestReviewPanel csrfToken={activeSession.csrf_token} locale={locale} requests={signupRequests} />
        ) : null}
      </div>
    </ApplicationShell5>
  );
}

async function fetchOptional<T>(promise: Promise<T | null>) {
  try {
    return await promise;
  } catch {
    return null;
  }
}

function buildReviewQueueParams() {
  const params = new URLSearchParams();
  params.append("state", "queued");
  params.append("state", "deferred");
  params.set("sort_by", "priority");
  params.set("sort_order", "desc");
  params.set("page", "1");
  return params;
}

function buildRunStatusParams() {
  const params = new URLSearchParams();
  params.append("state", "started");
  params.append("state", "failed");
  params.set("sort_by", "started_at");
  params.set("sort_order", "desc");
  params.set("page", "1");
  return params;
}

function reviewQueueLinkParams() {
  const params = new URLSearchParams();
  params.append("state", "queued");
  params.append("state", "deferred");
  return params;
}

function runLinkParams() {
  const params = new URLSearchParams();
  params.append("state", "started");
  params.append("state", "failed");
  return params;
}

function formatCount(value: number | null, fallback: string) {
  return value === null ? fallback : value.toLocaleString("en-CA");
}
