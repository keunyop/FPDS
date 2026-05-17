"use client";

import Link from "next/link";
import { ChartNoAxesColumnIncreasing } from "lucide-react";
import { usePathname, useRouter, useSearchParams, type ReadonlyURLSearchParams } from "next/navigation";
import { Suspense } from "react";

import { PublicNav } from "@/components/fpds/public/public-nav";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
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
            <span className="flex size-8 items-center justify-center rounded-md border border-primary/20 bg-primary text-primary-foreground shadow-sm">
              <ChartNoAxesColumnIncreasing className="size-4" aria-hidden="true" />
            </span>
            <span className="block text-lg font-bold text-foreground">
              <span className="block leading-none">{copy.shell.brand}</span>
            </span>
          </Link>
          <LocaleSelector className="flex lg:hidden" copy={copy} locale={locale} pathname={pathname} searchParams={searchParams} />
        </div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <PublicNav />
          <LocaleSelector className="hidden lg:flex" copy={copy} locale={locale} pathname={pathname} searchParams={searchParams} />
        </div>
      </div>
    </header>
  );
}

function LocaleSelector({
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
  const router = useRouter();
  const options = ["en", "ko", "ja"] as const;

  return (
    <div className={className ? `${className} items-center gap-2` : "flex items-center gap-2"}>
      <span className="text-xs font-medium text-muted-foreground">{copy.nav.localeLabel}</span>
      <Select value={locale} onValueChange={(value) => router.push(buildLocaleHref(pathname, searchParams, value))}>
        <SelectTrigger aria-label={copy.nav.localeLabel} className="h-8 min-w-28 bg-card text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent align="end">
          {options.map((option) => (
            <SelectItem key={option} value={option}>
              {getPublicMessages(option).localeName}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
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
