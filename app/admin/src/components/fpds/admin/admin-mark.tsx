import { cn } from "@/lib/utils";

type AdminMarkProps = {
  className?: string;
};

export function AdminMark({ className }: AdminMarkProps) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "relative grid h-8 w-8 shrink-0 grid-rows-3 gap-1 border border-sidebar-border bg-sidebar-accent p-1.5",
        className,
      )}
    >
      <span className="h-px self-center bg-sidebar-foreground/55" />
      <span className="h-px self-center bg-sidebar-primary" />
      <span className="h-px self-center bg-sidebar-foreground/55" />
      <span className="absolute -right-1 top-1 h-2 w-2 border border-sidebar bg-sidebar-primary" />
    </span>
  );
}
