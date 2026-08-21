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
        <circle cx="8.75" cy="12" r="6.5" stroke="currentColor" strokeWidth="2.5" />
        <circle cx="23.25" cy="12" r="6.5" stroke="currentColor" strokeWidth="2.5" />
        <circle cx="8.75" cy="12" r="2" fill="currentColor" />
        <circle cx="23.25" cy="12" r="2" fill="currentColor" />
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
    <span aria-label="Bankoompare" className={cn("inline-flex items-baseline whitespace-nowrap", className)}>
      <span aria-hidden="true">
        Bank<span className={eyeClassName}>oo</span>mpare
      </span>
    </span>
  );
}
