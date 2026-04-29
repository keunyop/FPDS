"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import * as React from "react";
import {
  Activity,
  ArrowUpRight,
  BookOpenText,
  FileClock,
  Gauge,
  LayoutDashboard,
  LogOut,
  Search,
  ScrollText,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  UserRound,
} from "lucide-react";

import { LogoutButton } from "@/app/admin/LogoutButton";
import { AdminLocaleSwitcher } from "@/components/admin-locale-switcher";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

type ShellUser = {
  name: string;
  loginId: string;
  role: string;
};

type ApplicationShell5Props = {
  children: React.ReactNode;
  environmentLabel: string;
  logoutApiOrigin: string;
  user: ShellUser;
  locale: AdminLocale;
  className?: string;
};

type NavItem = {
  label: string;
  description: string;
  href?: string;
  status: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
};

type NavGroup = {
  title: string;
  items: NavItem[];
};

type ShellCopy = {
  brand: string;
  shellLabel: string;
  shellNote: string;
  searchHint: string;
  mobileTitle: string;
  mobileNote: string;
  roleLabel: string;
  status: Record<"live" | "next" | "planned", string>;
  groups: {
    overview: string;
    review: string;
    operations: string;
    observability: string;
  };
  items: {
    overview: { label: string; description: string };
    reviews: { label: string; description: string };
    traceViewer: { label: string; description: string };
    runs: { label: string; description: string };
    banks: { label: string; description: string };
    productTypes: { label: string; description: string };
    sources: { label: string; description: string };
    changes: { label: string; description: string };
    auditLog: { label: string; description: string };
    publish: { label: string; description: string };
    usage: { label: string; description: string };
    dashboardHealth: { label: string; description: string };
  };
};

