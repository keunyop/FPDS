const LOCAL_BANK_LOGO_ASSETS: Record<string, string> = {
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
