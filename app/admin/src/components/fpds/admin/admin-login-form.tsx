"use client";

import Link from "next/link";
import { ArrowRight, Globe2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { AdminAuthFrame } from "@/components/fpds/admin/admin-auth-frame";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

type LoginCopy = {
  brand: string;
  title: string;
  description: string;
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

interface AdminLoginFormProps {
  apiOrigin: string;
  nextPath: string;
  locale: AdminLocale;
  className?: string;
}

const BASE_COPY: LoginCopy = {
  brand: "FPDS Admin",
  title: "Operator sign in",
  description: "Use your authorized FPDS operator account.",
  idLabel: "Operator ID",
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
    description: "승인된 FPDS 운영자 계정으로 로그인하세요.",
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
    description: "承認済みの FPDS 運用アカウントでログインしてください。",
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

const COUNTRY_COPY: Record<AdminLocale, { label: string; loading: string; unavailable: string }> = {
  en: {
    label: "Working country",
    loading: "Loading countries…",
    unavailable: "Countries could not be loaded. Check the Admin API and try again.",
  },
  ko: {
    label: "업무 국가",
    loading: "국가를 불러오는 중…",
    unavailable: "국가 목록을 불러올 수 없습니다. Admin API를 확인한 후 다시 시도해 주세요.",
  },
  ja: {
    label: "作業対象国",
    loading: "国を読み込み中…",
    unavailable: "国の一覧を読み込めません。Admin APIを確認して、もう一度お試しください。",
  },
};

const localeTagByAdminLocale: Record<AdminLocale, string> = {
  en: "en-CA",
  ko: "ko-KR",
  ja: "ja-JP",
};

const AdminLoginForm = ({ apiOrigin, nextPath, locale, className }: AdminLoginFormProps) => {
  const router = useRouter();
  const copy = LOGIN_COPY[locale];
  const countryCopy = COUNTRY_COPY[locale];
  const [countries, setCountries] = useState<string[]>([]);
  const [countryCode, setCountryCode] = useState("");
  const [countriesPending, setCountriesPending] = useState(true);
  const [countriesError, setCountriesError] = useState<string | null>(null);
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

  const countryDisplayNames = useMemo(
    () => new Intl.DisplayNames([localeTagByAdminLocale[locale]], { type: "region" }),
    [locale],
  );

  useEffect(() => {
    const controller = new AbortController();

    async function loadCountries() {
      setCountriesPending(true);
      setCountriesError(null);
      try {
        const response = await fetch(`${apiOrigin}/api/admin/auth/countries`, {
          cache: "no-store",
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error("country-list-unavailable");
        }
        const payload = (await response.json()) as {
          data?: { countries?: Array<{ country_code?: string }> };
        };
        const available = (payload.data?.countries ?? [])
          .map((item) => (item.country_code ?? "").trim().toUpperCase())
          .filter((item) => /^[A-Z]{2}$/.test(item));
        setCountries(available);
        setCountryCode((current) => current || (available.includes("CA") ? "CA" : available[0] ?? ""));
        if (available.length === 0) {
          setCountriesError(countryCopy.unavailable);
        }
      } catch (loadError) {
        if (loadError instanceof DOMException && loadError.name === "AbortError") {
          return;
        }
        setCountriesError(countryCopy.unavailable);
      } finally {
        if (!controller.signal.aborted) {
          setCountriesPending(false);
        }
      }
    }

    void loadCountries();
    return () => controller.abort();
  }, [apiOrigin, countryCopy.unavailable]);

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
        body: JSON.stringify({ country_code: countryCode, login_id: loginId, password }),
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
    <AdminAuthFrame
      brand={copy.brand}
      className={className}
      description={copy.description}
      footer={
        <p className="text-sm text-muted-foreground">
          {copy.needAccount}{" "}
          <Link className="inline-flex min-h-10 items-center font-semibold text-primary underline underline-offset-4" href={signupHref}>
            {copy.signUp}
          </Link>
        </p>
      }
      locale={locale}
      title={copy.title}
    >
      <form aria-busy={pending} className="grid gap-5" onSubmit={handleSubmit}>
              <div className="grid gap-2">
                <Label htmlFor="country-code">{countryCopy.label}</Label>
                <div className="relative">
                  <Globe2
                    aria-hidden="true"
                    className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
                  />
                  <select
                    aria-describedby={countriesError ? "country-error" : undefined}
                    className="flex h-11 w-full appearance-none rounded-md border border-input bg-background py-2 pl-10 pr-9 text-sm text-foreground shadow-xs outline-none transition-colors focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={countriesPending || countries.length === 0}
                    id="country-code"
                    name="country_code"
                    onChange={(event) => setCountryCode(event.target.value)}
                    required
                    value={countryCode}
                  >
                    {countriesPending ? <option value="">{countryCopy.loading}</option> : null}
                    {!countriesPending && countries.length === 0 ? <option value="">{countryCopy.unavailable}</option> : null}
                    {countries.map((code) => (
                      <option key={code} value={code}>
                        {countryDisplayNames.of(code) ?? code} ({code})
                      </option>
                    ))}
                  </select>
                  <span
                    aria-hidden="true"
                    className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground"
                  >
                    ▾
                  </span>
                </div>
                {countriesError ? (
                  <p className="text-sm leading-5 text-destructive" id="country-error">
                    {countriesError}
                  </p>
                ) : null}
              </div>

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
                  className="h-11"
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
                  className="h-11"
                />
              </div>

              <Button className="h-11 w-full" disabled={pending || countriesPending || !countryCode} type="submit">
                {pending ? copy.submitting : copy.submit}
                <ArrowRight className="h-4 w-4" />
              </Button>

              {error ? (
                <div aria-live="assertive" className="rounded-md border border-destructive/25 bg-critical-soft px-4 py-3 text-sm text-destructive" role="alert">
                  <p className="font-semibold">{copy.failureTitle}</p>
                  <p className="mt-1 leading-6">{error}</p>
                </div>
              ) : null}
      </form>
    </AdminAuthFrame>
  );
};

export { AdminLoginForm };
