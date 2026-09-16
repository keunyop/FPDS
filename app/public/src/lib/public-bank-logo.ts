const LOCAL_BANK_LOGO_ASSETS: Record<string, string> = {
  AB: "/bank-logos/ally.png",
  RB: "/bank-logos/regions.ico",
  FCB: "/bank-logos/first-citizens.png",
  KEYBANK: "/bank-logos/keybank.ico",
  BOAN: "/bank-logos/bank-of-america.ico",
  USBN: "/bank-logos/us-bank.ico",
  VANCITY: "/bank-logos/vancity.svg",
  MANULIFE: "/bank-logos/manulife.png",
  LAURENTIAN: "/bank-logos/laurentian.svg",
  BMO: "/bank-logos/bmo.svg",
  CIBC: "/bank-logos/cibc.svg",
  RBC: "/bank-logos/rbc.svg",
  SCOTIA: "/bank-logos/scotia.svg",
  TD: "/bank-logos/td.png"
};

export function resolvePublicBankLogo(bankCode: string, bankName: string) {
  const normalizedCode = bankCode.trim().toUpperCase();
  const fallbackCode =
    normalizedCode.slice(0, 4) || bankName.trim().slice(0, 2).toUpperCase();

  return {
    asset: LOCAL_BANK_LOGO_ASSETS[normalizedCode] ?? null,
    fallbackCode,
    normalizedCode
  };
}
