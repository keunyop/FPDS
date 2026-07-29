import { Activity, type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

type AdminStatStripTone = "success" | "info" | "warning" | "neutral";

type AdminStatStripItem = {
  label: string;
  value: string;
  note: string;
  tone: AdminStatStripTone;
  icon?: LucideIcon;
};

interface AdminStatStripProps {
  title?: string;
  description?: string;
  items: AdminStatStripItem[];
  className?: string;
  framed?: boolean;
}

const toneClassMap = {
  success: "text-success",
  info: "text-info",
  warning: "text-warning",
  neutral: "text-foreground"
} satisfies Record<AdminStatStripTone, string>;

const AdminStatStrip = ({
  title,
  description,
  items,
  className,
  framed = true
}: AdminStatStripProps) => {
  return (
    <section className={cn(framed ? "rounded-lg border border-border/80 bg-background p-4" : "min-w-0", className)}>
      {title || description ? (
        <div
          className={cn(
            "flex flex-col gap-2 md:flex-row md:items-end md:justify-between",
            framed ? "border-b border-border/80 pb-4" : "mb-3"
          )}
        >
          <div className="max-w-3xl">
            {title ? <h2 className="text-lg font-semibold tracking-tight text-foreground">{title}</h2> : null}
            {description ? <p className="mt-1 text-sm leading-6 text-muted-foreground">{description}</p> : null}
          </div>
        </div>
      ) : null}

      <div
        className={cn(
          "grid min-w-0 overflow-hidden rounded-lg border border-border bg-card md:grid-cols-2 xl:grid-cols-4",
          framed ? "mt-4" : "",
        )}
      >
        {items.map((item) => {
          const Icon = item.icon ?? Activity;

          return (
            <article
              className="min-w-0 border-b border-border px-4 py-3.5 last:border-b-0 md:border-r md:even:border-r-0 xl:border-b-0 xl:even:border-r xl:last:border-r-0"
              key={item.label}
            >
              <div className="flex min-w-0 items-center justify-between gap-3">
                <p className="min-w-0 text-xs font-semibold text-muted-foreground">{item.label}</p>
                <Icon className={cn("h-4 w-4", toneClassMap[item.tone])} aria-hidden="true" />
              </div>
              <p className="mt-2 break-words font-mono text-xl font-semibold tracking-[-0.02em] text-foreground">{item.value}</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{item.note}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
};

export { AdminStatStrip };
