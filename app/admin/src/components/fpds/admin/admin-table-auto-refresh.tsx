"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

type AdminTableAutoRefreshProps = {
  disabled?: boolean;
  intervalMs?: number;
  locale?: Locale;
};

type Locale = "en" | "ko" | "ja";

type PauseReason =
  | "busy"
  | "dialog"
  | "dirty"
  | "editing"
  | "hidden"
  | null;

const DEFAULT_INTERVAL_MS = 15_000;

const copy = {
  en: {
    active: "Auto refresh live",
    disabled: "Auto refresh off",
    lastRefresh: "Last refresh",
    paused: "Auto refresh paused",
    reasons: {
      busy: "an operation is in progress",
      dialog: "a dialog is open",
      dirty: "unsaved changes",
      editing: "editing in progress",
      hidden: "window is not visible",
    },
    waiting: "Waiting for first refresh",
  },
  ko: {
    active: "자동 새로고침 작동 중",
    disabled: "자동 새로고침 꺼짐",
    lastRefresh: "마지막 새로고침",
    paused: "자동 새로고침 일시정지",
    reasons: {
      busy: "작업 처리 중",
      dialog: "대화상자 열림",
      dirty: "저장되지 않은 변경사항",
      editing: "입력 중",
      hidden: "창이 보이지 않음",
    },
    waiting: "첫 새로고침 대기 중",
  },
  ja: {
    active: "自動更新中",
    disabled: "自動更新オフ",
    lastRefresh: "最終更新",
    paused: "自動更新を一時停止",
    reasons: {
      busy: "処理を実行中",
      dialog: "ダイアログを表示中",
      dirty: "未保存の変更あり",
      editing: "入力中",
      hidden: "ウィンドウが非表示",
    },
    waiting: "最初の更新を待機中",
  },
} satisfies Record<
  Locale,
  {
    active: string;
    disabled: string;
    lastRefresh: string;
    paused: string;
    reasons: Record<Exclude<PauseReason, null>, string>;
    waiting: string;
  }
>;

function readLocale(): Locale {
  const queryLocale = new URLSearchParams(window.location.search).get("locale");
  if (queryLocale === "ko" || queryLocale === "ja" || queryLocale === "en") {
    return queryLocale;
  }

  const language = document.documentElement.lang.toLowerCase();
  if (language.startsWith("ko")) {
    return "ko";
  }
  if (language.startsWith("ja")) {
    return "ja";
  }
  return "en";
}

function getPauseReason(): PauseReason {
  if (document.visibilityState !== "visible") {
    return "hidden";
  }

  if (
    document.querySelector(
      '[role="dialog"][data-state="open"], [data-slot="dialog-content"][data-state="open"]',
    )
  ) {
    return "dialog";
  }

  if (document.querySelector('[aria-busy="true"]')) {
    return "busy";
  }

  if (
    document.querySelector(
      [
        '[data-admin-dirty="true"]',
        '[data-dirty="true"]',
        '[data-admin-mutation="pending"]',
        '[data-admin-mutation-pending="true"]',
        '[data-mutation-pending="true"]',
      ].join(", "),
    )
  ) {
    return "dirty";
  }

  const activeElement = document.activeElement;
  if (
    activeElement instanceof HTMLElement &&
    (activeElement.matches("input, select, textarea, [role='combobox']") ||
      activeElement.isContentEditable)
  ) {
    return "editing";
  }

  return null;
}

export function AdminTableAutoRefresh({
  disabled = false,
  intervalMs = DEFAULT_INTERVAL_MS,
  locale: requestedLocale,
}: AdminTableAutoRefreshProps) {
  const router = useRouter();
  const [lastRefreshAt, setLastRefreshAt] = useState<Date | null>(null);
  const [locale, setLocale] = useState<Locale>(requestedLocale ?? "en");
  const [pauseReason, setPauseReason] = useState<PauseReason>(null);

  useEffect(() => {
    setLocale(requestedLocale ?? readLocale());
    setLastRefreshAt(new Date());

    function updateStatus() {
      setPauseReason(getPauseReason());
    }

    function requestRefresh() {
      const nextPauseReason = getPauseReason();
      setPauseReason(nextPauseReason);
      if (nextPauseReason === null) {
        router.refresh();
        setLastRefreshAt(new Date());
      }
    }

    updateStatus();

    if (disabled || intervalMs <= 0) {
      return;
    }

    const intervalId = window.setInterval(requestRefresh, intervalMs);
    const mutationObserver = new MutationObserver(updateStatus);
    mutationObserver.observe(document.body, {
      attributeFilter: [
        "aria-busy",
        "contenteditable",
        "data-admin-dirty",
        "data-admin-mutation",
        "data-admin-mutation-pending",
        "data-dirty",
        "data-mutation-pending",
        "data-state",
      ],
      attributes: true,
      childList: true,
      subtree: true,
    });

    function handleFocusChange() {
      window.setTimeout(updateStatus, 0);
    }

    function handleVisibilityChange() {
      if (document.visibilityState === "visible") {
        requestRefresh();
      } else {
        updateStatus();
      }
    }

    document.addEventListener("focusin", handleFocusChange);
    document.addEventListener("focusout", handleFocusChange);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      window.clearInterval(intervalId);
      mutationObserver.disconnect();
      document.removeEventListener("focusin", handleFocusChange);
      document.removeEventListener("focusout", handleFocusChange);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [disabled, intervalMs, requestedLocale, router]);

  const messages = copy[locale];
  const isDisabled = disabled || intervalMs <= 0;
  const stateLabel = isDisabled
    ? messages.disabled
    : pauseReason
      ? messages.paused
      : messages.active;
  const detail = isDisabled
    ? null
    : pauseReason
      ? messages.reasons[pauseReason]
      : `${Math.max(1, Math.round(intervalMs / 1_000))}s`;
  const formattedLastRefresh = useMemo(() => {
    if (!lastRefreshAt) {
      return messages.waiting;
    }

    return `${messages.lastRefresh} ${new Intl.DateTimeFormat(
      locale === "ko" ? "ko-KR" : locale === "ja" ? "ja-JP" : "en-CA",
      {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      },
    ).format(lastRefreshAt)}`;
  }, [lastRefreshAt, locale, messages.lastRefresh, messages.waiting]);

  return (
    <div className="-mb-4 flex min-h-8 justify-end">
      <span aria-atomic="true" aria-live="polite" className="sr-only" role="status">
        {stateLabel}
        {detail ? `: ${detail}` : ""}
      </span>
      <div className="inline-flex min-h-8 max-w-full flex-wrap items-center justify-end gap-x-2 gap-y-1 border border-border bg-card px-2.5 py-1 text-xs text-muted-foreground">
        <span
          aria-hidden="true"
          className={
            isDisabled
              ? "size-1.5 shrink-0 bg-muted-foreground"
              : pauseReason
                ? "size-1.5 shrink-0 bg-warning"
                : "size-1.5 shrink-0 bg-success"
          }
        />
        <span className="font-medium text-foreground">{stateLabel}</span>
        {detail ? <span>· {detail}</span> : null}
        <span className="border-l border-border pl-2">
          {formattedLastRefresh}
        </span>
      </div>
    </div>
  );
}
