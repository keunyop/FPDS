"use client";

import { ArrowRight, Database, ShieldCheck, Workflow } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, Suspense, useMemo, useState } from "react";

import { AdminLocaleSwitcher } from "@/components/admin-locale-switcher";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { type AdminLocale } from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

type LoginSupportItem = {
  title: string;
  description: string;
};

interface Login2Props {
  apiOrigin: string;
  nextPath: string;
  locale: AdminLocale;
  heading?: string;
  description?: string;
  supportItems?: LoginSupportItem[];
  className?: string;
}

const LOGIN_COPY = {
  en: {
    brand: "FPDS Admin",
    eyebrow: "Protected operations console",
    heading: "Operator sign-in",
    description:
      "Evidence-first review work begins in a secure FPDS admin shell that stays compact, route-oriented, and session aware.",
    supportItems: [
      {
        title: "Server-managed session",
        description: "The browser signs in with an opaque cookie instead of a bearer token.",
      },
      {
        title: "Tracked sign-in attempts",
        description: "Lockout-ready login attempts stay in Postgres alongside the admin auth service.",
      },
      {
        title: "Review shell ready",
        description: "A successful sign-in opens the protected FPDS operations shell for the next admin slices.",
      },
    ],
    deferred: "SSO and remember-me behavior remain intentionally deferred until the FPDS auth roadmap explicitly approves them.",
    formEyebrow: "Session sign-in",
    formTitle: "Enter your operator account",
    formDescription: "Access is limited to `admin`, `reviewer`, and `read_only` accounts provisioned through the FPDS bootstrap flow.",
    emailLabel: "Work email",
    emailPlaceholder: "admin@example.com",
    passwordLabel: "Password",
    passwordPlaceholder: "Enter your password",
    sessionNote: "Server-side session sign-in with DB-backed operator accounts.",
    secureSession: "Secure session",
    submit: "Sign in to FPDS Admin",
    submitting: "Signing in...",
    failureTitle: "Sign-in failed",
    loginFailed: "Login failed.",
    apiUnavailable: "The admin API is unavailable. Check the FastAPI service and try again.",
    footer: "Use an operator account created after the admin auth migration is applied. Successful sign-in returns you to",
    nextSuffix: ".",
  },
  ko: {
    brand: "FPDS 관리자",
    eyebrow: "보호된 운영 콘솔",
    heading: "운영자 로그인",
    description:
      "증거 우선 검토 작업은 작고 경로 중심이며 세션을 인식하는 안전한 FPDS 관리자 셸에서 시작됩니다.",
    supportItems: [
      {
        title: "서버 관리 세션",
        description: "브라우저는 베어러 토큰 대신 불투명 쿠키로 로그인합니다.",
      },
      {
        title: "로그인 시도 추적",
        description: "잠금 대비 로그인 시도 기록은 관리자 인증 서비스와 함께 Postgres에 저장됩니다.",
      },
      {
        title: "검토 셸 준비 완료",
        description: "로그인에 성공하면 다음 관리자 작업을 위한 보호된 FPDS 운영 셸이 열립니다.",
      },
    ],
    deferred: "SSO와 로그인 유지 기능은 FPDS 인증 로드맵이 명시적으로 승인할 때까지 의도적으로 보류됩니다.",
    formEyebrow: "세션 로그인",
    formTitle: "운영자 계정으로 로그인",
    formDescription: "`admin`, `reviewer`, `read_only` 계정만 FPDS 초기화 흐름으로 등록됩니다.",
    emailLabel: "업무용 이메일",
    emailPlaceholder: "admin@example.com",
    passwordLabel: "비밀번호",
    passwordPlaceholder: "비밀번호를 입력하세요",
    sessionNote: "DB 기반 운영자 계정을 사용하는 서버 측 세션 로그인입니다.",
    secureSession: "안전한 세션",
    submit: "FPDS 관리자에 로그인",
    submitting: "로그인 중...",
    failureTitle: "로그인 실패",
    loginFailed: "로그인에 실패했습니다.",
    apiUnavailable: "관리자 API에 연결할 수 없습니다. FastAPI 서비스를 확인한 뒤 다시 시도하세요.",
    footer: "관리자 인증 마이그레이션 적용 후 생성된 운영자 계정을 사용하세요. 로그인에 성공하면",
    nextSuffix: "로 돌아갑니다.",
  },
  ja: {
    brand: "FPDS 管理",
    eyebrow: "保護された運用コンソール",
    heading: "オペレーターサインイン",
    description:
      "証跡重視の審査作業は、コンパクトで経路中心、セッション対応の安全な FPDS 管理シェルから始まります。",
    supportItems: [
      {
        title: "サーバー管理セッション",
        description: "ブラウザはベアラートークンではなく不透明な cookie でサインインします。",
      },
      {
        title: "サインイン試行の追跡",
        description: "ロックアウト対応のサインイン試行は、管理認証サービスと一緒に Postgres に保存されます。",
      },
      {
        title: "審査シェル準備完了",
        description: "サインインに成功すると、次の管理スライス向けの保護された FPDS 運用シェルが開きます。",
      },
    ],
    deferred: "SSO と remember-me 動作は、FPDS 認証ロードマップが明示的に承認するまで意図的に保留します。",
    formEyebrow: "セッションサインイン",
    formTitle: "オペレーターアカウントでサインイン",
    formDescription: "`admin`、`reviewer`、`read_only` アカウントのみが FPDS の初期化フローで登録されます。",
    emailLabel: "勤務先メール",
    emailPlaceholder: "admin@example.com",
    passwordLabel: "パスワード",
    passwordPlaceholder: "パスワードを入力",
    sessionNote: "DB バックのオペレーターアカウントを使うサーバー側セッションサインインです。",
    secureSession: "安全なセッション",
    submit: "FPDS 管理へサインイン",
    submitting: "サインイン中...",
    failureTitle: "サインイン失敗",
    loginFailed: "サインインに失敗しました。",
    apiUnavailable: "管理 API にアクセスできません。FastAPI サービスを確認して再試行してください。",
    footer: "管理認証マイグレーション適用後に作成されたオペレーターアカウントを使ってください。サインイン成功後は",
    nextSuffix: "に戻ります。",
  },
} satisfies Record<AdminLocale, {
  brand: string;
  eyebrow: string;
  heading: string;
  description: string;
  supportItems: LoginSupportItem[];
  deferred: string;
  formEyebrow: string;
  formTitle: string;
  formDescription: string;
  emailLabel: string;
  emailPlaceholder: string;
  passwordLabel: string;
  passwordPlaceholder: string;
  sessionNote: string;
  secureSession: string;
  submit: string;
  submitting: string;
  failureTitle: string;
  loginFailed: string;
  apiUnavailable: string;
  footer: string;
  nextSuffix: string;
}>;

