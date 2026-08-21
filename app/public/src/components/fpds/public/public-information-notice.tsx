import { Info } from "lucide-react";

import { getPublicInformationNotice } from "@/lib/public-locale";

export function PublicInformationNotice({ locale }: { locale: string }) {
  const copy = getPublicInformationNotice(locale);

  return (
    <aside className="border-y border-foreground/20 bg-card/55 px-4 py-5 md:px-6 md:py-6" aria-labelledby="public-information-notice-title">
      <div className="grid gap-4 md:grid-cols-[auto_minmax(0,1fr)] md:gap-5">
        <span className="grid size-9 place-items-center rounded-full bg-primary/10 text-primary" aria-hidden="true">
          <Info className="size-4" />
        </span>
        <div className="min-w-0">
          <h2 id="public-information-notice-title" className="text-base font-semibold text-foreground">{copy.title}</h2>
          <div className="mt-2 grid gap-1.5 text-xs leading-5 text-muted-foreground md:text-sm md:leading-6">
            {copy.paragraphs.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
          </div>
        </div>
      </div>
    </aside>
  );
}
