"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

type AdminTableAutoRefreshProps = {
  disabled?: boolean;
  intervalMs?: number;
};

const DEFAULT_INTERVAL_MS = 15_000;

export function AdminTableAutoRefresh({
  disabled = false,
  intervalMs = DEFAULT_INTERVAL_MS,
}: AdminTableAutoRefreshProps) {
  const router = useRouter();

  useEffect(() => {
    if (disabled || intervalMs <= 0) {
      return;
    }

    function canRefresh() {
      if (document.visibilityState !== "visible") {
        return false;
      }

      const activeElement = document.activeElement;
      if (!(activeElement instanceof HTMLElement)) {
        return true;
      }

      return !(
        activeElement.matches("input, select, textarea") ||
        activeElement.isContentEditable
      );
    }

    function refreshVisiblePage() {
      if (canRefresh()) {
        router.refresh();
      }
    }

    const intervalId = window.setInterval(refreshVisiblePage, intervalMs);
    document.addEventListener("visibilitychange", refreshVisiblePage);

    return () => {
      window.clearInterval(intervalId);
      document.removeEventListener("visibilitychange", refreshVisiblePage);
    };
  }, [disabled, intervalMs, router]);

  return null;
}
