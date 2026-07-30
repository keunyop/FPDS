"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import * as React from "react";
import {
  Activity,
  Building2,
  Database,
  FileClock,
  Gauge,
  Globe2,
  History,
  LayoutDashboard,
  LogOut,
  ScrollText,
  Shapes,
  Sparkles,
  UserRound,
} from "lucide-react";

import { LogoutButton } from "@/app/admin/LogoutButton";
import { AdminLocaleSwitcher } from "@/components/admin-locale-switcher";
import { AdminCountrySwitcher } from "@/components/fpds/admin/admin-country-switcher";
import { AdminMark } from "@/components/fpds/admin/admin-mark";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

type ShellUser = {
  name: string;
  loginId: string;
  role: string;
};

type AdminShellProps = {
  children: React.ReactNode;
  countryCode: string;
  csrfToken: string | null | undefined;
  environmentLabel: string;
  logoutApiOrigin: string;
  user: ShellUser;
  locale: AdminLocale;
  className?: string;
};

type NavItem = {
  key:
    | "overview"
    | "reviews"
    | "runs"
    | "banks"
    | "sources"
    | "productTypes"
    | "countries"
    | "changes"
    | "audit"
    | "usage"
    | "health";
  href: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
};

type ShellCopy = {
  brand: string;
  dailyWork: string;
  moreTools: string;
  account: string;
  items: Partial<Record<NavItem["key"], string>>;
};

const primaryItems: NavItem[] = [
  { key: "overview", href: "/admin", icon: LayoutDashboard },
  { key: "reviews", href: "/admin/reviews", icon: FileClock },
  { key: "runs", href: "/admin/runs", icon: Activity },
  { key: "banks", href: "/admin/banks", icon: Building2 },
];

const toolItems: NavItem[] = [
  { key: "sources", href: "/admin/sources", icon: Database },
  { key: "productTypes", href: "/admin/product-types", icon: Shapes },
  { key: "countries", href: "/admin/countries", icon: Globe2 },
  { key: "changes", href: "/admin/changes", icon: History },
  { key: "audit", href: "/admin/audit", icon: ScrollText },
  { key: "usage", href: "/admin/usage", icon: Sparkles },
  { key: "health", href: "/admin/health/dashboard", icon: Gauge },
];

const copyByLocale: Record<AdminLocale, ShellCopy> = {
  en: {
    brand: "FPDS Admin",
    dailyWork: "Daily work",
    moreTools: "More tools",
    account: "Account",
    items: {
      overview: "Overview",
      reviews: "Review",
      runs: "Runs",
      banks: "Banks",
      sources: "Sources",
      productTypes: "Product types",
      changes: "Changes",
      audit: "Audit log",
      usage: "Usage",
      health: "Public health",
    },
  },
  ko: {
    brand: "FPDS 관리자",
    dailyWork: "주요 업무",
    moreTools: "기타 도구",
    account: "계정",
    items: {
      overview: "개요",
      reviews: "검토",
      runs: "실행",
      banks: "은행",
      sources: "소스",
      productTypes: "상품 유형",
      changes: "변경 이력",
      audit: "감사 로그",
      usage: "사용량",
      health: "공개 데이터 상태",
    },
  },
  ja: {
    brand: "FPDS 管理",
    dailyWork: "日常業務",
    moreTools: "その他のツール",
    account: "アカウント",
    items: {
      overview: "概要",
      reviews: "審査",
      runs: "実行",
      banks: "銀行",
      sources: "ソース",
      productTypes: "商品タイプ",
      changes: "変更履歴",
      audit: "監査ログ",
      usage: "使用量",
      health: "公開データ状態",
    },
  },
};

const countryMenuLabel: Record<AdminLocale, string> = {
  en: "Countries",
  ko: "\uAD6D\uAC00",
  ja: "\u56FD",
};

function navItemLabel(copy: ShellCopy, locale: AdminLocale, key: NavItem["key"]) {
  return key === "countries" ? countryMenuLabel[locale] : copy.items[key] ?? key;
}

