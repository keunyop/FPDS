"use client";

import { AlertTriangle, CheckCircle2, MessageSquareText, X } from "lucide-react";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import {
  getPublicFeedbackCopy,
  type PublicFeedbackCategory,
} from "@/lib/public-locale";
import { cn } from "@/lib/utils";

type PublicFeedbackDialogProps = {
  countryCode: string;
  locale: string;
  mode: "product_error" | "site_feedback";
  product?: {
    bankName: string;
    productId: string;
    productName: string;
  };
  triggerStyle?: "footer" | "notice";
};

const PRODUCT_CATEGORIES: readonly PublicFeedbackCategory[] = [
  "incorrect_rate_or_fee",
  "incorrect_product_details",
  "outdated_information",
  "missing_information",
  "broken_link",
  "other",
];

const SITE_CATEGORIES: readonly PublicFeedbackCategory[] = [
  "content_issue",
  "usability_issue",
  "feature_suggestion",
  "accessibility_issue",
  "other",
];

export function PublicFeedbackDialog({
  countryCode,
  locale,
  mode,
  product,
  triggerStyle = "notice",
}: PublicFeedbackDialogProps) {
  const copy = getPublicFeedbackCopy(locale);
  const categories = mode === "product_error" ? PRODUCT_CATEGORIES : SITE_CATEGORIES;
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<PublicFeedbackCategory | "">("");
  const [details, setDetails] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");

  function handleOpenChange(nextOpen: boolean) {
    if (nextOpen) {
      setCategory("");
      setDetails("");
      setStatus("idle");
    }
    setOpen(nextOpen);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!category || status === "submitting") return;

    setStatus("submitting");
    try {
      const response = await fetch("/api/public/feedback", {
        body: JSON.stringify({
          category,
          country_code: countryCode,
          details,
          locale,
          product_id: mode === "product_error" ? product?.productId : undefined,
          submission_type: mode,
        }),
        headers: { "content-type": "application/json" },
        method: "POST",
      });
      setStatus(response.ok ? "success" : "error");
    } catch {
      setStatus("error");
    }
  }

  const title = mode === "product_error" ? copy.productTitle : copy.siteTitle;
  const triggerLabel = mode === "product_error" ? copy.triggerProduct : copy.triggerSite;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button
          className={cn(
            triggerStyle === "notice" && "min-h-11 w-full rounded-full",
            triggerStyle === "footer" && "min-h-11 min-w-12 px-0 text-background/70 hover:bg-transparent hover:text-background focus-visible:ring-background/45"
          )}
          size="sm"
          variant={triggerStyle === "footer" ? "ghost" : "outline"}
        >
          {mode === "product_error" ? <AlertTriangle aria-hidden="true" /> : <MessageSquareText aria-hidden="true" />}
          {triggerLabel}
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogClose asChild>
          <Button className="absolute right-4 top-4" size="icon-sm" type="button" variant="ghost">
            <X aria-hidden="true" />
            <span className="sr-only">{copy.close}</span>
          </Button>
        </DialogClose>

        {status === "success" && category ? (
          <div className="grid gap-5" role="status">
            <DialogHeader>
              <CheckCircle2 className="size-8 text-verification" aria-hidden="true" />
              <DialogTitle>{copy.successTitle}</DialogTitle>
              <DialogDescription>{copy.successBody}</DialogDescription>
            </DialogHeader>
            <dl className="grid gap-3 rounded-lg border border-border bg-muted/35 p-4">
              {mode === "product_error" && product ? (
                <div>
                  <dt className="text-xs font-medium text-muted-foreground">{copy.productLabel}</dt>
                  <dd className="mt-1 text-sm font-medium">{product.bankName} · {product.productName}</dd>
                </div>
              ) : null}
              <div>
                <dt className="text-xs font-medium text-muted-foreground">{copy.submittedCategory}</dt>
                <dd className="mt-1 text-sm font-medium">{copy.categoryLabels[category]}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium text-muted-foreground">{copy.submittedDetails}</dt>
                <dd className="mt-1 whitespace-pre-wrap text-sm leading-6">{details || copy.noDetails}</dd>
              </div>
            </dl>
            <DialogFooter>
              <DialogClose asChild>
                <Button type="button">{copy.close}</Button>
              </DialogClose>
            </DialogFooter>
          </div>
        ) : (
          <form className="grid gap-5" onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>{title}</DialogTitle>
              <DialogDescription>{copy.privacyNote}</DialogDescription>
            </DialogHeader>

            {mode === "product_error" && product ? (
              <div className="rounded-lg border border-border bg-muted/35 p-3">
                <p className="text-xs font-medium text-muted-foreground">{copy.productLabel}</p>
                <p className="mt-1 text-sm font-medium">{product.bankName} · {product.productName}</p>
              </div>
            ) : null}

            <div className="grid gap-2">
              <label className="text-sm font-medium" htmlFor={"feedback-category-" + mode}>{copy.categoryLabel}</label>
              <select
                className="h-11 w-full rounded-lg border border-input bg-card px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/35"
                id={"feedback-category-" + mode}
                onChange={(event) => setCategory(event.target.value as PublicFeedbackCategory | "")}
                required
                value={category}
              >
                <option value="">{copy.categoryPlaceholder}</option>
                {categories.map((option) => (
                  <option key={option} value={option}>{copy.categoryLabels[option]}</option>
                ))}
              </select>
            </div>

            <div className="grid gap-2">
              <div className="flex items-center justify-between gap-3">
                <label className="text-sm font-medium" htmlFor={"feedback-details-" + mode}>{copy.detailsLabel}</label>
                <span className="font-mono text-xs text-muted-foreground">
                  {copy.detailsCount.replace("{count}", String(details.length))}
                </span>
              </div>
              <Textarea
                id={"feedback-details-" + mode}
                maxLength={2000}
                onChange={(event) => setDetails(event.target.value)}
                placeholder={copy.detailsPlaceholder}
                value={details}
              />
            </div>

            {status === "error" ? (
              <p className="text-sm font-medium text-destructive" role="alert">{copy.error}</p>
            ) : null}

            <DialogFooter>
              <DialogClose asChild>
                <Button disabled={status === "submitting"} type="button" variant="outline">{copy.cancel}</Button>
              </DialogClose>
              <Button disabled={!category || status === "submitting"} type="submit">
                {status === "submitting" ? copy.submitting : copy.submit}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
