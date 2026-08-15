"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

import { PublicCountryMenu } from "@/components/fpds/public/public-country-menu";
import { PublicMark, PublicWordmark } from "@/components/fpds/public/public-mark";
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
          <Link
            aria-label={`${copy.shell.brand} ${copy.nav.dashboard}`}
            href={buildScopedPublicHrefFromSearchParams("/dashboard", searchParams)}
            className="flex min-h-11 min-w-11 items-center justify-center gap-2.5 sm:justify-start"
          >
            <PublicMark />
            <PublicWordmark className="hidden text-lg font-semibold tracking-[-0.035em] text-foreground sm:inline-flex" />
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
