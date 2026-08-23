"use client";

import { LayoutGrid, List } from "lucide-react";
import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";

import type { CatalogViewMode } from "@/lib/public-query";
import { cn } from "@/lib/utils";

export function ResponsiveCatalogViewToggle({
  gridHref,
  gridLabel,
  groupLabel,
  listHref,
  listLabel,
  viewMode
}: {
  gridHref: string;
  gridLabel: string;
  groupLabel: string;
  listHref: string;
  listLabel: string;
  viewMode: CatalogViewMode;
}) {
  const [resolvedView, setResolvedView] = useState<"grid" | "list">(
    viewMode === "list" ? "list" : "grid"
  );

  useEffect(() => {
    if (viewMode !== "auto") {
      setResolvedView(viewMode);
      return;
    }

    const media = window.matchMedia("(max-width: 767px)");
    const update = () => setResolvedView(media.matches ? "list" : "grid");
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, [viewMode]);

  return (
    <div
      className="flex shrink-0 items-center rounded-lg border border-border bg-card/60 p-0.5"
      role="group"
      aria-label={groupLabel}
    >
      <ViewLink active={resolvedView === "grid"} href={gridHref} label={gridLabel}>
        <LayoutGrid className="size-4" aria-hidden="true" />
      </ViewLink>
      <ViewLink active={resolvedView === "list"} href={listHref} label={listLabel}>
        <List className="size-4" aria-hidden="true" />
      </ViewLink>
    </div>
  );
}

function ViewLink({
  active,
  children,
  href,
  label
}: {
  active: boolean;
  children: ReactNode;
  href: string;
  label: string;
}) {
  return (
    <Link
      aria-current={active ? "page" : undefined}
      aria-label={label}
      className={cn(
        "inline-flex size-10 shrink-0 items-center justify-center rounded-md transition-colors",
        active
          ? "bg-foreground text-background"
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
      href={href}
      title={label}
    >
      {children}
    </Link>
  );
}
