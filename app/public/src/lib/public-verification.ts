export type ProductVerification = {
  status: "within_window" | "review_due" | "expired" | "unknown";
  last_verified_at: string | null;
  review_due_at: string | null;
  expires_at: string | null;
  review_interval_days: number | null;
  expiry_days: number | null;
  evaluated_at: string;
};

const COPY = {
  en: {
    checked: "Product last checked", unknownDate: "Unknown", snapshot: "Snapshot generated",
    completed: "Snapshot available", stale: "Snapshot refresh delayed", unavailable: "Snapshot unavailable",
    within_window: "Within review period", review_due: "Recheck due", expired: "Verification expired", unknown: "Verification unknown",
    notice: "Snapshot generation does not recheck bank facts. Confirm current terms with the bank.",
    summary: "Products needing recheck or verification", due: "Recheck by", expiry: "Verification expires",
  },
  ko: {
    checked: "상품 마지막 확인", unknownDate: "알 수 없음", snapshot: "스냅샷 생성",
    completed: "스냅샷 제공 중", stale: "스냅샷 갱신 지연", unavailable: "스냅샷 없음",
    within_window: "확인 주기 이내", review_due: "재확인 필요", expired: "확인 기한 만료", unknown: "확인 상태 알 수 없음",
    notice: "스냅샷 생성은 은행 정보의 재확인이 아닙니다. 최신 조건은 은행에서 확인하세요.",
    summary: "재확인 또는 확인이 필요한 상품", due: "재확인 기한", expiry: "확인 유효 기한",
  },
  ja: {
    checked: "商品の最終確認", unknownDate: "不明", snapshot: "スナップショット生成",
    completed: "スナップショット提供中", stale: "スナップショット更新遅延", unavailable: "スナップショットなし",
    within_window: "確認期間内", review_due: "再確認が必要", expired: "確認期限切れ", unknown: "確認状態不明",
    notice: "スナップショット生成は銀行情報の再確認ではありません。最新条件は銀行で確認してください。",
    summary: "確認または再確認が必要な商品", due: "再確認期限", expiry: "確認の有効期限",
  },
};

export function getVerificationCopy(locale: string) {
  return COPY[locale as keyof typeof COPY] ?? COPY.en;
}

export function verificationDate(value: string | null | undefined, fallback: string) {
  const time = value ? Date.parse(value) : NaN;
  return Number.isFinite(time) ? new Date(time).toISOString().slice(0, 10) : fallback;
}

export function verificationStatus(value?: ProductVerification, now = Date.now()): ProductVerification["status"] {
  if (!value || value.status === "unknown") return "unknown";
  const checked = Date.parse(value.last_verified_at ?? "");
  const due = Date.parse(value.review_due_at ?? "");
  const expiry = Date.parse(value.expires_at ?? "");
  if (![checked, due, expiry, now].every(Number.isFinite) || checked > now || due <= checked || expiry <= due) return "unknown";
  if (now >= expiry || value.status === "expired") return "expired";
  if (now >= due || value.status === "review_due") return "review_due";
  return value.status === "within_window" ? "within_window" : "unknown";
}
