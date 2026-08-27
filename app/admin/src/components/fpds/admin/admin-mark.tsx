import { cn } from "@/lib/utils";

type AdminMarkProps = {
  className?: string;
};

export function AdminMark({ className }: AdminMarkProps) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "grid h-8 w-8 shrink-0 place-items-center rounded-[0.55rem] border border-sidebar-primary/25 bg-sidebar-primary text-sidebar-primary-foreground shadow-sm",
        className,
      )}
    >
      <svg className="size-5" fill="none" viewBox="0 0 24 24">
        <path
          d="M6.75 5.75h10.5M6.75 5.75v12.5M6.75 11.5h7.5"
          stroke="currentColor"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.75"
        />
        <circle cx="17.25" cy="17.75" fill="currentColor" r="1.75" />
      </svg>
    </span>
  );
}
