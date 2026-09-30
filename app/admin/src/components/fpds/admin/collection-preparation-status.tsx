import Link from "next/link";
import type { CollectionPreparation } from "@/lib/admin-api";
import { collectionPreparationMessage } from "@/lib/admin-collection-feedback";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

export function CollectionPreparationStatus({ locale, state }: { locale: AdminLocale; state?: CollectionPreparation }) {
  const message = collectionPreparationMessage(locale, state);
  if (!message) return null;
  return (
    <div className="mt-2 min-w-0 space-y-1 text-xs leading-5 text-muted-foreground">
      <p role="status" aria-live="polite">{message}</p>
      {state?.run_id ? (
        <Link className="font-medium text-primary underline underline-offset-4" href={buildAdminHref(`/admin/runs/${encodeURIComponent(state.run_id)}`, new URLSearchParams(), locale)}>
          {locale === "ko" ? "실행 보기" : locale === "ja" ? "実行を見る" : "View run"}
        </Link>
      ) : null}
    </div>
  );
}
