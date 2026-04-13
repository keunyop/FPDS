import { cookies } from "next/headers";

export type AdminSession = {
  user: {
    user_id: string;
    email: string;
    role: string;
    display_name: string;
    issued_at: string;
    expires_at: string;
  };
  csrf_token?: string | null;
};

export function getAdminApiOrigin() {
  return process.env.FPDS_ADMIN_API_ORIGIN ?? "http://localhost:4000";
}

export async function fetchAdminSession(): Promise<AdminSession | null> {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const response = await fetch(`${getAdminApiOrigin()}/api/admin/auth/session`, {
    cache: "no-store",
    headers: cookieHeader ? { cookie: cookieHeader } : {}
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Failed to load admin session.");
  }

  const payload = (await response.json()) as {
    data: AdminSession;
  };
  return payload.data;
}
