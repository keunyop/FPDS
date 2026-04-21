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
  Search,
  ScrollText,
  ShieldCheck,
  Sparkles,
  UploadCloud,
} from "lucide-react";

import { AdminLocaleSwitcher } from "@/components/admin-locale-switcher";
import { ScrollArea } from "@/components/ui/scroll-area";
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
  useSidebar,
} from "@/components/ui/sidebar";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

type ShellUser = {
  name: string;
  email: string;
  role: string;
};

type ApplicationShell5Props = {
  children: React.ReactNode;
  environmentLabel: string;
  user: ShellUser;
  locale: AdminLocale;
  headerActions?: React.ReactNode;
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
    shellNote: "Compact admin shell with route-oriented triage surfaces.",
    searchHint: "Search by bank, product, run, or candidate",
    mobileTitle: "Compact FPDS operator shell",
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
      overview: { label: "Overview", description: "Current triage entrypoint" },
      reviews: { label: "Review Queue", description: "Queue, validation, and decision intake" },
      traceViewer: { label: "Trace Viewer", description: "Evidence inspection and field provenance" },
      runs: { label: "Runs", description: "Execution diagnostics and failure context" },
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
    shellNote: "경로 중심 분류 화면을 담는 컴팩트한 관리자 셸입니다.",
    searchHint: "은행, 상품, 실행, 후보로 검색",
    mobileTitle: "컴팩트 FPDS 운영 셸",
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
      overview: { label: "개요", description: "현재 분류 시작점" },
      reviews: { label: "검토 대기열", description: "대기, 검증, 결정 접수" },
      traceViewer: { label: "추적 뷰어", description: "증거 검사와 필드 출처 확인" },
      runs: { label: "실행", description: "실행 진단과 실패 맥락" },
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
    shellNote: "経路中心のトリアージ画面をまとめたコンパクトな管理シェルです。",
    searchHint: "銀行、商品、実行、候補で検索",
    mobileTitle: "コンパクト FPDS 運用シェル",
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
      overview: { label: "概要", description: "現在のトリアージ入口" },
      reviews: { label: "審査キュー", description: "キュー、検証、判断の受付" },
      traceViewer: { label: "トレースビューア", description: "証跡確認とフィールド由来の追跡" },
      runs: { label: "実行", description: "実行診断と失敗文脈" },
      changes: { label: "変更履歴", description: "正規化された履歴と上書き文脈" },
      auditLog: { label: "監査ログ", description: "追記型の作業・認証履歴" },
      publish: { label: "公開", description: "再試行、保留、照合作業の監視" },
      usage: { label: "使用量", description: "LLM 使用量とコストの可視化" },
      dashboardHealth: { label: "ダッシュボード健全性", description: "提供鮮度と完全性" },
    },
  },
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
          label: "Banks",
          description: "Bank list, homepage setup, and coverage",
          href: "/admin/banks",
          status: copy.status.live,
          icon: Search,
        },
        {
          label: "Product Types",
          description: "Registry, descriptions, and AI fallback metadata",
          href: "/admin/product-types",
          status: copy.status.live,
          icon: Sparkles,
        },
        {
          label: "Sources",
          description: "Generated source detail, read-only",
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
  environmentLabel,
  locale,
  navGroups,
  pathname,
  user,
}: {
  activeGroupIndex: number;
  environmentLabel: string;
  locale: AdminLocale;
  navGroups: NavGroup[];
  pathname: string | null;
  user: ShellUser;
}) {
  const activeGroup = navGroups[activeGroupIndex];
  const copy = shellCopyByLocale[locale];

  return (
    <Sidebar className="top-14 h-[calc(100svh-3.5rem)]!" collapsible="icon" variant="inset">
      <SidebarHeader className="gap-4 border-b border-sidebar-border/70 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">{copy.brand}</p>
            <p className="mt-1 text-sm font-medium text-sidebar-foreground">{activeGroup.title}</p>
          </div>
          <span className="inline-flex items-center rounded-full bg-info-soft px-3 py-1 text-[11px] font-medium text-info">
            {environmentLabel}
          </span>
        </div>
        <div className="rounded-2xl border border-sidebar-border/70 bg-background/80 px-3 py-2 text-sm text-muted-foreground">
          {copy.shellNote}
        </div>
      </SidebarHeader>

      <SidebarContent className="overflow-hidden">
        <ScrollArea className="min-h-0 flex-1">
          <SidebarGroup>
            <SidebarGroupLabel>{activeGroup.title}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {activeGroup.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = item.href === pathname;

                  return (
                    <SidebarMenuItem key={item.label}>
                      {item.href ? (
                        <SidebarMenuButton asChild isActive={isActive} size="lg">
                          <Link href={buildAdminHref(item.href, new URLSearchParams(), locale)}>
                            <Icon className="h-4 w-4" />
                            <div className="grid flex-1 text-left">
                              <span>{item.label}</span>
                              <span className="text-xs text-muted-foreground">{item.description}</span>
                            </div>
                            <span className="rounded-full bg-success-soft px-2 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-success">
                              {item.status}
                            </span>
                          </Link>
                        </SidebarMenuButton>
                      ) : (
                        <div className="flex items-start gap-3 rounded-xl px-3 py-3 text-sm text-muted-foreground">
                          <Icon className="mt-0.5 h-4 w-4 shrink-0" />
                          <div className="grid flex-1 gap-1">
                            <span className="font-medium text-sidebar-foreground">{item.label}</span>
                            <span className="text-xs leading-5">{item.description}</span>
                          </div>
                          <span className="rounded-full bg-muted px-2 py-1 text-[10px] font-medium uppercase tracking-[0.12em]">
                            {item.status}
                          </span>
                        </div>
                      )}
                    </SidebarMenuItem>
                  );
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </ScrollArea>
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border/70 p-4">
        <div className="rounded-2xl border border-sidebar-border/70 bg-background/80 p-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-sidebar-foreground">{user.name}</p>
              <p className="truncate text-xs text-muted-foreground">{user.email}</p>
            </div>
          </div>
          <div className="mt-3 flex items-center justify-between rounded-xl bg-muted/60 px-3 py-2 text-xs">
            <span className="text-muted-foreground">{copy.roleLabel}</span>
            <span className="font-medium text-sidebar-foreground">{user.role}</span>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}

const ApplicationShell5 = ({
  children,
  environmentLabel,
  user,
  locale,
  headerActions,
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
              <div className="hidden md:block">
                <p className="text-sm font-semibold text-foreground">{copy.brand}</p>
                <p className="text-xs text-muted-foreground">{copy.shellLabel}</p>
              </div>
            </div>

            <ModuleTabs activeGroupIndex={activeGroupIndex} groups={navGroups} onChange={setActiveGroupIndex} />

            <div className="ml-auto hidden items-center gap-3 md:flex">
              <div className="flex items-center gap-2 rounded-full border border-border/80 bg-card px-3 py-2 text-sm text-muted-foreground">
                <Search className="h-4 w-4" />
                {copy.searchHint}
              </div>
              <React.Suspense fallback={null}>
                <AdminLocaleSwitcher locale={locale} />
              </React.Suspense>
              <React.Suspense fallback={null}>{headerActions}</React.Suspense>
            </div>
          </div>
        </header>

        <div className="flex flex-1">
          <AppSidebar
            activeGroupIndex={activeGroupIndex}
            environmentLabel={environmentLabel}
            locale={locale}
            navGroups={navGroups}
            pathname={pathname}
            user={user}
          />

          <SidebarInset className="bg-transparent pb-20 md:pb-0">
            <div className="flex min-h-[calc(100vh-3.5rem)] flex-col">
              <div className="border-b bg-background/70 px-4 py-3 backdrop-blur md:hidden">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-foreground">{navGroups[activeGroupIndex].title}</p>
                    <p className="text-xs text-muted-foreground">{copy.mobileTitle}</p>
                  </div>
                  <React.Suspense fallback={null}>{headerActions}</React.Suspense>
                </div>
                <div className="mt-3 flex items-center justify-between rounded-2xl border border-border/80 bg-card px-3 py-2 text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-2">
                    <ArrowUpRight className="h-3.5 w-3.5" />
                    {copy.mobileNote}
                  </span>
                </div>
              </div>

              <main className="flex-1 px-4 py-6 md:px-6 lg:px-8">{children}</main>
            </div>
          </SidebarInset>
        </div>
      </div>

      <MobileBottomNav activeGroupIndex={activeGroupIndex} groups={navGroups} onChange={setActiveGroupIndex} />
    </SidebarProvider>
  );
};

export { ApplicationShell5 };
