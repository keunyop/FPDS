"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

import { getPublicMessages, normalizePublicLocale } from "@/lib/public-locale";
import { buildScopedPublicHrefFromSearchParams, type PublicRoutePath } from "@/lib/public-query";
import { cn } from "@/lib/utils";

export function PublicNav() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const locale = normalizePublicLocale(searchParams.get("locale") ?? "");
  const copy = getPublicMessages(locale);
  const navItems: Array<{ href: PublicRoutePath; label: string }> = [
    { href: "/products", label: copy.nav.products },
    { href: "/dashboard", label: copy.nav.dashboard }
  ];

  return (
    <nav className="flex items-center gap-2 rounded-full border border-border/80 bg-card/90 p-1 text-sm shadow-sm">
      {navItems.map((item) => {
        const active = pathname === item.href;
        const href = buildScopedPublicHrefFromSearchParams(item.href, searchParams);

        return (
          <Link
            key={item.href}
            href={href}
            className={cn(
              "rounded-full px-4 py-2 font-medium transition-colors",
              active ? "bg-secondary text-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
