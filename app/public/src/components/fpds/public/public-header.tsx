"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

import { PublicCountryMenu } from "@/components/fpds/public/public-country-menu";
import { PublicMark, PublicWordmark } from "@/components/fpds/public/public-mark";
import { PublicMobileMenu } from "@/components/fpds/public/public-mobile-menu";
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
      <div className="mx-auto flex min-h-16 w-full max-w-7xl items-center justify-between gap-3 px-4 py-2 md:px-6">
        <div className="flex min-w-0 items-center justify-between">
          <Link
            aria-label={`${copy.shell.brand} ${copy.nav.dashboard}`}
            href={buildScopedPublicHrefFromSearchParams("/", searchParams)}
            className="flex min-h-11 min-w-0 items-center justify-start gap-1"
          >
            <PublicMark />
            <PublicWordmark className="text-lg font-semibold tracking-[-0.04em] text-foreground sm:text-[1.375rem]" />
          </Link>
        </div>
        <div className="hidden min-w-0 items-center gap-2 md:flex">
          <PublicNav />
          <PublicCountryMenu />
        </div>
        <div className="shrink-0 md:hidden">
          <PublicMobileMenu />
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
