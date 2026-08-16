import { cn } from "@/lib/utils";

export function PublicMark({ className = "" }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "grid size-10 shrink-0 place-items-center text-primary",
        className
      )}
    >
      <svg className="h-7 w-9" viewBox="0 0 32 24" fill="none">
        <circle cx="10" cy="12" r="7" stroke="currentColor" strokeWidth="2.5" />
        <circle cx="22" cy="12" r="7" stroke="currentColor" strokeWidth="2.5" />
        <circle cx="10" cy="12" r="2" fill="currentColor" />
        <circle cx="22" cy="12" r="2" fill="currentColor" />
      </svg>
    </span>
  );
}

export function PublicWordmark({
  className = "",
  eyeClassName = "text-primary"
}: {
  className?: string;
  eyeClassName?: string;
}) {
  return (
    <span aria-label="Bankoom" className={cn("inline-flex items-baseline whitespace-nowrap", className)}>
      <span aria-hidden="true">
        Bank<span className={eyeClassName}>oo</span>m
      </span>
    </span>
  );
}
