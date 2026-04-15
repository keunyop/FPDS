"use client";

import Link from "next/link";
import { usePathname, useSearchParams, type ReadonlyURLSearchParams } from "next/navigation";
import { Suspense } from "react";

import { PublicNav } from "@/components/fpds/public/public-nav";
import { getPublicMessages, normalizePublicLocale } from "@/lib/public-locale";

function buildLocaleHref(pathname: string, searchParams: ReadonlyURLSearchParams, locale: string) {
  const params = new URLSearchParams(searchParams.toString());
  if (locale === "en") {
    params.delete("locale");
  } else {
    params.set("locale", locale);
  }

  const query = params.toString();
  return query ? `${pathname}?${query}` : pathname;
}

function HeaderContent() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const locale = normalizePublicLocale(searchParams.get("locale") ?? "");
  const copy = getPublicMessages(locale);

  return (
    <header className="sticky top-0 z-30 border-b border-border/70 bg-background/88 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-4 md:px-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start justify-between gap-4">
          <div>
            <Link
              href={buildLocaleHref("/products", searchParams, locale)}
              className="text-sm font-semibold tracking-[0.18em] text-primary uppercase"
            >
              {copy.shell.brand}
            </Link>
            <p className="mt-1 text-sm text-muted-foreground">{copy.shell.tagline}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2 lg:hidden">
            <span className="text-xs font-medium text-muted-foreground">{copy.nav.localeLabel}</span>
            {(["en", "ko", "ja"] as const).map((option) => {
              const active = option === locale;
              return (
                <Link
                  key={option}
                  href={buildLocaleHref(pathname, searchParams, option)}
                  className={active ? "text-sm font-semibold text-foreground" : "text-sm text-muted-foreground hover:text-foreground"}
                >
                  {option.toUpperCase()}
                </Link>
              );
            })}
          </div>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <PublicNav />
          <div className="hidden items-center gap-2 rounded-full border border-border/80 bg-card/90 px-3 py-2 lg:flex">
            <span className="text-xs font-medium text-muted-foreground">{copy.nav.localeLabel}</span>
            {(["en", "ko", "ja"] as const).map((option) => {
              const active = option === locale;
              return (
                <Link
                  key={option}
                  href={buildLocaleHref(pathname, searchParams, option)}
                  className={active ? "text-sm font-semibold text-foreground" : "text-sm text-muted-foreground hover:text-foreground"}
                >
                  {option.toUpperCase()}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </header>
  );
}

export function PublicHeader() {
  return (
    <Suspense fallback={<div className="h-24 border-b border-border/70 bg-background/88" aria-hidden="true" />}>
      <HeaderContent />
    </Suspense>
  );
}
