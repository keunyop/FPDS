"use client";

import { useEffect } from "react";
import { useSearchParams } from "next/navigation";

import { getAdminIntlLocale, normalizeAdminLocale } from "@/lib/admin-i18n";

export function AdminLocaleDocumentSync() {
  const searchParams = useSearchParams();

  useEffect(() => {
    const locale = normalizeAdminLocale(searchParams.get("locale"));
    document.documentElement.lang = getAdminIntlLocale(locale);
    document.documentElement.dataset.locale = locale;
  }, [searchParams]);

  return null;
}