const supportIcons = [ShieldCheck, Database, Workflow] as const;

const Login2 = ({
  apiOrigin,
  nextPath,
  locale,
  heading,
  description,
  supportItems,
  className
}: Login2Props) => {
  const router = useRouter();
  const copy = LOGIN_COPY[locale];
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const safeNextPath = useMemo(() => {
    if (!nextPath.startsWith("/")) {
      return "/admin";
    }
    return nextPath;
  }, [nextPath]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);

    try {
      const response = await fetch(`${apiOrigin}/api/admin/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const payload = (await response.json()) as { error?: { message?: string } };
        setError(payload.error?.message ?? copy.loginFailed);
        return;
      }

      router.replace(safeNextPath);
      router.refresh();
    } catch {
      setError(copy.apiUnavailable);
    } finally {
      setPending(false);
    }
  }

  return (
    <section className={cn("min-h-screen px-4 py-8 md:px-6 md:py-10", className)}>
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-6xl items-center justify-center">
        <div className="grid w-full gap-6 lg:grid-cols-[1.08fr_0.92fr]">
          <div className="rounded-[1.75rem] border border-border/80 bg-gradient-to-b from-primary/10 via-background to-background p-6 shadow-sm sm:p-8">
            <div className="mb-8 flex items-center justify-between gap-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-primary">
                <span className="h-2 w-2 rounded-full bg-primary" />
                {copy.brand}
              </div>
              <Suspense fallback={null}>
                <AdminLocaleSwitcher locale={locale} />
              </Suspense>
            </div>

            <div className="max-w-xl space-y-4">
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.eyebrow}</p>
              <h1 className="text-balance text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">{heading ?? copy.heading}</h1>
              <p className="max-w-2xl text-pretty text-base leading-7 text-muted-foreground sm:text-lg">
                {description ?? copy.description}
              </p>
            </div>

            <div className="mt-8 grid gap-4">
              {(supportItems ?? copy.supportItems).map((item, index) => {
                const Icon = supportIcons[index % supportIcons.length];

                return (
                  <div
                    className="flex items-start gap-4 rounded-2xl border border-border/80 bg-card/85 p-4 shadow-sm"
                    key={item.title}
                  >
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="space-y-1">
                      <p className="font-medium text-foreground">{item.title}</p>
                      <p className="text-sm leading-6 text-muted-foreground">{item.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-8 rounded-2xl border border-border/80 bg-card/70 p-4 text-sm text-muted-foreground">
              {copy.deferred}
            </div>
          </div>

          <div className="flex items-center">
            <form
              className="w-full rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm backdrop-blur sm:p-8"
              onSubmit={handleSubmit}
            >
              <div className="space-y-2">
                <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">
                  {copy.formEyebrow}
                </p>
                <h2 className="text-2xl font-semibold tracking-tight text-foreground">{copy.formTitle}</h2>
                <p className="text-sm leading-6 text-muted-foreground">
                  {copy.formDescription}
                </p>
              </div>

              <div className="mt-8 grid gap-5">
                <div className="grid gap-2">
                  <Label htmlFor="email">{copy.emailLabel}</Label>
                  <Input
                    autoComplete="email"
                    id="email"
                    name="email"
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder={copy.emailPlaceholder}
                    required
                    type="email"
                    value={email}
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="password">{copy.passwordLabel}</Label>
                  <Input
                    autoComplete="current-password"
                    id="password"
                    name="password"
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder={copy.passwordPlaceholder}
                    required
                    type="password"
                    value={password}
                  />
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border/80 bg-muted/40 px-4 py-3 text-sm">
                  <span className="text-muted-foreground">{copy.sessionNote}</span>
                  <span className="inline-flex items-center gap-2 rounded-full bg-info-soft px-3 py-1 text-xs font-medium text-info">
                    <span className="h-2 w-2 rounded-full bg-info" />
                    {copy.secureSession}
                  </span>
                </div>

                <Button className="h-11 w-full rounded-xl text-sm font-medium" disabled={pending} type="submit">
                  {pending ? copy.submitting : copy.submit}
                  <ArrowRight className="h-4 w-4" />
                </Button>

                {error ? (
                  <div className="rounded-2xl border border-destructive/20 bg-critical-soft px-4 py-3 text-sm text-destructive">
                    <p className="font-medium">{copy.failureTitle}</p>
                    <p className="mt-1 leading-6">{error}</p>
                  </div>
                ) : null}

                <div className="rounded-2xl border border-border/80 bg-background px-4 py-3 text-sm text-muted-foreground">
                  {copy.footer} <span className="font-medium text-foreground">{safeNextPath}</span>
                  {copy.nextSuffix}
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
};

export { Login2 };
