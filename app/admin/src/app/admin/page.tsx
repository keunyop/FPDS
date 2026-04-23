import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { Banner1 } from "@/components/banner1";
import { SignupRequestReviewPanel } from "@/components/fpds/admin/signup-request-review-panel";
import { Stats5 } from "@/components/stats5";
import { fetchAdminSession, fetchSignupRequests, getAdminApiOrigin } from "@/lib/admin-api";
import { buildAdminHref, resolveAdminLocale, type AdminLocale } from "@/lib/admin-i18n";

import { LogoutButton } from "./LogoutButton";

const OVERVIEW_COPY = {
  en: {
    apiUnavailableTitle: "Admin API unavailable",
    apiUnavailableHeading: "The admin web shell is up, but the auth service is not reachable.",
    apiUnavailableBody:
      "Start the FastAPI service and refresh this page. The protected admin shell depends on `/api/admin/auth/session` before it can show operator context, route gating, or next-surface state.",
    apiUnavailableBlocked:
      "Protected navigation, current-operator context, and authenticated workflow surfaces.",
    eyebrow: "Protected overview",
    title:
      "Admin triage now spans overview, review, runs, and canonical change chronology inside the FPDS operations shell.",
    body:
      "The live overview keeps admin compact, route-oriented, and evidence aware. It is the stable entrypoint for review, trace, runs, publish, usage, and dashboard health without collapsing them into one oversized page.",
    sessionVerified: "Session verified",
    bannerTitle: "Current slice boundary",
    bannerDescription:
      "Review queue, review detail, trace, runs, change history, audit log, usage, and dashboard health are now live, while publish remains a separate follow-on operational surface.",
    metricsTitle: "Admin shell readiness",
    metricsDescription:
      "The live admin surface now starts from Shadcnblocks-based layout primitives and keeps FPDS workflow meaning on top.",
    metricsBadge: "Compact, route-oriented, evidence aware",
    metricsEyebrow: "Overview metrics",
    stats: [
      {
        label: "Auth service",
        value: "Healthy",
        note: "Protected shell is connected to the FastAPI session contract.",
      },
      {
        label: "Live admin surfaces",
        value: "9",
        note:
          "Login, overview, review queue, review detail, runs, changes, audit, usage, and dashboard health are now live inside the protected shell.",
      },
      {
        label: "Newest route",
        value: "/admin/health/dashboard",
        note: "Dashboard health now shows aggregate freshness, serving fallback, and manual retry beside usage observability.",
      },
      {
        label: "Theme mode",
        value: "radix-nova",
        note: "Admin stays compact, light-first, and route-oriented by design.",
      },
    ],
    priorityTitle: "Route-oriented by design",
    priorityBody: "The shell keeps high-risk operational surfaces distinct instead of flattening them into a single dashboard.",
    priorityBadge: "Route set expanding",
    emptyRecentFailuresTitle: "Recent failures",
    emptyRecentFailuresBody: "Overview can summarize failures later, but detailed diagnosis now belongs to the live runs route.",
    emptyUsageTitle: "Usage anomalies",
    emptyUsageBody: "Model, agent, and run anomalies will stay on the observability side of the shell.",
    timelineTitle: "Resume-friendly context",
    timelineBody: "The overview stays explicit about what is live, what changed now, and what comes next.",
    timelineEyebrow: "Implementation timeline",
  },
  ko: {
    apiUnavailableTitle: "관리자 API를 사용할 수 없음",
    apiUnavailableHeading: "관리자 웹 셸은 올라와 있지만 인증 서비스에 연결할 수 없습니다.",
    apiUnavailableBody:
      "FastAPI 서비스를 시작한 뒤 이 페이지를 새로 고치세요. 보호된 관리자 셸은 운영자 정보, 경로 게이팅, 다음 화면 상태를 보여 주기 전에 `/api/admin/auth/session`에 의존합니다.",
    apiUnavailableBlocked:
      "보호된 탐색, 현재 운영자 정보, 인증된 작업 화면을 사용할 수 없습니다.",
    eyebrow: "보호된 개요",
    title:
      "관리자 분류 작업은 이제 FPDS 운영 셸 안에서 개요, 검토, 실행, 정규화된 변경 이력까지 아우릅니다.",
    body:
      "실시간 개요는 관리자 화면을 작고, 경로 중심이며, 증거를 인식하는 형태로 유지합니다. 검토, 추적, 실행, 게시, 사용량, 대시보드 상태를 하나의 큰 페이지로 합치지 않고 안정적인 진입점으로 제공합니다.",
    sessionVerified: "세션 확인됨",
    bannerTitle: "현재 스라이스 경계",
    bannerDescription:
      "검토 대기열, 검토 상세, 추적, 실행, 변경 이력, 감사 로그는 이제 운영 중이며 게시, 사용량, 상태는 별도 화면으로 남겨 다음 WBS 스라이스에서 이어집니다.",
    metricsTitle: "관리자 셸 준비 상태",
    metricsDescription:
      "실시간 관리자 화면은 이제 Shadcnblocks 기반 레이아웃 원시 요소에서 시작하며 그 위에 FPDS 작업 의미를 유지합니다.",
    metricsBadge: "간결하고, 경로 중심이며, 증거를 인식",
    metricsEyebrow: "개요 지표",
    stats: [
      {
        label: "인증 서비스",
        value: "정상",
        note: "보호된 셸이 FastAPI 세션 계약에 연결되어 있습니다.",
      },
      {
        label: "운영 중인 관리자 화면",
        value: "8",
        note:
          "로그인, 개요, 검토 대기열, 검토 상세, 실행, 변경, 감사, 사용량이 모두 보호된 셸 안에서 운영 중입니다.",
      },
      {
        label: "최신 경로",
        value: "/admin/usage",
        note: "LLM 사용량은 이제 감사와 실행 진단 옆의 독립된 관찰성 화면입니다.",
      },
      {
        label: "테마 모드",
        value: "radix-nova",
        note: "관리자 화면은 간결하고, 밝은 배경 우선이며, 경로 중심으로 유지됩니다.",
      },
    ],
    priorityTitle: "경로 중심 설계",
    priorityBody: "이 셸은 위험도가 높은 운영 화면을 하나의 대시보드로 섞지 않고 분리해서 유지합니다.",
    priorityBadge: "경로 세트 확장 중",
    emptyRecentFailuresTitle: "최근 실패",
    emptyRecentFailuresBody: "개요는 나중에 실패를 요약할 수 있지만, 세부 진단은 이제 실행 화면의 역할입니다.",
    emptyUsageTitle: "사용량 이상",
    emptyUsageBody: "모델, 에이전트, 실행 이상치는 셸의 관찰성 영역에 남습니다.",
    timelineTitle: "다시 보기 쉬운 맥락",
    timelineBody: "개요는 지금 운영 중인 것, 이번에 바뀐 것, 다음에 올 것을 명확히 보여 줍니다.",
    timelineEyebrow: "구현 타임라인",
  },
  ja: {
    apiUnavailableTitle: "管理 API は利用できません",
    apiUnavailableHeading: "管理 Web シェルは起動していますが、認証サービスに到達できません。",
    apiUnavailableBody:
      "FastAPI サービスを起動してからこのページを再読み込みしてください。保護された管理シェルは、オペレーター情報、経路ガード、次の画面状態を表示する前に `/api/admin/auth/session` に依存します。",
    apiUnavailableBlocked:
      "保護されたナビゲーション、現在のオペレーター情報、認証済みワークフロー画面が利用できません。",
    eyebrow: "保護された概要",
    title:
      "管理トリアージは今、FPDS 運用シェルの中で概要、審査、実行、正規化された変更履歴までを横断します。",
    body:
      "ライブ概要は、管理画面をコンパクトで経路中心、かつ証跡を意識した形に保ちます。審査、トレース、実行、公開、使用量、ダッシュボード健全性を一つの大きなページにまとめず、安定した入口として提供します。",
    sessionVerified: "セッション確認済み",
    bannerTitle: "現在のスライス境界",
    bannerDescription:
      "審査キュー、審査詳細、トレース、実行、変更履歴、監査ログはすでに稼働中で、公開、使用量、健全性は別画面として次の WBS スライスに引き継がれます。",
    metricsTitle: "管理シェル準備状況",
    metricsDescription:
      "ライブ管理画面は Shadcnblocks ベースのレイアウト原始要素から始まり、その上に FPDS の作業意味を保持します。",
    metricsBadge: "コンパクト、経路中心、証跡対応",
    metricsEyebrow: "概要指標",
    stats: [
      {
        label: "認証サービス",
        value: "正常",
        note: "保護されたシェルは FastAPI のセッション契約に接続されています。",
      },
      {
        label: "稼働中の管理画面",
        value: "8",
        note:
          "サインイン、概要、審査キュー、審査詳細、実行、変更、監査、使用量がすべて保護されたシェル内で稼働しています。",
      },
      {
        label: "最新の経路",
        value: "/admin/usage",
        note: "LLM 使用量は今や、監査と実行診断の横にある独立した可観測画面です。",
      },
      {
        label: "テーマモード",
        value: "radix-nova",
        note: "管理画面はコンパクトで、ライト基調、経路中心に保たれます。",
      },
    ],
    priorityTitle: "経路中心の設計",
    priorityBody: "このシェルは、リスクの高い運用画面を一つのダッシュボードにまとめず分けて保持します。",
    priorityBadge: "経路セット拡張中",
    emptyRecentFailuresTitle: "最近の失敗",
    emptyRecentFailuresBody: "概要は後で失敗を要約できますが、詳細診断は今や実行画面の役割です。",
    emptyUsageTitle: "使用量の異常",
    emptyUsageBody: "モデル、エージェント、実行の異常はシェルの可観測性側に残ります。",
    timelineTitle: "再開しやすい文脈",
    timelineBody: "概要は、今稼働しているもの、今回変わったもの、次に来るものを明確に示します。",
    timelineEyebrow: "実装タイムライン",
  },
} as const satisfies Record<
  AdminLocale,
  {
    apiUnavailableTitle: string;
    apiUnavailableHeading: string;
    apiUnavailableBody: string;
    apiUnavailableBlocked: string;
    eyebrow: string;
    title: string;
    body: string;
    sessionVerified: string;
    bannerTitle: string;
    bannerDescription: string;
    metricsTitle: string;
    metricsDescription: string;
    metricsBadge: string;
    metricsEyebrow: string;
    stats: Array<{ label: string; value: string; note: string }>;
    priorityTitle: string;
    priorityBody: string;
    priorityBadge: string;
    emptyRecentFailuresTitle: string;
    emptyRecentFailuresBody: string;
    emptyUsageTitle: string;
    emptyUsageBody: string;
    timelineTitle: string;
    timelineBody: string;
    timelineEyebrow: string;
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
  let signupRequests: Awaited<ReturnType<typeof fetchSignupRequests>> = null;
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
        <section className="w-full rounded-[1.75rem] border border-destructive/20 bg-card/95 p-6 shadow-sm md:p-8">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-destructive">{copy.apiUnavailableTitle}</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">{copy.apiUnavailableHeading}</h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">{copy.apiUnavailableBody}</p>
          </div>
          <div className="mt-6 rounded-2xl border border-destructive/20 bg-critical-soft px-4 py-3 text-sm text-destructive">
            <strong className="block font-medium">{locale === "en" ? "What is blocked" : locale === "ko" ? "차단되는 항목" : "利用できないもの"}</strong>
            <span className="mt-1 block leading-6">{copy.apiUnavailableBlocked}</span>
          </div>
        </section>
      </main>
    );
  }

  const activeSession = session!;
  if (activeSession.user.role === "admin") {
    try {
      signupRequests = await fetchSignupRequests();
    } catch {
      signupRequests = null;
    }
  }
  const expiresAt = new Intl.DateTimeFormat(locale === "en" ? "en-CA" : locale === "ko" ? "ko-KR" : "ja-JP", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(activeSession.user.expires_at));
  const envLabel = process.env.NODE_ENV === "production" ? "Prod" : "Dev";
  const statItems = copy.stats.map((item, index) => ({
    label: item.label,
    value: index === 2 ? item.value : item.value,
    note: item.note,
    tone: (["success", "info", "warning", "neutral"] as const)[index] ?? "neutral",
  }));

  return (
    <ApplicationShell5
      environmentLabel={envLabel}
      locale={locale}
      headerActions={<LogoutButton apiOrigin={getAdminApiOrigin()} />}
      user={{
        name: activeSession.user.display_name,
        email: activeSession.user.email ?? activeSession.user.login_id,
        role: activeSession.user.role,
      }}
    >
      <section className="grid gap-6">
        <div className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.eyebrow}</p>
              <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">{copy.title}</h1>
              <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">{copy.body}</p>
            </div>

            <div className="inline-flex items-center rounded-full bg-success-soft px-3 py-1 text-xs font-medium text-success">
              {copy.sessionVerified}
            </div>
          </div>

          <div className="mt-6">
            <Banner1
              defaultVisible={true}
              description={copy.bannerDescription}
              dismissible={false}
              title={copy.bannerTitle}
              tone="warning"
            />
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-border/80 bg-background px-4 py-4">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">Operator</p>
              <p className="mt-2 text-sm font-medium text-foreground">{activeSession.user.display_name}</p>
            </div>
            <div className="rounded-2xl border border-border/80 bg-background px-4 py-4">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">ID</p>
              <p className="mt-2 text-sm font-medium text-foreground">{activeSession.user.login_id}</p>
            </div>
            <div className="rounded-2xl border border-border/80 bg-background px-4 py-4">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">Role</p>
              <p className="mt-2 text-sm font-medium text-foreground">{activeSession.user.role}</p>
            </div>
            <div className="rounded-2xl border border-border/80 bg-background px-4 py-4">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">Session expires</p>
              <p className="mt-2 text-sm font-medium text-foreground">{expiresAt}</p>
            </div>
          </div>
        </div>

        {activeSession.user.role === "admin" ? (
          <SignupRequestReviewPanel csrfToken={activeSession.csrf_token} locale={locale} requests={signupRequests} />
        ) : null}

        <Stats5 items={statItems} title={copy.metricsTitle} description={copy.metricsDescription} />

        <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <div className="flex items-start justify-between gap-4 border-b border-border/80 pb-5">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.priorityBadge}</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{copy.priorityTitle}</h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy.priorityBody}</p>
              </div>
              <span className="rounded-full bg-info-soft px-3 py-1 text-xs font-medium text-info">
                {locale === "en" ? "Route set expanding" : locale === "ko" ? "경로 세트 확장 중" : "経路セット拡張中"}
              </span>
            </div>

            <div className="mt-6 grid gap-4">
              <div className="rounded-2xl border border-dashed border-border bg-background px-4 py-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium text-foreground">{copy.emptyRecentFailuresTitle}</p>
                  <span className="rounded-full bg-muted px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
                    {locale === "en" ? "Empty by design" : locale === "ko" ? "설계상 비움" : "設計上空"}
                  </span>
                </div>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy.emptyRecentFailuresBody}</p>
              </div>
              <div className="rounded-2xl border border-dashed border-border bg-background px-4 py-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium text-foreground">{copy.emptyUsageTitle}</p>
                  <span className="rounded-full bg-muted px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
                    {locale === "en" ? "Empty by design" : locale === "ko" ? "설계상 비움" : "設計上空"}
                  </span>
                </div>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy.emptyUsageBody}</p>
              </div>
            </div>
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <div className="border-b border-border/80 pb-5">
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.timelineEyebrow}</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{copy.timelineTitle}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy.timelineBody}</p>
            </div>

            <div className="mt-6 grid gap-4">
              {timelineItems.map((item) => (
                <div className="rounded-2xl border border-border/80 bg-background px-4 py-4" key={item.meta}>
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-medium text-foreground">{item.title[locale]}</p>
                    <span className="text-xs text-muted-foreground">{item.meta}</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.copy[locale]}</p>
                </div>
              ))}
            </div>
          </article>
        </section>
      </section>
    </ApplicationShell5>
  );
}

