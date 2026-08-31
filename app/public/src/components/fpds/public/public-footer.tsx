"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { PublicLocaleMenu } from "@/components/fpds/public/public-locale-menu";
import { PublicMark, PublicWordmark } from "@/components/fpds/public/public-mark";
import { PublicFeedbackDialog } from "@/components/fpds/public/public-feedback-dialog";
import { getPublicMessages, normalizePublicLocale, type PublicLocale } from "@/lib/public-locale";
import { buildScopedPublicHrefFromSearchParams, normalizeCountryCodeValue } from "@/lib/public-query";

const FOOTER_COPY: Record<PublicLocale, { legalNote: string }> = {
  en: {
    legalNote: "Information may change. Confirm rates and conditions on the bank's official page."
  },
  ko: {
    legalNote: "정보는 변경될 수 있습니다. 가입 전 은행 공식 페이지에서 금리와 조건을 확인하세요."
  },
  ja: {
    legalNote: "情報は変更される場合があります。申込前に銀行の公式ページで金利と条件を確認してください。"
  }
};

function FooterContent() {
  const searchParams = useSearchParams();
  const locale = normalizePublicLocale(searchParams.get("locale") ?? "");
  const copy = getPublicMessages(locale);
  const footerCopy = FOOTER_COPY[locale];
  const countryCode = normalizeCountryCodeValue(searchParams.get("country_code") ?? "");
  const dashboardHref = buildScopedPublicHrefFromSearchParams("/", searchParams);
  const productsHref = buildScopedPublicHrefFromSearchParams("/products", searchParams);
  const cardsHref = buildScopedPublicHrefFromSearchParams("/cards", searchParams);
  const loansHref = buildScopedPublicHrefFromSearchParams("/loans", searchParams);
  const methodologyHref = buildScopedPublicHrefFromSearchParams("/methodology", searchParams);

  return (
    <footer className="mt-12 border-t border-foreground/15 bg-foreground text-background">
      <div className="mx-auto w-full max-w-7xl px-4 py-9 md:px-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <Link href={dashboardHref} className="inline-flex min-h-11 items-center gap-1.5">
              <PublicMark className="text-background" />
              <PublicWordmark
                className="text-xl font-semibold tracking-[-0.04em] text-background"
              />
            </Link>
            <p className="mt-1 text-sm text-background/65">{copy.shell.tagline}</p>
          </div>

          <nav className="flex flex-wrap gap-x-5 gap-y-2 text-sm font-medium text-background" aria-label={copy.nav.footerLabel}>
            <FooterLink href={dashboardHref}>{copy.nav.dashboard}</FooterLink>
            <FooterLink href={productsHref}>{copy.nav.products}</FooterLink>
            <FooterLink href={cardsHref}>{copy.nav.card}</FooterLink>
            <FooterLink href={loansHref}>{copy.nav.loan}</FooterLink>
            <FooterLink href={methodologyHref}>{copy.nav.methodology}</FooterLink>
            <PublicFeedbackDialog countryCode={countryCode} locale={locale} mode="site_feedback" triggerStyle="footer" />
          </nav>
        </div>

        <div className="mt-6 flex flex-col gap-4 border-t border-background/15 pt-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="max-w-3xl text-xs leading-5 text-background/60">{footerCopy.legalNote}</p>
          <PublicLocaleMenu align="end" className="flex shrink-0" triggerClassName="w-full justify-between sm:w-auto" />
        </div>
      </div>
    </footer>
  );
}

export function PublicFooter() {
  return (
    <Suspense fallback={<div className="h-24 border-t border-border/80 bg-foreground" aria-hidden="true" />}>
      <FooterContent />
    </Suspense>
  );
}

function FooterLink({ children, href }: Readonly<{ children: React.ReactNode; href: string }>) {
  return (
    <Link className="inline-flex min-h-11 min-w-12 items-center justify-center whitespace-nowrap text-background/70 transition-colors hover:text-background" href={href}>
      {children}
    </Link>
  );
}
