"use client";

import Link from "next/link";
import { ChartNoAxesColumnIncreasing } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { buildLocaleHref, PublicLocaleMenu } from "@/components/fpds/public/public-locale-menu";
import { PublicNav } from "@/components/fpds/public/public-nav";
import { getPublicMessages, normalizePublicLocale } from "@/lib/public-locale";

function HeaderContent() {
  const searchParams = useSearchParams();
  const locale = normalizePublicLocale(searchParams.get("locale") ?? "");
  const copy = getPublicMessages(locale);

  return (
    <header className="sticky top-0 z-30 border-b border-border/70 bg-background/90 shadow-[0_1px_18px_rgba(15,23,42,0.04)] backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-3 px-4 py-3 md:px-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center justify-between gap-4">
          <Link href={buildLocaleHref("/dashboard", searchParams, locale)} className="flex items-center gap-3">
            <span className="flex size-8 items-center justify-center rounded-md border border-primary/20 bg-primary text-primary-foreground shadow-sm">
              <ChartNoAxesColumnIncreasing className="size-4" aria-hidden="true" />
            </span>
            <span className="block text-xl font-semibold text-foreground">
              <span className="block leading-none">{copy.shell.brand}</span>
            </span>
          </Link>
          <PublicLocaleMenu className="flex lg:hidden" />
        </div>
        <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-center">
          <PublicNav />
          <PublicLocaleMenu className="hidden lg:flex" />
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
