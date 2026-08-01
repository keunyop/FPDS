"use client";

import { useEffect, useState } from "react";

type BankLogoMarkProps = {
  alt?: string | null;
  bankCode: string;
  bankName: string;
  logoUrl?: string | null;
};

export function BankLogoMark({
  alt,
  bankCode,
  bankName,
  logoUrl,
}: BankLogoMarkProps) {
  const normalizedLogoUrl = logoUrl?.trim() ?? "";
  const [failed, setFailed] = useState(false);
  const showLogo = Boolean(normalizedLogoUrl && !failed);

  useEffect(() => {
    setFailed(false);
  }, [normalizedLogoUrl]);

  return (
    <span
      className="flex h-10 w-14 shrink-0 items-center justify-center"
      data-bank-logo
    >
      {showLogo ? (
        <img
          alt={alt ?? `${bankName} logo`}
          className="block h-6 w-12 object-contain"
          decoding="async"
          height={24}
          loading="lazy"
          onError={() => setFailed(true)}
          src={normalizedLogoUrl}
          width={48}
        />
      ) : (
        <span className="text-[10px] font-semibold tracking-tight text-foreground">
          {bankCode.slice(0, 4)}
        </span>
      )}
    </span>
  );
}
