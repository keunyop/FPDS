import { cn } from "@/lib/utils";
import { resolvePublicBankLogo } from "@/lib/public-bank-logo";

type BankLogoProps = {
  bankCode: string;
  bankName: string;
  className?: string;
  size?: "sm" | "md";
};

export function BankLogo({ bankCode, bankName, className, size = "md" }: BankLogoProps) {
  const { asset, fallbackCode } = resolvePublicBankLogo(bankCode, bankName);
  const isSmall = size === "sm";
  const width = isSmall ? 64 : 96;
  const height = isSmall ? 36 : 48;

  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center",
        isSmall ? "h-9 w-16" : "h-12 w-24",
        className
      )}
    >
      {asset ? (
        <img
          alt={`${bankName} logo`}
          className="max-h-full max-w-full object-contain"
          decoding="async"
          height={height}
          loading="lazy"
          src={asset}
          width={width}
        />
      ) : (
        <span
          aria-label={`${fallbackCode} — ${bankName} logo`}
          className={cn(
            "font-semibold tracking-tight text-foreground",
            isSmall ? "text-[10px]" : "text-xs"
          )}
          role="img"
        >
          {fallbackCode}
        </span>
      )}
    </span>
  );
}
