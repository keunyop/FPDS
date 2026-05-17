"use client";

import { Home, Landmark, Search } from "lucide-react";
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
  const navItems: Array<{ disabled?: boolean; href?: PublicRoutePath; icon: ComponentType<{ className?: string }>; label: string }> = [
    { href: "/dashboard", icon: Home, label: copy.nav.dashboard },
    { href: "/products", icon: Search, label: copy.nav.products },
    { disabled: true, icon: Landmark, label: copy.nav.loan }
  ];

  return (
    <nav className="flex items-center gap-1 rounded-lg border border-border bg-card p-1 text-sm shadow-sm" aria-label="Public navigation">
      {navItems.map((item) => {
        const active = item.href ? pathname === item.href || (item.href === "/dashboard" && pathname === "/") : false;
        const Icon = item.icon;

        if (item.disabled || !item.href) {
          return (
            <span
              key={item.label}
              aria-disabled="true"
              className="inline-flex h-8 cursor-not-allowed items-center gap-2 rounded-md px-3 font-medium text-muted-foreground/55"
            >
              <Icon className="size-4" aria-hidden="true" />
              <span>{item.label}</span>
            </span>
          );
        }

        const href = buildScopedPublicHrefFromSearchParams(item.href, searchParams);

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
