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
    <header className="sticky top-0 z-30 border-b border-border bg-background/95 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-3 px-4 py-3 md:px-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center justify-between gap-4">
          <Link href={buildLocaleHref("/dashboard", searchParams, locale)} className="flex items-center gap-3">
            <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-xs font-semibold text-primary-foreground">
              FP
            </span>
            <span>
              <span className="block text-sm font-semibold tracking-wide text-foreground">{copy.shell.brand}</span>
              <span className="block text-xs text-muted-foreground">{copy.shell.tagline}</span>
            </span>
          </Link>
          <LocaleLinks className="lg:hidden" copy={copy} locale={locale} pathname={pathname} searchParams={searchParams} />
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <PublicNav />
          <LocaleLinks className="hidden lg:flex" copy={copy} locale={locale} pathname={pathname} searchParams={searchParams} />
        </div>
      </div>
    </header>
  );
}

function LocaleLinks({
  className,
  copy,
  locale,
  pathname,
  searchParams
}: {
  className?: string;
  copy: ReturnType<typeof getPublicMessages>;
  locale: string;
  pathname: string;
  searchParams: ReadonlyURLSearchParams;
}) {
  return (
    <div className={className ? `${className} items-center gap-2 rounded-lg border border-border bg-card px-2 py-1.5` : "flex items-center gap-2"}>
      <span className="text-xs font-medium text-muted-foreground">{copy.nav.localeLabel}</span>
      {(["en", "ko", "ja"] as const).map((option) => {
        const active = option === locale;
        return (
          <Link
            key={option}
            href={buildLocaleHref(pathname, searchParams, option)}
            className={active ? "text-xs font-semibold text-foreground" : "text-xs text-muted-foreground hover:text-foreground"}
          >
            {option.toUpperCase()}
          </Link>
        );
      })}
    </div>
  );
}

export function PublicHeader() {
  return (
    <Suspense fallback={<div className="h-16 border-b border-border bg-background" aria-hidden="true" />}>
      <HeaderContent />
    </Suspense>
  );
}
