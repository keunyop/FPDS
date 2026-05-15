"use client";

import { Gauge, Info, Search } from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import type { ComponentType } from "react";

import { getPublicMessages, normalizePublicLocale } from "@/lib/public-locale";
import { buildScopedPublicHrefFromSearchParams, type PublicRoutePath } from "@/lib/public-query";
import { cn } from "@/lib/utils";

export function PublicNav() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const locale = normalizePublicLocale(searchParams.get("locale") ?? "");
  const copy = getPublicMessages(locale);
  const navItems: Array<{ href: PublicRoutePath; icon: ComponentType<{ className?: string }>; label: string }> = [
    { href: "/dashboard", icon: Gauge, label: copy.nav.dashboard },
    { href: "/products", icon: Search, label: copy.nav.products },
    { href: "/methodology", icon: Info, label: copy.nav.methodology }
  ];

  return (
    <nav className="flex items-center gap-1 rounded-lg border border-border bg-card p-1 text-sm shadow-sm" aria-label="Public navigation">
      {navItems.map((item) => {
        const active = pathname === item.href || (item.href === "/dashboard" && pathname === "/");
        const href = buildScopedPublicHrefFromSearchParams(item.href, searchParams);
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={href}
            className={cn(
              "inline-flex h-8 items-center gap-2 rounded-md px-3 font-medium transition-colors",
              active ? "bg-secondary text-secondary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <Icon className="size-4" aria-hidden="true" />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
