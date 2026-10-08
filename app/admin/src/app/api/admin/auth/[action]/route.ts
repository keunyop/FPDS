import { getAdminApiOrigin } from "@/lib/admin-api";
import { proxyAdminAuth } from "@/lib/admin-auth-proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Context = { params: Promise<{ action: string }> };

async function handle(request: Request, { params }: Context) {
  return proxyAdminAuth(request, (await params).action, getAdminApiOrigin);
}

export const GET = handle;
export const POST = handle;
