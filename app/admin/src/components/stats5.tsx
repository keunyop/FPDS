import { Activity, type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

type Stats5Tone = "success" | "info" | "warning" | "neutral";

type Stats5Item = {
  label: string;
  value: string;
  note: string;
  tone: Stats5Tone;
  icon?: LucideIcon;
};

interface Stats5Props {
  title?: string;
  description?: string;
  items: Stats5Item[];
  className?: string;
  framed?: boolean;
}

const toneClassMap = {
  success: "text-success",
  info: "text-info",
  warning: "text-warning",
  neutral: "text-foreground"
} satisfies Record<Stats5Tone, string>;

const Stats5 = ({
  title,
  description,
  items,
  className,
  framed = true
}: Stats5Props) => {
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

      <div className={cn("grid min-w-0 gap-3 md:grid-cols-2 xl:grid-cols-4", framed ? "pt-4" : "")}>
        {items.map((item) => {
          const Icon = item.icon ?? Activity;

          return (
            <article className="min-w-0 rounded-lg border border-border/80 bg-card px-4 py-4" key={item.label}>
              <div className="flex min-w-0 items-center justify-between gap-3">
                <p className="min-w-0 text-sm font-medium text-muted-foreground">{item.label}</p>
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-lg bg-muted/70",
                    toneClassMap[item.tone]
                  )}
                >
                  <Icon className="h-4 w-4" />
                </div>
              </div>
              <p className="mt-3 break-words text-2xl font-semibold tracking-tight text-foreground">{item.value}</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{item.note}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
};

export { Stats5 };
