"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { FormEvent, Suspense, useMemo, useState } from "react";

import { AdminLocaleSwitcher } from "@/components/admin-locale-switcher";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

type SignupCopy = {
  brand: string;
  title: string;
  idLabel: string;
  idPlaceholder: string;
  nameLabel: string;
  namePlaceholder: string;
  passwordLabel: string;
  passwordPlaceholder: string;
  confirmPasswordLabel: string;
  confirmPasswordPlaceholder: string;
  submit: string;
  submitting: string;
  successTitle: string;
  successBody: string;
  mismatch: string;
  failed: string;
  apiUnavailable: string;
  haveAccount: string;
  login: string;
};

type SignupRequestFormProps = {
  apiOrigin: string;
  locale: AdminLocale;
  className?: string;
};

const BASE_COPY: SignupCopy = {
  brand: "FPDS ADMIN",
  title: "Sign up",
  idLabel: "Id",
  idPlaceholder: "Enter your id",
  nameLabel: "Name",
  namePlaceholder: "Enter your name",
  passwordLabel: "Password",
  passwordPlaceholder: "Enter your password",
  confirmPasswordLabel: "Confirm password",
  confirmPasswordPlaceholder: "Confirm your password",
  submit: "Sign up",
  submitting: "Submitting...",
  successTitle: "Request submitted",
  successBody: "Wait for admin approval before logging in.",
  mismatch: "Passwords do not match.",
  failed: "Sign up failed.",
  apiUnavailable: "The admin API is unavailable. Check the FastAPI service and try again.",
  haveAccount: "Already have an account?",
  login: "Login",
};

const SIGNUP_COPY: Record<AdminLocale, SignupCopy> = {
  en: BASE_COPY,
  ko: {
    ...BASE_COPY,
    title: "회원가입",
    idPlaceholder: "아이디를 입력하세요",
    nameLabel: "이름",
    namePlaceholder: "이름을 입력하세요",
    passwordLabel: "비밀번호",
    passwordPlaceholder: "비밀번호를 입력하세요",
    confirmPasswordLabel: "비밀번호 확인",
    confirmPasswordPlaceholder: "비밀번호를 다시 입력하세요",
    submit: "회원가입",
    submitting: "제출 중...",
    successTitle: "요청이 접수되었습니다",
    successBody: "관리자 승인 후 로그인할 수 있습니다.",
    mismatch: "비밀번호가 일치하지 않습니다.",
    failed: "회원가입에 실패했습니다.",
    apiUnavailable: "관리자 API에 연결할 수 없습니다. FastAPI 서비스를 확인한 후 다시 시도하세요.",
    haveAccount: "이미 계정이 있나요?",
    login: "로그인",
  },
  ja: {
    ...BASE_COPY,
    title: "新規登録",
    idPlaceholder: "IDを入力してください",
    nameLabel: "名前",
    namePlaceholder: "名前を入力してください",
    passwordLabel: "パスワード",
    passwordPlaceholder: "パスワードを入力してください",
    confirmPasswordLabel: "パスワード確認",
    confirmPasswordPlaceholder: "パスワードをもう一度入力してください",
    submit: "新規登録",
    submitting: "送信中...",
    successTitle: "申請を受け付けました",
    successBody: "管理者の承認後にログインできます。",
    mismatch: "パスワードが一致しません。",
    failed: "新規登録に失敗しました。",
    apiUnavailable: "管理者APIに接続できません。FastAPIサービスを確認してから再試行してください。",
    haveAccount: "すでにアカウントをお持ちですか？",
    login: "ログイン",
  },
};

export function SignupRequestForm({ apiOrigin, locale, className }: SignupRequestFormProps) {
  const copy = SIGNUP_COPY[locale];
  const loginHref = useMemo(() => buildAdminHref("/admin/login", new URLSearchParams(), locale), [locale]);

  const [loginId, setLoginId] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError(copy.mismatch);
      return;
    }

    setPending(true);

    try {
      const response = await fetch(`${apiOrigin}/api/admin/auth/signup-requests`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          login_id: loginId,
          display_name: displayName,
          password,
        }),
      });

      const payload = (await response.json()) as { error?: { message?: string } };
      if (!response.ok) {
        setError(payload.error?.message ?? copy.failed);
        return;
      }

      setSubmitted(true);
      setLoginId("");
      setDisplayName("");
      setPassword("");
      setConfirmPassword("");
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

            {submitted ? (
              <div className="mt-8 rounded-2xl border border-success/20 bg-success-soft px-4 py-4 text-sm text-success">
                <p className="font-medium">{copy.successTitle}</p>
                <p className="mt-1 leading-6">{copy.successBody}</p>
              </div>
            ) : null}

            <div className="mt-8 grid gap-5">
              <div className="grid gap-2">
                <Label htmlFor="signup-login-id">{copy.idLabel}</Label>
                <Input
                  autoCapitalize="none"
                  autoComplete="username"
                  id="signup-login-id"
                  name="login_id"
                  onChange={(event) => setLoginId(event.target.value)}
                  placeholder={copy.idPlaceholder}
                  required
                  type="text"
                  value={loginId}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="signup-display-name">{copy.nameLabel}</Label>
                <Input
                  autoComplete="name"
                  id="signup-display-name"
                  name="display_name"
                  onChange={(event) => setDisplayName(event.target.value)}
                  placeholder={copy.namePlaceholder}
                  required
                  type="text"
                  value={displayName}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="signup-password">{copy.passwordLabel}</Label>
                <Input
                  autoComplete="new-password"
                  id="signup-password"
                  name="password"
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder={copy.passwordPlaceholder}
                  required
                  type="password"
                  value={password}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="signup-confirm-password">{copy.confirmPasswordLabel}</Label>
                <Input
                  autoComplete="new-password"
                  id="signup-confirm-password"
                  name="confirm_password"
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  placeholder={copy.confirmPasswordPlaceholder}
                  required
                  type="password"
                  value={confirmPassword}
                />
              </div>

              <Button className="h-11 w-full rounded-xl text-sm font-medium" disabled={pending} type="submit">
                {pending ? copy.submitting : copy.submit}
                <ArrowRight className="h-4 w-4" />
              </Button>

              {error ? (
                <div className="rounded-2xl border border-destructive/20 bg-critical-soft px-4 py-3 text-sm text-destructive">
                  <p className="font-medium">{copy.failed}</p>
                  <p className="mt-1 leading-6">{error}</p>
                </div>
              ) : null}
            </div>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            {copy.haveAccount}{" "}
            <Link className="font-medium text-foreground underline underline-offset-4" href={loginHref}>
              {copy.login}
            </Link>
          </p>
        </div>
      </div>
    </section>
  );
}