const timelineItems = [
  {
    title: {
      en: "Admin session baseline shipped",
      ko: "관리자 세션 기준선 출시",
      ja: "管理セッション基盤を出荷",
    },
    copy: {
      en: "FastAPI-backed login, logout, and session introspection are live in the protected shell.",
      ko: "FastAPI 기반 로그인, 로그아웃, 세션 확인이 보호된 셸에서 운영 중입니다.",
      ja: "FastAPI ベースのサインイン、サインアウト、セッション参照が保護シェルで稼働しています。",
    },
    meta: "Completed in WBS 4.1",
  },
  {
    title: {
      en: "Review queue route is now live",
      ko: "검토 대기열 경로가 운영 중입니다",
      ja: "審査キュー経路が稼働中です",
    },
    copy: {
      en: "Protected `/admin/reviews` now lists real review tasks with active-state defaults, search, filters, and sorting.",
      ko: "보호된 `/admin/reviews`는 이제 실제 검토 작업을 활성 상태 기본값, 검색, 필터, 정렬과 함께 보여 줍니다.",
      ja: "保護された `/admin/reviews` は、実際の審査タスクをアクティブ既定、検索、フィルター、並び替え付きで表示します。",
    },
    meta: "Completed in WBS 4.2",
  },
  {
    title: {
      en: "Run diagnostics route is now live",
      ko: "실행 진단 경로가 운영 중입니다",
      ja: "実行診断経路が稼働中です",
    },
    copy: {
      en: "Protected `/admin/runs` and `/admin/runs/:runId` now explain run outcome, source impact, related review tasks, and usage summary.",
      ko: "보호된 `/admin/runs`와 `/admin/runs/:runId`는 이제 실행 결과, 소스 영향, 연관 검토 작업, 사용량 요약을 설명합니다.",
      ja: "保護された `/admin/runs` と `/admin/runs/:runId` は、実行結果、ソース影響、関連審査タスク、使用量要約を示します。",
    },
    meta: "Completed in WBS 4.5",
  },
  {
    title: {
      en: "Change history route is now live",
      ko: "변경 이력 경로가 운영 중입니다",
      ja: "変更履歴経路が稼働中です",
    },
    copy: {
      en: "Protected `/admin/changes` now shows canonical event chronology with changed fields, review context, run context, and manual-override audit context.",
      ko: "보호된 `/admin/changes`는 이제 변경 필드, 검토 맥락, 실행 맥락, 수동 재정의 감사 맥락이 포함된 정규화된 이벤트 연표를 보여 줍니다.",
      ja: "保護された `/admin/changes` は、変更フィールド、審査文脈、実行文脈、手動上書き監査文脈を含む正規化されたイベント年表を表示します。",
    },
    meta: "Completed in WBS 4.6",
  },
  {
    title: {
      en: "Audit log route is now live",
      ko: "감사 로그 경로가 운영 중입니다",
      ja: "監査ログ経路が稼働中です",
    },
    copy: {
      en: "Protected `/admin/audit` now keeps review, auth, and trace-access audit history queryable as an append-only operations surface.",
      ko: "보호된 `/admin/audit`는 이제 검토, 인증, 추적 접근 감사 이력을 추가 전용 운영 화면으로 조회 가능하게 유지합니다.",
      ja: "保護された `/admin/audit` は、審査、認証、トレースアクセスの監査履歴を追記専用の運用画面として検索可能に保ちます。",
    },
    meta: "Completed in WBS 4.7",
  },
  {
    title: {
      en: "Usage route is now live",
      ko: "사용량 경로가 운영 중입니다",
      ja: "使用量経路が稼働中です",
    },
    copy: {
      en: "Protected `/admin/usage` now surfaces totals, by-model, by-agent, by-run, trend, and anomaly drilldowns for LLM cost review.",
      ko: "보호된 `/admin/usage`는 이제 총계, 모델별, 에이전트별, 실행별, 추세, 이상치 드릴다운을 LLM 비용 검토용으로 제공합니다.",
      ja: "保護された `/admin/usage` は、合計、モデル別、エージェント別、実行別、トレンド、異常の掘り下げを LLM コスト確認向けに表示します。",
    },
    meta: "Completed in WBS 4.8",
  },
] as const;
