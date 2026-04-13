"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";

type LogoutButtonProps = {
  apiOrigin: string;
};

export function LogoutButton({ apiOrigin }: LogoutButtonProps) {
  const router = useRouter();
  const [pending, setPending] = useState(false);

  async function handleLogout() {
    setPending(true);
    try {
      await fetch(`${apiOrigin}/api/admin/auth/logout`, {
        method: "POST",
        credentials: "include"
      });
    } finally {
      router.replace("/admin/login");
      router.refresh();
      setPending(false);
    }
  }

  return (
    <Button disabled={pending} onClick={handleLogout} type="button" variant="outline">
      {pending ? "Signing out..." : "Sign out"}
    </Button>
  );
}
