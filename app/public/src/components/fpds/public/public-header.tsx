"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

import { PublicCountryMenu } from "@/components/fpds/public/public-country-menu";
import { PublicMark } from "@/components/fpds/public/public-mark";
import { PublicNav } from "@/components/fpds/public/public-nav";
import { getPublicMessages, normalizePublicLocale } from "@/lib/public-locale";
import { buildScopedPublicHrefFromSearchParams } from "@/lib/public-query";

function HeaderContent() {
  const searchParams = useSearchParams();
  const locale = normalizePublicLocale(searchParams.get("locale") ?? "");
  const copy = getPublicMessages(locale);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  return (
    <header className="sticky top-0 z-30 border-b border-border/80 bg-background/92 backdrop-blur-xl">
      <div className="mx-auto flex min-h-16 w-full max-w-7xl items-center justify-between gap-4 px-4 py-2 md:px-6">
        <div className="flex items-center justify-between gap-4">
          <Link href={buildScopedPublicHrefFromSearchParams("/dashboard", searchParams)} className="flex min-h-11 min-w-11 items-center justify-center gap-3 sm:justify-start">
            <PublicMark />
            <span className="hidden text-lg font-semibold tracking-[-0.02em] text-foreground sm:block">
              <span className="block leading-none">{copy.shell.brand}</span>
              <span className="mt-1 block font-mono text-[9px] font-medium uppercase tracking-[0.16em] text-muted-foreground">Financial product data</span>
            </span>
          </Link>
        </div>
        <div className="flex min-w-0 items-center gap-2">
          <PublicNav />
          <PublicCountryMenu />
        </div>
      </div>
    </header>
  );
}

export function PublicHeader() {
  return (
    <Suspense fallback={<div className="h-16 border-b border-border bg-background" aria-hidden="true" />}>
      <HeaderContent />
    </Suspense>
  );
}
