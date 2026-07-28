"use client";

import { ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

type AdminPageHeaderProps = {
  actions?: ReactNode;
  badges?: ReactNode;
  description?: string;
  path: readonly string[];
  title: string;
};

export function AdminPageHeader({ actions, badges, description, path, title }: AdminPageHeaderProps) {
  return (
    <header className="grid gap-3 border-b border-border pb-5">
      <nav aria-label="Breadcrumb" className="flex min-h-6 flex-wrap items-center gap-1.5 text-xs font-medium text-muted-foreground">
        {path.map((segment, index) => (
          <span className="inline-flex items-center gap-1.5" key={`${segment}-${index}`}>
            {index > 0 ? <ChevronRight className="h-4 w-4" aria-hidden="true" /> : null}
            <span className={index === path.length - 1 ? "font-medium text-foreground" : undefined}>{segment}</span>
          </span>
        ))}
      </nav>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold tracking-[-0.02em] text-foreground md:text-3xl">{title}</h1>
          {description ? <p className="mt-1.5 max-w-3xl text-sm leading-5 text-muted-foreground">{description}</p> : null}
        </div>
        {badges || actions ? (
          <div className="flex shrink-0 flex-wrap items-center gap-2">
            {badges}
            {actions}
          </div>
        ) : null}
      </div>
    </header>
  );
}
