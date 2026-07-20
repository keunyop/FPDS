import type { Metadata } from "next";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getPublicMessages, normalizePublicLocale } from "@/lib/public-locale";
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

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-8 md:px-6">
      <div className="flex flex-col gap-6">
        <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
          <div>
            <p className="text-sm font-medium text-primary">{copy.nav.methodology}</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-foreground md:text-4xl">{copy.methodology.title}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">{copy.methodology.description}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button asChild>
              <Link href={buildPublicHref("/products", filters)}>{copy.nav.products}</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href={buildPublicHref("/loans", filters)}>{copy.nav.loan}</Link>
            </Button>
            <Button asChild variant="ghost">
              <Link href={buildPublicHref("/dashboard", filters)}>{copy.nav.dashboard}</Link>
            </Button>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          {copy.methodology.sections.map((section) => (
            <Card key={section.title}>
              <CardHeader>
                <CardTitle>{section.title}</CardTitle>
                <CardDescription>{section.body}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </section>
      </div>
    </main>
  );
}
