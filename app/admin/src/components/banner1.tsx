"use client";

import { X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type BannerTone = "info" | "warning" | "success";

interface Banner1Props {
  title: string;
  description: string;
  linkText?: string;
  linkUrl?: string;
  tone?: BannerTone;
  defaultVisible?: boolean;
  dismissible?: boolean;
  className?: string;
}

const toneClassMap = {
  info: "border-info/20 bg-info-soft text-info",
  warning: "border-warning/20 bg-warning-soft text-warning",
  success: "border-success/20 bg-success-soft text-success"
} satisfies Record<BannerTone, string>;

const Banner1 = ({
  title,
  description,
  linkText,
  linkUrl,
  tone = "info",
  defaultVisible = true,
  dismissible = true,
  className
}: Banner1Props) => {
  const [isVisible, setIsVisible] = useState(defaultVisible);

  if (!isVisible) {
    return null;
  }

  return (
    <section className={cn("rounded-2xl border px-4 py-3 shadow-sm", toneClassMap[tone], className)}>
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <p className="text-sm font-medium">{title}</p>
          <p className="text-sm leading-6">
            {description}
            {linkText && linkUrl ? (
              <>
                {" "}
                <a className="font-medium underline underline-offset-2" href={linkUrl}>
                  {linkText}
                </a>
                .
              </>
            ) : null}
          </p>
        </div>

        {dismissible ? (
          <Button className="h-8 w-8 shrink-0" onClick={() => setIsVisible(false)} size="icon" type="button" variant="ghost">
            <X className="h-4 w-4" />
          </Button>
        ) : null}
      </div>
    </section>
  );
};

export { Banner1 };
