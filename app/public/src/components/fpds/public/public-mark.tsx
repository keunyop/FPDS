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
        <path
          d="M4.5 7.5H19M15.5 4L19 7.5L15.5 11"
          stroke="currentColor"
          strokeWidth="2.25"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M19.5 16.5H5M8.5 13L5 16.5L8.5 20"
          stroke="currentColor"
          strokeWidth="2.25"
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
      SwitchaBank
    </span>
  );
}
