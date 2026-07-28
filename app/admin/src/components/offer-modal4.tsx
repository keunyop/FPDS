"use client";

import { X } from "lucide-react";
import type { ReactNode } from "react";

import { AdminMark } from "@/components/fpds/admin/admin-mark";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

type OfferModal4Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  width?: "default" | "medium" | "narrow";
  description?: string;
  panelTitle?: string;
  panelDescription?: string;
  panelBadge?: string;
  panelStats?: Array<{
    label: string;
    value: string;
  }>;
  showPanel?: boolean;
  children: ReactNode;
  footer?: ReactNode;
};

function OfferModal4({
  open,
  onOpenChange,
  title,
  width = "default",
  description,
  panelTitle,
  panelDescription,
  panelBadge,
  panelStats = [],
  showPanel = true,
  children,
  footer,
}: OfferModal4Props) {
  return (
    <Dialog onOpenChange={onOpenChange} open={open}>
      <DialogContent
        showCloseButton={false}
        className={cn(
          "group grid max-h-[calc(100dvh-1.5rem)] w-[calc(100vw-1.5rem)] gap-0 overflow-hidden rounded-lg border border-border bg-card p-0 shadow-xl duration-200 data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95 sm:w-[calc(100vw-2.5rem)] lg:max-h-[calc(100dvh-3rem)]",
          showPanel
            ? "sm:max-w-[min(66rem,calc(100vw-2.5rem))] lg:max-w-[min(70rem,calc(100vw-4rem))]"
            : width === "narrow"
              ? "sm:max-w-[min(54rem,calc(100vw-2.5rem))] lg:max-w-[min(58rem,calc(100vw-4rem))]"
              : width === "medium"
                ? "sm:max-w-[min(64rem,calc(100vw-2.5rem))] lg:max-w-[min(68rem,calc(100vw-4rem))]"
              : "sm:max-w-[min(74rem,calc(100vw-2.5rem))] lg:max-w-[min(78rem,calc(100vw-4rem))]",
        )}
      >
        <div className="absolute right-4 top-4 z-20">
          <DialogClose asChild>
            <Button
              aria-label="Close dialog"
              variant="ghost"
              size="icon-sm"
              className="border border-border bg-card text-foreground transition-colors duration-200 hover:bg-muted"
            >
              <X aria-hidden="true" />
              <span className="sr-only">Close dialog</span>
            </Button>
          </DialogClose>
        </div>

        <div className={cn(showPanel ? "lg:grid lg:grid-cols-[18rem_minmax(0,1fr)]" : "")}>
          {showPanel ? (
            <aside
              aria-label="Operation context"
              className="hidden border-r border-sidebar-border bg-sidebar text-sidebar-foreground lg:flex lg:min-h-[34rem] lg:flex-col lg:px-6 lg:py-6"
            >
              <div className="flex items-center justify-between gap-3">
                <AdminMark />
                {panelBadge ? (
                  <span className="border border-sidebar-border bg-sidebar-accent px-2 py-1 text-xs font-medium text-sidebar-primary">
                    {panelBadge}
                  </span>
                ) : null}
              </div>

              <div className="mt-12 space-y-3">
                <p className="text-sm font-medium text-sidebar-foreground/65">
                  FPDS Admin workspace
                </p>
                {panelTitle ? (
                  <h3 className="text-2xl font-semibold leading-tight tracking-tight text-sidebar-foreground">
                    {panelTitle}
                  </h3>
                ) : null}
                {panelDescription ? (
                  <p className="text-sm leading-6 text-sidebar-foreground/70">
                    {panelDescription}
                  </p>
                ) : null}
              </div>

              {panelStats.length > 0 ? (
                <dl className="mt-auto divide-y divide-sidebar-border border-y border-sidebar-border">
                  {panelStats.map((item) => (
                    <div
                      className="grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-3 py-3"
                      key={item.label}
                    >
                      <dt className="text-xs leading-5 text-sidebar-foreground/60">
                        {item.label}
                      </dt>
                      <dd className="text-right text-sm font-semibold tabular-nums text-sidebar-foreground">
                        {item.value}
                      </dd>
                    </div>
                  ))}
                </dl>
              ) : null}
            </aside>
          ) : null}

          <div
            className={cn(
              "min-w-0 space-y-4 overflow-y-auto bg-card px-5 py-5 sm:px-7 sm:py-6 lg:px-8",
              showPanel ? "" : "lg:max-h-[calc(100dvh-3rem)]",
            )}
          >
            <div className="space-y-1.5 pr-10">
              <DialogTitle className="text-balance text-xl font-semibold leading-tight tracking-tight text-foreground sm:text-2xl lg:text-left">
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
              <DialogFooter className="mx-0 mb-0 border-t border-border bg-transparent px-0 pb-0 pt-4 text-left">
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
