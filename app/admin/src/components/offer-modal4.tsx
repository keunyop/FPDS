"use client";

import { Building2, ShieldCheck, Sparkles, X } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog";

type OfferModal4Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  panelTitle: string;
  panelDescription: string;
  panelBadge?: string;
  panelStats?: Array<{
    label: string;
    value: string;
  }>;
  children: ReactNode;
  footer?: ReactNode;
};

function OfferModal4({
  open,
  onOpenChange,
  title,
  description,
  panelTitle,
  panelDescription,
  panelBadge,
  panelStats = [],
  children,
  footer,
}: OfferModal4Props) {
  return (
    <Dialog onOpenChange={onOpenChange} open={open}>
      <DialogContent
        showCloseButton={false}
        className="group grid max-h-[calc(100dvh-2rem)] w-[calc(100vw-1.5rem)] gap-0 overflow-hidden rounded-[1.75rem] border border-border/80 bg-background p-0 shadow-2xl shadow-slate-950/12 data-[state=closed]:slide-out-to-bottom-30 data-[state=open]:slide-in-from-bottom-30 sm:w-[calc(100vw-2.5rem)] sm:max-w-[min(68rem,calc(100vw-2.5rem))] lg:max-h-[calc(100dvh-3rem)] lg:max-w-[min(72rem,calc(100vw-4rem))]"
      >
        <div className="absolute -end-px -top-px">
          <DialogClose asChild>
            <Button
              size="icon-sm"
              className="origin-top-right rounded-bl-2xl rounded-tr-[1.7rem] border border-border/70 bg-background/95 text-foreground shadow-sm transition-all duration-300 hover:bg-muted lg:scale-85 lg:opacity-0 lg:group-hover:scale-100 lg:group-hover:opacity-100 [@media(hover:none)]:scale-100 [@media(hover:none)]:opacity-100"
            >
              <X />
            </Button>
          </DialogClose>
        </div>

        <div className="lg:grid lg:grid-cols-[20rem_minmax(0,1fr)]">
          <div className="relative hidden overflow-hidden bg-[radial-gradient(circle_at_top,_rgb(14_116_144_/_0.24),_transparent_56%),linear-gradient(160deg,#0f172a_0%,#122033_42%,#153047_100%)] text-white lg:flex lg:min-h-[36rem] lg:flex-col lg:justify-between lg:px-8 lg:py-7">
          <div className="absolute inset-0 opacity-35">
            <div className="absolute left-8 top-10 h-28 w-28 rounded-full bg-white/10 blur-2xl" />
            <div className="absolute bottom-8 right-8 h-32 w-32 rounded-full bg-sky-300/20 blur-2xl" />
          </div>

          <div className="relative flex items-center justify-between">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium backdrop-blur-sm">
              <Building2 className="size-3.5" />
              FPDS Admin
            </div>
            {panelBadge ? (
              <div className="inline-flex items-center gap-1 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-xs font-medium text-emerald-100">
                <ShieldCheck className="size-3.5" />
                {panelBadge}
              </div>
            ) : null}
          </div>

          <div className="relative space-y-4">
            <div className="inline-flex size-12 items-center justify-center rounded-2xl bg-white/10 text-white backdrop-blur-sm">
              <Sparkles className="size-5" />
            </div>
            <div className="space-y-3">
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-white/70">
                FPDS Workspace
              </p>
              <h3 className="text-3xl font-semibold tracking-tight text-white">
                {panelTitle}
              </h3>
              <p className="text-sm leading-7 text-white/72">
                {panelDescription}
              </p>
            </div>
          </div>

          {panelStats.length > 0 ? (
            <div className="relative grid gap-3">
              {panelStats.map((item) => (
                <div
                  className="rounded-2xl border border-white/10 bg-white/8 px-4 py-3 backdrop-blur-sm"
                  key={item.label}
                >
                  <p className="text-xs uppercase tracking-[0.16em] text-white/60">
                    {item.label}
                  </p>
                  <p className="mt-2 text-lg font-semibold text-white">
                    {item.value}
                  </p>
                </div>
              ))}
            </div>
          ) : null}
          </div>

          <div className="min-w-0 space-y-4 overflow-y-auto bg-card/96 px-5 py-5 sm:px-7 sm:py-6 lg:px-8 lg:py-7">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-muted/60 px-3 py-1 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground lg:hidden">
                <Building2 className="size-3.5" />
                FPDS Admin
              </div>
              <DialogTitle className="text-balance text-2xl font-semibold tracking-tight text-foreground sm:text-3xl lg:text-left">
              {title}
              </DialogTitle>
              {description ? (
                <DialogDescription className="max-w-2xl text-sm leading-6 text-muted-foreground lg:text-left">
                  {description}
                </DialogDescription>
              ) : null}
            </div>

            <div className="space-y-2.5">{children}</div>

            {footer ? (
              <DialogFooter className="border-t border-border/70 pt-4 text-left">
                {footer}
              </DialogFooter>
            ) : null}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export { OfferModal4 };
