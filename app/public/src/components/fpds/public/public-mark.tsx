import { cn } from "@/lib/utils";

export function PublicMark({ className = "" }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "relative grid size-9 shrink-0 place-items-center overflow-hidden rounded-[0.7rem] bg-foreground text-background shadow-[0_8px_24px_rgba(28,39,35,0.14)]",
        className
      )}
    >
      <span className="grid h-4 w-4 grid-cols-3 items-end gap-[2px]">
        <span className="h-2 rounded-[1px] bg-current opacity-55" />
        <span className="h-4 rounded-[1px] bg-current" />
        <span className="h-3 rounded-[1px] bg-current opacity-75" />
      </span>
      <span className="absolute right-1.5 top-1.5 size-1.5 rounded-full bg-maple" />
    </span>
  );
}
