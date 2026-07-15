"use client";

import { ChartNoAxesColumnIncreasing } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, type ReactNode } from "react";

import { PublicLocaleMenu } from "@/components/fpds/public/public-locale-menu";
import { getPublicMessages, normalizePublicLocale, type PublicLocale } from "@/lib/public-locale";
import { buildScopedPublicHrefFromSearchParams } from "@/lib/public-query";
import { cn } from "@/lib/utils";

const FOOTER_COPY: Record<
  PublicLocale,
  {
    brandNote: string;
    coverage: string;
    data: string;
    explore: string;
    legalNote: string;
    planned: string;
    aggregate: string;
    evidenceBoundary: string;
    productTypes: string;
  }
> = {
  en: {
    brandNote: "Public financial product data for bank comparison.",
    coverage: "Coverage",
    data: "Data",
    explore: "Explore",
    legalNote: "Source evidence and internal review traces stay private.",
    planned: "Planned",
    aggregate: "Aggregate fields",
    evidenceBoundary: "Evidence boundary",
    productTypes: "Product types"
  },
  ko: {
    brandNote: "은행 비교를 위한 공개 금융상품 데이터입니다.",
    coverage: "커버리지",
    data: "데이터",
    explore: "탐색",
    legalNote: "원문 증거와 내부 검토 trace는 공개하지 않습니다.",
    planned: "예정",
    aggregate: "집계 필드",
    evidenceBoundary: "증거 경계",
    productTypes: "상품 유형"
  },
  ja: {
    brandNote: "銀行比較のための公開金融商品データです。",
    coverage: "掲載範囲",
    data: "データ",
    explore: "探す",
    legalNote: "原文証拠と内部レビュー trace は公開しません。",
    planned: "予定",
    aggregate: "集計フィールド",
    evidenceBoundary: "証拠の境界",
    productTypes: "商品タイプ"
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

  return (
    <footer className="border-t border-border/80 bg-card/80">
      <div className="mx-auto w-full max-w-7xl px-4 py-8 md:px-6 md:py-10">
        <div className="grid gap-8 lg:grid-cols-[minmax(16rem,0.9fr)_minmax(0,1.6fr)]">
          <div className="max-w-sm">
            <Link href={dashboardHref} className="inline-flex items-center gap-3">
              <span className="flex size-8 items-center justify-center rounded-md border border-primary/20 bg-primary text-primary-foreground shadow-sm">
                <ChartNoAxesColumnIncreasing className="size-4" aria-hidden="true" />
              </span>
              <span className="text-lg font-semibold text-foreground">{copy.shell.brand}</span>
            </Link>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">{footerCopy.brandNote}</p>
          </div>

          <div className="grid gap-6 sm:grid-cols-3">
            <FooterGroup title={footerCopy.explore}>
              <FooterLink href={dashboardHref}>{copy.nav.dashboard}</FooterLink>
              <FooterLink href={productsHref}>{copy.nav.products}</FooterLink>
              <FooterLink href={loansHref}>{copy.nav.loan}</FooterLink>
            </FooterGroup>
            <FooterGroup title={footerCopy.coverage}>
              <FooterLink href={productsHref}>{copy.dashboard.banksInScope}</FooterLink>
              <FooterLink href={productsHref}>{copy.dashboard.visibleProducts}</FooterLink>
              <FooterLink href={productsHref}>{footerCopy.productTypes}</FooterLink>
            </FooterGroup>
            <FooterGroup title={footerCopy.data}>
              <FooterText>{footerCopy.aggregate}</FooterText>
              <FooterText>{footerCopy.evidenceBoundary}</FooterText>
            </FooterGroup>
          </div>
        </div>

        <div className="mt-8 flex flex-col gap-4 border-t border-border/70 pt-5 sm:flex-row sm:items-center sm:justify-between">
          <PublicLocaleMenu align="start" className="flex" triggerClassName="w-full justify-between sm:w-auto" />
          <p className="max-w-3xl text-xs leading-5 text-muted-foreground">{footerCopy.legalNote}</p>
        </div>

        <div className="mt-4 text-xs text-muted-foreground">© FPDS 2026</div>
      </div>
    </footer>
  );
}

export function PublicFooter() {
  return (
    <Suspense fallback={<div className="h-28 border-t border-border/80 bg-card/80" aria-hidden="true" />}>
      <FooterContent />
    </Suspense>
  );
}

function FooterGroup({ children, title }: Readonly<{ children: ReactNode; title: string }>) {
  return (
    <div>
      <h2 className="text-sm font-semibold text-foreground">{title}</h2>
      <div className="mt-3 grid gap-2">{children}</div>
    </div>
  );
}

function FooterLink({ children, href }: Readonly<{ children: ReactNode; href: string }>) {
  return (
    <Link className="text-sm text-muted-foreground transition-colors hover:text-foreground" href={href}>
      {children}
    </Link>
  );
}

function FooterText({ children, className }: Readonly<{ children: ReactNode; className?: string }>) {
  return <span className={cn("text-sm text-muted-foreground", className)}>{children}</span>;
}
