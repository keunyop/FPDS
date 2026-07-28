"use client";

import { RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function AdminError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-svh items-center justify-center bg-background px-4 py-8">
      <section className="w-full max-w-2xl border border-destructive/30 bg-card p-6 md:p-8" role="alert">
        <p className="text-xs font-semibold text-destructive">ADMIN RENDER ERROR</p>
        <h1 className="mt-3 text-2xl font-semibold tracking-[-0.02em] text-foreground">This Admin view could not be loaded.</h1>
        <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">
          Retry the view. If the problem continues, check the API service and the related run or audit log.
        </p>
        {error.digest ? <p className="mt-4 font-mono text-xs text-muted-foreground">Reference {error.digest}</p> : null}
        <Button className="mt-6" onClick={reset} type="button">
          <RotateCcw className="h-4 w-4" aria-hidden="true" />
          Retry view
        </Button>
      </section>
    </main>
  );
}
