import Link from "next/link";
import { redirect } from "next/navigation";
import { Activity, ChevronRight, Gauge, ShieldCheck, UserCheck } from "lucide-react";

import { ApplicationShell5 } from "@/components/application-shell5";
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
    greetingPrefix: "Hello",
    subtitle: "Review the items that need attention, then jump to the owning surface.",
    sessionVerified: "Session verified",
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
    greetingPrefix: "안녕하세요",
    subtitle: "주의가 필요한 항목만 확인하고 담당 화면으로 이동하세요.",
    sessionVerified: "Session 확인됨",
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
    greetingPrefix: "こんにちは",
    subtitle: "対応が必要な項目を確認し、担当画面へ移動してください。",
    sessionVerified: "Session 確認済み",
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
    greetingPrefix: string;
    subtitle: string;
    sessionVerified: string;
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
  const firstName = displayName.split(/\s+/)[0] || copy.greetingFallback;
  const reviewCount = reviewQueue?.summary.active_items ?? null;
  const runAttentionCount = runs ? (runs.summary.state_counts.failed ?? 0) + runs.summary.partial_items : null;
  const dashboardIssueCount = dashboardHealth
    ? dashboardHealth.summary.failed_domains + dashboardHealth.summary.stale_domains + dashboardHealth.summary.empty_domains
    : null;
  const pendingSignupCount = activeSession.user.role === "admin" ? (signupRequests?.summary.pending_items ?? null) : null;

  const metricItems = [
    {
      label: copy.reviewQueue,
      value: formatCount(reviewCount, copy.unavailable),
      hint: copy.reviewQueueHint,
      tone: reviewCount && reviewCount > 0 ? "warning" : "neutral",
      icon: UserCheck,
      href: buildAdminHref("/admin/reviews", reviewQueueLinkParams(), locale),
    },
    {
      label: copy.runAttention,
      value: formatCount(runAttentionCount, copy.unavailable),
      hint: copy.runAttentionHint,
      tone: runAttentionCount && runAttentionCount > 0 ? "warning" : "neutral",
      icon: Activity,
      href: buildAdminHref("/admin/runs", runLinkParams(), locale),
    },
    {
      label: copy.dashboardHealth,
      value: dashboardIssueCount === null ? copy.unavailable : dashboardIssueCount === 0 ? copy.healthy : copy.needsAttention,
      hint: copy.dashboardHealthHint,
      tone: dashboardIssueCount && dashboardIssueCount > 0 ? "warning" : "success",
      icon: Gauge,
      href: buildAdminHref("/admin/health/dashboard", new URLSearchParams(), locale),
    },
    {
      label: activeSession.user.role === "admin" ? copy.signupRequests : copy.role,
      value: activeSession.user.role === "admin" ? formatCount(pendingSignupCount, copy.unavailable) : activeSession.user.role,
      hint: activeSession.user.role === "admin" ? copy.signupRequestsHint : copy.roleHint,
      tone: pendingSignupCount && pendingSignupCount > 0 ? "warning" : "neutral",
      icon: ShieldCheck,
      href: buildAdminHref("/admin", new URLSearchParams(), locale),
    },
  ] as const;

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
      <div className="mx-auto grid w-full max-w-7xl gap-8">
        <header className="grid gap-4">
          <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <span>{copy.breadcrumb[0]}</span>
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
            <span className="font-medium text-foreground">{copy.breadcrumb[1]}</span>
          </nav>

          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight text-foreground md:text-4xl">{copy.greetingPrefix}, {firstName} 👋</h1>
              <p className="mt-2 text-sm text-muted-foreground">{copy.subtitle}</p>
            </div>
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-success/20 bg-success-soft px-3 py-1 text-xs font-medium text-success">
              <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
              {copy.sessionVerified}
            </div>
          </div>
        </header>

        <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4" aria-label="Overview metrics">
          {metricItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                className="group rounded-lg border border-border bg-background p-4 transition-colors hover:border-primary/40 hover:bg-muted/40"
                href={item.href}
                key={item.label}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">{item.label}</p>
                    <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{item.value}</p>
                  </div>
                  <Icon
                    className={item.tone === "warning" ? "h-5 w-5 text-warning" : item.tone === "success" ? "h-5 w-5 text-success" : "h-5 w-5 text-muted-foreground"}
                    aria-hidden="true"
                  />
                </div>
                <p className="mt-3 text-xs text-muted-foreground">{item.hint}</p>
              </Link>
            );
          })}
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
