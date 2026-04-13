"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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
  UploadCloud
} from "lucide-react";
import * as React from "react";

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
  useSidebar
} from "@/components/ui/sidebar";
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
  headerActions?: React.ReactNode;
  className?: string;
};

type NavItem = {
  label: string;
  description: string;
  href?: string;
  status: "Live" | "Next" | "Planned";
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
};

type NavGroup = {
  title: string;
  items: NavItem[];
};

const navGroups: NavGroup[] = [
  {
    title: "Overview",
    items: [
      {
        label: "Overview",
        description: "Current triage entrypoint",
        href: "/admin",
        status: "Live",
        icon: LayoutDashboard
      }
    ]
  },
  {
    title: "Review",
    items: [
      {
        label: "Review Queue",
        description: "Queue, validation, and decision intake",
        href: "/admin/reviews",
        status: "Live",
        icon: FileClock
      },
      {
        label: "Trace Viewer",
        description: "Evidence inspection and field provenance",
        status: "Planned",
        icon: BookOpenText
      }
    ]
  },
  {
    title: "Operations",
    items: [
      {
        label: "Runs",
        description: "Execution diagnostics and failure context",
        href: "/admin/runs",
        status: "Live",
        icon: Activity
      },
      {
        label: "Changes",
        description: "Canonical chronology and override context",
        href: "/admin/changes",
        status: "Live",
        icon: ArrowUpRight
      },
      {
        label: "Audit Log",
        description: "Append-only workflow and auth trail",
        href: "/admin/audit",
        status: "Live",
        icon: ScrollText
      },
      {
        label: "Publish",
        description: "Retry, pending, and reconciliation monitor",
        status: "Planned",
        icon: UploadCloud
      }
    ]
  },
  {
    title: "Observability",
    items: [
      {
        label: "Usage",
        description: "LLM usage and cost visibility",
        href: "/admin/usage",
        status: "Live",
        icon: Sparkles
      },
      {
        label: "Dashboard Health",
        description: "Serving freshness and completeness",
        status: "Planned",
        icon: Gauge
      }
    ]
  }
];

function findMatchingGroupIndex(pathname: string | null) {
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
    })
  );
  return matchingIndex >= 0 ? matchingIndex : 0;
}

function ModuleTabs({
  activeGroupIndex,
  onChange
}: {
  activeGroupIndex: number;
  onChange: (index: number) => void;
}) {
  return (
    <nav aria-label="Primary modules" className="hidden flex-1 items-center gap-1 overflow-x-auto md:flex">
      {navGroups.map((group, index) => {
        const isActive = index === activeGroupIndex;

        return (
          <button
            className={cn(
              "rounded-xl px-3 py-2 text-sm font-medium transition-colors",
              isActive ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted/70 hover:text-foreground"
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
  onChange
}: {
  activeGroupIndex: number;
  onChange: (index: number) => void;
}) {
  const { setOpenMobile } = useSidebar();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t bg-background/95 backdrop-blur md:hidden">
      <div className="grid grid-cols-4">
        {navGroups.map((group, index) => {
          const Icon = group.items[0]?.icon;
          const isActive = index === activeGroupIndex;

          return (
            <button
              className={cn(
                "flex flex-col items-center gap-1 px-2 py-2 text-[11px] transition-colors",
                isActive ? "text-foreground" : "text-muted-foreground"
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
  pathname,
  user
}: {
  activeGroupIndex: number;
  environmentLabel: string;
  pathname: string | null;
  user: ShellUser;
}) {
  const activeGroup = navGroups[activeGroupIndex];

  return (
    <Sidebar className="top-14 h-[calc(100svh-3.5rem)]!" collapsible="icon" variant="inset">
      <SidebarHeader className="gap-4 border-b border-sidebar-border/70 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">FPDS Admin</p>
            <p className="mt-1 text-sm font-medium text-sidebar-foreground">{activeGroup.title}</p>
          </div>
          <span className="inline-flex items-center rounded-full bg-info-soft px-3 py-1 text-[11px] font-medium text-info">
            {environmentLabel}
          </span>
        </div>
        <div className="rounded-2xl border border-sidebar-border/70 bg-background/80 px-3 py-2 text-sm text-muted-foreground">
          Compact admin shell with route-oriented triage surfaces.
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
                          <Link href={item.href}>
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
            <span className="text-muted-foreground">Role</span>
            <span className="font-medium text-sidebar-foreground">{user.role}</span>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}

const ApplicationShell5 = ({ children, environmentLabel, user, headerActions, className }: ApplicationShell5Props) => {
  const pathname = usePathname();
  const [activeGroupIndex, setActiveGroupIndex] = React.useState(() => findMatchingGroupIndex(pathname));

  React.useEffect(() => {
    setActiveGroupIndex(findMatchingGroupIndex(pathname));
  }, [pathname]);

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
                <p className="text-sm font-semibold text-foreground">FPDS Admin</p>
                <p className="text-xs text-muted-foreground">Operations shell</p>
              </div>
            </div>

            <ModuleTabs activeGroupIndex={activeGroupIndex} onChange={setActiveGroupIndex} />

            <div className="ml-auto hidden items-center gap-3 md:flex">
              <div className="flex items-center gap-2 rounded-full border border-border/80 bg-card px-3 py-2 text-sm text-muted-foreground">
                <Search className="h-4 w-4" />
                Search by bank, product, run, or candidate soon
              </div>
              <div className="rounded-full border border-border/80 bg-card px-3 py-2 text-sm text-muted-foreground">
                EN / KO / JA
              </div>
              {headerActions}
            </div>
          </div>
        </header>

        <div className="flex flex-1">
          <AppSidebar
            activeGroupIndex={activeGroupIndex}
            environmentLabel={environmentLabel}
            pathname={pathname}
            user={user}
          />

          <SidebarInset className="bg-transparent pb-20 md:pb-0">
            <div className="flex min-h-[calc(100vh-3.5rem)] flex-col">
              <div className="border-b bg-background/70 px-4 py-3 backdrop-blur md:hidden">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-foreground">{navGroups[activeGroupIndex].title}</p>
                    <p className="text-xs text-muted-foreground">Compact FPDS operator shell</p>
                  </div>
                  {headerActions}
                </div>
                <div className="mt-3 flex items-center justify-between rounded-2xl border border-border/80 bg-card px-3 py-2 text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-2">
                    <ArrowUpRight className="h-3.5 w-3.5" />
                    Search, locale, and route actions stay in the shell
                  </span>
                </div>
              </div>

              <main className="flex-1 px-4 py-6 md:px-6 lg:px-8">{children}</main>
            </div>
          </SidebarInset>
        </div>
      </div>

      <MobileBottomNav activeGroupIndex={activeGroupIndex} onChange={setActiveGroupIndex} />
    </SidebarProvider>
  );
};

export { ApplicationShell5 };
