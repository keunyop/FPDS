import type { AdminLocale } from "@/lib/admin-i18n";

type AdminApiUnavailableProps = {
  locale?: AdminLocale;
  title: string;
};

const API_COPY = {
  en: {
    label: "Admin API unavailable",
    description: "Start the FastAPI service and refresh this page.",
  },
  ko: {
    label: "Admin API를 사용할 수 없습니다",
    description: "FastAPI 서비스를 시작한 뒤 이 페이지를 새로고침하세요.",
  },
  ja: {
    label: "Admin API を利用できません",
    description: "FastAPI サービスを起動してから、このページを再読み込みしてください。",
  },
} as const;

export function AdminApiUnavailable({ locale = "en", title }: AdminApiUnavailableProps) {
  const copy = API_COPY[locale];
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-3xl items-center px-4 py-8 md:px-6">
      <section className="w-full rounded-lg border border-destructive/20 bg-background p-5">
        <p className="text-sm font-medium text-destructive">{copy.label}</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          {copy.description}
        </p>
      </section>
    </main>
  );
}
