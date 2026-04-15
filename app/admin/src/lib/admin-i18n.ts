export type AdminLocale = "en" | "ko" | "ja";

export const ADMIN_LOCALES = ["en", "ko", "ja"] as const satisfies readonly AdminLocale[];
export const DEFAULT_ADMIN_LOCALE: AdminLocale = "en";

const ADMIN_INTL_LOCALES: Record<AdminLocale, string> = {
  en: "en-CA",
  ko: "ko-KR",
  ja: "ja-JP",
};

const ADMIN_LOCALE_LABELS: Record<AdminLocale, string> = {
  en: "EN",
  ko: "KO",
  ja: "JA",
};

const REVIEW_STATE_LABELS: Record<AdminLocale, Record<string, string>> = {
  en: {
    queued: "Queued",
    approved: "Approved",
    rejected: "Rejected",
    edited: "Edited",
    deferred: "Deferred",
  },
  ko: {
    queued: "대기",
    approved: "승인됨",
    rejected: "반려됨",
    edited: "수정 승인",
    deferred: "보류",
  },
  ja: {
    queued: "保留",
    approved: "承認済み",
    rejected: "却下済み",
    edited: "編集承認",
    deferred: "保留",
  },
};

const RUN_STATE_LABELS: Record<AdminLocale, Record<string, string>> = {
  en: {
    started: "Started",
    completed: "Completed",
    failed: "Failed",
    retried: "Retried",
  },
  ko: {
    started: "시작됨",
    completed: "완료",
    failed: "실패",
    retried: "재시도됨",
  },
  ja: {
    started: "開始済み",
    completed: "完了",
    failed: "失敗",
    retried: "再試行済み",
  },
};

const STAGE_STATUS_LABELS: Record<AdminLocale, Record<string, string>> = {
  en: {
    completed: "Completed",
    degraded: "Degraded",
    failed: "Failed",
    started: "Started",
    retried: "Retried",
  },
  ko: {
    completed: "완료",
    degraded: "성능 저하",
    failed: "실패",
    started: "시작됨",
    retried: "재시도됨",
  },
  ja: {
    completed: "完了",
    degraded: "低下",
    failed: "失敗",
    started: "開始済み",
    retried: "再試行済み",
  },
};

const VALIDATION_STATUS_LABELS: Record<AdminLocale, Record<string, string>> = {
  en: {
    pass: "Pass",
    warning: "Warning",
    error: "Error",
  },
  ko: {
    pass: "통과",
    warning: "경고",
    error: "오류",
  },
  ja: {
    pass: "合格",
    warning: "警告",
    error: "エラー",
  },
};

const CHANGE_TYPE_LABELS: Record<AdminLocale, Record<string, string>> = {
  en: {
    New: "New",
    Updated: "Updated",
    Discontinued: "Discontinued",
    Reclassified: "Reclassified",
    ManualOverride: "Manual override",
  },
  ko: {
    New: "신규",
    Updated: "수정됨",
    Discontinued: "중단됨",
    Reclassified: "재분류됨",
    ManualOverride: "수동 재정의",
  },
  ja: {
    New: "新規",
    Updated: "更新",
    Discontinued: "取扱終了",
    Reclassified: "再分類",
    ManualOverride: "手動上書き",
  },
};

const EVENT_CATEGORY_LABELS: Record<AdminLocale, Record<string, string>> = {
  en: {
    review: "Review",
    run: "Run",
    publish: "Publish",
    auth: "Auth",
    config: "Config",
    usage: "Usage",
  },
  ko: {
    review: "검토",
    run: "실행",
    publish: "게시",
    auth: "인증",
    config: "설정",
    usage: "사용량",
  },
  ja: {
    review: "審査",
    run: "実行",
    publish: "公開",
    auth: "認証",
    config: "設定",
    usage: "使用量",
  },
};

const ACTOR_TYPE_LABELS: Record<AdminLocale, Record<string, string>> = {
  en: {
    user: "User",
    system: "System",
    service: "Service",
    scheduler: "Scheduler",
  },
  ko: {
    user: "사용자",
    system: "시스템",
    service: "서비스",
    scheduler: "스케줄러",
  },
  ja: {
    user: "ユーザー",
    system: "システム",
    service: "サービス",
    scheduler: "スケジューラ",
  },
};

