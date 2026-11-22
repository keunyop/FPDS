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
      className="flex size-10 shrink-0 items-center justify-center rounded-md border border-border bg-card"
      data-bank-logo
    >
      {showLogo ? (
        <img
          alt={alt ?? `${bankName} logo`}
          className="block h-6 w-8 object-contain"
          decoding="async"
          height={24}
          loading="lazy"
          onError={() => setFailed(true)}
          src={normalizedLogoUrl}
          width={48}
        />
      ) : (
        <span aria-hidden="true" className="font-mono text-[10px] font-semibold text-muted-foreground">
          {bankCode.slice(0, 4)}
        </span>
      )}
    </span>
  );
}