const shellCopyByLocale: Record<AdminLocale, ShellCopy> = {
  en: {
    brand: "FPDS Admin",
    shellLabel: "Operations shell",
    shellNote: "Floating admin shell with route-oriented triage surfaces.",
    searchHint: "Search by bank, product, run, or candidate",
    mobileTitle: "Floating FPDS operator shell",
    mobileNote: "Search, locale, and route actions stay in the shell",
    roleLabel: "Role",
    status: {
      live: "Live",
      next: "Next",
      planned: "Planned",
    },
    groups: {
      overview: "Overview",
      review: "Review",
      operations: "Operations",
      observability: "Observability",
    },
    items: {
      overview: { label: "Dashboard", description: "Current triage entrypoint" },
      reviews: { label: "Review Queue", description: "Queue, validation, and decision intake" },
      traceViewer: { label: "Trace Viewer", description: "Evidence inspection and field provenance" },
      runs: { label: "Runs", description: "Execution diagnostics and failure context" },
      banks: { label: "Banks", description: "Bank list, homepage setup, and coverage" },
      productTypes: { label: "Product Types", description: "Registry, descriptions, and AI fallback metadata" },
      sources: { label: "Sources", description: "Generated source detail, read-only" },
      changes: { label: "Changes", description: "Canonical chronology and override context" },
      auditLog: { label: "Audit Log", description: "Append-only workflow and auth trail" },
      publish: { label: "Publish", description: "Retry, pending, and reconciliation monitor" },
      usage: { label: "Usage", description: "LLM usage and cost visibility" },
      dashboardHealth: { label: "Dashboard Health", description: "Serving freshness and completeness" },
    },
  },
  ko: {
    brand: "FPDS 관리자",
    shellLabel: "운영 셸",
    shellNote: "경로 중심 분류 화면을 담는 플로팅 관리자 셸입니다.",
    searchHint: "은행, 상품, 실행, 후보로 검색",
    mobileTitle: "플로팅 FPDS 운영 셸",
    mobileNote: "검색, 언어, 경로 동작은 셸에서 처리됩니다",
    roleLabel: "권한",
    status: {
      live: "운영중",
      next: "다음",
      planned: "예정",
    },
    groups: {
      overview: "개요",
      review: "검토",
      operations: "운영",
      observability: "관찰",
    },
    items: {
      overview: { label: "Dashboard", description: "현재 triage 시작점" },
      reviews: { label: "검토 대기열", description: "대기, 검증, 결정 접수" },
      traceViewer: { label: "추적 뷰어", description: "증거 검사와 필드 출처 확인" },
      runs: { label: "실행", description: "실행 진단과 실패 맥락" },
      banks: { label: "은행", description: "은행 목록, 홈페이지 설정, coverage" },
      productTypes: { label: "상품 유형", description: "Registry, 설명, AI fallback 메타데이터" },
      sources: { label: "소스", description: "생성된 source detail, 읽기 전용" },
      changes: { label: "변경 이력", description: "정규화된 이력과 재정의 맥락" },
      auditLog: { label: "감사 로그", description: "추적 가능한 작업 및 인증 이력" },
      publish: { label: "게시", description: "재시도, 대기, 조정 모니터" },
      usage: { label: "사용량", description: "LLM 사용량과 비용 가시성" },
      dashboardHealth: { label: "대시보드 상태", description: "제공 신선도와 완전성" },
    },
  },
  ja: {
    brand: "FPDS 管理",
    shellLabel: "運用シェル",
    shellNote: "経路中心のトリアージ画面をまとめたフローティング管理シェルです。",
    searchHint: "銀行、商品、実行、候補で検索",
    mobileTitle: "フローティング FPDS 運用シェル",
    mobileNote: "検索、言語、経路操作はシェル内で完結します",
    roleLabel: "ロール",
    status: {
      live: "運用中",
      next: "次",
      planned: "予定",
    },
    groups: {
      overview: "概要",
      review: "審査",
      operations: "運用",
      observability: "監視",
    },
    items: {
      overview: { label: "Dashboard", description: "現在のトリアージ入口" },
      reviews: { label: "審査キュー", description: "キュー、検証、判断の受付" },
      traceViewer: { label: "トレースビューア", description: "証跡確認とフィールド由来の追跡" },
      runs: { label: "実行", description: "実行診断と失敗文脈" },
      banks: { label: "銀行", description: "銀行一覧、ホームページ設定、カバレッジ" },
      productTypes: { label: "商品タイプ", description: "Registry、説明、AI fallback メタデータ" },
      sources: { label: "ソース", description: "生成された source detail、読み取り専用" },
      changes: { label: "変更履歴", description: "正規化された履歴と上書き文脈" },
      auditLog: { label: "監査ログ", description: "追記型の作業・認証履歴" },
      publish: { label: "公開", description: "再試行、保留、照合作業の監視" },
      usage: { label: "使用量", description: "LLM 使用量とコストの可視化" },
      dashboardHealth: { label: "ダッシュボード健全性", description: "提供鮮度と完全性" },
    },
  },
};

const accountMenuLabelByLocale: Record<AdminLocale, string> = {
  en: "Account",
  ko: "계정",
  ja: "アカウント",
};

function getNavGroups(locale: AdminLocale): NavGroup[] {
  const copy = shellCopyByLocale[locale];

  return [
    {
      title: copy.groups.overview,
      items: [
        {
          label: copy.items.overview.label,
          description: copy.items.overview.description,
          href: "/admin",
          status: copy.status.live,
          icon: LayoutDashboard,
        },
      ],
    },
    {
      title: copy.groups.review,
      items: [
        {
          label: copy.items.reviews.label,
          description: copy.items.reviews.description,
          href: "/admin/reviews",
          status: copy.status.live,
          icon: FileClock,
        },
        {
          label: copy.items.traceViewer.label,
          description: copy.items.traceViewer.description,
          status: copy.status.planned,
          icon: BookOpenText,
        },
      ],
    },
    {
      title: copy.groups.operations,
      items: [
        {
          label: copy.items.banks.label,
          description: copy.items.banks.description,
          href: "/admin/banks",
          status: copy.status.live,
          icon: Search,
        },
        {
          label: copy.items.productTypes.label,
          description: copy.items.productTypes.description,
          href: "/admin/product-types",
          status: copy.status.live,
          icon: Sparkles,
        },
        {
          label: copy.items.sources.label,
          description: copy.items.sources.description,
          href: "/admin/sources",
          status: copy.status.live,
          icon: BookOpenText,
        },
        {
          label: copy.items.runs.label,
          description: copy.items.runs.description,
          href: "/admin/runs",
          status: copy.status.live,
          icon: Activity,
        },
        {
          label: copy.items.changes.label,
          description: copy.items.changes.description,
          href: "/admin/changes",
          status: copy.status.live,
          icon: ArrowUpRight,
        },
        {
          label: copy.items.auditLog.label,
          description: copy.items.auditLog.description,
          href: "/admin/audit",
          status: copy.status.live,
          icon: ScrollText,
        },
        {
          label: copy.items.publish.label,
          description: copy.items.publish.description,
          status: copy.status.planned,
          icon: UploadCloud,
        },
      ],
    },
    {
      title: copy.groups.observability,
      items: [
        {
          label: copy.items.usage.label,
          description: copy.items.usage.description,
          href: "/admin/usage",
          status: copy.status.live,
          icon: Sparkles,
        },
        {
          label: copy.items.dashboardHealth.label,
          description: copy.items.dashboardHealth.description,
          href: "/admin/health/dashboard",
          status: copy.status.live,
          icon: Gauge,
        },
      ],
    },
  ];
}