const REVIEW_ACTION_LABELS: Record<AdminLocale, Record<string, string>> = {
  en: {
    approve: "Approve",
    reject: "Reject",
    edit_approve: "Edit & approve",
    defer: "Defer",
  },
  ko: {
    approve: "승인",
    reject: "반려",
    edit_approve: "수정 후 승인",
    defer: "보류",
  },
  ja: {
    approve: "承認",
    reject: "却下",
    edit_approve: "編集して承認",
    defer: "保留",
  },
};

const PRODUCT_TYPE_LABELS: Record<AdminLocale, Record<string, string>> = {
  en: {
    chequing: "Chequing",
    savings: "Savings",
    gic: "GIC",
  },
  ko: {
    chequing: "당좌예금",
    savings: "저축예금",
    gic: "정기예금",
  },
  ja: {
    chequing: "当座預金",
    savings: "普通預金",
    gic: "定期預金",
  },
};

export function normalizeAdminLocale(value: string | string[] | undefined | null): AdminLocale {
  const rawValue = Array.isArray(value) ? value[0] : value;
  const locale = (rawValue ?? "").trim().toLowerCase();
  return ADMIN_LOCALES.includes(locale as AdminLocale) ? (locale as AdminLocale) : DEFAULT_ADMIN_LOCALE;
}

export function resolveAdminLocale(searchParams: Record<string, string | string[] | undefined>): AdminLocale {
  return normalizeAdminLocale(searchParams.locale);
}

export function getAdminLocaleLabel(locale: AdminLocale) {
  return ADMIN_LOCALE_LABELS[locale];
}

export function getAdminIntlLocale(locale: AdminLocale) {
  return ADMIN_INTL_LOCALES[locale];
}

export function setAdminLocale(params: URLSearchParams, locale: AdminLocale) {
  if (locale === DEFAULT_ADMIN_LOCALE) {
    params.delete("locale");
    return params;
  }

  params.set("locale", locale);
  return params;
}

export function buildAdminHref(pathname: string, params: URLSearchParams, locale: AdminLocale) {
  const nextParams = new URLSearchParams(params);
  setAdminLocale(nextParams, locale);
  const query = nextParams.toString();
  return query ? `${pathname}?${query}` : pathname;
}

export function formatAdminDateTime(locale: AdminLocale, value: string | null) {
  if (!value) {
    return localizedMissing(locale);
  }

  return new Intl.DateTimeFormat(getAdminIntlLocale(locale), {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatAdminNumber(locale: AdminLocale, value: number | null, options?: Intl.NumberFormatOptions) {
  if (value === null) {
    return localizedMissing(locale);
  }

  return value.toLocaleString(getAdminIntlLocale(locale), options);
}

export function formatAdminPercent(locale: AdminLocale, value: number | null) {
  if (value === null) {
    return localizedMissing(locale);
  }

  return `${value.toFixed(2)}%`;
}

export function localizedMissing(locale: AdminLocale) {
  switch (locale) {
    case "ko":
      return "없음";
    case "ja":
      return "なし";
    default:
      return "n/a";
  }
}

export function translateReviewState(locale: AdminLocale, value: string) {
  return REVIEW_STATE_LABELS[locale][value] ?? value;
}

export function translateRunState(locale: AdminLocale, value: string) {
  return RUN_STATE_LABELS[locale][value] ?? value;
}

export function translateStageStatus(locale: AdminLocale, value: string) {
  return STAGE_STATUS_LABELS[locale][value] ?? value;
}

export function translateValidationStatus(locale: AdminLocale, value: string) {
  return VALIDATION_STATUS_LABELS[locale][value] ?? value;
}

export function translateChangeType(locale: AdminLocale, value: string) {
  return CHANGE_TYPE_LABELS[locale][value] ?? value;
}

export function translateEventCategory(locale: AdminLocale, value: string) {
  return EVENT_CATEGORY_LABELS[locale][value] ?? value;
}

export function translateActorType(locale: AdminLocale, value: string) {
  return ACTOR_TYPE_LABELS[locale][value] ?? value;
}

export function translateReviewAction(locale: AdminLocale, value: string) {
  return REVIEW_ACTION_LABELS[locale][value] ?? value;
}

export function translateProductType(locale: AdminLocale, value: string) {
  return PRODUCT_TYPE_LABELS[locale][value] ?? value;
}

export function formatAdminBoolean(locale: AdminLocale, value: boolean) {
  if (locale === "ko") {
    return value ? "예" : "아니오";
  }
  if (locale === "ja") {
    return value ? "はい" : "いいえ";
  }
  return value ? "Yes" : "No";
}
