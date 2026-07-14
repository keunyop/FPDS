"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";

const BANK_LOGO_ASSETS: Record<string, { src: string }> = {
  ALTERNA: { src: "https://www.alternabank.ca/media/vxmi4hy5/alterna-bank.svg" },
  B2B: { src: "https://b2bbank.com/sn_uploads/grid/B2B-Bank_EN_2-web_1.svg" },
  BMO: { src: "/bank-logos/bmo.svg" },
  BRIDGEWATER: { src: "https://bridgewaterbank.ca/wp-content/uploads/2018/10/logo-black.svg" },
  CTBANK: { src: "https://media.ctfs.com/navigation/NAV_CTB_EN_Logo.svg" },
  CIBC: { src: "/bank-logos/cibc.svg" },
  EQBANK: { src: "https://images.ctfassets.net/ymwa45h4u77x/4oX5L57Tc4Xrv2iKG72VPN/481fb11b7a59027ebd4316579313fe3d/eqbank-logo.svg" },
  FAIRSTONE: { src: "https://www.fairstone.ca/content/dam/fs/logos/FairstoneLogo_EN.svg" },
  FNBC: { src: "https://www.fnbc.ca/assets/img/logos/FNBC_Logo_Full.png" },
  HAVENTREE: { src: "https://images.ctfassets.net/hw93zeuesbqv/2KM8tvJXRifNUcZUOJRa4c/f69db98d25b1601edbe96c820f7fbdcd/HT_Symbol__2_.png" },
  HOMEEQUITY: { src: "https://www.homeequitybank.ca/favicon.ico" },
  LAURENTIAN: { src: "https://images.ctfassets.net/b5xlbty9p8dy/1N5u3c9NZEFH5cFWZjGuYO/b8ede62d4fe64efdcfcc279667cc450e/Logo.svg" },
  MANULIFE: { src: "https://www.manulifebank.ca/content/dam/manulife-bank/en_ca/logo/Manulife_Bank_ni_logo_black.svg" },
  MOTUS: { src: "https://www.motusbank.ca/favicon.ico" },
  NATIONAL: { src: "https://www.nbc.ca/content/dam/bnc/commun/logo/logo-nbc-155x50.svg" },
  OAKEN: { src: "https://www.oaken.com/media/5lejbr01/oaken-bil-logo_rgb.png" },
  PCFIN: { src: "https://www.pcfinancial.ca/favicon.ico" },
  PEOPLES: { src: "https://www.peoplesbank.ca/favicon.ico" },
  RBC: { src: "/bank-logos/rbc.svg" },
  RFA: { src: "https://www.rfa.ca/logo.svg" },
  ROGERSBANK: { src: "https://selfserve.rogersbank.com/icons/rb_logo.png" },
  SCOTIA: { src: "/bank-logos/scotia.svg" },
  SIMPLII: { src: "https://www.simplii.com/content/dam/simplii-assets/global/logos/simplii-logos/horizontal/simplii-financial-logotype-full-pink.svg" },
  TANGERINE: { src: "https://www.tangerine.ca/content/experience-fragments/tangerine/ca/en/header/master/_jcr_content/root/container_1282085336/container_745983912/container_1531797112_822927059/image.coreimg.svg/1777585120988/logo-tangerine-orange.svg" },
  TD: { src: "/bank-logos/td.png" },
  VANCITY: { src: "https://www.vancity.com/favicon.ico" },
  VERSABANK: { src: "https://www.versabank.com/wp-content/uploads/2024/10/logo-versabank-en.png" },
  WEALTHONE: { src: "https://www.wealthonebankofcanada.com/img/logos/wealth-one-header-logo.svg" },
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
  const [failed, setFailed] = useState(false);
  const showAsset = Boolean(asset && !failed);

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
      {showAsset ? (
        <img
          alt=""
          className="max-h-full max-w-full object-contain"
          decoding="async"
          loading="lazy"
          onError={() => setFailed(true)}
          src={asset.src}
        />
      ) : (
        <span aria-hidden="true" className={cn("font-semibold tracking-tight text-foreground", isSmall ? "text-[10px]" : "text-xs")}>
          {normalizedCode.slice(0, 4) || bankName.slice(0, 2).toUpperCase()}
        </span>
      )}
    </span>
  );
}
