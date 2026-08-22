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
      <svg className="size-8" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="8.5" stroke="currentColor" strokeWidth="2.1" />
        <path d="M3.5 12H20.5" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" />
        <path
          d="M12 3.5C9.78 5.76 8.55 8.67 8.55 12C8.55 15.33 9.78 18.24 12 20.5C14.22 18.24 15.45 15.33 15.45 12C15.45 8.67 14.22 5.76 12 3.5Z"
          stroke="currentColor"
          strokeWidth="2.1"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}

export function PublicWordmark({
  className = ""
}: {
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-baseline whitespace-nowrap", className)}>
      Bankompare
    </span>
  );
}
