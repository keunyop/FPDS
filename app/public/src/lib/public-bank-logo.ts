const LOCAL_BANK_LOGO_ASSETS: Record<string, string> = {
  ALTERNA: "/bank-logos/alterna.svg",
  B2B: "/bank-logos/b2b.svg",
  EQBANK: "/bank-logos/eq-bank.svg",
  NATIONAL: "/bank-logos/national-bank.svg",
  OAKEN: "/bank-logos/oaken.png",
  SIMPLII: "/bank-logos/simplii.svg",
  TANGERINE: "/bank-logos/tangerine.svg",
  WEALTHONE: "/bank-logos/wealth-one.png",
  SCU: "/bank-logos/servus.png",
  CCS: "/bank-logos/coast-capital.ico",
  DESJARDINS: "/bank-logos/desjardins.ico",
  CONA: "/bank-logos/capital-one.svg",
  CN: "/bank-logos/citi.png",
  GSBU: "/bank-logos/marcus.svg",
  HU: "/bank-logos/hsbc.svg",
  JCBN: "/bank-logos/chase.svg",
  PBNA: "/bank-logos/pnc.png",
  TB: "/bank-logos/truist.svg",
  WFBN: "/bank-logos/wells-fargo.png",
  BB: "/bank-logos/bmo.svg",
  TBNA: "/bank-logos/td.png",
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
