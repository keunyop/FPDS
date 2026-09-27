import { PublicFeedbackDialog } from '@/components/fpds/public/public-feedback-dialog';
import { guideCopy } from '@/lib/public-guides';

export function GuideEditorial({ locale }: { locale: string }) {
  const copy = guideCopy(locale);
  return <details className="mt-9 border-y border-border py-2" data-guide-editorial>
    <summary className="list-inside min-h-11 cursor-pointer py-3 text-sm font-medium underline-offset-4 hover:underline">{copy.editorial}</summary>
    <div className="grid max-w-3xl gap-3 pb-4 text-sm leading-6 text-muted-foreground">
      <p>{copy.publisher}</p>
      <p>{copy.method}</p>
      <p>{copy.language}</p>
      <p>{copy.corrections}</p>
      <div><PublicFeedbackDialog countryCode="CA" locale={locale} mode="site_feedback" /></div>
    </div>
  </details>;
}
