export default function AdminLoading() {
  return (
    <main aria-busy="true" aria-label="Loading FPDS Admin" className="min-h-svh bg-background">
      <div className="h-14 border-b border-sidebar-border bg-sidebar" />
      <div className="flex min-h-[calc(100svh-3.5rem)]">
        <aside className="hidden w-64 border-r border-sidebar-border bg-sidebar md:block" aria-hidden="true">
          <div className="grid gap-3 p-4">
            {Array.from({ length: 6 }, (_, index) => (
              <div className="h-9 animate-pulse bg-sidebar-accent" key={index} />
            ))}
          </div>
        </aside>
        <section className="mx-auto w-full max-w-7xl px-4 py-6 md:px-8">
          <div className="h-4 w-36 animate-pulse rounded-sm bg-muted" />
          <div className="mt-4 h-8 w-72 max-w-full animate-pulse rounded-sm bg-muted" />
          <div className="mt-8 grid overflow-hidden rounded-lg border border-border bg-card md:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }, (_, index) => (
              <div className="h-28 animate-pulse border-b border-border bg-muted/40 p-4 last:border-b-0 md:border-r xl:border-b-0" key={index} />
            ))}
          </div>
          <div className="mt-6 h-72 animate-pulse rounded-lg border border-border bg-card" />
        </section>
      </div>
    </main>
  );
}
