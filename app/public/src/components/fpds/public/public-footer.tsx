"use client";

import { ChartNoAxesColumnIncreasing } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { PublicLocaleMenu } from "@/components/fpds/public/public-locale-menu";
import { getPublicMessages, normalizePublicLocale, type PublicLocale } from "@/lib/public-locale";
import { buildScopedPublicHrefFromSearchParams } from "@/lib/public-query";

const FOOTER_COPY: Record<PublicLocale, { brandNote: string; legalNote: string }> = {
  en: {
    brandNote: "Comparable public financial product data.",
    legalNote: "Information may change. Confirm rates and conditions on the bank's official page."
  },
  ko: {
    brandNote: "비교 가능한 공개 금융상품 데이터.",
    legalNote: "정보는 변경될 수 있습니다. 가입 전 은행 공식 페이지에서 금리와 조건을 확인하세요."
  },
  ja: {
    brandNote: "比較できる公開金融商品データ。",
    legalNote: "情報は変更される場合があります。申込前に銀行の公式ページで金利と条件を確認してください。"
  }
};

function FooterContent() {
  const searchParams = useSearchParams();
  const locale = normalizePublicLocale(searchParams.get("locale") ?? "");
  const copy = getPublicMessages(locale);
  const footerCopy = FOOTER_COPY[locale];
  const dashboardHref = buildScopedPublicHrefFromSearchParams("/dashboard", searchParams);
  const productsHref = buildScopedPublicHrefFromSearchParams("/products", searchParams);
  const loansHref = buildScopedPublicHrefFromSearchParams("/loans", searchParams);
  const methodologyHref = buildScopedPublicHrefFromSearchParams("/methodology", searchParams);

  return (
    <footer className="border-t border-border/80 bg-card">
      <div className="mx-auto w-full max-w-7xl px-4 py-7 md:px-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <Link href={dashboardHref} className="inline-flex min-h-11 items-center gap-3">
              <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
                <ChartNoAxesColumnIncreasing className="size-4" aria-hidden="true" />
              </span>
              <span className="text-lg font-semibold text-foreground">{copy.shell.brand}</span>
            </Link>
            <p className="mt-1 text-sm text-muted-foreground">{footerCopy.brandNote}</p>
          </div>

          <nav className="flex flex-wrap gap-x-5 gap-y-2 text-sm font-medium" aria-label="Footer navigation">
            <FooterLink href={dashboardHref}>{copy.nav.dashboard}</FooterLink>
            <FooterLink href={productsHref}>{copy.nav.products}</FooterLink>
            <FooterLink href={loansHref}>{copy.nav.loan}</FooterLink>
            <FooterLink href={methodologyHref}>{copy.nav.methodology}</FooterLink>
          </nav>
        </div>

        <div className="mt-5 flex flex-col gap-4 border-t border-border/70 pt-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="max-w-3xl text-xs leading-5 text-muted-foreground">{footerCopy.legalNote}</p>
          <PublicLocaleMenu align="end" className="flex shrink-0" triggerClassName="w-full justify-between sm:w-auto" />
        </div>
      </div>
    </footer>
  );
}

export function PublicFooter() {
  return (
    <Suspense fallback={<div className="h-24 border-t border-border/80 bg-card" aria-hidden="true" />}>
      <FooterContent />
    </Suspense>
  );
}

function FooterLink({ children, href }: Readonly<{ children: React.ReactNode; href: string }>) {
  return (
    <Link className="inline-flex min-h-11 items-center text-muted-foreground transition-colors hover:text-foreground" href={href}>
      {children}
    </Link>
  );
}
