type AdminApiUnavailableProps = {
  title: string;
};

export function AdminApiUnavailable({ title }: AdminApiUnavailableProps) {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-3xl items-center px-4 py-8 md:px-6">
      <section className="w-full rounded-lg border border-destructive/20 bg-background p-5">
        <p className="text-sm font-medium text-destructive">Admin API unavailable</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          Start the FastAPI service and refresh this page.
        </p>
      </section>
    </main>
  );
}
