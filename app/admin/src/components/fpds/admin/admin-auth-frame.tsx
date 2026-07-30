import { Suspense, type ReactNode } from "react";

import { AdminLocaleSwitcher } from "@/components/admin-locale-switcher";
import { AdminMark } from "@/components/fpds/admin/admin-mark";
import type { AdminLocale } from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

const FRAME_COPY = {
  en: {
    mode: "Evidence operations",
    thesis: "Control the path from source evidence to public financial records.",
    note: "Authenticated workspace · actions are role-controlled and auditable",
  },
  ko: {
    mode: "증거 기반 운영",
    thesis: "출처 증거에서 공개 금융 기록까지의 흐름을 통제합니다.",
    note: "인증된 작업 공간 · 작업은 권한에 따라 통제되고 감사됩니다",
  },
  ja: {
    mode: "証跡ベースの運用",
    thesis: "ソース証跡から公開金融記録までの流れを統制します。",
    note: "認証済みワークスペース · 操作は権限管理され監査されます",
  },
} as const;

type AdminAuthFrameProps = {
  brand: string;
  children: ReactNode;
  className?: string;
  description: string;
  footer?: ReactNode;
  locale: AdminLocale;
  title: string;
};

export function AdminAuthFrame({
  brand,
  children,
  className,
  description,
  footer,
  locale,
  title,
}: AdminAuthFrameProps) {
  const copy = FRAME_COPY[locale];

  return (
    <section className={cn("min-h-svh overflow-x-hidden bg-background p-3 sm:p-5", className)}>
      <div className="mx-auto grid min-h-[calc(100svh-1.5rem)] w-full min-w-0 max-w-5xl overflow-hidden border border-border bg-card sm:min-h-[calc(100svh-2.5rem)] lg:grid-cols-[0.86fr_1.14fr]">
        <aside className="flex min-w-0 flex-col justify-between bg-sidebar p-6 text-sidebar-foreground sm:p-8 lg:p-10">
          <div>
            <div className="flex items-center gap-3">
              <AdminMark />
              <p className="text-base font-semibold tracking-[-0.02em]">{brand}</p>
            </div>
            <p className="mt-14 text-xs font-semibold text-sidebar-primary">{copy.mode}</p>
            <p className="mt-3 max-w-md break-keep text-2xl font-semibold leading-tight tracking-[-0.025em] sm:text-3xl">
              {copy.thesis}
            </p>
          </div>
          <p className="mt-10 max-w-sm text-xs leading-5 text-sidebar-foreground/60">{copy.note}</p>
        </aside>

        <main className="flex min-w-0 items-center px-5 py-8 sm:px-10 sm:py-12 lg:px-16">
          <div className="mx-auto w-full min-w-0 max-w-md">
            <div className="flex min-w-0 flex-col gap-4 sm:flex-row sm:items-start sm:justify-between sm:gap-5">
              <div className="min-w-0">
                <h1 className="text-2xl font-semibold tracking-[-0.02em] text-foreground">{title}</h1>
                <p className="mt-2 max-w-sm text-sm leading-5 text-muted-foreground">{description}</p>
              </div>
              <Suspense fallback={null}>
                <AdminLocaleSwitcher locale={locale} />
              </Suspense>
            </div>

            <div className="mt-8">{children}</div>
            {footer ? <div className="mt-7 border-t border-border pt-5">{footer}</div> : null}
          </div>
        </main>
      </div>
    </section>
  );
}
