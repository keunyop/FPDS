"use client";

import { AlertTriangle } from "lucide-react";

import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";

type DestructiveConfirmDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel: string;
  cancelLabel?: string;
  pending?: boolean;
  onConfirm: () => void | Promise<void>;
};

export function DestructiveConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  cancelLabel = "Cancel",
  pending = false,
  onConfirm,
}: DestructiveConfirmDialogProps) {
  return (
    <AlertDialog onOpenChange={onOpenChange} open={open}>
      <AlertDialogContent>
        <div className="flex items-start gap-4">
          <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-destructive/12 text-destructive">
            <AlertTriangle className="size-5" />
          </div>
          <AlertDialogHeader className="gap-3">
            <div className="inline-flex w-fit items-center rounded-full border border-destructive/15 bg-destructive/8 px-3 py-1 text-[0.7rem] font-medium uppercase tracking-[0.18em] text-destructive">
              Delete confirmation
            </div>
            <div className="space-y-2">
              <AlertDialogTitle>{title}</AlertDialogTitle>
              <AlertDialogDescription>{description}</AlertDialogDescription>
            </div>
          </AlertDialogHeader>
        </div>

        <div className="rounded-2xl border border-destructive/15 bg-destructive/6 px-4 py-3 text-sm leading-6 text-muted-foreground">
          This action is destructive and cannot be undone after it completes.
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={pending}>{cancelLabel}</AlertDialogCancel>
          <Button disabled={pending} onClick={() => void onConfirm()} type="button" variant="destructive">
            {pending ? "Deleting..." : confirmLabel}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
