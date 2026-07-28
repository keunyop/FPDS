export default function PublicLoading() {
  return (
    <main className="mx-auto w-full max-w-7xl animate-pulse px-4 py-6 md:px-6 md:py-9" aria-busy="true" aria-label="Loading public financial product data">
      <div className="border-y border-foreground/10 py-10">
        <div className="h-3 w-56 bg-muted" />
        <div className="mt-6 h-16 max-w-3xl bg-muted md:h-24" />
        <div className="mt-5 h-5 max-w-2xl bg-muted" />
        <div className="mt-7 flex gap-3">
          <div className="h-12 w-28 rounded-full bg-muted" />
          <div className="h-12 w-28 rounded-full bg-muted" />
        </div>
      </div>
      <div className="mt-8 grid gap-5 md:grid-cols-2">
        <div className="h-40 bg-muted/70" />
        <div className="h-40 bg-muted/70" />
      </div>
      <span className="sr-only">Loading</span>
    </main>
  );
}
