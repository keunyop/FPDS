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
  description = "The live admin surface now starts from Shadcnblocks-based layout primitives and keeps FPDS workflow meaning on top.",
  items,
  className
}: Stats5Props) => {
  return (
    <section className={cn("rounded-[1.75rem] border border-border/80 bg-card/90 p-6 shadow-sm", className)}>
      <div className="flex flex-col gap-3 border-b border-border/80 pb-6 md:flex-row md:items-end md:justify-between">
        <div className="max-w-3xl">
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Overview metrics</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{title}</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">{description}</p>
        </div>
        <div className="rounded-full border border-border/80 bg-muted/50 px-3 py-1 text-xs font-medium text-muted-foreground">
          Compact, route-oriented, evidence aware
        </div>
      </div>

      <div className="grid gap-4 pt-6 md:grid-cols-2 xl:grid-cols-4">
        {items.map((item) => {
          const Icon = toneIconMap[item.tone];

          return (
            <article className="rounded-2xl border border-border/80 bg-background px-4 py-5" key={item.label}>
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-muted-foreground">{item.label}</p>
                <div
                  className={cn(
                    "flex h-9 w-9 items-center justify-center rounded-2xl bg-muted/70",
                    toneClassMap[item.tone]
                  )}
                >
                  <Icon className="h-4 w-4" />
                </div>
              </div>
              <p className="mt-4 text-3xl font-semibold tracking-tight text-foreground">{item.value}</p>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.note}</p>
            </article>
          );
        })}
      </div>
    </section>
  );
};

export { Stats5 };
