import type { PublicProduct } from "@/lib/public-api";
import { getVerificationCopy, verificationDate, verificationStatus } from "@/lib/public-verification";
import { cn } from "@/lib/utils";

export function ProductVerification({ product, locale, detailed = false }: {
  product: PublicProduct; locale: string; detailed?: boolean;
}) {
  const copy = getVerificationCopy(locale);
  const status = verificationStatus(product.verification);
  const date = product.verification ? product.verification.last_verified_at : product.last_verified_at;
  return (
    <div className={cn("mt-2 min-w-0 text-xs leading-5 [overflow-wrap:anywhere]", status === "within_window" ? "text-muted-foreground" : "text-warning")} data-product-verification={status}>
      <p>{copy.checked}: <span className="tabular-nums">{verificationDate(date, copy.unknownDate)}</span> (UTC)</p>
      <p className="font-medium">{copy[status]}</p>
      {detailed ? <>
        {product.verification?.review_due_at ? <p>{copy.due}: {verificationDate(product.verification.review_due_at, copy.unknownDate)} (UTC)</p> : null}
        {product.verification?.expires_at ? <p>{copy.expiry}: {verificationDate(product.verification.expires_at, copy.unknownDate)} (UTC)</p> : null}
        <p className="mt-2 text-muted-foreground">{copy.notice}</p>
      </> : null}
    </div>
  );
}
