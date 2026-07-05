import { cn } from "@/lib/utils";

const BANK_LOGO_ASSETS: Record<string, { src: string }> = {
  ALTERNA: { src: "https://www.alternabank.ca/favicon.ico" },
  B2B: { src: "https://b2bbank.com/favicon.ico" },
  BMO: { src: "/bank-logos/bmo.svg" },
  BRIDGEWATER: { src: "https://www.bridgewaterbank.ca/favicon.ico" },
  CTBANK: { src: "https://www.ctfs.com/favicon.ico" },
  CIBC: { src: "/bank-logos/cibc.svg" },
  EQBANK: { src: "https://www.eqbank.ca/favicon.ico" },
  FAIRSTONE: { src: "https://www.fairstone.ca/favicon.ico" },
  FNBC: { src: "https://www.fnbc.ca/favicon.ico" },
  HAVENTREE: { src: "https://www.haventreebank.com/favicon.ico" },
  HOMEEQUITY: { src: "https://www.homeequitybank.ca/favicon.ico" },
  LAURENTIAN: { src: "https://www.laurentianbank.ca/favicon.ico" },
  MANULIFE: { src: "https://www.manulifebank.ca/favicon.ico" },
  MOTUS: { src: "https://www.motusbank.ca/favicon.ico" },
  NATIONAL: { src: "https://www.nbc.ca/favicon.ico" },
  OAKEN: { src: "https://www.oaken.com/favicon.ico" },
  PCFIN: { src: "https://www.pcfinancial.ca/favicon.ico" },
  PEOPLES: { src: "https://www.peoplesbank.ca/favicon.ico" },
  RBC: { src: "/bank-logos/rbc.svg" },
  RFA: { src: "https://www.rfa.ca/favicon.ico" },
  ROGERSBANK: { src: "https://www.rogersbank.com/favicon.ico" },
  SCOTIA: { src: "/bank-logos/scotia.svg" },
  SIMPLII: { src: "https://www.simplii.com/favicon.ico" },
  TANGERINE: { src: "https://www.tangerine.ca/favicon.ico" },
  TD: { src: "/bank-logos/td.png" },
  VANCITY: { src: "https://www.vancity.com/favicon.ico" },
  VERSABANK: { src: "https://www.versabank.com/favicon.ico" },
  WEALTHONE: { src: "https://www.wealthonebankofcanada.com/favicon.ico" },
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
        "inline-flex shrink-0 items-center justify-center",
        isSmall ? "h-9 w-16" : "h-12 w-24",
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
        <span className={cn("rounded-md border border-border/70 bg-white px-2 py-1 font-semibold text-foreground shadow-sm", isSmall ? "text-[10px]" : "text-xs")}>
          {normalizedCode.slice(0, 4) || bankName.slice(0, 2).toUpperCase()}
        </span>
      )}
    </span>
  );
}
