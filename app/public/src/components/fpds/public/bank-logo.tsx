import { cn } from "@/lib/utils";

const BANK_LOGO_ASSETS: Record<string, { src: string }> = {
  BMO: { src: "/bank-logos/bmo.svg" },
  CIBC: { src: "/bank-logos/cibc.svg" },
  RBC: { src: "/bank-logos/rbc.svg" },
  SCOTIA: { src: "/bank-logos/scotia.svg" },
  TD: { src: "/bank-logos/td.png" },
};

type BankLogoProps = {
  bankCode: string;
  bankName: string;
  className?: string;
  size?: "sm" | "md";
};

export function BankLogo({ bankCode, bankName, className, size = "md" }: BankLogoProps) {
  const normalizedCode = bankCode.trim().toUpperCase();
  const asset = BANK_LOGO_ASSETS[normalizedCode];
  const isSmall = size === "sm";

  return (
    <span
      aria-label={`${bankName} logo`}
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-md border border-border/60 bg-white shadow-sm",
        isSmall ? "h-8 w-16 p-1.5" : "h-11 w-24 p-2",
        className
      )}
      title={bankName}
    >
      {asset ? (
        <img
          alt=""
          className="max-h-full max-w-full object-contain"
          decoding="async"
          loading="lazy"
          src={asset.src}
        />
      ) : (
        <span className={cn("font-semibold text-foreground", isSmall ? "text-[10px]" : "text-xs")}>
          {normalizedCode.slice(0, 4) || bankName.slice(0, 2).toUpperCase()}
        </span>
      )}
    </span>
  );
}
