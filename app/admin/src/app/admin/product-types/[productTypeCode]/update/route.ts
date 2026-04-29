import { NextResponse } from "next/server";

import { getAdminApiOrigin } from "@/lib/admin-api";

type RouteContext = {
  params: Promise<{ productTypeCode: string }>;
};

export async function PATCH(request: Request, context: RouteContext) {
  const { productTypeCode } = await context.params;
  const apiResponse = await fetch(new URL(`/api/admin/product-types/${encodeURIComponent(productTypeCode)}`, getAdminApiOrigin()), {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...(request.headers.get("cookie") ? { cookie: request.headers.get("cookie") as string } : {}),
      ...(request.headers.get("x-csrf-token") ? { "X-CSRF-Token": request.headers.get("x-csrf-token") as string } : {}),
    },
    body: await request.text(),
    cache: "no-store",
  });

  const text = await apiResponse.text();
  return new NextResponse(text, {
    status: apiResponse.status,
    headers: {
      "Content-Type": apiResponse.headers.get("content-type") ?? "application/json",
    },
  });
}
