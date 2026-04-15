"use client";

import { useRouter } from "next/navigation";
import { useSearchParams } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { buildAdminHref, normalizeAdminLocale, type AdminLocale } from "@/lib/admin-i18n";

const LOGOUT_COPY: Record<AdminLocale, { idle: string; pending: string }> = {
  en: { idle: "Sign out", pending: "Signing out..." },
  ko: { idle: "로그아웃", pending: "로그아웃 중..." },
  ja: { idle: "サインアウト", pending: "サインアウト中..." },
};

type LogoutButtonProps = {
  apiOrigin: string;
};

export function LogoutButton({ apiOrigin }: LogoutButtonProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const locale = normalizeAdminLocale(searchParams.get("locale"));
  const copy = LOGOUT_COPY[locale];
  const [pending, setPending] = useState(false);

  async function handleLogout() {
    setPending(true);
    try {
      await fetch(`${apiOrigin}/api/admin/auth/logout`, {
        method: "POST",
        credentials: "include"
      });
    } finally {
      router.replace(buildAdminHref("/admin/login", new URLSearchParams(), locale));
      router.refresh();
      setPending(false);
    }
  }

  return (
    <Button disabled={pending} onClick={handleLogout} type="button" variant="outline">
      {pending ? copy.pending : copy.idle}
    </Button>
  );
}