function findMatchingGroupIndex(pathname: string | null, navGroups: NavGroup[]) {
  if (!pathname) {
    return 0;
  }

  const matchingIndex = navGroups.findIndex((group) =>
    group.items.some((item) => {
      if (!item.href) {
        return false;
      }
      if (item.href === "/admin") {
        return pathname === item.href;
      }
      return pathname === item.href || pathname.startsWith(`${item.href}/`);
    }),
  );

  return matchingIndex >= 0 ? matchingIndex : 0;
}

function isNavItemActive(pathname: string | null, href?: string) {
  if (!pathname || !href) {
    return false;
  }

  if (href === "/admin") {
    return pathname === href;
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

function ModuleTabs({
  activeGroupIndex,
  groups,
  onChange,
}: {
  activeGroupIndex: number;
  groups: NavGroup[];
  onChange: (index: number) => void;
}) {
  return (
    <nav aria-label="Primary modules" className="hidden flex-1 items-center gap-1 overflow-x-auto md:flex">
      {groups.map((group, index) => {
        const isActive = index === activeGroupIndex;

        return (
          <button
            className={cn(
              "rounded-xl px-3 py-2 text-sm font-medium transition-colors",
              isActive ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted/70 hover:text-foreground",
            )}
            key={group.title}
            onClick={() => onChange(index)}
            type="button"
          >
            {group.title}
          </button>
        );
      })}
    </nav>
  );
}

function MobileBottomNav({
  activeGroupIndex,
  groups,
  onChange,
}: {
  activeGroupIndex: number;
  groups: NavGroup[];
  onChange: (index: number) => void;
}) {
  const { setOpenMobile } = useSidebar();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t bg-background/95 backdrop-blur md:hidden">
      <div className="grid grid-cols-4">
        {groups.map((group, index) => {
          const Icon = group.items[0]?.icon;
          const isActive = index === activeGroupIndex;

          return (
            <button
              className={cn(
                "flex flex-col items-center gap-1 px-2 py-2 text-[11px] transition-colors",
                isActive ? "text-foreground" : "text-muted-foreground",
              )}
              key={group.title}
              onClick={() => {
                onChange(index);
                setOpenMobile(false);
              }}
              type="button"
            >
              {Icon ? <Icon className="h-4 w-4" /> : null}
              <span className="truncate">{group.title}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

function AppSidebar({
  activeGroupIndex,
  locale,
  logoutApiOrigin,
  navGroups,
  pathname,
  user,
}: {
  activeGroupIndex: number;
  locale: AdminLocale;
  logoutApiOrigin: string;
  navGroups: NavGroup[];
  pathname: string | null;
  user: ShellUser;
}) {
  const activeGroup = navGroups[activeGroupIndex];
  const accountMenuLabel = accountMenuLabelByLocale[locale];
  const userInitial = user.loginId.trim().charAt(0).toUpperCase() || "U";

  return (
    <Sidebar className="top-14 h-[calc(100svh-3.5rem)]! border-r bg-sidebar" collapsible="icon">
      <SidebarHeader className="px-2 py-2">
        <div className="flex items-center justify-between gap-2">
          <p className="truncate px-2 text-sm font-semibold text-sidebar-foreground group-data-[collapsible=icon]:hidden">
            {activeGroup.title}
          </p>
          <SidebarTrigger className="hidden md:inline-flex" />
        </div>
      </SidebarHeader>
      <SidebarContent className="overflow-hidden">
        <ScrollArea className="min-h-0 flex-1">
          <SidebarGroup className="px-2 py-3">
            <SidebarGroupContent>
              <SidebarMenu className="gap-1">
                {activeGroup.items
                  .filter((item) => item.href)
                  .map((item) => {
                  const Icon = item.icon;
                  const isActive = isNavItemActive(pathname, item.href);

                  return (
                    <SidebarMenuItem key={item.label}>
                      <SidebarMenuButton asChild className="bg-transparent" isActive={isActive} tooltip={item.label}>
                        <Link href={buildAdminHref(item.href!, new URLSearchParams(), locale)}>
                          <Icon className="h-4 w-4" />
                          <span>{item.label}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </ScrollArea>
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
                    <span className="truncate text-xs text-muted-foreground">{user.loginId}</span>
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
                <DropdownMenuSeparator className="hidden" />
                <div className="hidden px-1 py-1 text-xs text-muted-foreground">
                  <span className="font-medium text-foreground" />
                  {" · "}
                  {null}
                </div>
                <DropdownMenuSeparator />
                <div className="p-1">
                  <DropdownMenuItem className="justify-start gap-2 text-left" disabled>
                    <UserRound className="h-4 w-4" />
                    <span>{accountMenuLabel}</span>
                  </DropdownMenuItem>
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

const ApplicationShell5 = ({
  children,
  environmentLabel,
  logoutApiOrigin,
  user,
  locale,
  className,
}: ApplicationShell5Props) => {
  const pathname = usePathname();
  const navGroups = getNavGroups(locale);
  const copy = shellCopyByLocale[locale];
  const [activeGroupIndex, setActiveGroupIndex] = React.useState(() => findMatchingGroupIndex(pathname, navGroups));

  React.useEffect(() => {
    setActiveGroupIndex(findMatchingGroupIndex(pathname, navGroups));
  }, [pathname, locale]);

  return (
    <SidebarProvider className={cn("min-h-screen bg-transparent", className)}>
      <div className="flex min-h-screen w-full flex-col">
        <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur">
          <div className="flex h-14 items-center gap-3 px-4 md:px-6">
            <SidebarTrigger className="md:hidden" />
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <p className="text-base font-semibold tracking-tight text-foreground">{copy.brand}</p>
            </div>

            <ModuleTabs activeGroupIndex={activeGroupIndex} groups={navGroups} onChange={setActiveGroupIndex} />

            <div className="ml-auto flex items-center gap-2">
              <span className="hidden items-center rounded-full border border-border/80 bg-card px-2.5 py-1 text-[11px] font-medium text-muted-foreground sm:inline-flex">
                {environmentLabel}
              </span>
              <React.Suspense fallback={null}>
                <AdminLocaleSwitcher locale={locale} />
              </React.Suspense>
            </div>
          </div>
        </header>

        <div className="flex min-w-0 flex-1">
          <AppSidebar
            activeGroupIndex={activeGroupIndex}
            locale={locale}
            logoutApiOrigin={logoutApiOrigin}
            navGroups={navGroups}
            pathname={pathname}
            user={user}
          />

          <SidebarInset className="min-w-0 bg-transparent pb-20 md:pb-0">
            <div className="flex min-h-[calc(100vh-3.5rem)] min-w-0 flex-col">
              <div className="border-b bg-background/70 px-4 py-3 backdrop-blur md:hidden">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-foreground">{navGroups[activeGroupIndex].title}</p>
                  <span className="inline-flex items-center rounded-full border border-border/80 bg-card px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                    {environmentLabel}
                  </span>
                </div>
              </div>

              <main className="min-w-0 max-w-full flex-1 overflow-x-hidden px-4 py-6 md:px-6 lg:px-8">{children}</main>
            </div>
          </SidebarInset>
        </div>
      </div>

      <MobileBottomNav activeGroupIndex={activeGroupIndex} groups={navGroups} onChange={setActiveGroupIndex} />
    </SidebarProvider>
  );
};

export { ApplicationShell5 };
