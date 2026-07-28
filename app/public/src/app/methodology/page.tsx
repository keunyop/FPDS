import type { Metadata } from "next";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { getPublicDesignCopy, getPublicMessages, normalizePublicLocale } from "@/lib/public-locale";
import { buildPublicHref, parseDashboardPageFilters } from "@/lib/public-query";

type MethodologyPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export async function generateMetadata({ searchParams }: MethodologyPageProps): Promise<Metadata> {
  const resolvedSearchParams = (await searchParams) ?? {};
  const locale = normalizePublicLocale(typeof resolvedSearchParams.locale === "string" ? resolvedSearchParams.locale : "");
  const copy = getPublicMessages(locale);

  return {
    title: copy.methodology.pageTitle,
    description: copy.methodology.pageDescription
  };
}

export default async function MethodologyPage({ searchParams }: MethodologyPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const filters = parseDashboardPageFilters(resolvedSearchParams);
  const copy = getPublicMessages(filters.locale);
  const designCopy = getPublicDesignCopy(filters.locale);

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-7 md:px-6 md:py-10">
      <div className="flex flex-col gap-10">
        <section className="grid gap-7 border-y border-foreground/15 py-8 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end lg:py-12">
          <div>
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-verification">{copy.nav.methodology}</p>
            <h1 className="text-balance mt-4 font-display text-5xl font-semibold leading-[0.95] tracking-[-0.055em] text-foreground md:text-7xl">{copy.methodology.title}</h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">{designCopy.methodologyIntro}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button asChild className="rounded-full">
              <Link href={buildPublicHref("/products", filters)}>{copy.nav.products}</Link>
            </Button>
            <Button asChild className="rounded-full" variant="outline">
              <Link href={buildPublicHref("/loans", filters)}>{copy.nav.loan}</Link>
            </Button>
            <Button asChild className="rounded-full" variant="ghost">
              <Link href={buildPublicHref("/dashboard", filters)}>{copy.nav.dashboard}</Link>
            </Button>
          </div>
        </section>

        <section aria-labelledby="record-path-title">
          <div className="grid gap-8 lg:grid-cols-[17rem_minmax(0,1fr)]">
            <div>
              <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">{designCopy.verified}</p>
              <h2 id="record-path-title" className="mt-2 text-2xl font-semibold tracking-[-0.03em]">{designCopy.recordPath}</h2>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">{designCopy.recordPathBody}</p>
            </div>
            <ol className="grid border-y border-foreground/15 md:grid-cols-2">
              {designCopy.methodologySteps.map((step, index) => (
                <li className={`min-h-44 border-border p-5 ${index % 2 === 0 ? "md:border-r" : ""} ${index < 2 ? "border-b" : ""}`} key={step.label}>
                  <span className="font-mono text-[10px] font-semibold text-maple">{step.label}</span>
                  <h3 className="mt-6 text-lg font-semibold tracking-[-0.02em]">{step.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{step.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section aria-labelledby="method-rules-title">
          <div className="border-b border-foreground/15 pb-4">
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">{designCopy.evidenceBoundary}</p>
            <h2 id="method-rules-title" className="mt-2 text-2xl font-semibold tracking-[-0.03em]">{copy.methodology.description}</h2>
          </div>
          <div className="grid md:grid-cols-2">
            {copy.methodology.sections.map((section, index) => (
              <article className={`border-b border-border py-6 ${index % 2 === 0 ? "md:pr-8" : "md:border-l md:pl-8"}`} key={section.title}>
                <p className="font-mono text-[10px] text-muted-foreground">0{index + 1}</p>
                <h3 className="mt-2 text-lg font-semibold">{section.title}</h3>
                <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">{section.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="flex flex-col gap-4 border-y border-maple/30 bg-accent/35 px-5 py-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold">{designCopy.compareBoundary}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{designCopy.compareDifferences}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button asChild className="rounded-full">
              <Link href={buildPublicHref("/products", filters)}>{copy.nav.products}</Link>
            </Button>
            <Button asChild className="rounded-full" variant="outline">
              <Link href={buildPublicHref("/loans", filters)}>{copy.nav.loan}</Link>
            </Button>
          </div>
        </section>
      </div>
    </main>
  );
}
