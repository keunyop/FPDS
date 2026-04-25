import { Activity, ArrowRight, ShieldCheck, Sparkles } from "lucide-react";

import { cn } from "@/lib/utils";

type Stats5Tone = "success" | "info" | "warning" | "neutral";

type Stats5Item = {
  label: string;
  value: string;
  note: string;
  tone: Stats5Tone;
};

interface Stats5Props {
  title?: string;
  description?: string;
  items: Stats5Item[];
  className?: string;
}

const toneIconMap = {
  success: ShieldCheck,
  info: Sparkles,
  warning: ArrowRight,
  neutral: Activity
} satisfies Record<Stats5Tone, typeof Activity>;

const toneClassMap = {
  success: "text-success",
  info: "text-info",
  warning: "text-warning",
  neutral: "text-foreground"
} satisfies Record<Stats5Tone, string>;

const Stats5 = ({
  title = "Admin shell readiness",
  description,
  items,
  className
}: Stats5Props) => {
  return (
    <section className={cn("rounded-lg border border-border/80 bg-background p-4", className)}>
      <div className="flex flex-col gap-2 border-b border-border/80 pb-4 md:flex-row md:items-end md:justify-between">
        <div className="max-w-3xl">
          <h2 className="text-lg font-semibold tracking-tight text-foreground">{title}</h2>
          {description ? <p className="mt-1 text-sm leading-6 text-muted-foreground">{description}</p> : null}
        </div>
      </div>

      <div className="grid gap-3 pt-4 md:grid-cols-2 xl:grid-cols-4">
        {items.map((item) => {
          const Icon = toneIconMap[item.tone];

          return (
            <article className="rounded-lg border border-border/80 bg-card px-4 py-4" key={item.label}>
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-muted-foreground">{item.label}</p>
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-lg bg-muted/70",
                    toneClassMap[item.tone]
                  )}
                >
                  <Icon className="h-4 w-4" />
                </div>
              </div>
              <p className="mt-3 text-2xl font-semibold tracking-tight text-foreground">{item.value}</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{item.note}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
};

export { Stats5 };
