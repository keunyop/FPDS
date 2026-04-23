"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, Suspense, useMemo, useState } from "react";

import { AdminLocaleSwitcher } from "@/components/admin-locale-switcher";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

type LoginCopy = {
  brand: string;
  title: string;
  idLabel: string;
  idPlaceholder: string;
  passwordLabel: string;
  passwordPlaceholder: string;
  submit: string;
  submitting: string;
  failureTitle: string;
  loginFailed: string;
  apiUnavailable: string;
  needAccount: string;
  signUp: string;
};

interface Login2Props {
  apiOrigin: string;
  nextPath: string;
  locale: AdminLocale;
  className?: string;
}

const BASE_COPY: LoginCopy = {
  brand: "FPDS ADMIN",
  title: "Login",
  idLabel: "Id",
  idPlaceholder: "Enter your id",
  passwordLabel: "Password",
  passwordPlaceholder: "Enter your password",
  submit: "Login",
  submitting: "Logging in...",
  failureTitle: "Login failed",
  loginFailed: "Login failed.",
  apiUnavailable: "The admin API is unavailable. Check the FastAPI service and try again.",
  needAccount: "Need an account?",
  signUp: "Sign up",
};

const LOGIN_COPY: Record<AdminLocale, LoginCopy> = {
  en: BASE_COPY,
  ko: {
    ...BASE_COPY,
    title: "로그인",
    idPlaceholder: "아이디를 입력하세요",
    passwordLabel: "비밀번호",
    passwordPlaceholder: "비밀번호를 입력하세요",
    submit: "로그인",
    submitting: "로그인 중...",
    failureTitle: "로그인 실패",
    loginFailed: "로그인에 실패했습니다.",
    apiUnavailable: "관리자 API에 연결할 수 없습니다. FastAPI 서비스를 확인한 후 다시 시도하세요.",
    needAccount: "계정이 없나요?",
    signUp: "회원가입",
  },
  ja: {
    ...BASE_COPY,
    title: "ログイン",
    idPlaceholder: "IDを入力してください",
    passwordLabel: "パスワード",
    passwordPlaceholder: "パスワードを入力してください",
    submit: "ログイン",
    submitting: "ログイン中...",
    failureTitle: "ログイン失敗",
    loginFailed: "ログインに失敗しました。",
    apiUnavailable: "管理者APIに接続できません。FastAPIサービスを確認してから再試行してください。",
    needAccount: "アカウントが必要ですか？",
    signUp: "新規登録",
  },
};

const Login2 = ({ apiOrigin, nextPath, locale, className }: Login2Props) => {
  const router = useRouter();
  const copy = LOGIN_COPY[locale];
  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const safeNextPath = useMemo(() => {
    if (!nextPath.startsWith("/")) {
      return "/admin";
    }
    return nextPath;
  }, [nextPath]);

  const signupHref = useMemo(() => buildAdminHref("/admin/signup", new URLSearchParams(), locale), [locale]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);

    try {
      const response = await fetch(`${apiOrigin}/api/admin/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ login_id: loginId, password }),
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
    <section className={cn("min-h-screen bg-muted/25 px-4 py-8 md:px-6 md:py-10", className)}>
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-sm items-center justify-center">
        <div className="w-full space-y-5">
          <div className="text-center">
            <h1 className="text-3xl font-semibold tracking-[0.12em] text-foreground sm:text-4xl">{copy.brand}</h1>
          </div>

          <form
            className="w-full rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm backdrop-blur sm:p-8"
            onSubmit={handleSubmit}
          >
            <div className="flex items-center justify-between gap-4">
              <h2 className="text-2xl font-semibold tracking-tight text-foreground">{copy.title}</h2>
              <Suspense fallback={null}>
                <AdminLocaleSwitcher locale={locale} />
              </Suspense>
            </div>

            <div className="mt-8 grid gap-5">
              <div className="grid gap-2">
                <Label htmlFor="login-id">{copy.idLabel}</Label>
                <Input
                  autoCapitalize="none"
                  autoComplete="username"
                  id="login-id"
                  name="login_id"
                  onChange={(event) => setLoginId(event.target.value)}
                  placeholder={copy.idPlaceholder}
                  required
                  type="text"
                  value={loginId}
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
            </div>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            {copy.needAccount}{" "}
            <Link className="font-medium text-foreground underline underline-offset-4" href={signupHref}>
              {copy.signUp}
            </Link>
          </p>
        </div>
      </div>
    </section>
  );
};

export { Login2 };
