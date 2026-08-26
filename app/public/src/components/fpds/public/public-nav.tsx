"use client";

import { CreditCard, House, Landmark, Search } from "lucide-react";
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
    { href: "/", icon: House, label: copy.nav.dashboard },
    { href: "/products", icon: Search, label: copy.nav.products },
    { href: "/cards", icon: CreditCard, label: copy.nav.card },
    { href: "/loans", icon: Landmark, label: copy.nav.loan }
  ];

  return (
    <nav className="flex max-w-full items-center gap-0.5 text-sm" aria-label={copy.nav.primaryLabel}>
      {navItems.map((item) => {
        const active = pathname === item.href;
        const Icon = item.icon;

        const href = buildScopedPublicHrefFromSearchParams(item.href, searchParams);

        return (
          <Link
            key={item.href}
            href={href}
            className={cn(
              "inline-flex min-h-11 min-w-11 shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-full px-2.5 font-medium transition-colors first:hidden sm:first:inline-flex lg:px-3.5",
              active ? "bg-foreground text-background" : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <Icon className="size-4" aria-hidden="true" />
            <span className="hidden lg:inline">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
