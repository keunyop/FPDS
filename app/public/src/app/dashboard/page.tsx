import Link from "next/link";

import { Button } from "@/components/ui/button";

type DashboardPlaceholderPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function DashboardPlaceholderPage({ searchParams }: DashboardPlaceholderPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const params = new URLSearchParams();

  for (const [key, value] of Object.entries(resolvedSearchParams)) {
    if (Array.isArray(value)) {
      for (const entry of value) {
        if (entry) {
          params.append(key, entry);
        }
      }
      continue;
    }
    if (value) {
      params.set(key, value);
    }
  }

  const backHref = params.toString() ? `/products?${params.toString()}` : "/products";

  return (
    <main className="mx-auto flex w-full max-w-5xl px-4 py-12 md:px-6 md:py-16">
      <section className="w-full rounded-[2rem] border border-border/80 bg-card/95 p-8 shadow-[0_24px_60px_rgba(15,23,42,0.08)] md:p-10">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-primary">WBS 5.10 Next</p>
        <h1 className="mt-4 max-w-2xl text-4xl font-semibold tracking-tight text-foreground">
          Insight Dashboard UI is the next public slice after the Product Grid.
        </h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-muted-foreground">
          The shared filter vocabulary is already preserved in the query string, but the actual KPI, ranking, and scatter
          surface belongs to `WBS 5.10` and the grid-to-dashboard state choreography belongs to `WBS 5.11`.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild>
            <Link href={backHref}>Return to Product Grid</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/products">Clear scope and browse products</Link>
          </Button>
        </div>
      </section>
    </main>
  );
}