function isActive(pathname: string | null, href: string) {
  if (!pathname) {
    return false;
  }

  if (href === "/admin") {
    return pathname === href;
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

function currentItem(pathname: string | null) {
  return [...primaryItems, ...toolItems].find((item) => isActive(pathname, item.href)) ?? primaryItems[0];
}

function AdminNavLink({
  item,
  locale,
  pathname,
}: {
  item: NavItem;
  locale: AdminLocale;
  pathname: string | null;
}) {
  const copy = copyByLocale[locale];
  const active = isActive(pathname, item.href);
  const Icon = item.icon;
  const label = navItemLabel(copy, locale, item.key);

  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild className="bg-transparent" isActive={active} tooltip={label}>
        <Link
          aria-current={active ? "page" : undefined}
          href={buildAdminHref(item.href, new URLSearchParams(), locale)}
        >
          <Icon className="h-4 w-4" aria-hidden="true" />
          <span>{label}</span>
        </Link>
      </SidebarMenuButton>
    </SidebarMenuItem>
  );
}

function PrimaryNav({
  locale,
  pathname,
}: {
  locale: AdminLocale;
  pathname: string | null;
}) {
  const copy = copyByLocale[locale];

  return (
    <nav aria-label={copy.dailyWork} className="hidden min-w-0 flex-1 items-center gap-1 overflow-x-auto md:flex">
      {primaryItems.map((item) => {
        const active = isActive(pathname, item.href);

        return (
          <Link
            aria-current={active ? "page" : undefined}
            className={cn(
              "inline-flex min-h-10 items-center border-b-2 px-3 text-sm font-semibold transition-colors",
              active
                ? "border-sidebar-primary text-sidebar-foreground"
                : "border-transparent text-sidebar-foreground/60 hover:border-sidebar-border hover:text-sidebar-foreground",
            )}
            href={buildAdminHref(item.href, new URLSearchParams(), locale)}
            key={item.key}
          >
            {navItemLabel(copy, locale, item.key)}
          </Link>
        );
      })}
    </nav>
  );
}

function MobileBottomNav({
  locale,
  pathname,
}: {
  locale: AdminLocale;
  pathname: string | null;
}) {
  const copy = copyByLocale[locale];

  return (
    <nav
      aria-label={copy.dailyWork}
      className="fixed inset-x-0 bottom-0 z-40 border-t border-sidebar-border bg-sidebar md:hidden"
    >
      <div className="grid grid-cols-4">
        {primaryItems.map((item) => {
          const active = isActive(pathname, item.href);
          const Icon = item.icon;

          return (
            <Link
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex min-h-14 flex-col items-center justify-center gap-1 border-t-2 px-2 py-1.5 text-[11px] font-semibold transition-colors",
                active
                  ? "border-sidebar-primary text-sidebar-primary"
                  : "border-transparent text-sidebar-foreground/65 hover:text-sidebar-foreground",
              )}
              href={buildAdminHref(item.href, new URLSearchParams(), locale)}
              key={item.key}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              <span className="truncate">{navItemLabel(copy, locale, item.key)}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

function AppSidebar({
  locale,
  logoutApiOrigin,
  pathname,
  user,
}: {
  locale: AdminLocale;
  logoutApiOrigin: string;
  pathname: string | null;
  user: ShellUser;
}) {
  const copy = copyByLocale[locale];
  const userInitial = user.loginId.trim().charAt(0).toUpperCase() || "U";
  const visibleToolItems = user.role.toLowerCase() === "admin"
    ? toolItems
    : toolItems.filter((item) => item.key !== "countries");

  return (
    <Sidebar className="top-14 h-[calc(100svh-3.5rem)]! border-r bg-sidebar" collapsible="icon">
      <SidebarHeader className="px-2 py-2">
        <div className="flex items-center justify-end">
          <SidebarTrigger className="hidden md:inline-flex" />
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup className="px-2 py-2">
          <SidebarGroupLabel>{copy.dailyWork}</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1">
              {primaryItems.map((item) => (
                <AdminNavLink item={item} locale={locale} pathname={pathname} key={item.key} />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="px-2 py-2">
          <SidebarGroupLabel>{copy.moreTools}</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1">
              {visibleToolItems.map((item) => (
                <AdminNavLink item={item} locale={locale} pathname={pathname} key={item.key} />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t px-2 py-3">
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  className="h-12 w-full justify-start bg-transparent data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                  size="lg"
                >
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-primary/10 font-semibold text-primary">{userInitial}</AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-medium">{user.name}</span>
                    <span className="truncate text-xs text-sidebar-foreground/55">{user.loginId}</span>
                  </div>
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-64 min-w-64" side="top">
                <DropdownMenuLabel className="p-0 font-normal">
                  <div className="flex items-center gap-3 px-1 py-1.5 text-left">
                    <Avatar className="h-9 w-9">
                      <AvatarFallback className="bg-primary/10 font-semibold text-primary">{userInitial}</AvatarFallback>
                    </Avatar>
                    <div className="grid min-w-0 flex-1">
                      <span className="truncate text-sm font-medium text-foreground">{user.name}</span>
                      <span className="truncate text-xs text-muted-foreground">{user.loginId}</span>
                    </div>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <div className="p-1">
                  <DropdownMenuItem className="justify-start gap-2 text-left" disabled>
                    <UserRound className="h-4 w-4" />
                    <span>{copy.account}</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <React.Suspense fallback={null}>
                    <AdminLocaleSwitcher locale={locale} variant="menu" />
                  </React.Suspense>
                  <DropdownMenuSeparator />
                  <LogoutButton
                    apiOrigin={logoutApiOrigin}
                    className="w-full justify-start px-1.5 text-left"
                    icon={LogOut}
                    variant="ghost"
                  />
                </div>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}

function AdminShell({
  children,
  countryCode,
  csrfToken,
  environmentLabel,
  logoutApiOrigin,
  user,
  locale,
  className,
}: AdminShellProps) {
  const pathname = usePathname();
  const copy = copyByLocale[locale];
  const selectedItem = currentItem(pathname);

  return (
    <SidebarProvider className={cn("min-h-screen bg-transparent", className)}>
      <div className="flex min-h-screen w-full flex-col">
        <header className="sticky top-0 z-40 border-b border-sidebar-border bg-sidebar text-sidebar-foreground">
          <div className="flex h-14 items-center gap-3 px-4 md:px-6">
            <SidebarTrigger className="md:hidden" />
            <div className="flex items-center gap-3">
              <AdminMark />
              <p className="text-base font-semibold tracking-[-0.02em] text-sidebar-foreground">{copy.brand}</p>
            </div>

            <PrimaryNav locale={locale} pathname={pathname} />

            <div className="ml-auto flex items-center gap-2">
              <AdminCountrySwitcher countryCode={countryCode} csrfToken={csrfToken} locale={locale} />
              <span className="hidden min-h-8 items-center border border-sidebar-border bg-sidebar-accent px-2.5 text-[11px] font-semibold text-sidebar-foreground/75 sm:inline-flex">
                {environmentLabel}
              </span>
            </div>
          </div>
        </header>

        <div className="flex min-w-0 flex-1">
          <AppSidebar
            locale={locale}
            logoutApiOrigin={logoutApiOrigin}
            pathname={pathname}
            user={user}
          />

          <SidebarInset className="min-w-0 bg-transparent pb-20 md:pb-0">
            <div className="flex min-h-[calc(100vh-3.5rem)] min-w-0 flex-col">
              <div className="border-b border-border bg-card px-4 py-2.5 md:hidden">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-foreground">{navItemLabel(copy, locale, selectedItem.key)}</p>
                  <span className="inline-flex min-h-8 items-center border border-border bg-muted px-2.5 text-[11px] font-semibold text-muted-foreground">
                    {environmentLabel}
                  </span>
                </div>
              </div>

              <main className="min-w-0 max-w-full flex-1 overflow-x-hidden px-4 py-6 md:px-6 lg:px-8">
                {children}
              </main>
            </div>
          </SidebarInset>
        </div>
      </div>

      <MobileBottomNav locale={locale} pathname={pathname} />
    </SidebarProvider>
  );
}

export { AdminShell };
