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
    <header className="grid gap-4">
      <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-1.5 text-sm text-muted-foreground">
        {path.map((segment, index) => (
          <span className="inline-flex items-center gap-1.5" key={`${segment}-${index}`}>
            {index > 0 ? <ChevronRight className="h-4 w-4" aria-hidden="true" /> : null}
            <span className={index === path.length - 1 ? "font-medium text-foreground" : undefined}>{segment}</span>
          </span>
        ))}
      </nav>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0">
          <h1 className="text-3xl font-semibold tracking-tight text-foreground md:text-4xl">{title}</h1>
          {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{description}</p> : null}
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
