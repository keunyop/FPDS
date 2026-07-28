"use client";

import { useSearchParams } from "next/navigation";
import { useEffect } from "react";

import { normalizePublicLocale } from "@/lib/public-locale";

export function PublicLocaleSync() {
  const searchParams = useSearchParams();
  const locale = normalizePublicLocale(searchParams.get("locale") ?? "");

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  return null;
}
