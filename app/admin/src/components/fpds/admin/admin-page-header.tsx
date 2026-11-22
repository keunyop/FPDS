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
  const parents = path.at(-1) === title ? path.slice(0, -1) : path;
  return (
    <header className="grid gap-2 pb-1">
      {parents.length > 0 && <p className="flex flex-wrap items-center gap-1.5 text-xs font-medium text-muted-foreground">
        {parents.map((segment, index) => (
          <span className="inline-flex items-center gap-1.5" key={`${segment}-${index}`}>
            {index > 0 ? <ChevronRight className="h-4 w-4" aria-hidden="true" /> : null}
            {segment}
          </span>
        ))}
      </p>}

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground md:text-[2rem] md:leading-10">{title}</h1>
          {description ? <p className="mt-1.5 max-w-3xl text-sm leading-5 text-muted-foreground">{description}</p> : null}
        </div>
        {badges || actions ? (
          <div className="flex min-w-0 max-w-full flex-wrap items-center gap-2">
            {badges}
            {actions}
          </div>
        ) : null}
      </div>
    </header>
  );
}
