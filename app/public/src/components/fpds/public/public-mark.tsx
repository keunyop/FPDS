import { cn } from "@/lib/utils";

export function PublicMark({ className = "" }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "grid size-9 shrink-0 place-items-center text-primary",
        className
      )}
    >
      <svg className="h-6 w-8" viewBox="0 0 32 24" fill="none">
        <circle cx="10" cy="12" r="7" stroke="currentColor" strokeWidth="2.5" />
        <circle cx="22" cy="12" r="7" stroke="currentColor" strokeWidth="2.5" />
        <circle cx="8" cy="12" r="2" fill="currentColor" />
        <circle cx="24" cy="12" r="2" fill="currentColor" />
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
    <span aria-label="Bankoom" className={cn("inline-flex items-baseline", className)}>
      <span aria-hidden="true">
        Bank<span className={eyeClassName}>oo</span>m
      </span>
    </span>
  );
}
