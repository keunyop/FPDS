"use client";

import { useRouter } from "next/navigation";
import { useSearchParams } from "next/navigation";
import type { ComponentProps, ComponentType } from "react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { requestAdminLogout } from "@/lib/admin-auth-client";
import { buildAdminHref, normalizeAdminLocale, type AdminLocale } from "@/lib/admin-i18n";

const LOGOUT_COPY: Record<AdminLocale, { idle: string; pending: string; failure: string }> = {
  en: { idle: "Sign out", pending: "Signing out...", failure: "Sign out failed. Your session may still be active. Try again." },
  ko: { idle: "로그아웃", pending: "로그아웃 중...", failure: "로그아웃하지 못했습니다. 세션이 유지될 수 있습니다. 다시 시도하세요." },
  ja: { idle: "サインアウト", pending: "サインアウト中...", failure: "サインアウトできませんでした。セッションが有効な可能性があります。再試行してください。" },
};

type LogoutButtonProps = {
  apiOrigin: string;
  csrfToken?: string | null;
  className?: string;
  icon?: ComponentType<ComponentProps<"svg">>;
  variant?: ComponentProps<typeof Button>["variant"];
};

export function LogoutButton({ apiOrigin, csrfToken, className, icon: Icon, variant = "outline" }: LogoutButtonProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const locale = normalizeAdminLocale(searchParams.get("locale"));
  const copy = LOGOUT_COPY[locale];
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);

  async function handleLogout() {
    setPending(true);
    setFailed(false);
    try {
      await requestAdminLogout(apiOrigin, csrfToken);
      router.replace(buildAdminHref("/admin/login", new URLSearchParams(), locale));
      router.refresh();
    } catch {
      setFailed(true);
    } finally {
      setPending(false);
    }
  }

  return (
    <div aria-busy={pending}>
      <Button className={className} disabled={pending} onClick={handleLogout} type="button" variant={variant}>
        {Icon ? <Icon /> : null}
        {pending ? copy.pending : copy.idle}
      </Button>
      {failed ? <p className="px-1.5 py-2 text-sm text-destructive" role="alert">{copy.failure}</p> : null}
    </div>
  );
}
